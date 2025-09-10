"""
itl-k8s-oidc: One-command setup for Kubernetes OIDC via Keycloak + kubelogin.

Automates installation of krew and oidc-login plugin, and configures
Kubernetes OIDC authentication.
"""

try:
    from importlib.metadata import version
except ImportError:
    # Python < 3.8
    from importlib_metadata import version

try:
    # Get version from package metadata
    __version__ = version("itl-k8s-oidc")
except Exception:
    # Fallback for development/editable installs
    __version__ = "1.0.2"