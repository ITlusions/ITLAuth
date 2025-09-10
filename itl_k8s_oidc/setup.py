"""
Core setup functionality for ITL Kubernetes OIDC authentication.

Handles kubectl checking, krew installation, oidc-login plugin installation,
and OIDC configuration setup.
"""

import os
import subprocess
import sys
import tempfile
import urllib.request
import shutil
from pathlib import Path
from typing import Optional, Tuple
import platform

from .config import OIDCConfig


class OIDCSetupError(Exception):
    """Custom exception for OIDC setup errors."""
    pass


class KubernetesOIDCSetup:
    """Main class for setting up Kubernetes OIDC authentication."""
    
    def __init__(self, config: OIDCConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def run_command(self, cmd: list[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        self.log(f"Running command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=check
            )
            if self.verbose and result.stdout:
                self.log(f"Command output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {' '.join(cmd)}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            raise OIDCSetupError(error_msg) from e
    
    def check_kubectl(self) -> bool:
        """Check if kubectl is available and accessible."""
        self.log("Checking kubectl availability...")
        try:
            result = self.run_command(["kubectl", "version", "--client=true", "--short"])
            self.log("kubectl is available")
            return True
        except OIDCSetupError:
            self.log("kubectl is not available or not in PATH", "ERROR")
            return False
    
    def check_krew(self) -> bool:
        """Check if krew is installed."""
        self.log("Checking krew availability...")
        try:
            self.run_command(["kubectl", "krew", "version"])
            self.log("krew is already installed")
            return True
        except OIDCSetupError:
            self.log("krew is not installed")
            return False
    
    def install_krew(self) -> None:
        """Install krew kubectl plugin manager."""
        self.log("Installing krew...")
        
        # Determine platform and architecture
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map architecture names
        arch_map = {
            'x86_64': 'amd64',
            'amd64': 'amd64',
            'arm64': 'arm64',
            'aarch64': 'arm64',
        }
        
        if machine in arch_map:
            arch = arch_map[machine]
        else:
            raise OIDCSetupError(f"Unsupported architecture: {machine}")
        
        if system == "linux":
            os_name = "linux"
        elif system == "darwin":
            os_name = "darwin"
        elif system == "windows":
            os_name = "windows"
        else:
            raise OIDCSetupError(f"Unsupported operating system: {system}")
        
        # Download and install krew
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download krew
            krew_url = f"https://github.com/kubernetes-sigs/krew/releases/latest/download/krew-{os_name}_{arch}.tar.gz"
            krew_archive = temp_path / "krew.tar.gz"
            
            self.log(f"Downloading krew from {krew_url}")
            try:
                urllib.request.urlretrieve(krew_url, krew_archive)
            except Exception as e:
                raise OIDCSetupError(f"Failed to download krew: {e}") from e
            
            # Extract krew
            import tarfile
            with tarfile.open(krew_archive, 'r:gz') as tar:
                tar.extractall(temp_path)
            
            # Find krew binary
            krew_binary = None
            for file in temp_path.glob("krew-*"):
                if file.is_file() and os.access(file, os.X_OK):
                    krew_binary = file
                    break
            
            if not krew_binary:
                raise OIDCSetupError("Could not find krew binary in downloaded archive")
            
            # Install krew
            env = os.environ.copy()
            env["KREW_ROOT"] = str(Path.home() / ".krew")
            
            self.run_command([str(krew_binary), "install", "krew"], capture_output=False)
            
            # Add krew to PATH for this session
            krew_bin_path = Path.home() / ".krew" / "bin"
            if str(krew_bin_path) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{krew_bin_path}:{os.environ.get('PATH', '')}"
            
            self.log("krew installed successfully")
    
    def install_oidc_login_plugin(self) -> None:
        """Install the oidc-login plugin via krew."""
        self.log("Installing oidc-login plugin...")
        try:
            self.run_command(["kubectl", "krew", "install", "oidc-login"])
            self.log("oidc-login plugin installed successfully")
        except OIDCSetupError as e:
            # Check if plugin is already installed
            try:
                self.run_command(["kubectl", "oidc-login", "--help"])
                self.log("oidc-login plugin is already installed")
            except OIDCSetupError:
                raise e
    
    def setup_oidc_login(self) -> None:
        """Run kubectl oidc-login setup with the configured parameters."""
        self.log("Setting up OIDC login configuration...")
        
        cmd = ["kubectl", "oidc-login", "setup"]
        
        # Add issuer URL
        cmd.extend(["--oidc-issuer-url", self.config.issuer_url])
        
        # Add client ID
        cmd.extend(["--oidc-client-id", self.config.client_id])
        
        # Add optional parameters
        if self.config.use_device_code:
            cmd.append("--oidc-use-device-code")
        
        if self.config.custom_ca_path:
            cmd.extend(["--certificate-authority", self.config.custom_ca_path])
        
        # Set kubeconfig if specified
        env = os.environ.copy()
        if self.config.kubeconfig_path:
            env["KUBECONFIG"] = self.config.kubeconfig_path
        
        self.log(f"Running OIDC setup with issuer: {self.config.issuer_url}")
        try:
            # Run setup interactively (don't capture output for interactive setup)
            subprocess.run(cmd, env=env, check=True)
            self.log("OIDC login setup completed successfully")
        except subprocess.CalledProcessError as e:
            raise OIDCSetupError(f"OIDC login setup failed: {e}") from e
    
    def verify_auth(self) -> bool:
        """Verify authentication by running kubectl auth whoami."""
        if not self.config.verify_auth:
            return True
            
        self.log("Verifying authentication...")
        try:
            env = os.environ.copy()
            if self.config.kubeconfig_path:
                env["KUBECONFIG"] = self.config.kubeconfig_path
                
            result = self.run_command(["kubectl", "auth", "whoami"], capture_output=True)
            self.log(f"Authentication verified: {result.stdout.strip()}")
            return True
        except OIDCSetupError:
            self.log("Authentication verification failed", "WARNING")
            return False
    
    def run_setup(self) -> None:
        """Run the complete OIDC setup process."""
        self.log("Starting ITL Kubernetes OIDC setup...")
        
        # Check kubectl
        if not self.check_kubectl():
            raise OIDCSetupError(
                "kubectl is not available. Please install kubectl and ensure it's in your PATH."
            )
        
        # Check and install krew if needed
        if not self.check_krew():
            self.install_krew()
        
        # Install oidc-login plugin
        self.install_oidc_login_plugin()
        
        # Setup OIDC login
        self.setup_oidc_login()
        
        # Verify authentication if requested
        if self.config.verify_auth:
            self.verify_auth()
        
        self.log("ITL Kubernetes OIDC setup completed successfully!")
        print("\n✅ OIDC setup completed successfully!")
        print(f"   Issuer URL: {self.config.issuer_url}")
        print(f"   Client ID: {self.config.client_id}")
        
        if self.config.kubeconfig_path:
            print(f"   Kubeconfig: {self.config.kubeconfig_path}")
        
        print("\nYou can now use 'kubectl oidc-login' to authenticate with your Kubernetes cluster.")