#!/usr/bin/env python3
"""
ITL Token Manager CLI
Azure kubelogin-inspired CLI for managing Keycloak API tokens
"""
import click
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from .keycloak_client import KeycloakClient
from .token_cache import token_cache
from .interactive_auth import InteractiveAuth
from .clusters import ClustersManager, OIDC_CONTEXTS
from .cluster_commands import cluster


ASCII_BANNER = r"""
  _____ _______ _       ______ _      _____ 
 |_   _|__   __| |     / ____/| |    |_   _|
   | |    | |  | |    | |     | |      | |  
   | |    | |  | |    | |     | |      | |  
  _| |_   | |  | |____| |____ | |____ _| |_ 
 |_____|  |_|  |______|\_____/|______|_____|
                                             
    ITLusions Token Manager v1.0.0
    Keycloak Authentication CLI
"""


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_banner():
    """Print ASCII banner"""
    click.echo(f"{Colors.CYAN}{ASCII_BANNER}{Colors.END}")


def print_success(msg):
    click.echo(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg):
    click.echo(f"{Colors.RED}✗{Colors.END} {msg}", err=True)


def print_info(msg):
    click.echo(f"{Colors.CYAN}ℹ{Colors.END} {msg}")


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version='1.0.0')
def cli(ctx):
    """
    ITL Token Manager - Keycloak API Token Management CLI
    
    Manage API tokens for ITlusions services using Keycloak service accounts.
    Similar to Azure's 'az' CLI but for Keycloak.
    
    Environment Variables:
        KEYCLOAK_URL              Keycloak server URL (default: https://sts.itlusions.com)
        KEYCLOAK_REALM            Keycloak realm (default: itlusions)
        KEYCLOAK_CLIENT_ID        Service account client ID
        KEYCLOAK_CLIENT_SECRET    Service account client secret
    
    Examples:
        # Get token using credentials
        itlc get-token --client-id=my-app --client-secret=secret
        
        # Interactive login
        itlc login
        
        # Check current user
        itlc whoami
    """
    # Show banner only when no command is provided (help screen)
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo(ctx.get_help())


@cli.command()
@click.option('--client-id', help='Service account client ID')
@click.option('--client-secret', help='Service account client secret')
@click.option('--output', '-o', type=click.Choice(['json', 'token', 'table']), default='token',
              help='Output format')
