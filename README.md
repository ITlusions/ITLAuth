# ITLC - ITL Control Plane CLI

**Keycloak authentication and resource management CLI for ITlusions**

## Quick Start

```bash
# Install
pip install itlc

# Setup OIDC authentication for kubectl
itlc configure oidc

# Interactive login
itlc login

# Check current user
itlc whoami

# Get service account token
itlc get-token --client-id=my-app --client-secret=secret
```

## Features

- **Interactive Authentication** - Browser-based OAuth login (Azure CLI-style)
- **Token Management** - Automatic caching and refresh
- **Realm Management** - Multi-tenant realm switching
- **Core Resource Management** - Tenants, subscriptions, resource groups, management groups, locations
- **Kubernetes Integration** - OIDC authentication for kubectl
- **Service Accounts** - CI/CD automation support
- **Cluster Management** - Register and manage Kubernetes clusters

## Installation

### From Source

```bash
git clone https://github.com/ITlusions/ITL.ControlPlane.Cli.git
cd ITL.ControlPlane.Cli
pip install -e .
```

### Using pip (when published)

```bash
pip install itlc
```

## Documentation

📚 **Complete documentation is available in the [docs/](docs/) folder:**

- [Getting Started](docs/getting-started/README.md) - Installation and setup
- [Authentication](docs/authentication/README.md) - Login, tokens, and realms
- [Kubernetes Integration](docs/kubernetes/README.md) - OIDC setup and kubectl
- [Core Resources](docs/CORE_RESOURCES.md) - Tenants, subscriptions, resource groups via API Gateway
- [Resource Management](docs/RESOURCE_MANAGEMENT.md) - Control Plane resources (legacy)
- [Architecture](docs/architecture/README.md) - Design and security
- [Examples](docs/examples/) - Configuration examples
- [Scripts](docs/scripts/) - Automation scripts
- [Archive](docs/archive/) - Additional guides and references

## Environment Variables

```bash
export KEYCLOAK_URL=https://sts.itlusions.com       # Keycloak server
export KEYCLOAK_REALM=itlusions                     # Keycloak realm
export KEYCLOAK_CLIENT_ID=my-app                    # Service account client ID
export KEYCLOAK_CLIENT_SECRET=secret                # Service account secret
export CONTROLPLANE_URL=http://localhost:8000       # Control Plane API (direct)
export CONTROLPLANE_GATEWAY_URL=https://api.itlusions.com  # API Gateway
```

## Common Commands

### Authentication

```bash
# Interactive login
itlc login

# Check current user
itlc whoami

# Logout
itlc logout
```

### Token Management

```bash
# Get access token
itlc get-token

# Inspect JWT token
itlc inspect <token> --decode

# List cached tokens
itlc cache-list

# Clear cache
itlc clear-cache --all
```

### Realm Management

```bash
# List available realms
itlc realm list

# Switch realm
itlc realm set production

# Show realm info
itlc realm info
```

### Resource Management

```bash
# Create tenant
itlc tenant create my-tenant --display-name "My Tenant" --domain mycompany.com

# List tenants
itlc tenant list

# Create subscription
itlc subscription create my-sub --display-name "My Subscription" --tenant-id my-tenant

# List subscriptions
itlc subscription list

# Create resource group
itlc resourcegroup create my-rg my-sub --location westeurope

# Create management group hierarchy
itlc managementgroup create root-mg --display-name "Organization Root"
itlc managementgroup create platform-mg --display-name "Platform" --parent-id root-mg

# List management groups
itlc managementgroup list

# List locations
itlc location list

# Create custom location
itlc location create my-datacenter --display-name "My Datacenter" --region "Netherlands" --location-type DataCenter
```

### Kubernetes Clusters

```bash
# Setup OIDC authentication
itlc configure oidc

# List registered clusters
itlc cluster list

# Add cluster
itlc cluster add --name k8s-prod --server https://api.k8s.example.com

# Use with kubectl
kubectl --context=k8s-prod get nodes
```

## Development

```bash
# Clone repository
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth

# Install in development mode
pip install -e .

# Run tests
pytest

# Run specific test
python -m unittest tests.test_basic
```

## Project Structure

```
ITL.ControlPlane.Cli/
├── src/itlc/              # Main CLI package
│   ├── __main__.py        # CLI entry point
│   ├── keycloak_client.py # Keycloak integration
│   ├── interactive_auth.py# Browser-based login
│   ├── token_cache.py     # Token caching
│   ├── controlplane_client.py  # Control Plane API
│   ├── core_commands.py   # Core resource commands
│   └── ...                # Other modules
├── docs/                  # Documentation
├── tests/                 # Test suite
├── pyproject.toml         # Package configuration
├── setup.py               # Setup script
└── README.md              # This file
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **Documentation**: [docs/](docs/)
- **Repository**: https://github.com/ITlusions/ITL.ControlPlane.Cli
- **Issues**: https://github.com/ITlusions/ITL.ControlPlane.Cli/issues
- **ITlusions**: https://www.itlusions.com

---

**Made by [ITlusions](https://www.itlusions.com)** - Kubernetes • OIDC • Keycloak • Enterprise Auth
