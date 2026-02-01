# Troubleshooting Guide

## Common Issues

### 1. Cannot Connect to Gateway

**Symptom:** `Connection refused` or `Failed to connect to http://localhost:5000`

**Solutions:**
```bash
# Check if gateway is running
docker-compose ps
# Output should show gatewayd running

# If not running, start it
docker-compose up -d gatewayd

# Check logs
docker-compose logs gatewayd

# If port conflict, change in docker-compose.yml
# ports:
#   - "5001:5000"  # Changed from 5000:5000
```

### 2. Session Token Invalid/Expired

**Symptom:** `{"error": "Invalid or expired session"}`

**Solutions:**
```bash
# Create a new session
python examples/create_session.py

# This returns a fresh token valid for 1 hour
# export GATEWAY_SESSION_TOKEN=<new_token>

# Or increase TTL in gatewayd/app.py
ttl_seconds = 86400  # 24 hours instead of 3600
```

### 3. Credentials Not Found

**Symptom:** `{"error": "Failed to retrieve credentials"}`

**Solutions:**
```bash
# 1. Verify credentials file exists
cat config/credentials.json

# 2. Check selector format is correct
# Should be: tenant_id:provider:credential_name
# Example: default:github:personal

# 3. Verify selector is in credentials.json
grep "default:github:personal" config/credentials.json

# 4. Initialize test credentials
python config/init_credentials.py

# 5. Enable DEBUG logging
export LOG_LEVEL=DEBUG
docker-compose restart gatewayd
```

### 4. Approval Request Blocks Forever

**Symptom:** Request hangs, never returns, eventually times out

**Solutions:**
```bash
# 1. Check approval exists
python examples/approval_example.py check <approval_id>

# 2. Check gateway logs for approval creation
docker-compose logs gatewayd | grep "Approval request"

# 3. Manually approve
python examples/approval_example.py approve <approval_id>

# 4. If still hung, restart gateway
docker-compose restart gatewayd
# WARNING: This cancels all pending approvals

# 5. Increase timeout for testing
# In gatewayd/app.py:
# approved = approval_orchestrator.wait_for_approval(
#     approval_id, timeout_seconds=7200  # 2 hours
# )
```

### 5. SSH Gateway Not Accessible

**Symptom:** `ssh: connect to host localhost port 2222: Connection refused`

**Solutions:**
```bash
# Check SSH gateway is running
docker-compose ps ssh-gw

# If not, start it
docker-compose up -d ssh-gw

# Check logs
docker-compose logs ssh-gw

# Test connectivity
nc -zv localhost 2222

# SSH requires ForceCommand setup, for testing:
# Use HTTP proxy instead:
export GATEWAY_SESSION_TOKEN=<token>
python examples/read_request.py
```

### 6. Credential Injection Not Working

**Symptom:** CLI command fails with auth error despite having credentials

**Solutions:**
```bash
# 1. Verify credentials have required fields
# For AWS: access_key, secret_key
# For GitHub: token
# For GCP: credentials_json (path) or bearer_token

# 2. Check wrapper is injecting correctly
# Add debug to ssh-gw/wrappers/base.py:
print(f"Credentials keys: {credentials.keys()}", file=sys.stderr)

# 3. Verify environment variable names
# AWS wrapper sets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# GitHub wrapper sets: GH_TOKEN

# 4. Test credential fetch directly
# In gatewayd, add debug logging:
logger.debug(f"Credentials: {credentials}")  # Will show in logs
```

### 7. Policy Classification Wrong

**Symptom:** Read operation treated as write (or vice versa)

**Solutions:**
```bash
# 1. Check policy.json mode
cat config/policies.json

# 2. Test classification directly
python -c "
from gatewayd.policy import PolicyEngine
p = PolicyEngine()
result = p.classify_cli_command('aws', 'put-object')
print(f'Result: {result}')
"

# 3. Add custom classification rule
# In config/policies.json:
{
  "default": {
    "mode": "strict",
    "exceptions": [
      {
        "provider": "aws",
        "methods": ["PUT"],
        "paths": ["/logging/*"]
      }
    ]
  }
}

# 4. Review heuristics in gatewayd/policy.py
# Adjust keywords if needed
```

### 8. Docker Build Failures

**Symptom:** `docker-compose up` fails with build errors

**Solutions:**
```bash
# 1. Clean and rebuild
docker-compose down
docker-compose build --no-cache

# 2. Check Python version
# Dockerfile uses python:3.11-slim
# If you need different version, edit Dockerfile.gatewayd

# 3. Check internet connectivity
# Docker needs to download base image and packages
docker pull python:3.11-slim

# 4. Check requirements.txt syntax
cat requirements.txt

# 5. Increase Docker memory if build fails
# Docker Desktop settings → Resources → Memory
```

### 9. Cannot Write to Config Files

**Symptom:** `Permission denied` when writing credentials

**Solutions:**
```bash
# 1. Check file permissions
ls -la config/

# 2. Make writable
chmod 644 config/*.json

# 3. If running in Docker, check mount permissions
# May need to run as root or adjust volume permissions

# 4. Verify directory is writable
touch config/test.txt
rm config/test.txt
```

### 10. Logs Not Showing

**Symptom:** No output from `docker-compose logs`

**Solutions:**
```bash
# 1. Check log level
export LOG_LEVEL=DEBUG
docker-compose restart gatewayd

# 2. View current logs
docker-compose logs -f --tail=50 gatewayd

# 3. Check container is running
docker ps | grep gatewayd

# 4. Access container directly
docker exec -it ai-gate-gateway bash
python -m gatewayd.app

# 5. Capture stdout/stderr to file
docker-compose up gatewayd > /tmp/gateway.log 2>&1
```

## Testing Tools

### cURL Examples

```bash
# Create session
curl -X POST http://localhost:5000/session/new \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"default","enrollment_secret":"test-secret-123"}'

# Health check
curl http://localhost:5000/health

# Make read request
curl -X GET http://localhost:5000/api/v1/proxy/user \
  -H "Authorization: Bearer <token>" \
  -H "X-Provider: github" \
  -H "X-Creds: default:github:personal"

# Check approval status
curl http://localhost:5000/approvals/<approval_id>/status \
  -H "Authorization: Bearer <token>"
```

### Python Testing

```python
import requests

# Create session
r = requests.post("http://localhost:5000/session/new", json={
    "tenant_id": "default",
    "enrollment_secret": "test-secret-123"
})
token = r.json()["session_token"]

# Test read request
r = requests.get("http://localhost:5000/api/v1/proxy/user", headers={
    "Authorization": f"Bearer {token}",
    "X-Provider": "github",
    "X-Creds": "default:github:personal"
})
print(r.status_code, r.json())
```

## Emergency Recovery

### Kill All Running Gateways

```bash
docker-compose down
docker kill $(docker ps -q --filter ancestor=ai-gate-gateway)
```

### Reset All State

```bash
# Completely clean slate
docker-compose down -v  # Remove volumes
rm config/credentials.json config/enrollments.json
docker-compose up -d
python config/init_credentials.py
```

### Access Container Shell

```bash
# Debug gateway
docker exec -it ai-gate-gateway bash
python -m pdb gatewayd/app.py

# Debug SSH gateway
docker exec -it ai-gate-ssh bash

# Debug agent
docker exec -it ai-gate-agent bash
```

## Getting Help

1. Check logs: `docker-compose logs -f`
2. Review ARCHITECTURE.md for request flow
3. Check DEVELOPMENT.md for setup
4. Search GitHub issues
5. Enable DEBUG logging and review output

