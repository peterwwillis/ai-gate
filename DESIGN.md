# Agent Gateway Design

This document describes the finalized design for a credential‑segregating, approval‑gated gateway system that supports autonomous coding agents while enforcing strict security controls.

---

## 1. Overview

You are building a **gateway‑centric security architecture** where:

- Agents (Claude Code, Codex CLI, Pi/custom loops) run with **allow‑all local execution**.
- Agents have **no direct credentials** for external systems.
- All **remote side effects** (API calls, cloud CLIs, GitHub, Slack, etc.) must pass through a **gateway**.
- The gateway:
  - classifies actions as **read vs write**,
  - **blocks writes** until human approval,
  - injects credentials internally,
  - never exposes write secrets to agents.

Agents are therefore powerful locally but *operationally powerless* without gateway approval.

---

## 2. Target Agent Runtimes

Supported on day one:

- Claude Code
- Codex CLI
- Custom Pi‑based agent loop

Constraints:

- Multiple concurrent agents (≈10 per user/tenant)
- Agents run inside **Docker‑in‑Docker** containers inside a **QEMU VM**
- Works on **Linux and macOS hosts**

Multi‑tenancy is supported (initially one user, extensible later).

---

## 3. Trust Boundaries and Network Enforcement

### Agent Environment

- **No credentials** mounted or present (`~/.aws`, `~/.config/gcloud`, etc.).
- **Strict egress control** using `iptables` inside the Linux VM:
  - allow only:
    - the gateway HTTP proxy
    - the SSH gateway host
    - (optionally) Squid proxy for constrained web access
  - block:
    - all other outbound traffic
    - instance metadata endpoints (`169.254.169.254`)
    - link‑local ranges

DNS resolution should also be forced through a controlled resolver or proxy.

This makes agent‑side “allow all” safe.

---

## 4. Core Components

### A. `gatewayd` (Python service)

A single, minimal Python service providing:

1. **HTTP Forward Proxy**
   - Acts as a generic API proxy for external providers.
   - Inspects requests, classifies read/write, gates writes, injects credentials, forwards verbatim.

2. **Approval Orchestrator**
   - Generates approval requests.
   - Sends notifications (Slack DM, terminal, desktop notifications).
   - Blocks the originating request until approved/denied or timeout (default 1 hour).
   - Supports:
     - approve once
     - approve for N minutes
     - approve always (persistent rule)

3. **Credential Broker**
   - Loads long‑lived secrets from:
     - 1Password CLI
     - Vault
     - AWS Secrets Manager
   - Supports:
     - AWS (AssumeRole, SSO refresh, static keys)
     - GCP (impersonation, ADC, static JSON)
     - GitHub (PAT first, Apps later)
     - Slack / Datadog / Linear tokens
   - Never returns write credentials to agents.

4. **Policy Engine (in‑process module)**
   - Strict vs Cautious security modes
   - Provider‑specific exceptions

No database or message queue required.

---

### B. SSH Gateway (`ssh-gw`)

- Runs `sshd` with **ForceCommand** (no shell access).
- Dispatcher allowlists only remote‑capable CLIs:
  - `aws`, `gcloud`, `gh`, `terraform`, `kubectl`, `datadog`, `linear`, `curl`
- Each command is routed to a **wrapper**.

Wrappers:

- Normalize intent (operation, resources, args)
- Ask `gatewayd` to classify + approve
- Fetch credentials from `gatewayd`
- Execute CLI locally
- Scrub credentials after execution

Wrappers never store secrets themselves.

---

## 5. Agent Authentication to Gateway

Agents authenticate using **temporary sessions**:

- Each tenant has an enrollment secret.
- Agent requests a session:
  - `POST /session/new` with tenant ID + enrollment secret
- Gateway returns a short‑lived session token.
- All subsequent calls use:
  - `Authorization: Bearer <session_token>`

This prevents arbitrary clients from driving approvals.

