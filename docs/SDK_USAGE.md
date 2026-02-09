# ITLAuth SDK Usage Examples

This document provides examples for using the ITLAuth Keycloak Client SDK.

## Installation

```bash
pip install itl-kubectl-oidc-setup
```

Or from source:

```bash
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth
pip install -e .
```

## Quick Start

### Basic Token Acquisition (Client Credentials)

```python
from itlc import KeycloakClient

# Create client with default settings (ITlusions STS)
client = KeycloakClient()

# Get access token using client credentials
token_response = client.get_access_token(
    client_id='your-service-account',
    client_secret='your-secret'
)

if token_response:
    access_token = token_response['access_token']
    print(f"Token acquired: {access_token[:20]}...")
    print(f"Expires in: {token_response['expires_in']} seconds")
else:
    print("Failed to acquire token")
```

### Custom Keycloak Server

```python
from itlc import KeycloakClient

# Use custom Keycloak server and realm
client = KeycloakClient(
    keycloak_url='https://your-keycloak.example.com',
    realm='your-realm'
)

token_response = client.get_access_token(
    client_id='my-app',
    client_secret='secret'
)
```

### Token Introspection

```python
from itlc import KeycloakClient

client = KeycloakClient()

# Introspect a token to check if it's valid
introspection = client.introspect_token(
    token='your-access-token',
    client_id='your-client-id',
    client_secret='your-secret'
)

if introspection and introspection.get('active'):
    print("Token is valid")
    print(f"Username: {introspection.get('username')}")
    print(f"Client: {introspection.get('client_id')}")
    print(f"Scopes: {introspection.get('scope')}")
else:
    print("Token is invalid or expired")
```

### Environment-based Credentials

```python
import os
from itlc import KeycloakClient

# Set credentials via environment variables
os.environ['KEYCLOAK_CLIENT_ID'] = 'my-service-account'
os.environ['KEYCLOAK_CLIENT_SECRET'] = 'my-secret'

client = KeycloakClient()

# Discover credentials from environment
credentials = client.get_credentials_from_env()

if credentials:
    print(f"Found credentials from: {credentials['source']}")
    
    # Use discovered credentials
    token = client.get_access_token(
        credentials['client_id'],
        credentials['client_secret']
    )
```

### Token Caching

```python
from itlc import KeycloakClient, TokenCache

client = KeycloakClient()
cache = TokenCache()

client_id = 'my-service'
client_secret = 'my-secret'

# Check cache first
cached_token = cache.get_token(client_id)

if cached_token and cached_token.get('access_token'):
    print("Using cached token")
    token = cached_token['access_token']
else:
    print("Getting new token")
    token_response = client.get_access_token(client_id, client_secret)
    
    if token_response:
        # Save to cache
        cache.save_token(client_id, token_response)
        token = token_response['access_token']
```

### Interactive Authentication (Browser-based PKCE)

```python
from itlc import InteractiveAuth

# Create interactive auth handler
auth = InteractiveAuth(
    keycloak_url='https://sts.itlusions.com',
    realm='itlusions',
    client_id='itl-cli'
)

# Login via browser (opens browser for OAuth flow)
context = auth.login()

if context:
    print(f"Logged in as: {context['user']['preferred_username']}")
    print(f"Email: {context['user']['email']}")
    
    # Access token is available
    access_token = context['access_token']
else:
    print("Login failed or was cancelled")

# Check current login status
current_context = auth.get_current_context()
if current_context:
    print("Already logged in!")

# Logout
auth.logout()
```

## Complete Example: Service Account Token with Caching