@click.option('--realm', help='Keycloak realm')
@click.option('--keycloak-url', help='Keycloak URL')
@click.option('--no-cache', is_flag=True, help='Skip cache, always get fresh token')
def get_token(client_id, client_secret, output, realm, keycloak_url, no_cache):
    """
    Get access token for a service account.
    
    Credentials can be provided via options or environment variables:
      - KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET
      - ITL_CLIENT_ID and ITL_CLIENT_SECRET
      - Mounted secrets at /etc/secrets/keycloak/
    
    Examples:
        # Using command line options
        itlc get-token --client-id=my-app --client-secret=secret
        
        # Using environment variables
        export KEYCLOAK_CLIENT_ID=my-app
        export KEYCLOAK_CLIENT_SECRET=secret
        itlc get-token
        
        # JSON output for scripting
        itlc get-token --output=json
    """
    try:
        # Initialize Keycloak client
        client = KeycloakClient(keycloak_url, realm)
        
        # Get credentials from options or environment
        if not client_id or not client_secret:
            creds = client.get_credentials_from_env()
            if not creds:
                print_error("No credentials provided")
                print_info("Set KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET environment variables")
                print_info("Or use --client-id and --client-secret options")
                sys.exit(1)
            client_id = creds['client_id']
            client_secret = creds['client_secret']
        
        # Check cache first (unless --no-cache)
        if not no_cache:
            cached = token_cache.get_token(client_id)
            if cached:
                if output == 'token':
                    click.echo(cached['access_token'])
                elif output == 'json':
                    click.echo(json.dumps(cached, indent=2))
                elif output == 'table':
                    print_info("Using cached token")
                    click.echo(f"\nClient ID: {client_id}")
                    click.echo(f"Token Type: {cached.get('token_type', 'Bearer')}")
                    click.echo(f"Expires: {cached.get('expires_at')}")
                    click.echo(f"Token: {cached['access_token'][:30]}...{cached['access_token'][-20:]}")
                return
        
        # Get fresh token from Keycloak
        token_data = client.get_access_token(client_id, client_secret)
        
        if not token_data:
            print_error("Failed to get access token")
            sys.exit(1)
        
        # Cache the token
        token_cache.save_token(client_id, token_data)
        
        access_token = token_data['access_token']
        
        if output == 'token':
            click.echo(access_token)
        elif output == 'json':
            click.echo(json.dumps(token_data, indent=2))
        elif output == 'table':
            print_success("Access token acquired")
            click.echo(f"\nClient ID: {client_id}")
            click.echo(f"Token Type: {token_data.get('token_type', 'Bearer')}")
            click.echo(f"Expires In: {token_data.get('expires_in', 'unknown')} seconds")
            click.echo(f"Token: {access_token[:30]}...{access_token[-20:]}")
            click.echo(f"\nUsage:")
            click.echo(f'  curl -H "Authorization: Bearer {access_token}" <API_URL>')
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('token')
@click.option('--decode', is_flag=True, help='Decode JWT payload')
def inspect(token, decode):
    """
    Inspect a JWT token.
    
    Examples:
        # Basic inspection
        itl-token inspect <token>
        
        # Decode JWT header and payload
        itl-token inspect <token> --decode
    """
    try:
        if decode:
            # Decode JWT
            import base64
            parts = token.split('.')
            if len(parts) != 3:
                print_error("Invalid JWT token format")
                sys.exit(1)
            
            # Decode header and payload
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            
            click.echo(f"\n{Colors.BOLD}JWT Header:{Colors.END}")
            click.echo(json.dumps(header, indent=2))
            
            click.echo(f"\n{Colors.BOLD}JWT Payload:{Colors.END}")
            click.echo(json.dumps(payload, indent=2))
            
            # Show expiry
            if 'exp' in payload:
                exp_time = datetime.fromtimestamp(payload['exp'])
                now = datetime.now()
                if exp_time > now:
                    diff = exp_time - now
                    print_success(f"\nToken expires in: {diff}")
                else:
                    print_error(f"\nToken expired: {exp_time}")
        else:
            # Basic info
            click.echo(f"\nToken length: {len(token)} characters")
            click.echo(f"Token prefix: {token[:20]}...")
            click.echo(f"Token suffix: ...{token[-20:]}")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('token')
@click.option('--client-id', help='Client ID for introspection')
@click.option('--client-secret', help='Client secret for introspection')
@click.option('--realm', help='Keycloak realm')
@click.option('--keycloak-url', help='Keycloak URL')
def introspect(token, client_id, client_secret, realm, keycloak_url):
    """
    Introspect a token using Keycloak's introspection endpoint.
    
    Validates token and returns detailed information from Keycloak.
    
    Example:
        itl-token introspect <token> --client-id=<id> --client-secret=<secret>
    """
    try:
        client = KeycloakClient(keycloak_url, realm)
        
        if not client_id or not client_secret:
            creds = client.get_credentials_from_env()
            if not creds:
                print_error("--client-id and --client-secret required")
                print_info("Or set KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET")
                sys.exit(1)
            client_id = creds['client_id']
            client_secret = creds['client_secret']
        
        result = client.introspect_token(token, client_id, client_secret)
        
        if not result:
            print_error("Token introspection failed")
            sys.exit(1)
        
        click.echo(json.dumps(result, indent=2))
        
        if result.get('active'):
            print_success("\nToken is active")
        else:
            print_error("\nToken is not active")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--all', 'all_cache', is_flag=True, help='Clear all cached tokens')
def clear_cache(all_cache):
    """
    Clear token cache.
    
    Example:
        itl-token clear-cache --all
    """
    try:
        if all_cache:
            token_cache.clear_all()
            print_success("All cached tokens cleared")
        else:
            print_info("Use --all to clear all cached tokens")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
