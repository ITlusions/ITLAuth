#!/usr/bin/env python3
"""
Server Onboarding Module for ITL CLI

Handles automatic cluster registration and server setup with ITL STS platform.
"""
import subprocess
import sys
import platform
import requests
from pathlib import Path
from typing import Optional
import json


class ServerOnboardingClient:
    """Client for server onboarding operations"""
    
    def __init__(self, api_url: str = "https://auth.itlusions.com", token: Optional[str] = None):
        """Initialize server onboarding client"""
        self.api_url = api_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def generate_setup_token(self, cluster_name: str, environment: str = 'development') -> Optional[str]:
        """Generate a setup token for cluster registration"""
        try:
            response = self.session.post(
                f"{self.api_url}/api/server-setup/generate-token",
                json={
                    "cluster_name": cluster_name,
                    "environment": environment
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('token')
            else:
                return None
        except Exception as e:
            return None
    
    def validate_setup_token(self, token: str) -> bool:
        """Validate a setup token"""
        try:
            response = self.session.post(
                f"{self.api_url}/api/server-setup/validate-token",
                json={"token": token},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def register_cluster(self, cluster_name: str, token: str, environment: str = 'development') -> bool:
        """Register cluster with setup token"""
        try:
            response = self.session.post(
                f"{self.api_url}/api/server-setup/register",
                json={
                    "cluster_name": cluster_name,
                    "token": token,
                    "environment": environment
                },
                timeout=30
            )
            return response.status_code in [200, 201]
        except Exception:
            return False


def check_kubectl_installed() -> bool:
    """Check if kubectl is installed"""
    try:
        result = subprocess.run(
            ['kubectl', 'version', '--client'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def apply_cluster_setup(token: str) -> bool:
    """Apply cluster setup using kubectl"""
    try:
        result = subprocess.run(
            ['kubectl', 'apply', '-f', 'https://auth.itlusions.com/setup', f'--token={token}'],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except Exception:
        return False


def display_setup_instructions(location: str, token: str, cluster_name: str) -> None:
    """Display setup instructions based on execution location"""
    if location == 'local':
        click_echo(f"Run this command on your local machine:")
        click_echo(f"  kubectl apply -f https://auth.itlusions.com/setup --token={token}\n")
    
    elif location == 'remote':
        click_echo(f"Run these commands on your remote server setup:")
        click_echo(f"  1. scp ~/.kube/config user@remote-server:~/kubeconfig")
        click_echo(f"  2. ssh user@remote-server")
        click_echo(f"  3. kubectl --kubeconfig=~/kubeconfig --context={cluster_name} apply -f https://auth.itlusions.com/setup --token={token}\n")
    
    elif location == 'terraform':
        click_echo(f"Add this to your Terraform configuration:")
        tf_code = f'''
resource "null_resource" "itl_setup" {{
  provisioner "local-exec" {{
    command = "kubectl apply -f https://auth.itlusions.com/setup --token={token}"
  }}
  depends_on = [kubernetes_cluster.my_cluster]
}}
'''
        click_echo(tf_code)


def save_token_locally(token: str, cluster_name: str) -> Path:
    """Save token to local file for reference"""
    config_dir = Path.home() / '.itl' / 'onboarding'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    token_file = config_dir / f'{cluster_name}.token'
    token_file.write_text(token)
    token_file.chmod(0o600)
    
    return token_file


def click_echo(msg: str) -> None:
    """Echo message (compatible with click when available)"""
    try:
        import click
        click.echo(msg)
    except ImportError:
        print(msg)
