# Privileged Identity Management (PIM)

Complete gids voor Just-In-Time privilege elevation in Kubernetes, endpoints en cloud resources.

## 📚 Documentation Overview

### Getting Started

1. **[Complete PIM Guide](PRIVILEGE_ELEVATION_COMPLETE.md)** - Start hier!
   - Overzicht van alle 4 elevation types (Kubernetes, Local, Azure AD, API Scopes)
   - ITLC CLI commands
   - Configuratie voorbeelden
   - Security & compliance
   - Deployment strategie

### Implementation Guides

2. **[Keycloak PIM Implementation](KEYCLOAK_PIM_IMPLEMENTATIE.md)** (Nederlands)
   - Stap-voor-stap implementatie met standaard Keycloak Helm chart
   - PIM Controller deployment
   - Database setup
   - Geen custom Keycloak image nodig

3. **[Privilege Agent](PRIVILEGE_AGENT.md)**
   - Local privilege elevation op Windows/Linux/macOS
   - Software installatie ZONDER admin rechten
   - Custom package support
   - Installation service met 4 permission levels
   - Installatie & configuratie

### Legacy Documentation (Deprecated)

- `PIM_JUST_IN_TIME_ACCESS.md` → Replaced by `PRIVILEGE_ELEVATION_COMPLETE.md`
- `LOCAL_PRIVILEGE_AGENT.md` → Replaced by `PRIVILEGE_AGENT.md`

## 🎯 Quick Start

### For End Users
```bash
# Request temporary Kubernetes access
itlc elevate --role=cluster-admin --duration=2h --reason="Debug prod issue"

# Request software installation (no admin rights needed)
itlc install --app=docker-desktop --reason="Development setup"

# Request custom package (requires approval)
itlc install --custom --package="./tool.msi" --reason="Customer tool" --ticket=PROJ-123
```

### For Approvers
```bash
# List pending requests
itlc approve list

# Approve request
itlc approve 1 --comment="Approved for incident response"
```

### For Administrators
1. Deploy Keycloak + PIM Controller → [Keycloak PIM Implementatie](KEYCLOAK_PIM_IMPLEMENTATIE.md)
2. Deploy Privilege Agents on endpoints → [Privilege Agent](PRIVILEGE_AGENT.md)
3. Configure eligible roles and permissions → [Complete Guide](PRIVILEGE_ELEVATION_COMPLETE.md)

## 🏗️ Architecture

```
┌────────────────────────────────────────┐
│     Keycloak + PIM Controller          │
│  - Approval workflows                  │
│  - Eligible roles                      │
│  - Audit logging                       │
└───────────┬────────────────────────────┘
            │
    ┌───────┼────────┐
    │       │        │
    ▼       ▼        ▼
┌─────┐  ┌─────┐  ┌─────┐
│ K8s │  │ VMs │  │APIs │
└─────┘  └─────┘  └─────┘
```

## 🔐 Elevation Types

| Type | Scope | Approval | Use Case |
|------|-------|----------|----------|
| **Keycloak Groups** | Kubernetes RBAC | Optional | Temporary cluster access |
| **Local Groups** | Workstation/Server | Optional | Temporary admin rights |
| **Azure AD Groups** | Azure Resources | Required | Hybrid cloud access |
| **API Scopes** | OAuth2 APIs | Optional | Microservices auth |

## 📖 Related Documentation

- [Authentication Overview](../authentication/) - Token management & interactive login
- [Kubernetes Integration](../kubernetes/) - OIDC setup for K8s API server
- [Architecture](../architecture/) - Self-hosted security benefits

## 🆘 Support

- [Troubleshooting](../kubernetes/TROUBLESHOOTING.md)
- [GitHub Issues](https://github.com/ITlusions/ITLAuth/issues)
- [Discussions](https://github.com/ITlusions/ITLAuth/discussions)