def config():
    """
    Show current configuration.
    
    Displays environment variables and cache location.
    """
    click.echo(f"\n{Colors.BOLD}ITL Token Manager Configuration:{Colors.END}\n")
    
    # Environment variables
    click.echo(f"Keycloak URL: {os.getenv('KEYCLOAK_URL', 'Not set (default: https://sts.itlusions.com)')}")
    click.echo(f"Keycloak Realm: {os.getenv('KEYCLOAK_REALM', 'Not set (default: itlusions)')}")
    click.echo(f"Client ID: {os.getenv('KEYCLOAK_CLIENT_ID') or os.getenv('ITL_CLIENT_ID', 'Not set')}")
    click.echo(f"Client Secret: {'***' if (os.getenv('KEYCLOAK_CLIENT_SECRET') or os.getenv('ITL_CLIENT_SECRET')) else 'Not set'}")
    
    # Cache directory
    cache_dir = token_cache.cache_dir
    click.echo(f"\nCache Directory: {cache_dir}")
    click.echo(f"Cache Exists: {cache_dir.exists()}")
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob('*.json'))
        click.echo(f"Cached Tokens: {len(cache_files)}")
        
        if cache_files:
            click.echo(f"\n{Colors.BOLD}Cached Tokens:{Colors.END}")
            for cached in token_cache.list_cached():
                click.echo(f"  • {cached['client_id']} (expires: {cached['expires_at']})")


@cli.command()
def cache_list():
    """
    List all cached tokens.
    
    Shows cached tokens with expiry information.
    """
    try:
        cached_tokens = token_cache.list_cached()
        
        if not cached_tokens:
            print_info("No cached tokens")
            return
        
        click.echo(f"\n{Colors.BOLD}Cached Tokens:{Colors.END}\n")
        click.echo(f"{'CLIENT ID':<40} {'CACHED AT':<25} {'EXPIRES AT':<25}")
        click.echo("-" * 90)
        
        for token in cached_tokens:
            click.echo(f"{token['client_id']:<40} {token['cached_at']:<25} {token['expires_at']:<25}")
        
        click.echo()
        print_success(f"Found {len(cached_tokens)} cached tokens")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--realm', help='Realm to login to')
@click.option('--keycloak-url', help='Keycloak URL')
def login(realm, keycloak_url):
    """
    Interactive login with browser (Azure CLI-style).
    
    Opens browser for authentication, similar to 'az login'.
    Supports multi-realm/tenant selection.
    
    Examples:
        # Login to default realm
        itlc login
        
        # Login to specific realm
        itlc login --realm=production
        
        # Login to different Keycloak instance
        itlc login --keycloak-url=https://auth.example.com
    """
    try:
        keycloak_url = keycloak_url or os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        realm = realm or os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, realm)
        token_response = auth.login(realm)
        
        if token_response:
            print_success("Authentication successful!")
            print_info(f"Realm: {realm}")
            print_info(f"Token saved to context")
            print_info(f"\nUse 'itlc whoami' to see user info")
        else:
            print_error("Authentication failed")
            sys.exit(1)
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.group()
def realm():
    """
    Manage Keycloak realm/tenant configuration.
    
    Similar to Azure CLI 'az account' commands for managing subscriptions/tenants.
    """
    pass


@realm.command('list')
def realm_list():
    """
    List realms where you are authenticated.
    
    Security: Only shows realms you've successfully logged into.
    Users in realm X cannot see realms Y or Z (realm isolation).
    
    Similar to 'az account list' in Azure CLI.
    
    Example:
        itlc realm list
    """
    try:
        keycloak_url = os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        realm_name = os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, realm_name)
        realms = auth.list_realms()
        
        if realms:
            click.echo(f"\n{Colors.BOLD}Authenticated Realms:{Colors.END}\n")
            for r in realms:
                # Check if current realm
                context = auth.get_context()
                is_current = context and context.get('realm') == r
                marker = f"{Colors.GREEN}*{Colors.END} " if is_current else "  "
                click.echo(f"{marker}{r}")
            click.echo()
            print_info("You can only see realms you've authenticated to (realm isolation)")
        else:
            print_info("Not authenticated to any realm. Run 'itlc login' first.")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@realm.command('discover')
