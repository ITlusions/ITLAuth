#!/usr/bin/env python3
"""
ITLAuth Installation Verification Script

This script checks if ITLAuth is properly installed and configured.
"""

import sys
import subprocess
import shutil
from pathlib import Path


class Colors:
    """ANSI color codes."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header():
    """Print the script header."""
    print(f"{Colors.GREEN}{Colors.BOLD}")
    print("═══════════════════════════════════════════════════════")
    print("  ITLAuth Installation Verification")
    print("═══════════════════════════════════════════════════════")
    print(f"{Colors.END}\n")


def check_mark(success):
    """Return a check or cross mark."""
    return f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"


def check_python():
    """Check Python version."""
    print(f"{Colors.CYAN}Checking Python...{Colors.END}")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version >= (3, 8):
        print(f"  {check_mark(True)} Python {version_str}")
        return True
    else:
        print(f"  {check_mark(False)} Python {version_str} (requires 3.8+)")
        return False


def check_pip():
    """Check if pip is available."""
    print(f"{Colors.CYAN}Checking pip...{Colors.END}")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip().split()[1]
        print(f"  {check_mark(True)} pip {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        print(f"  {check_mark(False)} pip not found")
        return False


def check_package_installed():
    """Check if the package is installed."""
    print(f"{Colors.CYAN}Checking itl-kubectl-oidc-setup package...{Colors.END}")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "itl-kubectl-oidc-setup"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse version from output
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                version = line.split(':')[1].strip()
                print(f"  {check_mark(True)} Package installed (version {version})")
                return True
        
        print(f"  {check_mark(True)} Package installed")
        return True
    except subprocess.CalledProcessError:
        print(f"  {check_mark(False)} Package not installed")
        return False


def check_command_available():
    """Check if the command is available in PATH."""
    print(f"{Colors.CYAN}Checking command availability...{Colors.END}")
    
    cmd_path = shutil.which("itl-kubectl-oidc-setup")
    if cmd_path:
        print(f"  {check_mark(True)} Command found at: {cmd_path}")
        
        # Try to get version
        try:
            result = subprocess.run(
                ["itl-kubectl-oidc-setup", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            # Parse version more robustly
            output = result.stdout.strip()
            if output:
                # Extract version number from output
                parts = output.split()
                if len(parts) >= 2:
                    version = parts[-1]
                    print(f"  {check_mark(True)} Version: {version}")
                else:
                    print(f"  {check_mark(True)} Version check successful")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, IndexError) as e:
            print(f"  {check_mark(False)} Could not determine version: {e}")
        
        return True
    else:
        print(f"  {check_mark(False)} Command not found in PATH")
        
        # Try to find it in common locations
        home = Path.home()
        common_paths = [
            home / ".local" / "bin" / "itl-kubectl-oidc-setup",
        ]
        
        # Add Python Library paths dynamically for macOS
        if sys.platform == "darwin":
            python_lib_base = home / "Library" / "Python"
            if python_lib_base.exists():
                for version_dir in python_lib_base.iterdir():
                    if version_dir.is_dir():
                        bin_path = version_dir / "bin" / "itl-kubectl-oidc-setup"
                        common_paths.append(bin_path)
        
        for path in common_paths:
            if path.exists():
                print(f"  {Colors.YELLOW}⚠{Colors.END} Found at: {path}")
                print(f"  {Colors.YELLOW}⚠{Colors.END} Add to PATH: export PATH=\"{path.parent}:$PATH\"")
                return False
        
        return False


def check_kubectl():
    """Check if kubectl is installed."""
    print(f"{Colors.CYAN}Checking kubectl (optional)...{Colors.END}")
    
    cmd_path = shutil.which("kubectl")
    if cmd_path:
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client", "--short"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            print(f"  {check_mark(True)} kubectl found: {version}")
        except subprocess.CalledProcessError:
            print(f"  {check_mark(True)} kubectl found at: {cmd_path}")
        return True
    else:
        print(f"  {check_mark(False)} kubectl not found (will be installed by setup tool)")
        return False


def check_kubeconfig():
    """Check if kubeconfig exists."""
    print(f"{Colors.CYAN}Checking kubeconfig (optional)...{Colors.END}")
    
    kubeconfig = Path.home() / ".kube" / "config"
    if kubeconfig.exists():
        print(f"  {check_mark(True)} kubeconfig found at: {kubeconfig}")
        return True
    else:
        print(f"  {check_mark(False)} kubeconfig not found (will be created by setup tool)")
        return False


def print_summary(checks):
    """Print summary and next steps."""
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check_name, result in checks.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {check_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    # Determine overall status
    required_checks = ["Python", "pip", "Package", "Command"]
    required_passed = all(checks.get(check, False) for check in required_checks)
    
    if required_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Installation verified successfully!{Colors.END}\n")
        print(f"{Colors.BOLD}Next steps:{Colors.END}")
        print(f"  1. Run: {Colors.CYAN}itl-kubectl-oidc-setup{Colors.END}")
        print(f"  2. Follow the interactive prompts")
        print(f"  3. Authenticate with your ITlusions credentials\n")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Installation incomplete{Colors.END}\n")
        print(f"{Colors.BOLD}Recommendations:{Colors.END}")
        
        if not checks.get("Python", False):
            print(f"  • Install Python 3.8 or higher")
        if not checks.get("pip", False):
            print(f"  • Install pip: python -m ensurepip")
        if not checks.get("Package", False):
            print(f"  • Install package: pip install itl-kubectl-oidc-setup")
        if not checks.get("Command", False):
            print(f"  • Add Python bin directory to PATH")
        print()


def main():
    """Main verification process."""
    print_header()
    
    checks = {}
    
    # Required checks
    checks["Python"] = check_python()
    checks["pip"] = check_pip()
    checks["Package"] = check_package_installed()
    checks["Command"] = check_command_available()
    
    print()
    
    # Optional checks
    checks["kubectl"] = check_kubectl()
    checks["kubeconfig"] = check_kubeconfig()
    
    # Print summary
    print_summary(checks)
    
    # Exit with appropriate code
    required_checks = ["Python", "pip", "Package", "Command"]
    if all(checks.get(check, False) for check in required_checks):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
