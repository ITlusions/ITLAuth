"""
Utility functions for itl-k8s-oidc.

Provides subprocess helpers, OS/arch detection, and OIDC discovery functionality.
"""

import json
import platform
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple


class SetupError(Exception):
    """Custom exception for setup errors."""
    pass


def run_command(
    cmd: List[str], 
    check: bool = True, 
    capture_output: bool = True,
    env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """
    Run a command and return the result with robust error reporting.
    
    Args:
        cmd: Command to run as list of strings
        check: Whether to raise exception on non-zero exit code
        capture_output: Whether to capture stdout/stderr
        env: Environment variables to use
    
    Returns:
        CompletedProcess instance
    
    Raises:
        SetupError: If command fails and check=True
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check,
            env=env
        )
        return result
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(cmd)}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        if e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"
        raise SetupError(error_msg) from e
    except FileNotFoundError as e:
        raise SetupError(f"Command not found: {cmd[0]}") from e


def ensure_kubectl_available() -> bool:
    """
    Check if kubectl is available and accessible.
    
    Returns:
        True if kubectl is available, False otherwise
    """
    try:
        run_command(["kubectl", "version", "--client=true"], capture_output=True)
        return True
    except SetupError:
        return False


def get_os_arch() -> Tuple[str, str]:
    """
    Detect OS and architecture for downloading binaries.
    
    Returns:
        Tuple of (os_name, arch_name) suitable for GitHub releases
    
    Raises:
        SetupError: If OS or architecture is unsupported
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map architecture names
    arch_map = {
        'x86_64': 'amd64',
        'amd64': 'amd64',
        'arm64': 'arm64',
        'aarch64': 'arm64',
    }
    
    if machine not in arch_map:
        raise SetupError(f"Unsupported architecture: {machine}")
    
    arch = arch_map[machine]
    
    if system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "darwin"
    elif system == "windows":
        os_name = "windows"
    else:
        raise SetupError(f"Unsupported operating system: {system}")
    
    return os_name, arch


def download_file(url: str, destination: str) -> None:
    """
    Download a file from URL to destination.
    
    Args:
        url: URL to download from
        destination: Local file path to save to
    
    Raises:
        SetupError: If download fails
    """
    try:
        urllib.request.urlretrieve(url, destination)
    except urllib.error.URLError as e:
        raise SetupError(f"Failed to download {url}: {e}") from e


def fetch_oidc_discovery(issuer_url: str) -> Dict[str, Any]:
    """
    Fetch and validate OIDC discovery document.
    
    Args:
        issuer_url: OIDC issuer URL
    
    Returns:
        Parsed discovery document
    
    Raises:
        SetupError: If discovery document cannot be fetched or is invalid
    """
    discovery_url = issuer_url.rstrip('/') + '/.well-known/openid_configuration'
    
    try:
        with urllib.request.urlopen(discovery_url) as response:
            discovery_doc = json.loads(response.read().decode())
    except urllib.error.URLError as e:
        raise SetupError(f"Failed to fetch OIDC discovery from {discovery_url}: {e}") from e
    except json.JSONDecodeError as e:
        raise SetupError(f"Invalid JSON in OIDC discovery document: {e}") from e
    
    # Validate required fields
    required_fields = ['issuer', 'authorization_endpoint', 'token_endpoint']
    missing_fields = [field for field in required_fields if field not in discovery_doc]
    
    if missing_fields:
        raise SetupError(f"OIDC discovery document missing required fields: {missing_fields}")
    
    # Validate issuer matches
    if discovery_doc['issuer'] != issuer_url:
        raise SetupError(
            f"OIDC issuer mismatch: expected {issuer_url}, got {discovery_doc['issuer']}"
        )
    
    return discovery_doc


def ensure_plugin(plugin_name: str, auto_install: bool = True) -> bool:
    """
    Ensure a kubectl plugin is installed.
    
    Args:
        plugin_name: Name of the plugin to check/install
        auto_install: Whether to auto-install if missing
    
    Returns:
        True if plugin is available, False otherwise
    
    Raises:
        SetupError: If auto-installation fails
    """
    # Check if plugin is already available
    try:
        run_command(["kubectl", plugin_name, "--help"], capture_output=True)
        return True
    except SetupError:
        pass
    
    if not auto_install:
        return False
    
    # Try to install via krew
    try:
        run_command(["kubectl", "krew", "install", plugin_name])
        return True
    except SetupError as e:
        raise SetupError(f"Failed to install plugin {plugin_name}: {e}") from e


def format_error(error: Exception) -> str:
    """
    Format an error for display to the user.
    
    Args:
        error: Exception to format
    
    Returns:
        Formatted error message
    """
    if isinstance(error, SetupError):
        return str(error)
    else:
        return f"Unexpected error: {error}"