@click.option('--server', help='Keycloak server URL (default: https://sts.itlusions.com)')
def realm_discover(server):
    """
    Discover available realms on Keycloak server.
    
    Queries the Keycloak server to find available realms without authentication.
    Use this to find realms before logging in.
    
    Example:
        itlc realm discover
        itlc realm discover --server https://sts.yourcompany.com
    """
    try:
        keycloak_url = server or os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        current_realm = os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, current_realm)
        discovered = auth.discover_realms(keycloak_url)
        
        if discovered:
            click.echo(f"\n{Colors.BOLD}Discovered Realms on {keycloak_url}:{Colors.END}\n")
            
            # Get current authenticated realm
            context = auth.get_context()
            current_realm_name = context.get('realm') if context else None
            
            for realm_info in discovered:
                realm_name = realm_info['name']
                is_current = realm_name == current_realm_name
                
                if is_current:
                    marker = f"{Colors.GREEN}* {Colors.END}"
                    status = f"{Colors.GREEN}(authenticated){Colors.END}"
                else:
                    marker = "  "
                    status = ""
                
                click.echo(f"{marker}{realm_name} {status}")
            
            click.echo()
            print_info(f"Found {len(discovered)} realm(s)")
            
            if not context:
                click.echo(f"\n{Colors.YELLOW}Tip:{Colors.END} To authenticate to a realm:")
                click.echo(f"  itlc realm set <realm-name>")
                click.echo(f"  itlc login")
        else:
            print_info(f"No realms discovered on {keycloak_url}")
            click.echo("\nNote: Realm discovery uses common realm names.")
            click.echo("If you know your realm name, you can set it directly:")
            click.echo(f"  itlc realm set <realm-name>")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@realm.command('set')
@click.argument('realm_name')
def realm_set(realm_name):
    """
    Set default realm/tenant.
    
    Changes the default realm for subsequent commands (similar to 'az account set').
    
    Example:
        itlc realm set production
    """
    try:
        keycloak_url = os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        current_realm = os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, current_realm)
        
        if auth.set_realm(realm_name):
            print_success(f"Default realm set to: {realm_name}")
        else:
            sys.exit(1)
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@realm.command('show')
def realm_show():
    """
    Show current realm/tenant.
    
    Displays the currently selected realm (similar to 'az account show').
    
    Example:
        itlc realm show
    """
    try:
        keycloak_url = os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        current_realm = os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, current_realm)
        context = auth.get_context()
        
        if context:
            click.echo(f"\n{Colors.BOLD}Current Realm:{Colors.END}\n")
            click.echo(f"Realm: {context.get('realm')}")
            click.echo(f"Keycloak URL: {context.get('keycloak_url')}")
            click.echo(f"Token Type: {context.get('token_type', 'Bearer')}")
            click.echo(f"Scope: {context.get('scope', 'N/A')}")
            click.echo()
        else:
            print_info("Not logged in. Run 'itlc login' first.")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
def whoami():
    """
    Show current user information.
    
    Displays information about the currently logged-in user (similar to 'az account show').
    
    Example:
        itlc whoami
    """
    try:
        keycloak_url = os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        realm = os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, realm)
        context = auth.get_context()
        
        if not context:
            print_info("Not logged in. Run 'itlc login' first.")
            sys.exit(1)
        
        # Decode ID token to get user info
        id_token = context.get('id_token')
        if id_token:
            import base64
            parts = id_token.split('.')
            if len(parts) >= 2:
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
                
                click.echo(f"\n{Colors.BOLD}User Information:{Colors.END}\n")
                click.echo(f"Username: {payload.get('preferred_username', 'N/A')}")
                click.echo(f"Email: {payload.get('email', 'N/A')}")
                click.echo(f"Name: {payload.get('name', 'N/A')}")
                click.echo(f"Realm: {context.get('realm')}")
                click.echo(f"Keycloak URL: {context.get('keycloak_url')}")
                click.echo()
        else:
            print_info("No user information available")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
def logout():
    """
    Logout and clear authentication context.
    
    Removes saved tokens and context (similar to 'az logout').
    
    Example:
        itlc logout
    """
    try:
        keycloak_url = os.getenv('KEYCLOAK_URL', 'https://sts.itlusions.com')
        realm = os.getenv('KEYCLOAK_REALM', 'itlusions')
        
        auth = InteractiveAuth(keycloak_url, realm)
        auth.clear_context()
        
        print_success("Logged out successfully")
        print_info("Authentication context cleared")
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@cli.group()
def configure():
    """
    Configure OIDC and Kubernetes integration.
    
    Setup OIDC authentication contexts for kubectl and manage
    Kubernetes cluster access with Keycloak authentication.
    
    Commands:
      oidc       - Setup OIDC authentication contexts
    
    Examples:
      itlc configure oidc
      itlc configure oidc --python-only
    """
    pass


