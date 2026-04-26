# ITL Privileged Identity Management (PIM)

**Complete gids voor Just-In-Time privilege elevation in Kubernetes, endpoints en cloud resources**

ITL PIM biedt Azure Entra ID PIM-style tijdelijke privilege elevation voor je complete IT-infrastructuur: Kubernetes clusters, lokale machines, Azure resources en API's. Alles met automatische approval workflows, time-bound access en complete audit trails.

## Inhoudsopgave

1. [Overzicht & Architectuur](#overzicht--architectuur)
2. [Elevation Types](#elevation-types)
3. [ITLC CLI Commands](#itlc-cli-commands)
4. [Configuratie](#configuratie)
5. [Implementatie](#implementatie)
6. [Security & Compliance](#security--compliance)
7. [Deployment & Rollout](#deployment--rollout)

---

## Overzicht & Architectuur

### Wat is Just-In-Time Access?

In plaats van permanente admin rechten, krijgen engineers tijdelijke toegang wanneer ze het nodig hebben:

```bash
# Geen permanent cluster-admin meer, maar:
itlc elevate --role=cluster-admin --duration=2h --reason="Debug prod issue INC-5678"

# ✓ Elevation activated for 2 hours
# ✓ Automatic removal after expiration
# ✓ Complete audit trail (who, what, when, why)
```

### High-Level Architectuur

```
┌──────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Keycloak + PIM Controller                   │ │
│  │  - Centrale approval workflow                          │ │
│  │  - Eligible roles configuratie                         │ │
│  │  - Token issuance met temporary claims                 │ │
│  │  - Audit logging                                       │ │
│  └───────┬──────────────────────────┬─────────────────────┘ │
│          │                          │                        │
└──────────┼──────────────────────────┼────────────────────────┘
           │                          │
           │                          │
    ┌──────▼─────────┐        ┌──────▼─────────┐
    │   Kubernetes   │        │  Local Agents  │
    │    Clusters    │        │  (Endpoints)   │
    └────────────────┘        └────────────────┘
           │                          │
           │                          │
    ┌──────▼─────────┐        ┌──────▼─────────┐
    │   Azure AD     │        │      APIs      │
    │   Resources    │        │  (OAuth2)      │
    └────────────────┘        └────────────────┘
```

### Workflow Overzicht

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Engineer Request                                         │
│    itlc elevate --role=cluster-admin --duration=2h          │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PIM Controller Validation                                │
│    ✓ Eligible? ✓ MFA recent? ✓ Within duration limits?    │
└─────────────┬───────────────────────────────────────────────┘
              │
              ├───► Self-service: Activate immediately
              │
              └───► Requires approval: Notify approvers
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ 3. Approval Decision   │
                          │    itlc approve <id>   │
                          └───────────┬────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Activation                                               │
│    • Kubernetes: Add to Keycloak group → Token includes    │
│    • Local: Signal agent → Add to OS group                 │
│    • Azure AD: Call Graph API → Add to AAD group           │
│    • API: Issue token with elevated scopes                 │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Automatic Expiration                                     │
│    • Cleanup job runs every 5 minutes                       │
│    • Removes from groups / revokes scopes                   │
│    • Audit log entry                                        │
│    • User notification (15 min warning)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Elevation Types

ITL PIM ondersteunt **vier types** privilege elevation:

### Type 1: Keycloak Groups (Kubernetes RBAC)

**Gebruik:** Tijdelijke toegang tot Kubernetes clusters

**Use cases:**
- `k8s-cluster-admin` → Full cluster administration
- `k8s-production-read` → Read-only access to production
- `k8s-namespace-dev-admin` → Admin in specific namespace

**Voorbeeld:**
```bash
itlc elevate --type=group --name=k8s-cluster-admin --duration=2h
```

**Technische werking:**
1. User wordt tijdelijk toegevoegd aan Keycloak groep
2. JWT token refresh → `groups` claim bevat nieuwe groep
3. Kubernetes RBAC evalueert ClusterRoleBinding:
   ```yaml
   subjects:
   - kind: Group
     name: k8s-cluster-admin
   ```
4. Na expiration: Automatic removal uit groep

**Latency:** Immediate (next token refresh, max 5 min)  
**Requires logout:** Nee  
**Offline capable:** Ja (cached tokens blijven geldig)

---

### Type 2: Local Machine Groups (Endpoint Security)

**Gebruik:** Tijdelijke admin rechten op workstations/servers

**Use cases:**
- `local-admin` → Administrators (Windows) / sudo (Linux)
- `local-docker` → docker-users groep
- `local-power-users` → Elevated zonder full admin

**Voorbeeld:**
```bash
itlc elevate --type=local-group --name=local-admin --duration=30m --reason="Install software"
```

**Technische werking:**
1. PIM Controller registreert elevation in database
2. **Privilege Agent** op workstation poll elke 30s
3. Agent detecteert nieuwe assignment
4. Agent voegt user toe aan lokale OS groep:
   - Windows: `net localgroup Administrators user /add`
   - Linux: `usermod -aG sudo user`
   - macOS: `dseditgroup -o edit -a user -t user admin`
5. Na expiration: Agent verwijdert uit groep

**Latency:** ~30 seconden (agent poll interval)  
**Requires logout:** Soms (Windows meestal wel, Linux niet)  
**Offline capable:** Nee (agent moet PIM controller kunnen bereiken)

**Zie:** [Privilege Agent Setup Guide](PRIVILEGE_AGENT.md) voor volledige agent documentatie

---

### Type 3: Azure AD Groups (Hybrid Cloud)

**Gebruik:** Tijdelijke toegang tot Azure resources via AAD groepen

**Use cases:**
- `azure-subscription-contributors` → Azure subscription Contributor
- `azure-key-vault-admins` → Key Vault toegang
- `azure-sql-admins` → Database admin

**Voorbeeld:**
```bash
itlc elevate --type=azure-group --name=azure-subscription-contributors --duration=4h
```

**Technische werking:**
1. Keycloak is gefedereerd met Azure AD als IdP
2. PIM Controller gebruikt Azure AD Graph API
3. User wordt toegevoegd aan Azure AD groep via API:
   ```python
   graph_client.groups.members.add(group_id, user_id)
   ```
4. Azure RBAC evalueert group membership voor resource access
5. Na expiration: Automatic removal via Graph API

**Prerequisites:**
- Keycloak federation met Azure AD
- Service Principal met `Directory.ReadWrite.All` permission
- Azure AD Premium P2 license

**Latency:** 1-2 minuten (Azure AD sync)  
**Requires logout:** Nee  
**Offline capable:** Nee (Azure AD API moet bereikbaar zijn)

---

### Type 4: API Scopes (OAuth2 API Access)

**Gebruik:** Tijdelijke elevated OAuth2 scopes voor API toegang

**Use cases:**
- `payment-api:admin` → Admin operations op payment API
- `user-api:write` → Write access user management
- `analytics-api:export` → Export grote datasets
- `vault-api:rotate-secrets` → Rotate secrets in Vault

**Voorbeeld:**
```bash
itlc elevate --type=api-scope --name=payment-api:admin --duration=1h
```

**Technische werking:**
1. PIM Controller issued OAuth2 token met extra scopes
2. Token bevat `pim_scopes` claim met expiration:
   ```json
   {
     "scope": "payment-api:read payment-api:admin",
     "pim_scopes": [{
       "scope": "payment-api:admin",
       "expires_at": "2026-01-23T17:00:00Z"
     }]
   }
   ```
3. API valideert token EN checks `pim_scopes` expiration:
   ```python
   def check_permission(token, required_scope):
       if required_scope in token['scope']:
           pim_scope = [s for s in token['pim_scopes'] if s['scope'] == required_scope]
           if pim_scope and datetime.now() > parse(pim_scope[0]['expires_at']):
               raise ScopeExpired()
       return True
   ```
4. Token refresh **niet mogelijk** voor elevated scopes

**Latency:** Immediate (token issuance)  
**Requires logout:** Nee  
**Offline capable:** Ja (token-based, werkt zonder controller)

---

### Comparison Matrix

| Feature | Keycloak Groups | Local Groups | Azure AD Groups | API Scopes |
|---------|----------------|--------------|-----------------|------------|
| **Scope** | Kubernetes | Workstations | Azure resources | APIs |
| **Latency** | Immediate | ~30s | 1-2 min | Immediate |
| **Logout needed** | Nee | Soms | Nee | Nee |
| **Offline** | Ja | Nee | Nee | Ja |
| **Audit** | Keycloak + K8s | Agent + SIEM | Azure AD logs | API logs |
| **Cost** | Free | Free | AAD P2 required | Free |
| **Best voor** | Cloud-native | Legacy endpoints | Hybrid cloud | Microservices |

---

### Mixed Elevations

Je kunt **meerdere types tegelijk** aanvragen:

**Voorbeeld 1: Full Stack Debugging**
```bash
itlc elevate \
  --type=group --name=k8s-cluster-admin \
  --type=local-group --name=local-admin \
  --type=api-scope --name=payment-api:admin \
  --duration=2h \
  --reason="Debug production payment issue INC-5678" \
  --ticket=INC-5678

# Result:
# ✓ Kubernetes: cluster-admin toegang
# ✓ Local: Administrators groep op workstation
# ✓ API: payment-api:admin scope
# → Kan pods debuggen, tools installeren, EN API calls maken
```

**Voorbeeld 2: Cloud Operations**
```bash
itlc elevate \
  --type=azure-group --name=azure-key-vault-admins \
  --type=api-scope --name=vault-api:rotate-secrets \
  --duration=4h \
  --reason="Rotate compromised secrets"

# Result:
# ✓ Azure: Key Vault admin via AAD
# ✓ API: Vault API elevated scopes
```

**Voorbeeld 3: Emergency Incident Response**
```bash
itlc elevate \
  --type=group --name=k8s-cluster-admin \
  --type=local-group --name=local-admin \
  --type=azure-group --name=azure-security-admins \
  --type=api-scope --name=user-api:admin \
  --type=api-scope --name=audit-api:export \
  --duration=8h \
  --reason="Security incident SEC-2026-001" \
  --ticket=SEC-2026-001

# Requires approval from security lead
# Full access to ALL systems for incident response
```

---

## ITLC CLI Commands

### Elevation Requests

```bash
# Basic (backwards compatible)
itlc elevate --role=cluster-admin --duration=2h

# Explicit type
itlc elevate --type=group --name=k8s-cluster-admin --duration=2h

# Local machine elevation
itlc elevate --type=local-group --name=local-admin --duration=30m

# Azure AD group
itlc elevate --type=azure-group --name=azure-subscription-contributors --duration=4h

# API scope
itlc elevate --type=api-scope --name=payment-api:admin --duration=1h

# Multiple scopes
itlc elevate \
  --type=api-scope --name=user-api:admin \
  --type=api-scope --name=payment-api:write \
  --duration=2h

# Met justification (verplicht voor sommige roles)
itlc elevate --role=production-write --duration=1h \
  --reason="Deploy hotfix payment bug" \
  --ticket=INC-12345

# Check eligibility zonder activeren
itlc elevate --check --role=cluster-admin
```

### Active Elevations Bekijken

```bash
# Lijst current elevations
itlc whoami --show-pim

# Output:
# Current elevations:
#   ✓ cluster-admin (expires in 1h 23m)
#     └─ Granted by: manager@company.com
#     └─ Reason: Production debugging INC-12345
#   
#   ✓ local-admin (expires in 15m)
#     └─ Self-activated (eligible role)

# Detailed view met timestamps
itlc elevation list --detailed
```

### Elevation Verlengen

```bash
# Extend huidige elevation (if allowed)
itlc elevate extend --role=cluster-admin --duration=2h

# Check of extension mogelijk is
itlc elevate extend --check --role=cluster-admin
```

### Vroeg Deactiveren

```bash
# Manual deactivation
itlc elevate deactivate --role=cluster-admin

# Deactivate alles
itlc elevate deactivate --all
```

### Approval Workflow (Voor Approvers)

```bash
# List pending requests
itlc approve list

# Output:
# Pending PIM requests:
#   [1] john@company.com → cluster-admin (2h)
#       Reason: Debug production payment processing
#       Ticket: INC-12345
#       Requested: 5 minutes ago

# Approve
itlc approve 1 --comment="Approved for incident response"

# Deny
itlc deny 1 --reason="Please use staging environment first"

# Approve met reduced duration
itlc approve 2 --duration=30m --comment="Approved for 30m only"

# Auto-approve delegation
itlc approve auto-enable --team=backend --roles=production-read
```

### Audit Trail

```bash
# View eigen PIM history
itlc elevation history

# View team activity (managers)
itlc elevation history --team=backend --last=7d

# Export audit log
itlc elevation audit --export=csv --output=pim-audit-jan-2026.csv

# Real-time monitoring (security team)
itlc elevation watch
```

---

## Configuratie

### 1. Eligible Roles Definiëren

```yaml
# keycloak-pim-config.yaml
realm: production

eligibleRoles:
  # ============================================================
  # KUBERNETES RBAC (Keycloak Groups)
  # ============================================================
  
  - name: k8s-production-read
    displayName: "Production Read Access"
    description: "Read-only access to production namespaces"
    type: group
    approvalRequired: false
    maxDuration: 4h
    defaultDuration: 2h
    eligibleMembers:
      - group: k8s-developers
      - group: sre-team
    mfaRequired: true
  
  - name: k8s-cluster-admin
    displayName: "Cluster Administrator"
    description: "Full cluster administration access"
    type: group
    approvalRequired: true
    approvers:
      - group: sre-managers
      - user: platform-lead@company.com
    minApprovers: 1
    maxDuration: 24h
    defaultDuration: 8h
    eligibleMembers:
      - group: sre-team
    mfaRequired: true
    requireJustification: true
    requireTicket: true
    notifyOnActivation:
      - security-team@company.com
  
  # ============================================================
  # LOCAL MACHINE GROUPS (Endpoint Security)
  # ============================================================
  
  - name: local-docker
    displayName: "Docker Access"
    description: "Access to Docker daemon on workstation"
    type: local-group
    approvalRequired: false
    maxDuration: 24h
    defaultDuration: 8h
    eligibleMembers:
      - group: developers
    targetGroups:  # OS-specific mappings
      windows:
        - docker-users
      linux:
        - docker
      macos:
        - docker
  
  - name: local-admin
    displayName: "Local Administrator"
    description: "Temporary local admin on workstation"
    type: local-group
    approvalRequired: true
    approvers:
      - group: it-managers
    maxDuration: 4h
    defaultDuration: 1h
    eligibleMembers:
      - group: employees
    targetGroups:
      windows:
        - Administrators
      linux:
        - sudo
        - wheel
      macos:
        - admin
    mfaRequired: true
    requireJustification: true
    notifyOnActivation:
      - security-team@company.com
  
  # ============================================================
  # AZURE AD GROUPS (Hybrid Cloud)
  # ============================================================
  
  - name: azure-subscription-contributors
    displayName: "Azure Subscription Contributors"
    description: "Contributor role on production subscription"
    type: azure-group
    azureGroupId: "12345678-1234-1234-1234-123456789abc"
    approvalRequired: true
    approvers:
      - group: cloud-admins
    maxDuration: 8h
    eligibleMembers:
      - group: sre-team
      - group: cloud-engineers
    mfaRequired: true
    requireJustification: true
    requireTicket: true
  
  # ============================================================
  # API SCOPES (OAuth2 APIs)
  # ============================================================
  
  - name: payment-api:admin
    displayName: "Payment API Admin"
    description: "Admin operations on payment API"
    type: api-scope
    apiIdentifier: "payment-api"  # Keycloak client ID
    scope: "admin"
    approvalRequired: true
    approvers:
      - group: finance-managers
      - group: platform-leads
    maxDuration: 2h
    defaultDuration: 1h
    eligibleMembers:
      - group: backend-developers
      - group: sre-team
    mfaRequired: true
    requireJustification: true
    requireTicket: true
    notifyOnActivation:
      - finance-team@company.com
    rateLimit:
      enabled: true
      requests: 1000
      window: 3600  # 1000 requests per hour
  
  - name: user-api:admin
    displayName: "User API Admin"
    description: "User management admin operations"
    type: api-scope
    apiIdentifier: "user-api"
    scope: "admin"
    approvalRequired: true
    approvers:
      - group: security-team
    maxDuration: 4h
    eligibleMembers:
      - group: sre-team
      - group: security-engineers
    mfaRequired: true
    auditExtraVerbose: true  # Log every API call
  
  - name: analytics-api:export
    displayName: "Analytics Export"
    description: "Export large datasets from analytics"
    type: api-scope
    apiIdentifier: "analytics-api"
    scope: "export"
    approvalRequired: false  # Self-service
    maxDuration: 8h
    eligibleMembers:
      - group: data-analysts
      - group: data-scientists
    requireJustification: true
    rateLimit:
      enabled: true
      requests: 10
      window: 28800  # Max 10 exports per session

# ============================================================
# GLOBAL PIM SETTINGS
# ============================================================

pimSettings:
  # Expiration warning
  expirationWarning: 15m
  
  # Max concurrent elevations per user
  maxConcurrentElevations: 3
  
  # Cool-down after deactivation
  cooldownPeriod: 5m
  
  # MFA re-verification interval
  mfaRevalidation: 12h
  
  # Audit log retention
  auditRetention: 2y
  
  # Notifications
  notifications:
    slack:
      webhook: https://hooks.slack.com/services/...
      channel: "#security-pim"
    email:
      recipients:
        - security-team@company.com
    teams:
      webhook: https://outlook.office.com/webhook/...
  
  # Break-glass accounts (bypass PIM)
  breakGlassAccounts:
    - emergency-admin@company.com
  
  # Automatic approval windows
  changeWindows:
    - name: "Tuesday/Thursday Deployments"
      schedule: "TUE,THU 20:00-22:00 UTC"
      autoApproveRoles:
        - k8s-production-write
        - production-deploy
```

### 2. Kubernetes RBAC Configuratie

```yaml
# kubernetes-pim-rbac.yaml

# Cluster Admin
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: pim-cluster-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: Group
  name: k8s-cluster-admin  # PIM-managed
  apiGroup: rbac.authorization.k8s.io

# Production Read
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: production-read
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: pim-production-read
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: production-read
subjects:
- kind: Group
  name: k8s-production-read  # PIM-managed

# Namespace-scoped
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pim-namespace-admin
  namespace: production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- kind: Group
  name: k8s-namespace-admin-production
```

---

## Implementatie

Zie [KEYCLOAK_PIM_IMPLEMENTATIE.md](KEYCLOAK_PIM_IMPLEMENTATIE.md) voor complete stap-voor-stap implementatie guide.

### Quick Start Overzicht

**1. Deploy Keycloak** (standaard Bitnami Helm chart)
```bash
helm install keycloak bitnami/keycloak --namespace auth
```

**2. Deploy PIM PostgreSQL Database**
```bash
kubectl apply -f pim-postgresql.yaml
kubectl -n auth exec -i deployment/pim-postgres -- psql -U pim -d keycloak_pim < pim-schema.sql
```

**3. Deploy PIM Controller**
```bash
docker build -t your-registry/pim-controller:latest pim-controller/
docker push your-registry/pim-controller:latest
kubectl apply -f pim-controller-deployment.yaml
```

**4. Deploy Cleanup CronJob**
```bash
kubectl apply -f pim-cleanup-cronjob.yaml
```

**5. Configure Keycloak** (maak PIM groepen aan)
```bash
# Via Admin UI of kcadm CLI
kubectl -n auth exec deployment/keycloak -- \
  /opt/keycloak/bin/kcadm.sh create groups -r production -s name=k8s-cluster-admin
```

**6. Deploy Privilege Agent** (op workstations)
```bash
# Zie PRIVILEGE_AGENT.md voor complete guide
curl -fsSL https://releases.itlusions.com/pim-agent/install-linux.sh | sudo bash
```

**7. Test de Setup**
```bash
itlc elevate --role=k8s-production-read --duration=2h --reason="Testing"
itlc whoami --show-pim
kubectl get pods --all-namespaces  # Should work
```

---

## Security & Compliance

### 1. MFA Enforcement

```yaml
roles:
  - name: cluster-admin
    mfaRequired: true
    mfaRevalidation: 12h  # Re-verify every 12h
```

Keycloak enforces MFA at authentication time. PIM checks `auth_time` claim in token.

### 2. Audit Logging

**Alle PIM acties worden gelogd:**
- Elevation requests (who, what, when, why, ticket)
- Approval decisions (approver, decision, comment)
- Activations (timestamp, duration, granted_by)
- Expirations (automatic or manual)
- Deactivations (who deactivated)
- Access attempts while elevated

**Log destinations:**
- PIM Controller database (PostgreSQL)
- Keycloak audit logs
- Kubernetes audit logs
- Local agent logs (endpoints)
- Azure AD audit logs (for AAD groups)
- API access logs (for scope elevations)
- Central SIEM (Splunk, ELK, etc.)

**Compliance reports:**
```bash
# Export full audit trail
itlc elevation audit --export=csv --output=pim-audit-2026-q1.csv

# Filter by user/role/timeframe
itlc elevation audit --user=john@company.com --last=30d

# Generate compliance report
itlc compliance report --standard=SOC2 --output=soc2-pim-report.pdf
```

### 3. Break-Glass Access

**Emergency accounts die PIM bypassen:**
```yaml
breakGlassAccounts:
  - emergency-admin@company.com  # Permanent cluster-admin
```

**Use case:** Keycloak down → kan niet elevaten → emergency account nodig om te fixen.

**Monitoring:** Elke gebruik van break-glass account triggert immediate alert naar security team.

### 4. Separation of Duties

```yaml
# Approvers kunnen NIET hun eigen requests approven
roles:
  - name: production-write
    approvers:
      - group: release-managers
    eligibleMembers:
      - group: developers  # Developers can request
    # Release managers (approvers) are NOT in developers group
```

### 5. Monitoring & Alerting

```yaml
alerts:
  # Long-duration elevations
  - condition: pim_elevation_duration > 4h
    action: notify_security_team
  
  # High frequency
  - condition: pim_elevation_count_per_user > 5/day
    action: flag_for_review
  
  # After-hours activity
  - condition: pim_elevation_after_hours
    action: notify_manager
  
  # Break-glass usage
  - condition: break_glass_account_used
    action: immediate_alert_security_team
    severity: critical
```

---

## Deployment & Rollout

### Migration Strategy

**Fase 1: Shadow Mode (2 weken)**
- Enable PIM maar enforce niet
- Permanente toegang blijft bestaan
- Track wie wat zou aanvragen (analytics)
- Measure approval latency
- Train approvers

**Fase 2: Soft Enforcement (1 maand)**
- Remove permanent cluster-admin from developers
- SRE team behoudt permanent toegang (fallback)
- Self-service roles enabled
- Monitor adoption en pain points

**Fase 3: Full Enforcement**
- Remove permanent admin van iedereen (behalve break-glass)
- All access via PIM
- Approval workflows actief
- Monitor compliance

### Gradual Rollout

**Week 1-2:** 10 pilot users (developers)
- Test basic flows
- Refine role definitions
- Fix UX issues

**Week 3-4:** Development team (50 users)
- Monitor approval latency
- Tune duration limits
- Train approvers

**Week 5-8:** All engineers (200 users)
- Full production rollout
- 24/7 support ready
- Escalation procedures

**Week 9+:** Complete organization
- Non-technical users (voor local-admin)
- Contractors/external users
- Quarterly access reviews

### Success Metrics

**Adoption:**
- % users using PIM vs permanent access
- Average time to elevation activation
- Self-service vs approval-required ratio

**Security:**
- Reduction in standing privileges
- Time-to-revocation (average elevation duration)
- Audit trail completeness

**Efficiency:**
- Average approval latency
- Requests denied (why?)
- Break-glass usage frequency

### Rollback Plan

Als PIM controller faalt:

1. **Immediate:** Break-glass accounts blijven werken
2. **Short-term:** Re-enable permanente toegang voor kritieke personen
3. **Fix:** Debug PIM controller, restore from backup
4. **Resume:** Gradual re-activation PIM enforcement

---

## Benefits vs. Permanent Access

| Aspect | Permanent Admin | JIT with PIM |
|--------|----------------|--------------|
| **Attack surface** | 24/7 exposure | Only when needed |
| **Blast radius** | High (always available) | Limited (time-boxed) |
| **Audit trail** | Login/logout only | Full justification + approval |
| **Compliance** | Difficult to justify | Clear (temporary, justified) |
| **Accountability** | Weak (who did what?) | Strong (reason + ticket) |
| **Credential theft** | Immediate full access | Must request elevation (detected) |
| **Insider threat** | High risk | Reduced (monitored, time-limited) |
| **Compliance cost** | High (quarterly reviews) | Low (automatic audit) |

### ROI Calculation

**Cost of permanent admin (100 users):**
- Quarterly access reviews: 40 hours/year × $150/hr = $6,000
- Compliance audit prep: 80 hours/year × $150/hr = $12,000
- Security incidents (avg 1/year): $50,000
- **Total:** $68,000/year

**Cost of PIM:**
- Implementation: $30,000 one-time
- Operational: $10,000/year (maintenance)
- **Savings:** $28,000/year (break-even after 13 months)

**Plus intangible benefits:**
- Reduced security incident probability (-50%)
- Faster compliance audits (-70% time)
- Better security posture (measurable)

---

## Troubleshooting

### PIM Controller Issues

```bash
# Check controller health
kubectl -n auth get pods -l app=pim-controller
kubectl -n auth logs deployment/pim-controller

# Database connectivity
kubectl -n auth exec deployment/pim-controller -- \
  psql -h pim-postgres -U pim -d keycloak_pim -c "SELECT COUNT(*) FROM pim_assignments;"

# Keycloak connectivity
kubectl -n auth exec deployment/pim-controller -- \
  curl -v http://keycloak:8080/health
```

### Elevation Not Working

```bash
# Check eligibility
itlc elevate --check --role=cluster-admin

# View detailed error
itlc elevate --role=cluster-admin --debug

# Check Keycloak groups
kubectl -n auth exec deployment/keycloak -- \
  /opt/keycloak/bin/kcadm.sh get groups -r production
```

### Agent Not Syncing (Local Groups)

```bash
# Check agent status
sudo systemctl status pim-agent

# Force immediate sync
sudo systemctl restart pim-agent

# Check connectivity to controller
curl -v https://pim.company.com/api/v1/health

# View agent logs
sudo journalctl -u pim-agent -f
```

### Approval Not Received

```bash
# Check pending requests
itlc approve list

# Verify notification config
kubectl -n auth get configmap pim-controller-config -o yaml | grep -A5 notifications

# Test webhook manually
curl -X POST https://hooks.slack.com/services/... -d '{"text":"Test"}'
```

---

## Next Steps

1. **[Privilege Agent Setup](PRIVILEGE_AGENT.md)** - Deploy agents op workstations
2. **[Keycloak PIM Implementatie](KEYCLOAK_PIM_IMPLEMENTATIE.md)** - Complete deployment guide
3. **[API Integration Guide](API_SCOPE_INTEGRATION.md)** - Integreer je APIs met PIM scopes
4. **[Azure AD Federation](AZURE_AD_FEDERATION.md)** - Configureer Azure AD integration

---

## Support & Community

- **GitHub:** https://github.com/ITlusions/ITLAuth
- **Discussions:** https://github.com/ITlusions/ITLAuth/discussions
- **Slack:** #itlauth-support
- **Docs:** https://docs.itlauth.com

---

**ITL PIM** - Privilege management zoals het hoort: temporary, justified, auditable.
