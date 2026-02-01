# Development Guide

## Project Structure

```
ai-gate/
├── gatewayd/                 # HTTP gateway service
│   ├── app.py               # Flask application entry point
│   ├── auth.py              # Session management
│   ├── proxy.py             # HTTP forward proxy
│   ├── credentials.py       # Credential broker
│   ├── policy.py            # Policy engine & classification
│   └── approvals.py         # Approval orchestrator
├── ssh-gw/                  # SSH gateway service
│   ├── dispatcher.py        # SSH command dispatcher
│   └── wrappers/            # CLI command wrappers
│       ├── base.py          # Base wrapper class
│       ├── aws_wrapper.py
│       ├── gh_wrapper.py
│       ├── terraform_wrapper.py
│       ├── kubectl_wrapper.py
│       ├── gcloud_wrapper.py
│       ├── curl_wrapper.py
│       ├── datadog_wrapper.py
│       └── linear_wrapper.py
├── config/                  # Configuration files
│   ├── policies.json        # Security policies
│   ├── credentials.json     # Credential storage
│   └── enrollments.json     # Tenant enrollment secrets
├── examples/                # Example usage scripts
├── tests/                   # Test suite
├── docker-compose.yml       # Local development environment
├── requirements.txt         # Python dependencies
└── DESIGN.md               # Architecture & rationale
```

## Development Workflow

### 1. Local Setup

```bash
# Clone repository
git clone https://github.com/peterwwillis/ai-gate.git
cd ai-gate

# Create Python environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Install dependencies
pip install -r requirements.txt

# Initialize test credentials
python config/init_credentials.py
```

### 2. Run Services Locally

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d
docker-compose logs -f gatewayd
```

**Option B: Manual (for debugging)**
```bash
# Terminal 1: Gateway
cd gatewayd
export FLASK_ENV=development
python -m flask run --port 5000

# Terminal 2: Tests/Examples
cd examples
python create_session.py
```

### 3. Testing

```bash
# Run all tests
bash tests/run_tests.sh

# Run specific test
python -m pytest tests/test_policy.py -v

# Run with coverage
pip install coverage pytest
coverage run -m pytest tests/
coverage report
```

## Adding a New CLI Wrapper

**Example: Adding a new provider (e.g., `pulumi`)**

1. Create wrapper file:

```python
# ssh-gw/wrappers/pulumi_wrapper.py
import sys
from base import CLIWrapper, ActionType

class PulumiWrapper(CLIWrapper):
    COMMAND_NAME = "pulumi"
    
    def classify_action(self) -> ActionType:
        """Classify pulumi command as read or write."""
        if not self.args:
            return ActionType.READ
        
        subcommand = self.args[0].lower()
        
        # Mutating operations
        if subcommand in ["up", "destroy", "refresh"]:
            return ActionType.WRITE
        
        return ActionType.READ
    
    def _inject_credentials(self, env, credentials):
        if "api_token" in credentials:
            env["PULUMI_ACCESS_TOKEN"] = credentials["api_token"]

def main():
    wrapper = PulumiWrapper(sys.argv[1:])
    return wrapper.run()

if __name__ == "__main__":
    sys.exit(main())
```

2. Register in dispatcher:

```python
# ssh-gw/dispatcher.py
ALLOWED_COMMANDS = {
    # ... existing ...
    "pulumi": "pulumi_wrapper.py",
}
```

3. Add credentials to config:

```json
{
  "default:pulumi:prod": {
    "type": "pulumi_token",
    "api_token": "..."
  }
}
```

4. Test:

```bash
# Start gateway
docker-compose up -d

# Create session
export GATEWAY_SESSION_TOKEN=$(python examples/create_session.py | grep Token | awk '{print $NF}')

# Test via SSH
ssh -p 2222 localhost pulumi stack
```

## Extending the Policy Engine

**Add custom exception:**

```json
{
  "default": {
    "mode": "cautious",
    "exceptions": [
      {
        "provider": "aws",
        "methods": ["POST"],
        "paths": ["/s3/buckets/my-logs/*"]
      }
    ]
  }
}
```

## Integrating Credential Storage

Replace JSON with 1Password/Vault:

```python
# gatewayd/credentials.py
def load_from_1password(self, tenant_id: str, selector: str):
    """Load from 1Password CLI."""
    import subprocess
    
    result = subprocess.run(
        ["op", "read", f"op://vault/{selector}"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None
```

## Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
docker-compose up gatewayd
```

### Inspect Request/Response

```python
# Add to gatewayd/app.py
@app.before_request
def log_request_details():
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(f"Body: {request.get_data()}")
```

### Test Approval Flow

```bash
# Terminal 1: Create write request
export GATEWAY_SESSION_TOKEN=<token>
python examples/write_request.py
# Copy approval_id from output

# Terminal 2: Check status
python examples/approval_example.py check <approval_id>

# Terminal 3: Approve
python examples/approval_example.py approve <approval_id>

# Original request should complete
```

## Common Issues

### Session token expired
```bash
# Create new session
python examples/create_session.py
export GATEWAY_SESSION_TOKEN=<new_token>
```

### Gateway not responding
```bash
# Check if running
docker-compose ps

# View logs
docker-compose logs gatewayd

# Restart
docker-compose restart gatewayd
```

### Credentials not found
- Check `config/credentials.json` has entry
- Verify selector format: `tenant:provider:name`
- Enable DEBUG logging to see credential lookup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run `bash tests/run_tests.sh`
5. Submit pull request

## Release Checklist

- [ ] Update version in `gatewayd/__init__.py`
- [ ] Update CHANGELOG
- [ ] Run full test suite
- [ ] Build Docker images
- [ ] Tag release
- [ ] Push to registry
