#!/usr/bin/env python3
"""
Kubernetes Credential Exec Plugin for OIDC Authentication

This module implements the Kubernetes credential exec protocol (client.authentication.k8s.io/v1beta1)
to provide OIDC tokens for kubectl authentication without requiring the kubelogin binary.

Usage in kubeconfig:
    users:
      - name: oidc-user
        user:
          exec:
            apiVersion: client.authentication.k8s.io/v1beta1
            command: python
            args:
              - -m
              - itl_kubectl_oidc_setup.auth
"""

import json
import sys
import os
import time
import webbrowser
import urllib.request
import urllib.parse
import hashlib
import base64
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import threading


class OIDCConfig:
    """OIDC configuration for ITlusions Keycloak."""
    ISSUER_URL = "https://sts.itlusions.com/realms/itlusions"
    CLIENT_ID = "kubernetes-oidc"
    REDIRECT_URI = "http://localhost:8000/callback"
    SCOPES = ["openid", "email", "profile", "groups"]
    TOKEN_CACHE_DIR = Path.home() / ".kube" / "cache" / "oidc"


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OIDC callback."""
    
    auth_code = None
    auth_error = None
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass
    
    def do_GET(self):
        """Handle callback GET request."""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            CallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">Authentication Successful!</h1>
                    <p>You can close this window and return to your terminal.</p>
                </body>
                </html>
            '''
            self.wfile.write(html.encode('utf-8'))
        elif 'error' in params:
            CallbackHandler.auth_error = params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_desc = params.get('error_description', ['Unknown error'])[0]
            html = f'''
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Authentication Failed</h1>
                    <p>Error: {error_desc}</p>
                </body>
                </html>
            '''
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def get_token_cache_path():
    """Get path to token cache file."""
    cache_dir = OIDCConfig.TOKEN_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "itlusions_token.json"


def load_cached_token():
    """Load cached token if available and valid."""
    cache_path = get_token_cache_path()
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r') as f:
            token_data = json.load(f)
        
        # Check if token is still valid (with 5 minute buffer)
        if 'expiry' in token_data:
            expiry = token_data['expiry']
            if time.time() < expiry - 300:  # 5 minute buffer
                return token_data
    except:
        pass
    
    return None


def save_token_cache(token_data):
    """Save token to cache."""
    cache_path = get_token_cache_path()
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(token_data, f)
        cache_path.chmod(0o600)  # Secure permissions
    except:
        pass  # Fail silently if we can't cache


def get_oidc_token():
    """Perform OIDC authentication flow and return token."""
    
    # Check cache first
    cached = load_cached_token()
    if cached and 'token' in cached:
        return cached['token'], cached.get('expiry')
    
    # Start local HTTP server for callback
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        
        # Build authorization URL
        auth_params = {
            'client_id': OIDCConfig.CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': OIDCConfig.REDIRECT_URI,
            'scope': ' '.join(OIDCConfig.SCOPES),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{OIDCConfig.ISSUER_URL}/protocol/openid-connect/auth?{urllib.parse.urlencode(auth_params)}"
        
        # Open browser for authentication
        print("🔐 Opening browser for authentication...", file=sys.stderr)
        print(f"   If browser doesn't open, visit: {auth_url}", file=sys.stderr)
        webbrowser.open(auth_url)
        
        # Wait for callback (max 2 minutes)
        timeout = 120
        start_time = time.time()
        
        while CallbackHandler.auth_code is None and CallbackHandler.auth_error is None:
            if time.time() - start_time > timeout:
                raise Exception("Authentication timeout - no response received")
            time.sleep(0.5)
        
        if CallbackHandler.auth_error:
            raise Exception(f"Authentication failed: {CallbackHandler.auth_error}")
        
        if not CallbackHandler.auth_code:
            raise Exception("No authorization code received")
        
        # Exchange code for token
        token_url = f"{OIDCConfig.ISSUER_URL}/protocol/openid-connect/token"
        token_params = {
            'grant_type': 'authorization_code',
            'code': CallbackHandler.auth_code,
            'redirect_uri': OIDCConfig.REDIRECT_URI,
            'client_id': OIDCConfig.CLIENT_ID,
            'code_verifier': code_verifier
        }
        
        data = urllib.parse.urlencode(token_params).encode()
        req = urllib.request.Request(token_url, data=data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            token_response = json.loads(response.read().decode())
        
        id_token = token_response.get('id_token')
        expires_in = token_response.get('expires_in', 3600)
        
        if not id_token:
            raise Exception("No ID token in response")
        
        # Calculate expiry
        expiry = int(time.time() + expires_in)
        
        # Cache token
        cache_data = {
            'token': id_token,
            'expiry': expiry,
            'refresh_token': token_response.get('refresh_token')
        }
        save_token_cache(cache_data)
        
        return id_token, expiry
        
    finally:
        server.shutdown()


def output_credential(token, expiry):
    """Output credential in ExecCredential format."""
    
    # Convert expiry to RFC3339 format
    from datetime import datetime, timezone
    expiry_time = datetime.fromtimestamp(expiry, tz=timezone.utc).isoformat()
    
    credential = {
        "apiVersion": "client.authentication.k8s.io/v1beta1",
        "kind": "ExecCredential",
        "status": {
            "token": token,
            "expirationTimestamp": expiry_time
        }
    }
    
    print(json.dumps(credential))


def main():
    """Main entry point for credential exec plugin."""
    try:
        # Check if running in interactive mode
        interactive = os.environ.get('KUBECTL_EXEC_INTERACTIVE_MODE') == 'IfAvailable'
        
        if not interactive:
            print("Error: This credential plugin requires interactive mode", file=sys.stderr)
            sys.exit(1)
        
        # Get OIDC token
        token, expiry = get_oidc_token()
        
        # Output credential
        output_credential(token, expiry)
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
