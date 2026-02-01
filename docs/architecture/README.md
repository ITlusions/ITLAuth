# Architecture & Design

High-level architecture documentation and design decisions for ITLAuth.

## 📚 Documentation

### Security

1. **[Self-Hosted Security](SELF_HOSTED_SECURITY.md)**
   - Why self-host authentication vs third-party SaaS
   - Security benefits & risks
   - Compliance considerations (GDPR, SOC2, HIPAA)
   - Cost analysis
   - Real-world examples

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    ITLAuth Architecture                    │
└────────────────────────────────────────────────────────────┘

┌──────────────┐
│   End Users  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│  ITLC CLI    │────▶│   Keycloak      │
│  (itlc)      │     │   (STS)         │
└──────┬───────┘     └────────┬────────┘
       │                      │
       │                      │
       ▼                      ▼
┌──────────────┐     ┌─────────────────┐
│  Kubernetes  │     │  PIM Controller │
│  API Server  │     │  + Agent        │
└──────────────┘     └─────────────────┘
```

## 🔐 Security Model

### Defense in Depth

1. **Authentication Layer** (Keycloak)
   - OIDC/OAuth2 standards
   - MFA support
   - Session management

2. **Authorization Layer** (Kubernetes RBAC + PIM)
   - Group-based permissions
   - Just-in-time access
   - Approval workflows

3. **Audit Layer**
   - Complete audit trail
   - Who/what/when/why
   - Compliance reporting

## 🎯 Design Principles

### 1. Zero Standing Privileges
- No permanent admin access
- Just-in-time elevation
- Automatic expiration

### 2. Least Privilege
- Granular permissions (4 levels)
- Role-based access
- Separation of duties

### 3. Defense in Depth
- Multi-layer security
- Approval workflows
- MFA enforcement

### 4. Complete Auditability
- All actions logged
- Immutable audit trail
- Compliance-ready

### 5. Self-Hosted Control
- On-premises or private cloud
- No third-party data sharing
- Regulatory compliance

## 📊 Deployment Models

### 1. On-Premises
```
Company Datacenter
├── Keycloak (HA)
├── PIM Controller
├── PostgreSQL (audit DB)
└── Privilege Agents (endpoints)
```

**Pros:**
- Complete data control
- Air-gapped environments
- Custom security policies

**Cons:**
- Infrastructure management
- Update management
- Higher initial cost

### 2. Private Cloud (Azure/AWS/GCP)
```
Private VPC/VNet
├── Keycloak (managed K8s)
├── PIM Controller (pods)
├── PostgreSQL (managed service)
└── Agents (VMs)
```

**Pros:**
- Managed infrastructure
- Scalability
- Disaster recovery

**Cons:**
- Cloud provider dependency
- Egress costs
- Compliance considerations

### 3. Hybrid
```
On-Prem                     Cloud
├── Keycloak (primary)  ←→  ├── Keycloak (replica)
├── Legacy apps             ├── Cloud workloads
└── Sensitive data          └── Development
```

**Pros:**
- Flexibility
- Gradual migration
- Risk distribution

**Cons:**
- Complexity
- Sync challenges
- Network requirements

## 🔄 Token Flow

```
1. User Request
   └─▶ itlc login

2. Authentication
   └─▶ Browser opens → Keycloak
   └─▶ User authenticates (+ MFA)
   └─▶ Keycloak issues tokens

3. Token Storage
   └─▶ ITLC caches tokens locally
   └─▶ Encrypted storage

4. API Request
   └─▶ kubectl get pods
   └─▶ kubectl exec: itlc get-token
   └─▶ Returns cached/refreshed token

5. API Server Validation
   └─▶ Validates JWT signature
   └─▶ Checks expiration
   └─▶ Extracts groups claim

6. RBAC Evaluation
   └─▶ Maps groups to roles
   └─▶ Authorizes request
   └─▶ Returns response
```

## 📖 Related Documentation

- [Self-Hosted Security](SELF_HOSTED_SECURITY.md) - Detailed security analysis
- [PIM](../pim/) - Privilege elevation architecture
- [Authentication](../authentication/) - Token management
- [Kubernetes](../kubernetes/) - K8s integration

## 📝 Decision Records

### Why Keycloak?
- ✅ Open-source (Apache 2.0)
- ✅ OIDC/OAuth2 compliant
- ✅ Enterprise features (MFA, federation)
- ✅ Self-hostable
- ✅ Active community

### Why Not Auth0/Okta?
- ❌ Third-party data custody
- ❌ Monthly costs per user
- ❌ Compliance restrictions
- ❌ Vendor lock-in
- ✅ Good for some use cases (SaaS apps)

### Why JWT Tokens?
- ✅ Stateless validation
- ✅ Standard format (RFC 7519)
- ✅ Contains claims (groups, roles)
- ✅ Short-lived security
- ✅ Kubernetes native support

### Why Client Credentials (Service Accounts)?
- ✅ Non-interactive auth
- ✅ CI/CD friendly
- ✅ Scoped permissions
- ✅ Revocable
- ✅ Auditable

## 🛡️ Threat Model

### Threats Mitigated
- ✅ Credential theft → Short-lived tokens
- ✅ Standing privileges → JIT elevation
- ✅ Insider threat → Complete audit + approval
- ✅ Lateral movement → Least privilege + segmentation

### Threats Considered
- ⚠️ Token theft → Short TTL + refresh rotation
- ⚠️ MitM attacks → TLS required
- ⚠️ Keycloak compromise → Defense in depth
- ⚠️ Phishing → MFA + approval workflows

### Out of Scope
- ❌ Physical security
- ❌ Endpoint compromise (handled by EDR)
- ❌ Network security (handled by firewalls)
- ❌ Application vulnerabilities
