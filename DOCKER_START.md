# Docker Compose Startup & Troubleshooting Guide

## Quick Start (After Fixes Applied)

```bash
cd /workspaces/ai-gate

# Step 1: Verify local environment
python3 tests/run_tests.sh

# Step 2: Build Docker images
docker compose build --no-cache

# Step 3: Start services
docker compose up
```

## Fixes Applied (See DOCKER_DEBUG.md for Details)

✅ **Import Fixes**: All relative imports in ssh-gw/wrappers now use `.base` syntax
✅ **Package Fixes**: Added __init__.py files to packages
✅ **Module Entry Point**: Created gatewayd/__main__.py
✅ **Docker-Compose**: Updated to use direct python command
✅ **Configuration**: Created config/gateway.yaml
✅ **SSH Gateway**: Simplified Dockerfile to avoid startup issues
✅ **Syntax**: All Python files validated for syntax errors

## Troubleshooting

### Issue 1: "No module named 'base'"
**Solution**: This is fixed by using relative imports (`.base`). All wrappers updated.

### Issue 2: Docker build fails with "COPY failed"
**Solution**: Ensure Dockerfiles reference correct paths from project root.

### Issue 3: Flask not found
**Solution**: Dependency is in requirements.txt and will be installed during `docker compose build`.

### Issue 4: Port 5000 already in use
**Solution**: 
```bash
docker compose down
sleep 2
docker compose up
```

### Issue 5: Git error on startup
**Solution**: This may be from earlier. Simply run docker-compose again:
```bash
docker compose --version  # Verify docker-compose works
docker compose up
```

## Manual Testing (Without Docker)

If Docker has issues, you can still test the Python code:

```bash
# Install dependencies
pip install -r requirements.txt

# Run syntax validation
python3 validate_syntax.py

# Run unit tests
bash tests/run_tests.sh

# Test imports
python3 -c "
from gatewayd.app import create_app
app = create_app()
print('✓ App created successfully')
with app.app_context():
    with app.test_client() as client:
        response = client.get('/health')
        print(f'✓ Health endpoint: {response.status_code}')
"
```

## Docker-Compose Step-by-Step

### 1. Build Phase
```bash
docker compose build --no-cache
```
This will:
- Download base Python image (python:3.11-slim)
- Install system dependencies (curl, git, aws-cli, etc.)
- Install Python packages from requirements.txt
- Copy code and config files
- Build three images: gateway, ssh-gw, agent

### 2. Start Phase
```bash
docker compose up
```
This will:
- Create three containers from the images
- Start gatewayd on port 5000
- Start ssh-gw on port 2222
- Start agent (tail -f /dev/null to keep running)
- Create ai-gate network for inter-container communication

### 3. Test Phase (In another terminal)
```bash
# Create session
python3 examples/create_session.py

# Test health
curl http://localhost:5000/health

# Full test
export TOKEN=$(python3 examples/create_session.py | grep "session_token" | jq -r .session_token)
python3 examples/read_request.py  # Should work immediately
python3 examples/write_request.py # Should require approval
```

## Logs & Debugging

### View logs
```bash
docker compose logs -f  # All services
docker compose logs -f gatewayd  # Just gateway
docker compose logs -f agent  # Just agent
```

### Attach to container
```bash
docker compose exec gatewayd bash
docker compose exec agent bash
```

### Clean rebuild
```bash
docker compose down -v  # Remove everything
docker compose build --no-cache  # Clean rebuild
docker compose up  # Start fresh
```

## Expected Success

When `docker compose up` works:
1. You should see log output from all three services
2. Gateway logs should show "Running on http://0.0.0.0:5000"
3. No error messages about imports or syntax
4. Services should stay running (Ctrl+C to stop)

From another terminal:
- `curl http://localhost:5000/health` returns 200 OK
- `python3 examples/create_session.py` returns a session token
- `python3 examples/read_request.py` makes successful API calls

## Key Files to Check if Issues Persist

| File | Purpose | Status |
|------|---------|--------|
| gatewayd/app.py | Main Flask app | ✅ No syntax errors |
| gatewayd/__main__.py | Module entry point | ✅ Created |
| gatewayd/policy.py | Policy engine | ✅ No syntax errors |
| gatewayd/auth.py | Session mgmt | ✅ No syntax errors |
| gatewayd/credentials.py | Credential broker | ✅ No syntax errors |
| gatewayd/approvals.py | Approval orchestrator | ✅ No syntax errors |
| gatewayd/proxy.py | HTTP proxy | ✅ No syntax errors |
| ssh-gw/dispatcher.py | SSH routing | ✅ No syntax errors |
| ssh-gw/wrappers/base.py | Wrapper base | ✅ No syntax errors |
| ssh-gw/wrappers/__init__.py | Package init | ✅ Created |
| config/gateway.yaml | Gateway config | ✅ Created |
| requirements.txt | Python dependencies | ✅ Valid |
| Dockerfile.gatewayd | Gateway image | ✅ Valid |
| Dockerfile.ssh-gw | SSH image | ✅ Simplified |
| Dockerfile.agent | Agent image | ✅ Valid |
| docker-compose.yml | Compose config | ✅ Valid |

## Success Criteria

✅ `docker compose build` completes without errors
✅ `docker compose up` starts all three services
✅ No Python import/syntax errors in logs
✅ Gateway health endpoint responds
✅ Session creation works
✅ Read requests complete
✅ Write requests block for approval
✅ Unit tests all pass

If all these are true: **Implementation is working correctly!**