```python
#!/usr/bin/env python3
"""
Complete example: Get token with automatic caching
"""
from itlc import KeycloakClient, TokenCache
import os

def get_api_token():
    """
    Get API token with automatic caching.
    Returns access token or None.
    """
    # Initialize client and cache
    client = KeycloakClient(
        keycloak_url=os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com'),
        realm=os.getenv('KEYCLOAK_REALM', 'itlusions')
    )
    cache = TokenCache()
    
    # Try to get credentials from environment
    credentials = client.get_credentials_from_env()
    
    if not credentials:
        print("No credentials found in environment")
        print("Set KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET")
        return None
    
    client_id = credentials['client_id']
    client_secret = credentials['client_secret']
    
    # Check cache first
    cached = cache.get_token(client_id)
    if cached:
        print(f"Using cached token (expires at {cached['expires_at']})")
        return cached['access_token']
    
    # Get new token
    print("Fetching new token...")
    token_response = client.get_access_token(client_id, client_secret)
    
    if not token_response:
        print("Failed to get access token")
        return None
    
    # Cache the token
    cache.save_token(client_id, token_response)
    print(f"Token cached (expires in {token_response['expires_in']}s)")
    
    return token_response['access_token']

if __name__ == '__main__':
    token = get_api_token()
    if token:
        print(f"\nSuccess! Token: {token[:30]}...")
    else:
        print("\nFailed to get token")
```

## Error Handling

```python
from itlc import KeycloakClient
import requests

client = KeycloakClient()

try:
    token = client.get_access_token('client-id', 'client-secret')
    
    if token is None:
        print("Authentication failed - check credentials")
    else:
        print("Success!")
        
except requests.exceptions.Timeout:
    print("Request timed out - check network connection")
except requests.exceptions.ConnectionError:
    print("Connection error - Keycloak server may be down")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Type Hints

The SDK includes comprehensive type hints for better IDE support:

```python
from typing import Optional, Dict, Any
from itlc import KeycloakClient

def get_token(client: KeycloakClient) -> Optional[Dict[str, Any]]:
    """
    Type-safe token acquisition
    """
    return client.get_access_token('client', 'secret')
```

## Integration with Control Plane API

```python
from itlc import KeycloakClient, TokenCache
import requests

def call_control_plane_api(endpoint: str) -> dict:
    """
    Call Control Plane API with automatic token management
    """
    client = KeycloakClient()
    cache = TokenCache()
    
    # Get credentials
    creds = client.get_credentials_from_env()
    if not creds:
        raise ValueError("No credentials configured")
    
    # Get cached or fresh token
    cached = cache.get_token(creds['client_id'])
    if cached:
        token = cached['access_token']
    else:
        token_resp = client.get_access_token(
            creds['client_id'],
            creds['client_secret']
        )
        cache.save_token(creds['client_id'], token_resp)
        token = token_resp['access_token']
    
    # Call API
    response = requests.get(
        f"https://api.example.com{endpoint}",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    return response.json()
```

## Environment Variables

The SDK supports multiple environment variable formats:

### Keycloak-prefixed (Priority 1)
```bash
export KEYCLOAK_URL="https://sts.example.com"
export KEYCLOAK_REALM="production"
export KEYCLOAK_CLIENT_ID="my-app"
export KEYCLOAK_CLIENT_SECRET="secret"
```

### ITL-prefixed (Priority 2)
```bash
export ITL_CLIENT_ID="my-app"
export ITL_CLIENT_SECRET="secret"
```

### Mounted Secrets (Priority 3 - Kubernetes)
Credentials at:
- `/etc/secrets/keycloak/client-id`
- `/etc/secrets/keycloak/client-secret`

## Testing

The SDK includes comprehensive tests:

```bash
# Run all tests
pytest tests/test_keycloak_client.py -v

# Run with coverage
pytest tests/test_keycloak_client.py --cov=itlc.keycloak_client --cov-report=term-missing

# Run specific test class
pytest tests/test_keycloak_client.py::TestKeycloakClientInit -v
```

## Additional Resources

- [ITLAuth README](../README.md) - Main documentation
- [Token CLI Documentation](../src/itlc/README.md) - CLI tool guide
- [API Reference](../docs/) - Full API documentation
- [GitHub Repository](https://github.com/ITlusions/ITLAuth) - Source code

## Support

For issues or questions:
- GitHub Issues: https://github.com/ITlusions/ITLAuth/issues
- Email: info@itlusions.com
