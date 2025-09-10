"""
Command-line interface for itl-k8s-oidc.

Provides the itl-oidc-setup command with argparse and proper precedence handling.
"""

import argparse
import sys
from typing import Dict, Any

from .config import (
    load_config, save_config, get_default_config, 
    merge_config_sources, load_env_config
)
from .utils import ensure_kubectl_available, format_error, SetupError
from .krew import install_krew_and_plugin
from .kubelogin import setup_kubelogin, verify_auth, check_oidc_login_available


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="itl-oidc-setup",
        description=(
            "One-command setup: Kubernetes OIDC via Keycloak + kubelogin "
            "(auto-installs krew + oidc-login)."
        ),
        epilog=(
            "Configuration precedence (highest to lowest): "
            "CLI args > env ITL_OIDC_* > config file > defaults. "
            "Examples: itl-oidc-setup --verify, "
            "itl-oidc-setup --issuer-url https://sts.itlusions.com/realms/myrealm --save-default"
        )
    )
    
    # Main configuration options
    parser.add_argument(
        "--issuer-url",
        help="OIDC issuer URL (overrides env ITL_OIDC_ISSUER_URL and config file)"
    )
    
    parser.add_argument(
        "--client-id",
        help="OIDC client ID (default: kubelogin)"
    )
    
    parser.add_argument(
        "--scopes",
        help="OIDC scopes (default: openid,profile,email)"
    )
    
    # Setup options
    parser.add_argument(
        "--kubeconfig",
        help="Path to kubeconfig file (default: $KUBECONFIG or ~/.kube/config)"
    )
    
    parser.add_argument(
        "--ca-file",
        help="Path to custom CA certificate file"
    )
    
    parser.add_argument(
        "--device-code",
        action="store_true",
        help="Use device code flow for authentication"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify authentication after setup using kubectl auth whoami"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    
    # Installation control
    parser.add_argument(
        "--no-install-krew",
        action="store_true",
        help="Do not auto-install krew if missing"
    )
    
    parser.add_argument(
        "--no-install-plugin",
        action="store_true",
        help="Do not auto-install oidc-login plugin if missing"
    )
    
    # Extra arguments
    parser.add_argument(
        "--extra-arg",
        action="append",
        dest="extra_args",
        help="Additional arguments to pass to kubectl oidc-login setup (can be used multiple times)"
    )
    
    # Configuration management
    parser.add_argument(
        "--save-default",
        action="store_true",
        help="Save the resolved configuration as defaults to config file"
    )
    
    # Output control
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser


def resolve_configuration(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Resolve configuration from all sources with proper precedence.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        Final resolved configuration
    """
    # Load configuration from all sources
    cli_config = {
        "issuer_url": args.issuer_url,
        "client_id": args.client_id,
        "scopes": args.scopes,
    }
    
    env_config = load_env_config()
    file_config = load_config()
    default_config = get_default_config()
    
    # Merge configurations with proper precedence
    config = merge_config_sources(cli_config, env_config, file_config, default_config)
    
    # Add non-merging options
    config.update({
        "kubeconfig": args.kubeconfig,
        "ca_file": args.ca_file,
        "device_code": args.device_code,
        "verify": args.verify,
        "dry_run": args.dry_run,
        "no_install_krew": args.no_install_krew,
        "no_install_plugin": args.no_install_plugin,
        "extra_args": args.extra_args or [],
        "save_default": args.save_default,
        "verbose": args.verbose,
    })
    
    return config


def print_status(message: str, verbose: bool = False, error: bool = False) -> None:
    """Print a status message."""
    if error:
        print(f"❌ {message}", file=sys.stderr)
    elif verbose:
        print(f"🔧 {message}")
    else:
        print(f"✅ {message}")


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Resolve configuration
        config = resolve_configuration(args)
        
        if config["verbose"]:
            print("🔧 Resolved configuration:")
            for key, value in config.items():
                if key not in ["verbose"] and value:
                    print(f"   {key}: {value}")
            print()
        
        # Save default configuration if requested
        if config["save_default"]:
            save_config({
                "issuer_url": config["issuer_url"],
                "client_id": config["client_id"],
                "scopes": config["scopes"],
            })
            print_status("Default configuration saved", config["verbose"])
        
        if config["dry_run"]:
            print("🔍 Dry run mode - showing what would be done:")
            print()
        
        # Check kubectl availability
        print_status("Checking kubectl availability...", config["verbose"])
        if not ensure_kubectl_available():
            raise SetupError("kubectl is not available. Please install kubectl and ensure it's in your PATH.")
        
        print_status("kubectl is available", config["verbose"])
        
        # Install krew and oidc-login plugin if needed
        if not config["no_install_krew"] or not config["no_install_plugin"]:
            print_status("Ensuring krew and oidc-login plugin are available...", config["verbose"])
            
            if config["dry_run"]:
                print("Would install krew and oidc-login plugin if needed")
            else:
                install_krew_and_plugin(
                    "oidc-login",
                    auto_install_krew=not config["no_install_krew"]
                )
            
            print_status("krew and oidc-login plugin are available", config["verbose"])
        
        # Setup kubelogin
        print_status("Setting up kubelogin...", config["verbose"])
        
        if config["dry_run"]:
            setup_kubelogin(
                issuer_url=config["issuer_url"],
                client_id=config["client_id"],
                scopes=config["scopes"],
                kubeconfig=config["kubeconfig"],
                ca_file=config["ca_file"],
                device_code=config["device_code"],
                extra_args=config["extra_args"],
                dry_run=True
            )
        else:
            setup_kubelogin(
                issuer_url=config["issuer_url"],
                client_id=config["client_id"],
                scopes=config["scopes"],
                kubeconfig=config["kubeconfig"],
                ca_file=config["ca_file"],
                device_code=config["device_code"],
                extra_args=config["extra_args"]
            )
        
        print_status("kubelogin setup completed", config["verbose"])
        
        # Verify authentication if requested
        if config["verify"] and not config["dry_run"]:
            print_status("Verifying authentication...", config["verbose"])
            
            try:
                whoami_output = verify_auth(kubeconfig=config["kubeconfig"])
                print_status(f"Authentication verified: {whoami_output}", config["verbose"])
            except SetupError as e:
                print_status(f"Authentication verification failed: {e}", config["verbose"], error=True)
                sys.exit(1)
        
        # Final success message
        if not config["dry_run"]:
            print()
            print("🎉 ITL Kubernetes OIDC setup completed successfully!")
            print(f"   Issuer URL: {config['issuer_url']}")
            print(f"   Client ID: {config['client_id']}")
            if config["kubeconfig"]:
                print(f"   Kubeconfig: {config['kubeconfig']}")
            print()
            print("You can now use 'kubectl oidc-login' to authenticate with your Kubernetes cluster.")
        
    except SetupError as e:
        print_status(format_error(e), error=True)
        sys.exit(1)
    except KeyboardInterrupt:
        print_status("Setup cancelled by user", error=True)
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", error=True)
        if config.get("verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()