"""
ITlusions Kubernetes OIDC Setup Tool

A command-line tool that automatically installs and configures kubectl 
with OIDC authentication for ITlusions Kubernetes clusters using Keycloak.

Features:
- Automatic kubectl installation (if needed)
- kubelogin plugin installation 
- OIDC configuration for ITlusions Keycloak
- Cross-platform support (Windows, macOS, Linux)
- Interactive setup and testing

Usage:
    kubectl-oidc-setup
    kubectl-oidc-setup --cluster my-cluster
    kubectl-oidc-setup --no-test
"""

__version__ = "1.0.0"
__author__ = "ITlusions"
__email__ = "info@itlusions.com"
__url__ = "https://github.com/ITlusions/itl-kubectl-oidc-setup"