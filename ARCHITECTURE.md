# Architecture Deep Dive

## Request Flow

### 1. Session Creation

```
Agent → POST /session/new + tenant_id + enrollment_secret
        ↓
   SessionManager.verify_enrollment()
        ↓
   Generate session token (valid 1 hour)
        ↓
Agent ← Bearer token + expiry
```

### 2. Read Request (No Approval)

```
Agent → GET /api/v1/proxy/<path> + Bearer token + X-Provider + X-Creds
        ↓
   SessionManager.validate_token()
        ↓
   PolicyEngine.requires_approval() → False (reads never need approval)
        ↓
   CredentialBroker.get_credentials(X-Creds)
        ↓
   HTTPProxy.forward_request() with credentials injected
        ↓
   External API
        ↓
Agent ← Response (credentials scrubbed)
```

### 3. Write Request (Requires Approval)

```
Agent → POST /api/v1/proxy/<path> + Bearer token + X-Provider + X-Creds
        ↓
   SessionManager.validate_token()
        ↓
   PolicyEngine.requires_approval() → True (POST with write policy)
        ↓
   ApprovalOrchestrator.request_approval()
        ├→ Create approval record
        ├→ Generate approval_id
        ├→ Send notifications (Slack/terminal/desktop)
        └→ Block request
        ↓
   Human reviews notification and approves/denies
        ↓
   ApprovalOrchestrator.approve() / deny()
        ├→ Unblock request
        ├→ Set approval status
        └→ Signal waiting thread
        ↓
   CredentialBroker.get_credentials(X-Creds)
        ↓
   HTTPProxy.forward_request() with credentials injected
        ↓
   External API
        ↓
Agent ← Response
```

## Component Details

### PolicyEngine

**Read/Write Classification:**
- HTTP method (GET/HEAD/OPTIONS → read; POST/PUT/PATCH/DELETE → write)
- CLI command patterns (AWS `list*`, `describe*`, `get*` → read)
- Custom rules per provider

**Security Modes:**
- **Strict**: All writes require approval
- **Cautious**: Exceptions configured per tenant (e.g., GitHub user-owned branches)

### CredentialBroker

**Current Implementation:**
- JSON file storage (config/credentials.json)
- Environment variables (CRED_* pattern)

**Planned Integrations:**
- 1Password CLI: `op read "op://..."`
- HashiCorp Vault: Dynamic credential retrieval
- AWS Secrets Manager: Cross-region credential access

**Credential Types:**
- GitHub PAT (Personal Access Token)
- AWS: AssumeRole, SSO refresh, static keys
- GCP: Service account JSON, impersonation
- Slack/Datadog/Linear: Bearer tokens

### ApprovalOrchestrator

**Blocking Semantics:**
- Request blocks originating call
- Thread waits on approval event
- Timeout: 1 hour (configurable)
- No durability on restart

**Notification Channels:**
- Slack DM (send approval link)
- Terminal prompt (interactive decision)
- Desktop notifications (macOS, KDE Linux)

**Persistent Rules (Future):**
- "Approve for 30 minutes" → session-scoped rule
- "Always approve" → stored rule file

## SSH Gateway Flow

### Command Dispatch

```
sshd (ForceCommand=dispatcher.py)
        ↓
SSH_ORIGINAL_COMMAND = "aws list-buckets"
        ↓
dispatcher.dispatch_command("aws", ["list-buckets"])
        ↓
Load wrapper: wrappers/aws_wrapper.py
        ↓
AWSWrapper.classify_action() → "read"
        ↓
AWSWrapper.run()
  ├→ No approval needed (read)
  ├→ Fetch credentials
  ├→ Inject into environment
  ├→ Execute: subprocess.run(["aws", "list-buckets"], env=env_with_creds)
  └→ Scrub credentials from environment
        ↓
Return exit code
```

### Credential Injection

**HTTP Proxy:**
```python
headers["Authorization"] = f"token {credentials['token']}"
```

**SSH Wrappers:**
```python
env["AWS_ACCESS_KEY_ID"] = credentials["access_key"]
env["AWS_SECRET_ACCESS_KEY"] = credentials["secret_key"]
# Execute command
subprocess.run(cmd, env=env)
# Scrub
del env["AWS_ACCESS_KEY_ID"]
del env["AWS_SECRET_ACCESS_KEY"]
```

## Security Properties

### Trust Boundaries

1. **Agents**: No credentials, strict egress via iptables
2. **Gateway**: Single point of trust, credential segregation
3. **Approval**: Based on user session security (Slack, terminal, desktop)

### Attack Scenarios

**Agent Compromise:**
- Agent has no credentials → limited lateral movement
- SSH/curl commands are allowlisted
- Network blocked except to gateway

**Gateway Compromise:**
- Attacker gains temporary access
- Pending approvals cancel on restart
- Credentials stored at rest only (1Password/Vault if integrated)
- No message persistence

**Approval Spoofing:**
- Trust based on Slack/terminal/desktop security
- Rate limiting not implemented yet
- Future: 2FA, approval quorum

## Performance Considerations

- **No database**: Approval state in memory (lost on restart)
- **No message queue**: Blocking semaphore per approval
- **Concurrent agents**: ~10 per tenant (estimated based on memory/threads)
- **Timeout**: 1 hour default (configurable, not enforced by wall clock yet)

## Future Enhancements

### Immediate (v0.2)

- [ ] Slack/terminal/desktop notifications
- [ ] Persistent approval rules file
- [ ] Request audit logging
- [ ] Rate limiting

### Medium-term (v0.3)

- [ ] 1Password/Vault integration
- [ ] Multi-tenant dashboard
- [ ] Approval quorum/escalation
- [ ] Custom notification channels

### Long-term (v1.0)

- [ ] Database-backed approval history
- [ ] Machine learning classification refinement
- [ ] Fine-grained RBAC
- [ ] Namespace isolation
