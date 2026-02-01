"""
ITL Token Manager CLI
Azure kubelogin-inspired CLI for managing Keycloak API tokens
"""

__version__ = "1.0.0"
__author__ = "ITlusions"
__description__ = "Keycloak API Token Management CLI"

from .token_cache import TokenCache, token_cache
from .keycloak_client import KeycloakClient
from .interactive_auth import InteractiveAuth
from .controlplane_client import ControlPlaneClient
from .server_onboarding import ServerOnboardingClient
from .kubectl_oidc_setup import KubectlOIDCSetup
from .oidc_auth import OIDCConfig, get_oidc_token, output_credential

__all__ = [
    'TokenCache', 
    'token_cache', 
    'KeycloakClient', 
    'InteractiveAuth', 
    'ControlPlaneClient',
    'ServerOnboardingClient',
    'KubectlOIDCSetup',
    'OIDCConfig',
    'get_oidc_token',
    'output_credential'
]