@configure.command(name='oidc')
@click.option('--python-only', is_flag=True, help='Setup Python OIDC only (skip kubelogin binary)')
@click.option('--cluster-name', help='Kubernetes cluster context name')
@click.option('--server', help='Kubernetes API server URL')
@click.option('--no-test', is_flag=True, help='Skip authentication test')
def configure_oidc(python_only, cluster_name, server, no_test):
    """
    Setup OIDC authentication contexts for kubectl.
    
    This command configures your kubeconfig with OIDC authentication
    contexts that use Keycloak for authentication. It creates pre-configured
    contexts for both direct and SSH tunnel access.
    
    Authentication Methods:
      - Python (itlc.oidc_auth) - No external dependencies
      - Binary (kubectl-oidc_login) - Requires kubelogin plugin
    
    Created Contexts:
      - itl-python: Python OIDC, direct access
      - itl: Binary OIDC, direct access (if not --python-only)
      - itl-ssh-tunnel-python: Python OIDC via SSH tunnel
      - itl-ssh-tunnel: Binary OIDC via SSH tunnel (if not --python-only)
    
    Examples:
      # Full setup with both methods
      itlc configure oidc
      
      # Python-only (minimal dependencies)
      itlc configure oidc --python-only
      
      # Specify cluster details
      itlc configure oidc --server https://10.99.100.4:6443
      
      # Skip the test at the end
      itlc configure oidc --no-test
    """
    try:
        from .kubectl_oidc_setup import KubectlOIDCSetup
        
        print_info("Setting up OIDC authentication for kubectl...")
        click.echo()
        
        # Initialize setup
        setup = KubectlOIDCSetup()
        
        # Configure OIDC contexts
        if server:
            print_info(f"Using cluster server: {server}")
            # TODO: Update KubectlOIDCSetup to accept server parameter
            # For now, user needs to edit kubeconfig manually
            print_info("Note: You may need to update cluster server in kubeconfig")
        
        # Run the setup
        print_info("Configuring OIDC authentication contexts...")
        
        # Import and use the setup class methods
        # The setup class will handle creating the contexts
        try:
            # Create kubeconfig with OIDC contexts
            kubeconfig_path = Path.home() / '.kube' / 'config'
            
            if not kubeconfig_path.exists():
                kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
                with open(kubeconfig_path, 'w') as f:
                    f.write(setup.DEFAULT_CLUSTER_CONFIG)
                print_success("Created kubeconfig with OIDC contexts")
            else:
                # Merge with existing config
                print_info("Kubeconfig exists, you may need to merge OIDC contexts manually")
                print_info("See: itlc configure oidc --help for context configuration")
        
        except Exception as e:
            print_error(f"Setup error: {str(e)}")
            raise
        
        click.echo()
        print_success("OIDC authentication configured!")
        click.echo()
        
        print_info("Available contexts:")
        contexts = [
            ("itl-python", "Python OIDC (recommended)", "Direct access"),
            ("itl-ssh-tunnel-python", "Python OIDC via SSH", "Tunnel on 127.0.0.1:16643"),
        ]
        
        if not python_only:
            contexts.extend([
                ("itl", "Binary OIDC (kubelogin)", "Direct access"),
                ("itl-ssh-tunnel", "Binary OIDC via SSH", "Tunnel on 127.0.0.1:16643"),
            ])
        
        for ctx_name, desc, access in contexts:
            click.echo(f"  {Colors.CYAN}{ctx_name:<25}{Colors.END} {desc:<30} ({access})")
        
        click.echo()
        print_info("Test authentication:")
        click.echo(f"  kubectl --context=itl-python get nodes")
        click.echo()
        
        print_info("Register your cluster:")
        click.echo(f"  itlc cluster add --name my-cluster --server https://api.example.com:6443")
        click.echo()
        
        print_info("Documentation:")
        click.echo(f"  https://github.com/ITlusions/ITLAuth/blob/main/docs/OIDC_SETUP.md")
        
    except ImportError as e:
        print_error(f"Failed to import OIDC setup module: {str(e)}")
        print_info("Make sure itlc is properly installed: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print_error(f"Configuration failed: {str(e)}")
        sys.exit(1)


# Register command groups with main CLI
cli.add_command(cluster)
cli.add_command(configure)


if __name__ == '__main__':
    cli()
