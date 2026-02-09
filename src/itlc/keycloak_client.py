"""
Keycloak Client for Token Management
Standalone client without Flask dependencies
"""
import requests
import os
from typing import Optional, Dict, Any
from pathlib import Path


class KeycloakClient:
    """
    Standalone Keycloak client for token operations.
    No Flask dependencies - works from CLI.
    """
    
    def __init__(self, keycloak_url: Optional[str] = None, realm: Optional[str] = None) -> None:
        self.keycloak_url = keycloak_url or os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        self.realm = realm or os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        # Remove trailing slash
        self.keycloak_url = self.keycloak_url.rstrip('/')
    
    def get_access_token(self, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """
        Get access token using client credentials flow.
        
        Args:
            client_id: Service account client ID
            client_secret: Service account client secret
            
        Returns:
            Token response dictionary or None on failure
        """
        try:
            token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
            
            response = requests.post(
                token_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def introspect_token(self, token: str, client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """
        Introspect a token to check validity.
        
        Args:
            token: Access token to introspect
            client_id: Client ID for authentication
            client_secret: Client secret for authentication
            
        Returns:
            Introspection result or None
        """
        try:
            introspect_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token/introspect"
            
            response = requests.post(
                introspect_url,
                data={
                    'token': token,
                    'client_id': client_id,
                    'client_secret': client_secret
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"Error introspecting token: {e}")
            return None
    
    def get_credentials_from_env(self) -> Optional[Dict[str, str]]:
        """
        Get credentials from environment variables.
        
        Tries multiple sources:
        1. KEYCLOAK_CLIENT_ID + KEYCLOAK_CLIENT_SECRET
        2. ITL_CLIENT_ID + ITL_CLIENT_SECRET
        3. Mounted secrets at /etc/secrets/keycloak/
        
        Returns:
            Dictionary with client_id and client_secret, or None
        """
        # Try Keycloak-prefixed env vars
        if os.getenv('KEYCLOAK_CLIENT_ID') and os.getenv('KEYCLOAK_CLIENT_SECRET'):
            return {
                'client_id': os.getenv('KEYCLOAK_CLIENT_ID'),
                'client_secret': os.getenv('KEYCLOAK_CLIENT_SECRET'),
                'source': 'environment'
            }
        
        # Try ITL-prefixed env vars
        if os.getenv('ITL_CLIENT_ID') and os.getenv('ITL_CLIENT_SECRET'):
            return {
                'client_id': os.getenv('ITL_CLIENT_ID'),
                'client_secret': os.getenv('ITL_CLIENT_SECRET'),
                'source': 'environment'
            }
        
        # Try mounted secrets (Kubernetes)
        secret_path = Path('/etc/secrets/keycloak')
        client_id_file = secret_path / 'client-id'
        client_secret_file = secret_path / 'client-secret'
        
        if client_id_file.exists() and client_secret_file.exists():
            try:
                return {
                    'client_id': client_id_file.read_text().strip(),
                    'client_secret': client_secret_file.read_text().strip(),
                    'source': 'mounted_secrets'
                }
            except Exception:
                pass
        
        return None
