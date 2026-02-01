# Getting Started with AI-GATE

## Quick Start

### 1. Initialize Test Credentials

```bash
python config/init_credentials.py
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- `gatewayd` on port 5000
- `ssh-gw` (SSH gateway) on port 2222
- `agent` container for testing

### 3. Create a Session

```bash
python examples/create_session.py
```

This returns a `GATEWAY_SESSION_TOKEN`. Export it:

```bash
export GATEWAY_SESSION_TOKEN=<token>
```

### 4. Make Requests

**Read request (no approval needed):**
```bash
python examples/read_request.py
```

**Write request (requires approval):**
```bash
python examples/write_request.py
```

When a write request is made, you'll see the approval ID. In another terminal:

```bash
python examples/approval_example.py approve <approval_id>
```

## Architecture

### gatewayd (HTTP Proxy)

The central gateway service:
- **HTTP Forward Proxy**: Routes requests, classifies read/write
- **Approval Orchestrator**: Manages approval requests and notifications
- **Credential Broker**: Loads and injects credentials
- **Policy Engine**: Determines if approval is required

**Key endpoints:**
- `POST /session/new` - Create agent session
- `GET /api/v1/proxy/<path>` - Make proxied request
- `POST /approvals/<id>/approve` - Approve request
- `POST /approvals/<id>/deny` - Deny request
- `GET /approvals/<id>/status` - Check approval status

### ssh-gw (SSH Gateway)

Restricted SSH with CLI wrappers:
- Runs `sshd` with `ForceCommand` (no shell access)
- Routes to command-specific wrappers
- Wrappers classify commands, request approval, inject credentials

**Supported commands:**
- `aws` - AWS CLI
- `gcloud` - Google Cloud CLI
- `gh` - GitHub CLI
- `terraform` - Terraform
- `kubectl` - Kubernetes CLI
- `datadog` - Datadog CLI
- `linear` - Linear CLI
- `curl` - curl

## Configuration

### Policies (`config/policies.json`)

Define security mode (Strict/Cautious) and exceptions:

```json
{
  "default": {
    "mode": "strict",
    "exceptions": []
  }
}
```

- **Strict**: All writes require approval
- **Cautious**: Writes require approval except for configured exceptions

### Credentials (`config/credentials.json`)

Store credentials with tenant+selector keys:

```json
{
  "default:github:personal": {
    "type": "github_pat",
    "token": "..."
  }
}
```

Request with header:
```
X-Creds: default:github:personal
```

### Enrollments (`config/enrollments.json`)

Tenant enrollment secrets for creating sessions:

```json
{
  "default": "test-secret-123"
}
```

## Read vs Write Classification

The gateway classifies operations using **conservative heuristics**:

| Provider | Read | Write |
|----------|------|-------|
| AWS | `list*`, `describe*`, `get*` | everything else |
| GCP | `list`, `describe` | `create`, `delete`, `update`, `deploy`, `set`, `enable`, `disable` |
| Terraform | N/A | `apply`, `destroy` |
| kubectl | N/A | `apply`, `delete`, `scale`, `patch`, `set image`, `rollout restart` |
| GitHub | N/A | `create`, `delete`, `update`, `merge`, `close`, `open` |
| curl | GET only | Any other HTTP method |

## Development

### Run Tests

```bash
python -m pytest tests/
```

### View Logs

```bash
docker-compose logs -f gatewayd
```

### Debug Mode

```bash
docker-compose up gatewayd --build
# Set DEBUG=true in environment
```

## Next Steps

1. **Integrate with 1Password/Vault** - Replace JSON credential files
2. **Add Slack/Terminal notifications** - Alert users of pending approvals
3. **Implement persistent rules** - "Approve always" for trusted operations
4. **Add audit logging** - Track all operations and approvals
5. **Multi-tenant management** - Full tenant isolation and policy management
6. **CLI client SDK** - Easy Python library for agents
