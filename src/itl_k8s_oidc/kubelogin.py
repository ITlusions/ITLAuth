"""
kubelogin setup and verification for itl-k8s-oidc.

Handles OIDC discovery validation, kubelogin setup, and optional verification.
"""

import os
from typing import Dict, List, Optional, Any

from .utils import run_command, fetch_oidc_discovery, SetupError


def validate_oidc_discovery(issuer_url: str) -> Dict[str, Any]:
    """
    Validate OIDC discovery document for the issuer.
    
    Args:
        issuer_url: OIDC issuer URL
    
    Returns:
        Discovery document dictionary
    
    Raises:
        SetupError: If discovery validation fails
    """
    return fetch_oidc_discovery(issuer_url)


def setup_kubelogin(
    issuer_url: str,
    client_id: str,
    scopes: str,
    kubeconfig: Optional[str] = None,
    ca_file: Optional[str] = None,
    device_code: bool = False,
    extra_args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False
) -> None:
    """
    Run kubectl oidc-login setup with the specified parameters.
    
    Args:
        issuer_url: OIDC issuer URL
        client_id: OIDC client ID
        scopes: OIDC scopes (comma-separated)
        kubeconfig: Path to kubeconfig file
        ca_file: Path to custom CA certificate file
        device_code: Whether to use device code flow
        extra_args: Additional arguments to pass to oidc-login
        env: Environment variables to use
        dry_run: If True, only print the command that would be run
    
    Raises:
        SetupError: If setup fails
    """
    if env is None:
        env = os.environ.copy()
    
    # Set kubeconfig in environment if specified
    if kubeconfig:
        env["KUBECONFIG"] = kubeconfig
    
    # Build the command
    cmd = ["kubectl", "oidc-login", "setup"]
    
    # Add required parameters
    cmd.extend(["--oidc-issuer-url", issuer_url])
    cmd.extend(["--oidc-client-id", client_id])
    cmd.extend(["--oidc-extra-scope", scopes])
    
    # Add optional parameters
    if device_code:
        cmd.append("--oidc-use-device-code")
    
    if ca_file:
        cmd.extend(["--certificate-authority", ca_file])
    
    # Add any extra arguments
    if extra_args:
        cmd.extend(extra_args)
    
    if dry_run:
        print(f"Would run: {' '.join(cmd)}")
        if kubeconfig:
            print(f"With KUBECONFIG={kubeconfig}")
        return
    
    # Validate OIDC discovery before running setup
    try:
        validate_oidc_discovery(issuer_url)
    except SetupError as e:
        raise SetupError(f"OIDC issuer validation failed: {e}") from e
    
    # Run the setup command interactively
    try:
        run_command(cmd, env=env, capture_output=False)
    except SetupError as e:
        raise SetupError(f"kubelogin setup failed: {e}") from e


def verify_auth(kubeconfig: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> str:
    """
    Verify authentication using kubectl auth whoami.
    
    Args:
        kubeconfig: Path to kubeconfig file
        env: Environment variables to use
    
    Returns:
        Output from kubectl auth whoami
    
    Raises:
        SetupError: If verification fails
    """
    if env is None:
        env = os.environ.copy()
    
    # Set kubeconfig in environment if specified
    if kubeconfig:
        env["KUBECONFIG"] = kubeconfig
    
    try:
        result = run_command(["kubectl", "auth", "whoami"], env=env, capture_output=True)
        return result.stdout.strip()
    except SetupError as e:
        raise SetupError(f"Authentication verification failed: {e}") from e


def check_oidc_login_available(env: Optional[Dict[str, str]] = None) -> bool:
    """
    Check if the oidc-login plugin is available.
    
    Args:
        env: Environment variables to use
    
    Returns:
        True if oidc-login plugin is available, False otherwise
    """
    if env is None:
        env = os.environ.copy()
    
    try:
        run_command(["kubectl", "oidc-login", "--help"], env=env, capture_output=True)
        return True
    except SetupError:
        return False