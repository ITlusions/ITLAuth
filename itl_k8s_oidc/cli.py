"""
Command-line interface for ITL Kubernetes OIDC setup.

Provides the itl-oidc-setup command with all configuration options.
"""

import sys
import click
from pathlib import Path

from .config import OIDCConfig
from .setup import KubernetesOIDCSetup, OIDCSetupError


@click.command()
@click.option(
    '--issuer-url', '-i',
    help=f'OIDC issuer URL (default: {OIDCConfig.DEFAULT_ISSUER_URL})'
)
@click.option(
    '--client-id', '-c',
    default='kubernetes',
    help='OIDC client ID (default: kubernetes)'
)
@click.option(
    '--use-device-code', '-d',
    is_flag=True,
    help='Use device code flow for authentication'
)
@click.option(
    '--custom-ca', '--ca',
    'custom_ca_path',
    type=click.Path(exists=True),
    help='Path to custom CA certificate file'
)
@click.option(
    '--kubeconfig', '-k',
    'kubeconfig_path',
    type=click.Path(),
    help='Path to kubeconfig file (default: $KUBECONFIG or ~/.kube/config)'
)
@click.option(
    '--verify-auth', '-v',
    is_flag=True,
    help='Verify authentication after setup using kubectl auth whoami'
)
@click.option(
    '--config-file', '-f',
    'config_file_path',
    type=click.Path(exists=True),
    help='Path to configuration file'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version='0.1.0', prog_name='itl-oidc-setup')
def main(
    issuer_url,
    client_id,
    use_device_code,
    custom_ca_path,
    kubeconfig_path,
    verify_auth,
    config_file_path,
    verbose
):
    """
    ITL Kubernetes OIDC Setup Tool
    
    Automates Kubernetes authentication setup via Keycloak OIDC.
    
    This tool will:
    1. Check kubectl availability
    2. Install krew (kubectl plugin manager) if needed
    3. Install the oidc-login plugin
    4. Configure OIDC authentication for your Kubernetes cluster
    
    Configuration precedence (highest to lowest):
    1. CLI arguments
    2. Environment variables (OIDC_ISSUER_URL, etc.)
    3. Configuration file
    4. Default values
    
    Examples:
    
      # Use default ITlusions issuer
      itl-oidc-setup
      
      # Use custom issuer
      itl-oidc-setup --issuer-url https://my-keycloak.example.com/realms/myrealm
      
      # Use device code flow with custom CA
      itl-oidc-setup --use-device-code --custom-ca /path/to/ca.crt
      
      # Specify custom kubeconfig and verify auth
      itl-oidc-setup --kubeconfig ~/.kube/prod-config --verify-auth
    """
    try:
        # Initialize configuration
        config = OIDCConfig()
        
        # Load configuration in order of precedence
        # 1. Load from default config file locations
        config.load_default_config()
        
        # 2. Load from specific config file if provided
        if config_file_path:
            config.load_from_file(config_file_path)
        
        # 3. Load from environment variables
        config.load_from_env()
        
        # 4. Update with CLI arguments (highest precedence)
        config.update_from_cli_args(
            issuer_url=issuer_url,
            client_id=client_id,
            use_device_code=use_device_code,
            custom_ca_path=custom_ca_path,
            kubeconfig_path=kubeconfig_path,
            verify_auth=verify_auth
        )
        
        if verbose:
            click.echo("Configuration loaded:")
            for key, value in config.to_dict().items():
                if value is not None:
                    click.echo(f"  {key}: {value}")
            click.echo()
        
        # Run the setup
        setup = KubernetesOIDCSetup(config, verbose=verbose)
        setup.run_setup()
        
    except OIDCSetupError as e:
        click.echo(f"❌ Setup failed: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n❌ Setup cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()