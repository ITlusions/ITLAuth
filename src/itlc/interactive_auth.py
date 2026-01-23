"""
Interactive Authentication Module
Azure CLI-style browser-based login with PKCE flow
"""
import hashlib
import base64
import secrets
import webbrowser
import json
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from pathlib import Path
from typing import Optional, Dict, List
import threading
import time


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    auth_code = None
    
    def do_GET(self):
        """Handle OAuth callback"""
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            CallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Load success HTML template
            template_path = os.path.join(os.path.dirname(__file__), 'callback_success.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                success_html = f.read()
            
            self.wfile.write(success_html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Load error HTML template
            template_path = os.path.join(os.path.dirname(__file__), 'callback_error.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                error_html = f.read()
            
            self.wfile.write(error_html.encode())
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


class InteractiveAuth:
    """
    Interactive authentication with browser-based OAuth flow.
    Similar to Azure CLI 'az login' experience.
    """
    
    def __init__(self, keycloak_url: str, realm: str, client_id: str = 'itl-cli'):
        self.keycloak_url = keycloak_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.callback_port = 8765
        self.redirect_uri = f'http://localhost:{self.callback_port}/callback'
        
        # Context storage
        self.context_dir = Path.home() / '.itl'
        self.context_file = self.context_dir / 'context.json'
        self.context_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_pkce_pair(self) -> tuple:
        """Generate PKCE code verifier and challenge"""
        # Code verifier: 43-128 character random string
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Code challenge: base64url(sha256(code_verifier))
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def _start_callback_server(self) -> HTTPServer:
        """Start local HTTP server for OAuth callback"""
        server = HTTPServer(('localhost', self.callback_port), CallbackHandler)
        return server
    
    def login(self, realm: Optional[str] = None) -> Optional[Dict]:
        """
        Interactive login with browser.
        
        Args:
            realm: Optional realm to login to (overrides default)
            
        Returns:
            Token response or None on failure
        """
        if realm:
            self.realm = realm
        
        print(f"[*] Starting interactive login for realm: {self.realm}")
        
        # Generate PKCE pair
        code_verifier, code_challenge = self._generate_pkce_pair()
        
        # Build authorization URL
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        
        auth_url = (
            f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/auth"
            f"?{urlencode(auth_params)}"
        )
        
        # Start callback server
        server = self._start_callback_server()
        server_thread = threading.Thread(target=lambda: server.handle_request())
        server_thread.daemon = True
        server_thread.start()
        
        # Open browser
        print(f"[*] Opening browser for authentication...")
        print(f"[*] Listening on http://localhost:{self.callback_port}")
        print(f"\n    If browser doesn't open, visit:")
        print(f"    {auth_url}\n")
        
        webbrowser.open(auth_url)
        
        # Wait for callback
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while CallbackHandler.auth_code is None:
            if time.time() - start_time > timeout:
                print("[✗] Login timeout. Please try again.")
                server.server_close()
                return None
            time.sleep(0.5)
        
        auth_code = CallbackHandler.auth_code
        CallbackHandler.auth_code = None  # Reset for next login
        
        # Exchange code for token
        print("[*] Exchanging authorization code for token...")
        
        token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'code': auth_code,
            'code_verifier': code_verifier,
        }
        
        try:
            response = requests.post(token_url, data=token_data, timeout=10)
            
            if response.status_code == 200:
                token_response = response.json()
                print("[✓] Login successful!")
                
                # Save context
                self._save_context(token_response)
                
                return token_response
            else:
                print(f"[✗] Token exchange failed: {response.status_code}")
                print(f"    {response.text}")
                return None
                
        except Exception as e:
            print(f"[✗] Token exchange error: {e}")
            return None
        finally:
            server.server_close()
    
    def _save_context(self, token_response: Dict):
        """Save authentication context"""
        context = {
            'realm': self.realm,
            'keycloak_url': self.keycloak_url,
            'access_token': token_response.get('access_token'),
            'refresh_token': token_response.get('refresh_token'),
            'id_token': token_response.get('id_token'),
            'token_type': token_response.get('token_type', 'Bearer'),
            'expires_in': token_response.get('expires_in', 3600),
            'scope': token_response.get('scope', ''),
        }
        
        with open(self.context_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        print(f"[*] Context saved to {self.context_file}")
    
    def get_context(self) -> Optional[Dict]:
        """Get saved authentication context"""
        if not self.context_file.exists():
            return None
        
        try:
            with open(self.context_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def clear_context(self):
        """Clear saved authentication context"""
        if self.context_file.exists():
            self.context_file.unlink()
    
    def list_realms(self) -> List[str]:
        """
        List realms where user has authenticated.
        
        Security Note: Users can only see realms they've successfully authenticated to.
        This provides realm isolation - users in realm X cannot see realms Y or Z.
        
        Returns:
            List of realm names the user has access to
        """
        try:
            realms = []
            
            # Get current context
            context = self.get_context()
            if not context:
                print("[!] Not logged in. Run 'itlc login' first.")
                return []
            
            # Return only the realm the user is currently authenticated to
            # This ensures realm isolation - users can only see realms they have access to
            current_realm = context.get('realm', self.realm)
            if current_realm:
                realms.append(current_realm)
            
            # Note: Multi-realm support would require:
            # 1. Storing authentication contexts for multiple realms
            # 2. User having valid credentials/tokens for each realm
            # 3. Each realm's Keycloak client allowing the user access
            
            return realms
            
        except Exception as e:
            print(f"[✗] Failed to list realms: {e}")
            return []
    
    def discover_realms(self, keycloak_url: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Discover all available realms on the Keycloak server.
        
        This queries public Keycloak endpoints to discover realms without authentication.
        Use this to find realms before logging in.
        
        Args:
            keycloak_url: Keycloak server URL (defaults to self.keycloak_url)
            
        Returns:
            List of dictionaries with realm info (name, enabled status)
        """
        try:
            url = keycloak_url or self.keycloak_url
            
            # Try the realms endpoint (may require admin access on some Keycloak versions)
            realms_url = f"{url}/admin/realms"
            
            # First, try to get master realm's well-known config to verify server is accessible
            well_known_url = f"{url}/realms/master/.well-known/openid-configuration"
            
            try:
                response = requests.get(well_known_url, timeout=5)
                if response.status_code != 200:
                    print(f"[!] Keycloak server not accessible at {url}")
                    return []
            except requests.RequestException as e:
                print(f"[✗] Cannot reach Keycloak server: {e}")
                return []
            
            # Try to discover realms by attempting to access their well-known configs
            # Common realm names to try
            potential_realms = ['master', 'itlusions', 'itldev', 'production', 'staging', 'development']
            
            discovered_realms = []
            
            print(f"[*] Discovering realms on {url}...")
            
            for realm_name in potential_realms:
                realm_well_known = f"{url}/realms/{realm_name}/.well-known/openid-configuration"
                try:
                    response = requests.get(realm_well_known, timeout=2)
                    if response.status_code == 200:
                        config = response.json()
                        discovered_realms.append({
                            'name': realm_name,
                            'enabled': True,
                            'issuer': config.get('issuer', '')
                        })
                except requests.RequestException:
                    # Realm doesn't exist or not accessible
                    pass
            
            return discovered_realms
            
        except Exception as e:
            print(f"[✗] Failed to discover realms: {e}")
            return []
    
    def set_realm(self, realm: str) -> bool:
        """
        Set default realm in context.
        
        Args:
            realm: Realm name to set as default
            
        Returns:
            True if successful
        """
        context = self.get_context()
        if not context:
            print("[!] Not logged in. Run 'itlc login' first.")
            return False
        
        # Update realm in context
        context['realm'] = realm
        
        try:
            with open(self.context_file, 'w') as f:
                json.dump(context, f, indent=2)
            
            print(f"[✓] Default realm set to: {realm}")
            return True
            
        except Exception as e:
            print(f"[✗] Failed to set realm: {e}")
            return False
    
    def refresh_token(self) -> Optional[Dict]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token response or None
        """
        context = self.get_context()
        if not context or not context.get('refresh_token'):
            return None
        
        token_url = f"{self.keycloak_url}/realms/{context['realm']}/protocol/openid-connect/token"
        
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': context['refresh_token'],
        }
        
        try:
            response = requests.post(token_url, data=token_data, timeout=10)
            
            if response.status_code == 200:
                token_response = response.json()
                self._save_context(token_response)
                return token_response
            else:
                return None
                
        except Exception:
            return None
