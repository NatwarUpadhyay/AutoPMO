# Security Guide
## Security Architecture and Hardening for AutoPMO

---

## 📋 Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication](#authentication)
3. [Authorization](#authorization)
4. [Network Security](#network-security)
5. [Data Protection](#data-protection)
6. [Container Security](#container-security)
7. [Secrets Management](#secrets-management)
8. [Audit Logging](#audit-logging)
9. [Compliance](#compliance)
10. [Security Best Practices](#security-best-practices)

---

## 1. Security Overview

AutoPMO implements defense-in-depth security with multiple layers:

```
┌─────────────────────────────────────────────┐
│  1. Perimeter Security                      │
│     • API Gateway (Rate Limiting)           │
│     • WAF (Web Application Firewall)        │
│     • DDoS Protection                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  2. Authentication & Authorization          │
│     • Red Hat SSO (Keycloak)                │
│     • OAuth2/OIDC                          │
│     • MFA Enforcement                       │
│     • RBAC Policies                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  3. Network Security                        │
│     • Network Policies (Pod Isolation)      │
│     • Service Mesh (Istio mTLS)             │
│     • Egress Controls                       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  4. Application Security                    │
│     • Input Validation                      │
│     • SQL Injection Prevention              │
│     • XSS Protection                        │
│     • CSRF Tokens                           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  5. Container Security                      │
│     • SELinux Mandatory Access Control      │
│     • SecurityContext Constraints           │
│     • Image Scanning (Trivy)                │
│     • Pod Security Standards                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  6. Data Security                           │
│     • Encryption at Rest (LUKS)             │
│     • Encryption in Transit (TLS 1.3)       │
│     • Database Encryption (TDE)             │
│     • Secrets Management (Vault)            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  7. Audit & Monitoring                      │
│     • Audit Logs (all API calls)            │
│     • Security Event Monitoring (SIEM)      │
│     • Intrusion Detection (Falco)           │
└─────────────────────────────────────────────┘
```

### Security Certifications Target
- SOC 2 Type II
- ISO 27001
- GDPR Compliance
- HIPAA Compliance (optional module)

---

## 2. Authentication

### 2.1 Red Hat SSO (Keycloak) Configuration

```yaml
# Keycloak Realm Configuration
{
  "realm": "autopmo",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "editUsernameAllowed": false,
  "bruteForceProtected": true,
  "permanentLockout": false,
  "maxFailureWaitSeconds": 900,
  "minimumQuickLoginWaitSeconds": 60,
  "waitIncrementSeconds": 60,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,
  "failureFactor": 5
}
```

### 2.2 Multi-Factor Authentication (MFA)

**Enforced for**:
- All admin accounts
- Production environment access
- Privileged operations (delete, deploy)

**Supported Methods**:
- TOTP (Google Authenticator, Authy)
- WebAuthn (YubiKey, TouchID)
- SMS (backup only, not recommended for primary)

**Configuration**:
```bash
# Enable MFA requirement for realm
kcadm.sh update realms/autopmo -s "otpPolicyType=totp" \
  -s "otpPolicyAlgorithm=HmacSHA256" \
  -s "otpPolicyDigits=6" \
  -s "otpPolicyPeriod=30"

# Enforce MFA for admin role
kcadm.sh create authentication/required-actions \
  -r autopmo \
  -s alias=CONFIGURE_TOTP \
  -s name="Configure OTP" \
  -s providerId=CONFIGURE_TOTP \
  -s enabled=true \
  -s defaultAction=true
```

### 2.3 Session Management

```yaml
# Session Settings
session:
  timeout_idle: 30m  # Idle timeout
  timeout_absolute: 8h  # Max session duration
  cookie_secure: true
  cookie_httponly: true
  cookie_samesite: strict
  
# JWT Configuration
jwt:
  algorithm: RS256
  expiration: 15m  # Access token lifetime
  refresh_expiration: 7d  # Refresh token lifetime
  issuer: https://sso.autopmo.com
  audience: autopmo-api
```

---

## 3. Authorization

### 3.1 Role-Based Access Control (RBAC)

**Roles**:
```python
class Role:
    SYSTEM_ADMIN = "system_admin"
    PROJECT_MANAGER = "project_manager"  
    DEVELOPER = "developer"
    STAKEHOLDER = "stakeholder"
    AUDITOR = "auditor"
    ML_ENGINEER = "ml_engineer"
```

**Permission Matrix**:

| Resource | System Admin | PM | Developer | Stakeholder | Auditor |
|----------|--------------|-----|-----------|-------------|---------|
| projects:create | ✅ | ✅ | ❌ | ❌ | ❌ |
| projects:read | ✅ | ✅ | ✅ | ✅ | ✅ |
| projects:update | ✅ | ✅ | ❌ | ❌ | ❌ |
| projects:delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| tasks:assign | ✅ | ✅ | ❌ | ❌ | ❌ |
| tasks:update | ✅ | ✅ | ✅ | ❌ | ❌ |
| reports:generate | ✅ | ✅ | ✅ | ✅ | ❌ |
| agents:configure | ✅ | ❌ | ❌ | ❌ | ❌ |
| models:deploy | ✅ | ❌ | ❌ | ❌ | ❌ |
| audit:read | ✅ | ❌ | ❌ | ❌ | ✅ |

### 3.2 Attribute-Based Access Control (ABAC)

**Policies**:
```yaml
# Example: Project Manager can only access their own projects
policies:
  - name: pm_own_projects
    description: PMs can only access projects they own
    effect: allow
    subjects:
      roles: [project_manager]
    resources:
      types: [project]
    conditions:
      - project.owner_id == user.id
    actions: [read, update]
```

### 3.3 API Authorization

```python
# FastAPI Dependency for Authorization
from fastapi import Depends, HTTPException
from app.auth import get_current_user, require_permission

@app.post("/projects")
@require_permission("projects:create")
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    # Verify user has permission
    if not current_user.has_permission("projects:create"):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Additional checks
    if project.budget > 1000000 and not current_user.has_role("system_admin"):
        raise HTTPException(
            status_code=403, 
            detail="Budget over $1M requires admin approval"
        )
    
    # Proceed with project creation
    return await project_service.create(project, current_user)
```

---

## 4. Network Security

### 4.1 Network Policies

**Default Deny All**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: autopmo
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

**Allow Specific Traffic**:
```yaml
# Orchestrator can talk to specialized agents
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orchestrator-to-agents
  namespace: autopmo
spec:
  podSelector:
    matchLabels:
      app: specialized-agent
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: orchestrator-agent
    ports:
    - protocol: TCP
      port: 8080

---
# All agents can access database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agents-to-database
  namespace: autopmo
spec:
  podSelector:
    matchLabels:
      app: postgresql
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          component: agent
    ports:
    - protocol: TCP
      port: 5432
```

### 4.2 Service Mesh (Istio mTLS)

```yaml
# Enable strict mTLS across all services
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: autopmo
spec:
  mtls:
    mode: STRICT

---
# Authorization policy for agent communication
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: orchestrator-authz
  namespace: autopmo
spec:
  selector:
    matchLabels:
      app: orchestrator-agent
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/autopmo/sa/api-gateway"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/*"]
```

### 4.3 Egress Control

```yaml
# Deny egress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-egress
  namespace: autopmo
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53  # Allow DNS

---
# Whitelist external APIs
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-apis
  namespace: autopmo
spec:
  podSelector:
    matchLabels:
      app: orchestrator-agent
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          app: mistral-llm
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS to cloud APIs
```

---

## 5. Data Protection

### 5.1 Encryption at Rest

**PostgreSQL Transparent Data Encryption (TDE)**:
```sql
-- Enable TDE on PostgreSQL
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive columns
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    budget DECIMAL ENCRYPTED WITH (ALGORITHM = 'aes256', KEY = 'project_encryption_key'),
    created_at TIMESTAMP
);

-- Use column-level encryption for PII
ALTER TABLE users ADD COLUMN email_encrypted BYTEA;
UPDATE users SET email_encrypted = pgp_sym_encrypt(email, 'encryption_key');
```

**Volume Encryption (LUKS)**:
```bash
# Encrypt persistent volumes
cryptsetup luksFormat /dev/sdb
cryptsetup luksOpen /dev/sdb autopmo_pv
mkfs.ext4 /dev/mapper/autopmo_pv
```

### 5.2 Encryption in Transit

**TLS 1.3 Configuration**:
```yaml
# Ingress TLS settings
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autopmo-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - autopmo.example.com
    secretName: autopmo-tls-cert
```

### 5.3 Data Masking

```python
# PII Masking for logs and responses
import re

class PIIMasker:
    @staticmethod
    def mask_email(text: str) -> str:
        return re.sub(r'[\w\.-]+@[\w\.-]+', '***@***.***', text)
    
    @staticmethod
    def mask_ssn(text: str) -> str:
        return re.sub(r'\d{3}-\d{2}-\d{4}', '***-**-****', text)
    
    @staticmethod
    def mask_credit_card(text: str) -> str:
        return re.sub(r'\d{4}-\d{4}-\d{4}-\d{4}', '****-****-****-****', text)

# Usage in logging
logger.info(PIIMasker.mask_email(f"User {email} created project"))
```

---

## 6. Container Security

### 6.1 SELinux Policies

```yaml
# SELinux security context
apiVersion: v1
kind: Pod
metadata:
  name: orchestrator-agent
spec:
  securityContext:
    seLinuxOptions:
      level: "s0:c123,c456"
      type: "autopmo_agent_t"
  containers:
  - name: orchestrator
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL
      readOnlyRootFilesystem: true
```

### 6.2 Image Scanning

```bash
# Scan images with Trivy before deployment
trivy image quay.io/autopmo/orchestrator:1.0 \
  --severity HIGH,CRITICAL \
  --exit-code 1

# Sample output:
orchestrator:1.0 (alpine 3.18.0)
==================================
Total: 0 (HIGH: 0, CRITICAL: 0)

✅ Image scan passed - no vulnerabilities found
```

### 6.3 Pod Security Standards

```yaml
# Restricted Pod Security Standard
apiVersion: v1
kind: Namespace
metadata:
  name: autopmo
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

---

## 7. Secrets Management

### 7.1 HashiCorp Vault Integration

```python
# Vault client for retrieving secrets
import hvac

class VaultClient:
    def __init__(self, url: str, token: str):
        self.client = hvac.Client(url=url, token=token)
    
    def get_database_credentials(self) -> dict:
        """Retrieve dynamic database credentials"""
        secret = self.client.secrets.database.generate_credentials(
            name='autopmo-db-role'
        )
        return {
            'username': secret['data']['username'],
            'password': secret['data']['password'],
            'ttl': secret['lease_duration']
        }
    
    def rotate_api_key(self, service: str):
        """Rotate API keys"""
        new_key = secrets.token_urlsafe(32)
        self.client.secrets.kv.v2.create_or_update_secret(
            path=f'api-keys/{service}',
            secret={'key': new_key, 'rotated_at': datetime.utcnow().isoformat()}
        )
        return new_key

# Usage
vault = VaultClient(
    url=os.getenv('VAULT_ADDR'),
    token=os.getenv('VAULT_TOKEN')
)
db_creds = vault.get_database_credentials()
```

### 7.2 Secret Rotation Policy

**Automatic Rotation Schedule**:
- Database credentials: Every 90 days
- API keys: Every 180 days
- TLS certificates: Every 365 days
- Service account tokens: Every 30 days

### 7.3 Secrets in CI/CD

```yaml
# GitHub Actions secret usage
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Retrieve secrets from Vault
      uses: hashicorp/vault-action@v2
      with:
        url: ${{ secrets.VAULT_ADDR }}
        token: ${{ secrets.VAULT_TOKEN }}
        secrets: |
          secret/data/autopmo/db password | DB_PASSWORD;
          secret/data/autopmo/api key | API_KEY
    
    - name: Deploy
      env:
        DB_PASSWORD: ${{ env.DB_PASSWORD }}
      run: ./deploy.sh
```

---

## 8. Audit Logging

### 8.1 Audit Log Structure

```python
# Audit log entry format
{
  "timestamp": "2024-02-14T10:30:00Z",
  "event_id": "evt_123abc",
  "event_type": "project.created",
  "actor": {
    "user_id": "user_456def",
    "username": "john.smith@company.com",
    "ip_address": "203.0.113.42",
    "user_agent": "Mozilla/5.0..."
  },
  "resource": {
    "type": "project",
    "id": "proj_789ghi",
    "name": "ERP Migration"
  },
  "action": "create",
  "status": "success",
  "metadata": {
    "project_budget": 500000,
    "project_duration_weeks": 24
  },
  "request_id": "req_xyz123",
  "session_id": "sess_abc456"
}
```

### 8.2 Audit Events Captured

**Authentication Events**:
- User login (success/failure)
- MFA verification (success/failure)
- Password reset
- Session expiration
- Logout

**Authorization Events**:
- Permission denied
- Role assignment/removal
- Policy changes

**Data Access Events**:
- Project created/updated/deleted
- Sensitive data accessed
- Bulk data export

**Administrative Events**:
- User account created/disabled
- Configuration changes
- Agent deployment
- Model updates

### 8.3 Audit Log Retention

```python
# Audit log retention policy
RETENTION_POLICIES = {
    "authentication_events": 365,  # days
    "data_access_events": 2555,    # 7 years
    "administrative_events": 2555,  # 7 years
    "system_events": 90            # days
}

# Automated archival to cold storage
async def archive_old_logs():
    cutoff_date = datetime.now() - timedelta(days=365)
    old_logs = await db.query(
        "SELECT * FROM audit_logs WHERE timestamp < $1",
        cutoff_date
    )
    
    # Compress and upload to S3 Glacier
    archive_file = compress_logs(old_logs)
    await s3_client.upload(
        archive_file,
        bucket='autopmo-audit-archive',
        storage_class='GLACIER'
    )
    
    # Delete from hot storage
    await db.execute(
        "DELETE FROM audit_logs WHERE timestamp < $1",
        cutoff_date
    )
```

---

## 9. Compliance

### 9.1 GDPR Compliance

**Data Subject Rights**:
```python
# Right to Access
@app.get("/api/v1/gdpr/data-export")
async def export_user_data(user_id: str):
    """Export all user data in machine-readable format"""
    user_data = await collect_user_data(user_id)
    return JSONResponse(content=user_data)

# Right to Erasure (Right to be Forgotten)
@app.delete("/api/v1/gdpr/delete-user")
async def delete_user_data(user_id: str):
    """Permanently delete all user data"""
    await anonymize_user_records(user_id)
    await delete_user_account(user_id)
    return {"message": "User data deleted successfully"}

# Right to Data Portability
@app.get("/api/v1/gdpr/data-portability")
async def export_data_portable_format(user_id: str):
    """Export data in JSON format for portability"""
    data = await collect_user_data(user_id)
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=user_data.json"}
    )
```

### 9.2 SOC 2 Type II Controls

**Access Controls**:
- CC6.1: Logical and physical access controls
- CC6.2: Prior to issuing system credentials and granting system access
- CC6.3: System access is removed when appropriate

**Change Management**:
- CC8.1: Change management policies and procedures

**Monitoring**:
- CC7.2: The entity monitors system components and operations

### 9.3 Compliance Reporting

```bash
# Generate compliance report
autopmo compliance-report \
  --framework soc2 \
  --period 2024-Q1 \
  --output compliance-report-q1.pdf

# Output includes:
# - Control effectiveness ratings
# - Audit log summaries
# - Access review results
# - Incident reports
# - Remediation actions
```

---

## 10. Security Best Practices

### 10.1 Secure Development Lifecycle

**Code Review Checklist**:
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection (output encoding)
- [ ] CSRF tokens on state-changing operations
- [ ] Authentication required on protected endpoints
- [ ] Authorization checks before sensitive operations
- [ ] Secrets not hardcoded in source code
- [ ] Error messages don't leak sensitive info
- [ ] Logging doesn't include PII
- [ ] Dependencies scanned for vulnerabilities

### 10.2 Incident Response Plan

**Phases**:
1. **Detection**: Automated monitoring alerts
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threat
4. **Recovery**: Restore from backup
5. **Lessons Learned**: Post-incident review

**Contact Information**:
- Security Team: security@autopmo.com
- Incident Hotline: +1-555-SEC-INCI
- PagerDuty: security-oncall

### 10.3 Security Training

**Required for All Engineers**:
- OWASP Top 10 awareness
- Secure coding practices
- Phishing detection
- Incident reporting procedures

**Annual Refresher Training**:
- Security updates and trends
- New threat vectors
- Compliance changes

---

## Security Checklist

Pre-Production:
- [ ] All secrets stored in Vault
- [ ] TLS certificates valid and auto-renewing
- [ ] Network policies applied and tested
- [ ] SELinux enforcing mode enabled
- [ ] Container images scanned (no HIGH/CRITICAL vulns)
- [ ] MFA enabled for all admin accounts
- [ ] Audit logging configured
- [ ] Backup and recovery tested
- [ ] Incident response plan documented
- [ ] Security training completed

Post-Production:
- [ ] Monitor audit logs daily
- [ ] Review access logs weekly
- [ ] Rotate secrets quarterly
- [ ] Perform penetration testing annually
- [ ] Update security documentation
- [ ] Conduct tabletop exercises

---

## Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, email: security@autopmo.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested remediation (if any)

We'll respond within 24 hours and provide updates weekly.

---

**Version**: 1.0  
**Last Updated**: 2024-02-14  
**Maintainer**: AutoPMO Security Team
