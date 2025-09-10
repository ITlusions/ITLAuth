"""
Krew installation and plugin management for itl-k8s-oidc.

Handles automatic installation of krew and kubectl plugins.
"""

import os
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, Optional

from .utils import run_command, get_os_arch, download_file, SetupError


def check_krew_installed() -> bool:
    """
    Check if krew is installed and available.
    
    Returns:
        True if krew is available, False otherwise
    """
    try:
        run_command(["kubectl", "krew", "version"], capture_output=True)
        return True
    except SetupError:
        return False


def get_krew_download_url() -> str:
    """
    Get the download URL for the latest krew release.
    
    Returns:
        Download URL for krew binary
    
    Raises:
        SetupError: If OS/arch is unsupported
    """
    os_name, arch = get_os_arch()
    return f"https://github.com/kubernetes-sigs/krew/releases/latest/download/krew-{os_name}_{arch}.tar.gz"


def install_krew(env: Optional[Dict[str, str]] = None) -> None:
    """
    Install krew kubectl plugin manager.
    
    Args:
        env: Environment variables to use during installation
    
    Raises:
        SetupError: If installation fails
    """
    if env is None:
        env = os.environ.copy()
    
    # Set KREW_ROOT if not already set
    if "KREW_ROOT" not in env:
        env["KREW_ROOT"] = str(Path.home() / ".krew")
    
    krew_url = get_krew_download_url()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        krew_archive = temp_path / "krew.tar.gz"
        
        # Download krew
        download_file(krew_url, str(krew_archive))
        
        # Extract krew
        try:
            with tarfile.open(krew_archive, 'r:gz') as tar:
                tar.extractall(temp_path)
        except tarfile.TarError as e:
            raise SetupError(f"Failed to extract krew archive: {e}") from e
        
        # Find krew binary
        krew_binary = None
        for file in temp_path.glob("krew-*"):
            if file.is_file() and os.access(file, os.X_OK):
                krew_binary = file
                break
        
        if not krew_binary:
            raise SetupError("Could not find krew binary in downloaded archive")
        
        # Install krew
        try:
            run_command([str(krew_binary), "install", "krew"], env=env, capture_output=True)
        except SetupError as e:
            raise SetupError(f"Failed to install krew: {e}") from e
        
        # Add krew to PATH for current session
        krew_bin_path = Path(env["KREW_ROOT"]) / "bin"
        current_path = env.get("PATH", "")
        if str(krew_bin_path) not in current_path:
            env["PATH"] = f"{krew_bin_path}{os.pathsep}{current_path}"
            # Update the global environment for this process
            os.environ["PATH"] = env["PATH"]


def install_krew_and_plugin(plugin_name: str, env: Optional[Dict[str, str]] = None, auto_install_krew: bool = True) -> None:
    """
    Ensure krew is installed and install the specified plugin.
    
    Args:
        plugin_name: Name of the plugin to install
        env: Environment variables to use
        auto_install_krew: Whether to auto-install krew if missing
    
    Raises:
        SetupError: If installation fails
    """
    if env is None:
        env = os.environ.copy()
    
    # Check if krew is installed
    if not check_krew_installed():
        if not auto_install_krew:
            raise SetupError("krew is not installed and auto-installation is disabled")
        
        install_krew(env)
    
    # Install the plugin
    try:
        run_command(["kubectl", "krew", "install", plugin_name], env=env)
    except SetupError as e:
        # Check if plugin is already installed
        try:
            run_command(["kubectl", plugin_name, "--help"], capture_output=True, env=env)
            # Plugin is already available
            return
        except SetupError:
            # Plugin is not available, re-raise original error
            raise SetupError(f"Failed to install plugin {plugin_name}: {e}") from e


def update_krew_index(env: Optional[Dict[str, str]] = None) -> None:
    """
    Update the krew plugin index.
    
    Args:
        env: Environment variables to use
    
    Raises:
        SetupError: If update fails
    """
    if env is None:
        env = os.environ.copy()
    
    try:
        run_command(["kubectl", "krew", "update"], env=env, capture_output=True)
    except SetupError as e:
        # Update failure is not critical, just log it
        pass