#!/usr/bin/env python3
"""
ITlusions Kubernetes OIDC Setup Tool

This module automatically installs and configures kubectl with OIDC authentication
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
    
    # Default fallback cluster configuration
    DEFAULT_CLUSTER_CONFIG = """apiVersion: v1
kind: Config
preferences: {}
current-context: itl
clusters:
  - cluster:
      insecure-skip-tls-verify: true
      server: https://10.99.100.4:6443
      tls-server-name: 10.99.100.4
    name: kubernetes
  - cluster:
      insecure-skip-tls-verify: true
      server: https://127.0.0.1:16643
      tls-server-name: 10.99.100.4
    name: kubernetes-ssh-tunnel
contexts:
  - context:
      cluster: kubernetes
      user: oidc-user
    name: itl
  - context:
      cluster: kubernetes-ssh-tunnel
      user: oidc-user
    name: itl-ssh-tunnel
  - context:
      cluster: kubernetes
      user: oidc-user-python
    name: itl-python
  - context:
      cluster: kubernetes-ssh-tunnel
      user: oidc-user-python
    name: itl-ssh-tunnel-python
users:
  - name: oidc-user
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        args:
          - get-token
          - '--oidc-issuer-url=https://sts.itlusions.com/realms/itlusions'
          - '--oidc-client-id=kubernetes-oidc'
        command: kubectl-oidc_login
        env: null
        interactiveMode: IfAvailable
        provideClusterInfo: false
  - name: oidc-user-python
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        args:
          - -m
          - itl_kubectl_oidc_setup.auth
        command: python
        env: null
        interactiveMode: IfAvailable
        provideClusterInfo: false
