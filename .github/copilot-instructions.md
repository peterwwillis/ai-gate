# AI-GATE: Copilot Instructions

## Core Architecture

GATE is a **credential-segregating, approval-gated gateway** for AI agents. Agents execute locally with full freedom but cannot access external systems directly—all remote actions (API calls, cloud CLIs, GitHub, Slack) must pass through the gateway, which injects credentials and enforces human approval on writes.

### Key Design Principle
- **Agent Freedom + Credential Isolation + Blocking Approvals**: Agents are powerful locally but operationally powerless without gateway approval. This separates the risk of agent compromise from the risk of credential leak.

## Architecture Components

### 1. `gatewayd` (Python microservice)
Central gateway providing:
- **HTTP Forward Proxy**: Intercepts requests, classifies read/write, gates writes, injects credentials
- **Approval Orchestrator**: Sends notifications (Slack, terminal, desktop), blocks requests until approved/denied
- **Credential Broker**: Loads secrets from 1Password CLI / Vault / AWS Secrets Manager; supports AWS, GCP, GitHub, Slack, Datadog, Linear
- **Policy Engine**: Enforces Strict (all writes need approval) or Cautious (exceptions for safe operations) security modes

### 2. SSH Gateway (`ssh-gw`)
- Runs restricted `sshd` with ForceCommand (no shell access)
- Allowlists only remote-capable CLIs: `aws`, `gcloud`, `gh`, `terraform`, `kubectl`, `datadog`, `linear`, `curl`
- **Wrappers** for each CLI normalize intent, ask gateway to classify/approve, fetch credentials, execute, scrub secrets

### 3. Trust Boundaries
Agents run in restricted container environments with:
- **No credentials** mounted (no `~/.aws`, `~/.config/gcloud`)
- **Strict egress control** via iptables: only gateway HTTP proxy, SSH gateway host, optional Squid proxy
- **Blocked**: instance metadata, link-local ranges, unauthorized outbound traffic

## Critical Developer Patterns

### Credential Selection by Agents
Agents request credentials via HTTP header or SSH arg using tenant+selector:
```
X-Creds: aws:prod-readonly
--creds github:personal
```
Gateway maps selectors to stored credentials (configured per tenant in YAML).

### Read vs Write Classification
**HTTP**: GET/HEAD/OPTIONS = read; POST/PUT/PATCH/DELETE = write
**CLI Heuristics** (intentionally conservative):
- **AWS**: `list*`, `describe*`, `get*` → read; else → write
- **GCP**: `list`, `describe` → read; `create`, `delete`, `update`, `deploy`, `set`, `enable`, `disable` → write
- **Terraform**: `apply`, `destroy` → write
- **kubectl**: `apply`, `delete`, `scale`, `patch`, `set image`, `rollout restart` → write
- **GitHub (`gh`)**: mutating subcommands → write
- **curl**: non-GET → write

### Approval Flow
1. Agent initiates action (HTTP or SSH)
2. Gateway classifies read/write
3. If **write**, gateway creates approval request and **blocks** originating call
4. Notification sent (Slack DM, terminal prompt, desktop notification)
5. User approves/denies within timeout (default 1 hour)
6. Gateway resumes execution or returns error
7. Agent never knows about credentials; gateway injects them internally

### Credential Injection
- **HTTP Proxy**: Gateway adds auth headers
- **SSH Wrappers**: Environment variables or temp files (GCP JSON) with strict permissions, destroyed after execution

### Security Modes
- **Strict**: All writes require approval
- **Cautious**: Writes need approval except configured exceptions (e.g., GitHub writes to user-owned branches)

Protected branch rules (`main`, `release/*`) **always require approval** regardless of mode.

## Deployment Context
- Implemented in **Python** with minimal dependencies
- **No database, no message queue**—stateless design
- Agents run in **Docker-in-Docker inside QEMU VMs** (Linux/macOS hosts)
- Supports ~10 concurrent agents per tenant
- Multi-tenant ready (extensible from single-user)
- Initial testing via `docker compose` with dummy agent container

## Agent Authentication
- Agents authenticate via temporary sessions:
  1. `POST /session/new` with tenant ID + enrollment secret
  2. Gateway returns short-lived session token
  3. Subsequent calls use `Authorization: Bearer <token>`
- This prevents unauthorized clients from driving approvals

## Logging & Observability
- Structured JSON logs to file or stdout
- Log levels: metadata only, request+status, full request/response (with redaction)
- **No tamper-evident storage** required in v1

## Key Non-Functional Properties
- **Pending approvals not durable**: Gateway restart cancels in-flight requests
- **No idempotency guarantees** in v1
- **Emergency kill switch**: Terminate gateway process
- **Trust model**: Based on messaging system security (Slack, terminal access, desktop session)

## When Starting Implementation
1. Reference [DESIGN.md](../DESIGN.md) for detailed specifications and rationale
2. Agents are read-only to external systems until approval gates are functional
3. Start with HTTP proxy + basic classification logic; extend with CLI wrappers
4. Test approval flow with a minimal agent container + Slack notifications first