---

## 6. Approval UX and Blocking Semantics

Approvals are **blocking** by default.

### Notification Channels

- Slack DM
- Terminal prompt on trusted machine
- Desktop notifications (macOS + KDE Linux)
- Extensible to other messaging systems later

### Behavior

- Gateway creates an approval request.
- Originating SSH or HTTP request **blocks**.
- User approves or denies.
- Gateway resumes execution or returns an error.

Timeout:
- Default: 1 hour (configurable)

Failure semantics:
- Agent disconnect → cancel immediately
- Gateway restart → cancel pending approvals

---

## 7. Security Modes and Policy

### Strict Security

- **All writes require approval**.

### Cautious Security

- Writes require approval **except configured exceptions**.

Initial exceptions:

- **GitHub**:
  - Repo content writes to user‑owned branches
  - GitHub Actions on user‑owned branches
  - Protected branches (`main`, `release/*`) always gated
- **AWS / GCP**: no exceptions
- **Slack / Datadog / Linear**: no exceptions

Branch ownership is determined via naming convention (configurable).

Persistent approvals (“approve always”) are stored as file‑based rules.

---

## 8. Read vs Write Classification

### HTTP Proxy

- `GET`, `HEAD`, `OPTIONS` → read
- `POST`, `PUT`, `PATCH`, `DELETE` → write

Provider‑specific overrides may apply.

### CLI Heuristics (initial)

- `terraform apply|destroy` → write
- `kubectl apply|delete|scale|patch|set image|rollout restart` → write
- AWS:
  - `list*`, `describe*`, `get*` → read
  - everything else → write
- GCP:
  - `list`, `describe` → read
  - `create`, `delete`, `update`, `deploy`, `set`, `enable`, `disable` → write
- GitHub (`gh`): mutating subcommands → write
- `curl`: any non‑GET → write

Conservative by design.

---

## 9. Credential Selection by Agent

Agents may request a **credential selector**:

- HTTP header: `X-Creds: aws:prod-readonly`
- SSH arg: `--creds aws:prod-readonly`

Gateway:

1. Verifies selector is allowed for the tenant/session
2. Maps selector to stored credentials
3. Injects matching credentials internally

Example mapping:

```yaml
tenants:
  me:
    creds:
      aws:prod-readonly:
        type: aws_assumerole
        role_arn: arn:...
        source: vault:...
      github:personal:
        type: github_pat
        source: op://...
```

Supports AWS SSO refresh and mixed credential types.

---

## 10. Credential Injection Techniques

- **HTTP Proxy**: gateway adds auth headers itself
- **SSH Wrappers**:
  - environment variables for single subprocess
  - temp files with strict permissions (e.g., GCP JSON)

Secrets are destroyed immediately after execution.

---

## 11. Logging

- Structured JSON logs
- Output to:
  - file, or
  - stdout (pipeable to another process)

Log levels:

1. Metadata only
2. Request + status
3. Full request/response (with redaction)

No tamper‑evident storage required.

---

## 12. Failure and Recovery Semantics

- Pending approvals are **not durable**.
- Gateway restart cancels all in‑flight requests.
- No idempotency guarantees in v1.

---

## 13. Deployment and Testing

- Implemented in **Python** with minimal dependencies
- No database, no message queue
- Initial testing via `docker compose`:
  - `gatewayd`
  - `ssh-gw`
  - optional `squid`
  - dummy agent container

Integrates cleanly with existing DinD VM setup.

---

## 14. Human Approval Trust Model

- Trust is based on the messaging system used (Slack, terminal access, desktop session).
- No re‑authentication required for approvals.
- Emergency kill switch: **terminate the gateway process**.

---

## 15. Result

This design provides:

- Strong secret segregation
- Deterministic enforcement
- Blocking human‑in‑the‑loop control
- Compatibility with existing agent approval UX
- Minimal infrastructure complexity

The remaining work is mechanical implementation.

