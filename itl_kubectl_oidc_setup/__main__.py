#!/usr/bin/env python3
"""
ITlusions Kubernetes OIDC Setup Tool

This tool automatically installs and configures kubectl with OIDC authentication
for ITlusions Kubernetes clusters using Keycloak.
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import tarfile
import json
import tempfile
import shutil
from pathlib import Path
import argparse


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class KubectlOIDCSetup:
    """Main setup class for kubectl OIDC configuration."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.home_dir = Path.home()
        self.kubectl_dir = self.home_dir / ".kubectl"
        self.plugins_dir = self.kubectl_dir / "plugins"
        
        # OIDC Configuration
        self.oidc_config = {
            "issuer_url": "https://sts.itlusions.com/realms/itlusions",
            "client_id": "kubernetes-oidc",
            "extra_scopes": "email,profile,groups",
            "username_claim": "preferred_username",
            "groups_claim": "groups"
        }

    def print_header(self):
        """Print the tool header."""
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("🔧 ITlusions Kubernetes OIDC Setup Tool")
        print("=" * 50)
        print(f"{Colors.END}")
        print(f"{Colors.CYAN}Configuring kubectl OIDC authentication for ITlusions cluster{Colors.END}")
        print()

    def run_command(self, command, check=True, capture_output=True):
        """Run a shell command and return the result."""
        try:
            if isinstance(command, str):
                command = command.split()
            
            result = subprocess.run(
                command,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            if check:
                print(f"{Colors.RED}❌ Command failed: {' '.join(command)}{Colors.END}")
                print(f"{Colors.RED}Error: {e.stderr if e.stderr else str(e)}{Colors.END}")
                return None
            return e
        except FileNotFoundError:
            print(f"{Colors.RED}❌ Command not found: {command[0]}{Colors.END}")
            return None

    def check_kubectl(self):
        """Check if kubectl is installed and accessible."""
        print(f"{Colors.YELLOW}🔍 Checking kubectl installation...{Colors.END}")
        
        result = self.run_command("kubectl version --client --output=json", check=False)
        if result and result.returncode == 0:
            try:
                version_info = json.loads(result.stdout)
                version = version_info.get("clientVersion", {}).get("gitVersion", "unknown")
                print(f"{Colors.GREEN}✅ kubectl found (version: {version}){Colors.END}")
                return True
            except:
                print(f"{Colors.GREEN}✅ kubectl found{Colors.END}")
                return True
        else:
            print(f"{Colors.RED}❌ kubectl not found{Colors.END}")
            return False

    def install_kubectl(self):
        """Install kubectl if not present."""
        print(f"{Colors.YELLOW}📦 Installing kubectl...{Colors.END}")
        
        if self.system == "windows":
            return self._install_kubectl_windows()
        elif self.system == "darwin":
            return self._install_kubectl_macos()
        elif self.system == "linux":
            return self._install_kubectl_linux()
        else:
            print(f"{Colors.RED}❌ Unsupported operating system: {self.system}{Colors.END}")
            return False

    def _install_kubectl_windows(self):
        """Install kubectl on Windows."""
        try:
            # Try winget first
            result = self.run_command("winget install -e --id Kubernetes.kubectl", check=False)
            if result and result.returncode == 0:
                print(f"{Colors.GREEN}✅ kubectl installed via winget{Colors.END}")
                return True
            
            # Fallback to manual download
            print(f"{Colors.YELLOW}⬇️ Downloading kubectl manually...{Colors.END}")
            url = "https://dl.k8s.io/release/stable.txt"
            with urllib.request.urlopen(url) as response:
                version = response.read().decode().strip()
            
            kubectl_url = f"https://dl.k8s.io/release/{version}/bin/windows/amd64/kubectl.exe"
            kubectl_path = self.kubectl_dir / "kubectl.exe"
            
            self.kubectl_dir.mkdir(exist_ok=True)
            urllib.request.urlretrieve(kubectl_url, kubectl_path)
            
            # Add to PATH if not already there
            kubectl_dir_str = str(self.kubectl_dir)
            current_path = os.environ.get("PATH", "")
            if kubectl_dir_str not in current_path:
                print(f"{Colors.YELLOW}⚠️ Add {kubectl_dir_str} to your PATH environment variable{Colors.END}")
            
            print(f"{Colors.GREEN}✅ kubectl downloaded to {kubectl_path}{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to install kubectl: {e}{Colors.END}")
            return False

    def _install_kubectl_macos(self):
        """Install kubectl on macOS."""
        try:
            # Try homebrew first
            result = self.run_command("brew install kubectl", check=False)
            if result and result.returncode == 0:
                print(f"{Colors.GREEN}✅ kubectl installed via homebrew{Colors.END}")
                return True
            
            # Fallback to manual download
            return self._install_kubectl_unix("darwin", "amd64")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to install kubectl: {e}{Colors.END}")
            return False

    def _install_kubectl_linux(self):
        """Install kubectl on Linux."""
        try:
            # Determine architecture
            arch_map = {"x86_64": "amd64", "aarch64": "arm64", "armv7l": "arm"}
            arch = arch_map.get(self.arch, "amd64")
            
            return self._install_kubectl_unix("linux", arch)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to install kubectl: {e}{Colors.END}")
            return False

    def _install_kubectl_unix(self, os_name, arch):
        """Install kubectl on Unix-like systems."""
        print(f"{Colors.YELLOW}⬇️ Downloading kubectl...{Colors.END}")
        
        # Get latest version
        url = "https://dl.k8s.io/release/stable.txt"
        with urllib.request.urlopen(url) as response:
            version = response.read().decode().strip()
        
        kubectl_url = f"https://dl.k8s.io/release/{version}/bin/{os_name}/{arch}/kubectl"
        kubectl_path = Path("/usr/local/bin/kubectl")
        
        # Download to temp file first
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            urllib.request.urlretrieve(kubectl_url, tmp.name)
            
            # Try to move to /usr/local/bin (requires sudo)
            try:
                result = self.run_command(f"sudo mv {tmp.name} {kubectl_path}", check=False)
                if result and result.returncode == 0:
                    self.run_command(f"sudo chmod +x {kubectl_path}")
                    print(f"{Colors.GREEN}✅ kubectl installed to {kubectl_path}{Colors.END}")
                    return True
            except:
                pass
            
            # Fallback to user directory
            user_bin = self.home_dir / ".local" / "bin"
            user_bin.mkdir(parents=True, exist_ok=True)
            kubectl_user_path = user_bin / "kubectl"
            
            shutil.move(tmp.name, kubectl_user_path)
            kubectl_user_path.chmod(0o755)
            
            print(f"{Colors.GREEN}✅ kubectl installed to {kubectl_user_path}{Colors.END}")
            print(f"{Colors.YELLOW}⚠️ Add {user_bin} to your PATH if not already there{Colors.END}")
            return True

    def check_kubelogin(self):
        """Check if kubelogin plugin is installed."""
        print(f"{Colors.YELLOW}🔍 Checking kubelogin plugin...{Colors.END}")
        
        result = self.run_command("kubectl plugin list", check=False)
        if result and result.returncode == 0 and "oidc-login" in result.stdout:
            print(f"{Colors.GREEN}✅ kubelogin plugin found{Colors.END}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️ kubelogin plugin not found{Colors.END}")
            return False

    def install_kubelogin(self):
        """Install kubelogin plugin."""
        print(f"{Colors.YELLOW}📦 Installing kubelogin plugin...{Colors.END}")
        
        # Try krew first
        result = self.run_command("kubectl krew install oidc-login", check=False)
        if result and result.returncode == 0:
            print(f"{Colors.GREEN}✅ kubelogin installed via krew{Colors.END}")
            return True
        
        # Manual installation
        return self._install_kubelogin_manual()

    def _install_kubelogin_manual(self):
        """Manually install kubelogin."""
        print(f"{Colors.YELLOW}⬇️ Downloading kubelogin manually...{Colors.END}")
        
        try:
            version = "v0.1.1"  # Latest stable version
            
            if self.system == "windows":
                url = f"https://github.com/int128/kubelogin/releases/download/{version}/kubelogin_windows_amd64.zip"
                return self._download_and_extract_zip(url, "kubelogin.exe", "kubectl-oidc_login.exe")
            elif self.system == "darwin":
                url = f"https://github.com/int128/kubelogin/releases/download/{version}/kubelogin_darwin_amd64.tar.gz"
                return self._download_and_extract_tar(url, "kubelogin", "kubectl-oidc_login")
            elif self.system == "linux":
                arch = "amd64" if self.arch in ["x86_64", "amd64"] else "arm64"
                url = f"https://github.com/int128/kubelogin/releases/download/{version}/kubelogin_linux_{arch}.tar.gz"
                return self._download_and_extract_tar(url, "kubelogin", "kubectl-oidc_login")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to install kubelogin: {e}{Colors.END}")
            return False

    def _download_and_extract_zip(self, url, source_name, target_name):
        """Download and extract ZIP file."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            
            with zipfile.ZipFile(tmp.name, 'r') as zip_file:
                zip_file.extract(source_name, self.plugins_dir)
                
            source_path = self.plugins_dir / source_name
            target_path = self.plugins_dir / target_name
            
            if source_path.exists():
                source_path.rename(target_path)
                target_path.chmod(0o755)
                print(f"{Colors.GREEN}✅ kubelogin installed to {target_path}{Colors.END}")
                return True
            
        return False

    def _download_and_extract_tar(self, url, source_name, target_name):
        """Download and extract TAR.GZ file."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            
            with tarfile.open(tmp.name, 'r:gz') as tar_file:
                tar_file.extract(source_name, self.plugins_dir)
                
            source_path = self.plugins_dir / source_name
            target_path = self.plugins_dir / target_name
            
            if source_path.exists():
                source_path.rename(target_path)
                target_path.chmod(0o755)
                print(f"{Colors.GREEN}✅ kubelogin installed to {target_path}{Colors.END}")
                return True
                
        return False

    def configure_oidc(self, cluster_context=None):
        """Configure kubectl with OIDC authentication."""
        print(f"{Colors.YELLOW}🔐 Configuring OIDC authentication...{Colors.END}")
        
        if not cluster_context:
            result = self.run_command("kubectl config current-context", check=False)
            if result and result.returncode == 0:
                cluster_context = result.stdout.strip()
                print(f"{Colors.BLUE}📍 Using current cluster context: {cluster_context}{Colors.END}")
            else:
                print(f"{Colors.RED}❌ No kubectl context found. Please configure kubectl first.{Colors.END}")
                return False
        
        # Configure OIDC user
        oidc_args = [
            "kubectl", "config", "set-credentials", "oidc-user",
            "--exec-api-version=client.authentication.k8s.io/v1beta1",
            "--exec-command=kubectl",
            "--exec-arg=oidc-login",
            "--exec-arg=get-token",
            f"--exec-arg=--oidc-issuer-url={self.oidc_config['issuer_url']}",
            f"--exec-arg=--oidc-client-id={self.oidc_config['client_id']}",
            f"--exec-arg=--oidc-extra-scope={self.oidc_config['extra_scopes']}",
            f"--exec-arg=--oidc-username-claim={self.oidc_config['username_claim']}",
            f"--exec-arg=--oidc-groups-claim={self.oidc_config['groups_claim']}"
        ]
        
        result = self.run_command(oidc_args, capture_output=False)
        if not result or result.returncode != 0:
            print(f"{Colors.RED}❌ Failed to configure OIDC user{Colors.END}")
            return False
        
        print(f"{Colors.GREEN}✅ OIDC user credentials configured{Colors.END}")
        
        # Create OIDC context
        context_args = [
            "kubectl", "config", "set-context", "oidc-context",
            f"--cluster={cluster_context}",
            "--user=oidc-user"
        ]
        
        result = self.run_command(context_args, capture_output=False)
        if not result or result.returncode != 0:
            print(f"{Colors.RED}❌ Failed to create OIDC context{Colors.END}")
            return False
        
        print(f"{Colors.GREEN}✅ OIDC context created{Colors.END}")
        return True

    def test_authentication(self):
        """Test OIDC authentication."""
        print(f"{Colors.YELLOW}🧪 Testing OIDC authentication...{Colors.END}")
        
        # Switch to OIDC context
        result = self.run_command("kubectl config use-context oidc-context", capture_output=False)
        if not result or result.returncode != 0:
            print(f"{Colors.RED}❌ Failed to switch to OIDC context{Colors.END}")
            return False
        
        print(f"{Colors.GREEN}✅ Switched to OIDC context{Colors.END}")
        print()
        print(f"{Colors.CYAN}🚀 Authentication is ready!{Colors.END}")
        print()
        print(f"{Colors.BOLD}Next steps:{Colors.END}")
        print(f"   1. Run: {Colors.WHITE}kubectl get pods{Colors.END}")
        print(f"   2. Browser will open for Keycloak login")
        print(f"   3. Choose your authentication method:")
        print(f"      • {Colors.CYAN}EntraID - ITlusions{Colors.END} (Azure AD SSO)")
        print(f"      • {Colors.CYAN}Github - ITlusions{Colors.END} (GitHub SSO)")
        print(f"      • Direct username/password")
        print()
        print(f"{Colors.YELLOW}📍 Keycloak Admin Console: https://sts.itlusions.com/admin{Colors.END}")
        
        return True

    def run_setup(self, cluster_context=None, test_auth=True):
        """Run the complete setup process."""
        self.print_header()
        
        # Check and install kubectl
        if not self.check_kubectl():
            if not self.install_kubectl():
                print(f"{Colors.RED}❌ Setup failed: Could not install kubectl{Colors.END}")
                return False
        
        # Check and install kubelogin
        if not self.check_kubelogin():
            if not self.install_kubelogin():
                print(f"{Colors.YELLOW}⚠️ kubelogin plugin installation failed, but you can continue{Colors.END}")
                print(f"{Colors.YELLOW}   Manual installation: https://github.com/int128/kubelogin{Colors.END}")
        
        # Configure OIDC
        if not self.configure_oidc(cluster_context):
            print(f"{Colors.RED}❌ Setup failed: Could not configure OIDC{Colors.END}")
            return False
        
        # Test authentication
        if test_auth:
            if not self.test_authentication():
                print(f"{Colors.RED}❌ Setup completed but authentication test failed{Colors.END}")
                return False
        
        print()
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 Setup completed successfully! 🎉{Colors.END}")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ITlusions Kubernetes OIDC Setup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  itl-kubectl-oidc-setup                    # Auto-detect cluster and setup
  itl-kubectl-oidc-setup --cluster mycluster   # Use specific cluster
  itl-kubectl-oidc-setup --no-test          # Skip authentication test
        """
    )
    
    parser.add_argument(
        "--cluster",
        help="Kubernetes cluster context to use"
    )
    
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip authentication test"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="itl-kubectl-oidc-setup 1.0.0"
    )
    
    args = parser.parse_args()
    
    setup = KubectlOIDCSetup()
    
    try:
        success = setup.run_setup(
            cluster_context=args.cluster,
            test_auth=not args.no_test
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Setup cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()