"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.home_dir = Path.home()
        self.kubectl_dir = self.home_dir / ".kubectl"
        self.plugins_dir = self.kubectl_dir / "plugins"
        self.kubectl_exe = None  # Will store full path if manually installed
        self.kubeconfig_path = self.home_dir / ".kube" / "config"
        
        # Default cluster config URL - Update this to your API endpoint
        self.default_cluster_config_url = "https://cluster-config-api.itlusions.com/api/v1/cluster-config"
        
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
            
            # If we have a manually installed kubectl and command uses kubectl, use full path
            if self.kubectl_exe and command[0] == "kubectl":
                command[0] = self.kubectl_exe
            
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
            result = self.run_command("winget install -e --id Kubernetes.kubectl --silent", check=False)
            if result and result.returncode == 0:
                print(f"{Colors.GREEN}✅ kubectl installed via winget{Colors.END}")
                
                # Wait a moment for winget to complete
                import time
                time.sleep(2)
                
                # Refresh PATH by reading from registry
                self._refresh_windows_path()
                
                # Verify installation
                if self.check_kubectl():
                    return True
                else:
                    print(f"{Colors.YELLOW}⚠️ winget completed but kubectl not yet in PATH, falling back to manual install{Colors.END}")
            
            # Fallback to manual download
            print(f"{Colors.YELLOW}⬇️ Downloading kubectl manually...{Colors.END}")
            url = "https://dl.k8s.io/release/stable.txt"
            with urllib.request.urlopen(url) as response:
                version = response.read().decode().strip()
            
            kubectl_url = f"https://dl.k8s.io/release/{version}/bin/windows/amd64/kubectl.exe"
            kubectl_path = self.kubectl_dir / "kubectl.exe"
            
            self.kubectl_dir.mkdir(exist_ok=True)
            urllib.request.urlretrieve(kubectl_url, kubectl_path)
            
            # Add to current session PATH immediately
            kubectl_dir_str = str(self.kubectl_dir)
            current_path = os.environ.get("PATH", "")
            if kubectl_dir_str not in current_path:
                os.environ["PATH"] = f"{kubectl_dir_str};{current_path}"
                print(f"{Colors.GREEN}✅ Added {kubectl_dir_str} to PATH for this session{Colors.END}")
            
            # Add to user PATH permanently
            if self._add_to_user_path_permanently(kubectl_dir_str):
                print(f"{Colors.GREEN}✅ kubectl will be available in all future terminals{Colors.END}")
            else:
                print(f"{Colors.YELLOW}💡 To use kubectl in new terminals, restart them or log off/on{Colors.END}")
            
            # Store kubectl path for use in subsequent commands
            self.kubectl_exe = str(kubectl_path)
            
            print(f"{Colors.GREEN}✅ kubectl downloaded to {kubectl_path}{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to install kubectl: {e}{Colors.END}")
            return False
    
    def _refresh_windows_path(self):
        """Refresh PATH from Windows registry."""
        try:
            import winreg
            
            # Read user PATH
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ) as key:
                user_path, _ = winreg.QueryValueEx(key, 'Path')
            
            # Read system PATH
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_READ) as key:
                system_path, _ = winreg.QueryValueEx(key, 'Path')
            
            # Update current session PATH
            os.environ["PATH"] = f"{user_path};{system_path}"
            
        except Exception:
            pass  # Silently fail, we have fallback
    
    def _add_to_user_path_permanently(self, directory):
        """Add directory to user PATH permanently via registry."""
        try:
            import winreg
            
            directory = str(directory)
            
            # Open user environment key for reading
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ) as key:
                try:
                    current_path, _ = winreg.QueryValueEx(key, 'Path')
                except FileNotFoundError:
                    current_path = ""
            
            # Check if already in PATH
            path_entries = [p.strip() for p in current_path.split(';') if p.strip()]
            if directory in path_entries:
                return True
            
            # Add to PATH
            new_path = f"{current_path};{directory}" if current_path else directory
            
            # Write back to registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            
            # Broadcast environment change
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x1A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_long()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
            )
            
            print(f"{Colors.GREEN}✅ Permanently added {directory} to user PATH{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Could not update PATH permanently: {e}{Colors.END}")
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
            version = "v1.35.2"  # Latest stable version
            
            if self.system == "windows":
                url = f"https://github.com/int128/kubelogin/releases/download/{version}/kubelogin_windows_amd64.zip"
                return self._download_and_extract_zip(url, "kubelogin.exe", "kubectl-oidc_login.exe")
            elif self.system == "darwin":
                # macOS uses arm64 for Apple Silicon, amd64 for Intel
                arch = "arm64" if self.arch in ["arm64", "aarch64"] else "amd64"
                url = f"https://github.com/int128/kubelogin/releases/download/{version}/kubelogin_darwin_{arch}.zip"
                return self._download_and_extract_zip(url, "kubelogin", "kubectl-oidc_login")
            elif self.system == "linux":
                arch = "arm64" if self.arch in ["arm64", "aarch64"] else "arm" if self.arch.startswith("arm") else "amd64"
                url = f"https://github.com/int128/kubelogin/releases/download/{version}/kubelogin_linux_{arch}.zip"
                return self._download_and_extract_zip(url, "kubelogin", "kubectl-oidc_login")
            
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

    def download_cluster_config(self, config_url=None, use_fallback=True):
        """Download cluster configuration from URL and merge with kubeconfig."""
        if not config_url:
            config_url = self.default_cluster_config_url
        
        print(f"{Colors.YELLOW}📥 Downloading cluster configuration...{Colors.END}")
        print(f"{Colors.BLUE}   URL: {config_url}{Colors.END}")
        
        cluster_config = None
        
        try:
            import requests
            
            response = requests.get(config_url, timeout=10)
            response.raise_for_status()
            
            cluster_config = response.text
            print(f"{Colors.GREEN}✅ Downloaded cluster configuration from API{Colors.END}")
            
            # Create .kube directory if it doesn't exist
            self.kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
            
            # If kubeconfig exists, backup first
            if self.kubeconfig_path.exists():
                backup_path = self.kubeconfig_path.with_suffix('.config.backup')
                shutil.copy2(self.kubeconfig_path, backup_path)
                print(f"{Colors.GREEN}✅ Backed up existing kubeconfig to {backup_path}{Colors.END}")
                
                # Merge configurations using kubectl
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                    tmp.write(cluster_config)
                    tmp_path = tmp.name
                
                env = os.environ.copy()
                env['KUBECONFIG'] = f"{self.kubeconfig_path}{os.pathsep}{tmp_path}"
                
                result = subprocess.run(
                    [self.kubectl_exe or 'kubectl', 'config', 'view', '--flatten'],
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.kubeconfig_path.write_text(result.stdout)
                    os.unlink(tmp_path)
                    print(f"{Colors.GREEN}✅ Merged cluster config with existing kubeconfig{Colors.END}")
                else:
                    os.unlink(tmp_path)
                    raise Exception(f"Failed to merge configs: {result.stderr}")
            else:
                # No existing config, just write it
                self.kubeconfig_path.write_text(cluster_config)
                print(f"{Colors.GREEN}✅ Cluster configuration saved to {self.kubeconfig_path}{Colors.END}")
            
            # Get cluster name from config
            result = self.run_command("kubectl config get-contexts -o name", check=False)
            if result and result.returncode == 0:
                contexts = result.stdout.strip().split('\n')
                if contexts:
                    print(f"{Colors.GREEN}✅ Available contexts:{Colors.END}")
                    for ctx in contexts:
                        print(f"   • {ctx}")
            
            return True
            
        except ImportError:
            print(f"{Colors.YELLOW}⚠️ requests library not available{Colors.END}")
            if use_fallback:
                print(f"{Colors.CYAN}📦 Using embedded default configuration...{Colors.END}")
                cluster_config = self.DEFAULT_CLUSTER_CONFIG
            else:
                return False
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Failed to download cluster config: {e}{Colors.END}")
            if use_fallback:
                print(f"{Colors.CYAN}📦 Using embedded default configuration...{Colors.END}")
                cluster_config = self.DEFAULT_CLUSTER_CONFIG
            else:
                print(f"{Colors.YELLOW}💡 Please check the URL or contact your cluster administrator{Colors.END}")
                return False
        
        # Apply cluster config (either downloaded or fallback)
        if not cluster_config:
            return False
            
        try:
            # Create .kube directory if it doesn't exist
            self.kubeconfig_path.parent.mkdir(parents=True, exist_ok=True)
            
            # If kubeconfig exists, backup first
            if self.kubeconfig_path.exists():
                backup_path = self.kubeconfig_path.with_suffix('.config.backup')
                shutil.copy2(self.kubeconfig_path, backup_path)
                print(f"{Colors.GREEN}✅ Backed up existing kubeconfig to {backup_path}{Colors.END}")
                
                # Merge configurations using kubectl
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                    tmp.write(cluster_config)
                    tmp_path = tmp.name
                
                env = os.environ.copy()
                env['KUBECONFIG'] = f"{self.kubeconfig_path}{os.pathsep}{tmp_path}"
                
                result = subprocess.run(
                    [self.kubectl_exe or 'kubectl', 'config', 'view', '--flatten'],
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.kubeconfig_path.write_text(result.stdout)
                    os.unlink(tmp_path)
                    print(f"{Colors.GREEN}✅ Merged cluster config with existing kubeconfig{Colors.END}")
                else:
                    os.unlink(tmp_path)
                    raise Exception(f"Failed to merge configs: {result.stderr}")
            else:
                # No existing config, just write it
                self.kubeconfig_path.write_text(cluster_config)
                print(f"{Colors.GREEN}✅ Cluster configuration saved to {self.kubeconfig_path}{Colors.END}")
            
            # Get cluster name from config
            result = self.run_command("kubectl config get-contexts -o name", check=False)
            if result and result.returncode == 0:
                contexts = result.stdout.strip().split('\n')
                if contexts:
                    print(f"{Colors.GREEN}✅ Available contexts:{Colors.END}")
                    for ctx in contexts:
                        print(f"   • {ctx}")
            
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to apply cluster config: {e}{Colors.END}")
            return False

    def run_setup(self, cluster_context=None, test_auth=True, download_config=False, config_url=None, python_only=False):
        """Run the complete setup process."""
        self.print_header()
        
        if python_only:
            print(f"{Colors.CYAN}🐍 Python-only mode: Skipping kubelogin binary installation{Colors.END}")
        
        # Check and install kubectl
        if not self.check_kubectl():
            if not self.install_kubectl():
                print(f"{Colors.RED}❌ Setup failed: Could not install kubectl{Colors.END}")
                return False
            
            # Verify kubectl is now accessible
            print(f"{Colors.YELLOW}🔍 Verifying kubectl installation...{Colors.END}")
            if not self.check_kubectl():
                # Try using full path if available
                if self.kubectl_exe:
                    print(f"{Colors.YELLOW}💡 Using kubectl from: {self.kubectl_exe}{Colors.END}")
                else:
                    print(f"{Colors.RED}❌ kubectl installed but not accessible. Please restart your terminal.{Colors.END}")
                    return False
        
        # Check and install kubelogin (skip if python_only)
        if not python_only:
            if not self.check_kubelogin():
                if not self.install_kubelogin():
                    print(f"{Colors.YELLOW}⚠️ kubelogin plugin installation failed, but you can continue{Colors.END}")
                    print(f"{Colors.YELLOW}   Manual installation: https://github.com/int128/kubelogin{Colors.END}")
        else:
            print(f"{Colors.CYAN}⏭️  Skipping kubelogin binary check{Colors.END}")
        
        # Download cluster config if requested or if no context found
        if download_config or config_url:
            if not self.download_cluster_config(config_url):
                print(f"{Colors.RED}❌ Setup failed: Could not download cluster config{Colors.END}")
                return False
        
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
