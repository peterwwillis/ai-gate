# AI-GATE: Credential-Segregating, Approval-Gated Gateway for AI Agents

GATE is a security-focused gateway system that enables AI agents to safely execute actions requiring credentials or access to external systems.

## Core Concept

Rather than giving AI agents direct access to credentials, GATE implements a **credential-segregating, approval-gated architecture**:

- **Agents run locally with full freedom** but cannot access external systems directly
- **All remote actions** (API calls, cloud CLIs, GitHub, Slack) pass through the gateway
- **Gateway classifies operations** as read or write
- **Writes are blocked** until human approval
- **Credentials are injected** internally by the gateway
- **Agents never see secrets** — no risk of credential leaks from agent compromise

This design separates two critical risks:
1. **Agent compromise risk** (local execution freedom is isolated)
2. **Credential leak risk** (secrets never leave the gateway)

## Architecture

### Components

- **`gatewayd`** - HTTP forward proxy with approval orchestrator and credential broker
- **`ssh-gw`** - Restricted SSH gateway with allowlisted CLI wrappers
- **Policy Engine** - Classifies operations and determines approval requirements
- **Approval Orchestrator** - Manages blocking approvals with Slack/terminal notifications

### Key Features

✅ **Read/Write Classification** - Conservative heuristics for AWS, GCP, GitHub, Terraform, kubectl, etc.
✅ **Human-in-the-Loop Blocking** - Writes block until approved/denied (timeout: 1 hour default)
✅ **Credential Injection** - HTTP headers, SSH environment variables, temp files
✅ **Multi-Tenant Ready** - Tenant-scoped credentials and policies
✅ **Stateless Design** - No database or message queue required
✅ **Extensible Notifications** - Slack DM, terminal, desktop notifications

## Quick Start

See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions.

```bash
# 1. Initialize test credentials
python config/init_credentials.py

# 2. Start services
docker-compose up -d

# 3. Create agent session
python examples/create_session.py

# 4. Make requests
export GATEWAY_SESSION_TOKEN=<token>
python examples/read_request.py     # No approval needed
python examples/write_request.py    # Requires approval
```

## Security Model

- **Agents**: No credentials, strict egress control via iptables, Docker-in-Docker isolation
- **Gateway**: Central credential storage, request classification, approval blocking
- **Approval**: Based on Slack/terminal/desktop notifications (no re-auth required)
- **Emergency**: Kill switch — terminate gateway process

## Design Reference

See [DESIGN.md](DESIGN.md) for comprehensive architecture and rationale.

## License

Mozilla Public License Version 2.0 (MPL-2.0)