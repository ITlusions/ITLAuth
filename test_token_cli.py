#!/usr/bin/env python3
"""
Test script for ITL Token Manager CLI
Verify installation and basic functionality
"""
import subprocess
import sys


def run_command(cmd):
    """Run command and capture output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def test_cli_installed():
    """Test if CLI is installed"""
    print("[*] Testing CLI installation...")
    code, stdout, stderr = run_command("itlc --version")
    
    if code == 0:
        print(f"[✓] CLI installed: {stdout.strip()}")
        return True
    else:
        print(f"[✗] CLI not installed or not in PATH")
        print(f"    Error: {stderr}")
        return False


def test_help_command():
    """Test help command"""
    print("\n[*] Testing help command...")
    code, stdout, stderr = run_command("itlc --help")
    
    if code == 0 and "get-token" in stdout:
        print("[✓] Help command works")
        return True
    else:
        print("[✗] Help command failed")
        return False


def test_config_command():
    """Test config command"""
    print("\n[*] Testing config command...")
    code, stdout, stderr = run_command("itlc config")
    
    if code == 0 and "Configuration" in stdout:
        print("[✓] Config command works")
        print(f"\n{stdout}")
        return True
    else:
        print("[✗] Config command failed")
        return False


def test_cache_list():
    """Test cache-list command"""
    print("\n[*] Testing cache-list command...")
    code, stdout, stderr = run_command("itlc cache-list")
    
    if code == 0:
        print("[✓] Cache-list command works")
        return True
    else:
        print("[✗] Cache-list command failed")
        return False


def test_import():
    """Test Python imports"""
    print("\n[*] Testing Python imports...")
    try:
        from itl_token_cli import TokenCache, KeycloakClient
        print("[✓] Python imports work")
        return True
    except ImportError as e:
        print(f"[✗] Import failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ITL Token Manager CLI - Installation Test")
    print("=" * 60)
    
    tests = [
        test_cli_installed,
        test_help_command,
        test_config_command,
        test_cache_list,
        test_import,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\n[!] Some tests failed. Try reinstalling:")
        print("    cd d:\\repos\\ITLAuth")
        print("    pip install -e .")
        sys.exit(1)
    else:
        print("\n[✓] All tests passed!")
        print("\nNext steps:")
        print("  1. Set environment variables:")
        print("     $env:KEYCLOAK_CLIENT_ID = 'your-client-id'")
        print("     $env:KEYCLOAK_CLIENT_SECRET = 'your-secret'")
        print("  2. Get token:")
        print("     itlc get-token")
        sys.exit(0)


if __name__ == '__main__':
    main()
