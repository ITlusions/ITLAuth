#!/usr/bin/env python3
"""
Keycloak Service Account Manager
Comprehensive tool for managing Keycloak-based service accounts for Kubernetes
"""
import requests
import json
import yaml
import os
import base64
import subprocess
from datetime import datetime, timedelta
import getpass

class KeycloakServiceAccountManager:
    def __init__(self, keycloak_url="https://sts.itlusions.com", realm="itlusions"):
        self.keycloak_url = keycloak_url.rstrip('/')
        self.realm = realm
        self.admin_token = None
        
    def get_admin_token(self, username, password):
        """Get admin token for Keycloak operations"""
        url = f"{self.keycloak_url}/realms/master/protocol/openid-connect/token"
        data = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": "admin-cli"
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.admin_token = response.json().get("access_token")
            return True
        else:
            print(f"❌ Failed to get admin token: {response.text}")
            return False
    
    def create_service_account_client(self, client_id, description="Kubernetes Service Account"):
        """Create a service account client in Keycloak"""
        if not self.admin_token:
            print("❌ No admin token available")
            return None
            
        url = f"{self.keycloak_url}/admin/realms/{self.realm}/clients"
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        client_data = {
            "clientId": client_id,
            "name": f"{client_id} Service Account",
            "description": description,
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "serviceAccountsEnabled": True,
            "standardFlowEnabled": False,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "publicClient": False,
            "protocol": "openid-connect",
            "attributes": {
                "access.token.lifespan": "3600",
                "client.session.idle.timeout": "1800",
                "client.session.max.lifespan": "36000"
            }
        }
        
        response = requests.post(url, headers=headers, json=client_data)
        if response.status_code == 201:
            print(f"✅ Service account client '{client_id}' created")
            return self.get_client_info(client_id)
        else:
            print(f"❌ Failed to create client: {response.text}")
            return None
    
    def get_client_info(self, client_id):
        """Get client information including secret"""
        if not self.admin_token:
            return None
            
        # Get client UUID
        url = f"{self.keycloak_url}/admin/realms/{self.realm}/clients"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        params = {"clientId": client_id}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return None
            
        clients = response.json()
        if not clients:
            return None
            
        client_uuid = clients[0]["id"]
        
        # Get client secret
        secret_url = f"{self.keycloak_url}/admin/realms/{self.realm}/clients/{client_uuid}/client-secret"
        secret_response = requests.get(secret_url, headers=headers)
        
        if secret_response.status_code == 200:
            client_secret = secret_response.json().get("value")
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "client_uuid": client_uuid
            }
        return None
    
    def add_client_to_group(self, client_id, group_name="itl-cluster-admin"):
        """Add service account to a Keycloak group"""
        if not self.admin_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Get client info
        client_info = self.get_client_info(client_id)
        if not client_info:
            return False
            
        # Get service account user
        sa_url = f"{self.keycloak_url}/admin/realms/{self.realm}/clients/{client_info['client_uuid']}/service-account-user"
        sa_response = requests.get(sa_url, headers=headers)
        
        if sa_response.status_code != 200:
            print("❌ Failed to get service account user")
            return False
            
        sa_user_id = sa_response.json().get("id")
        
        # Get group ID
        groups_url = f"{self.keycloak_url}/admin/realms/{self.realm}/groups"
        groups_response = requests.get(groups_url, headers=headers, params={"search": group_name})
        
        if groups_response.status_code != 200:
            print(f"❌ Failed to find group: {group_name}")
            return False
            
        groups = groups_response.json()
        if not groups:
            print(f"❌ Group '{group_name}' not found")
            return False
            
        group_id = groups[0]["id"]
        
        # Add user to group
        add_url = f"{self.keycloak_url}/admin/realms/{self.realm}/users/{sa_user_id}/groups/{group_id}"
        add_response = requests.put(add_url, headers=headers)
        
        if add_response.status_code == 204:
            print(f"✅ Service account added to group: {group_name}")
            return True
        else:
            print(f"❌ Failed to add to group: {add_response.text}")
            return False
    
    def test_service_account(self, client_id, client_secret):
        """Test service account authentication"""
        url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            return {
                "access_token": token_data.get("access_token"),
                "expires_in": token_data.get("expires_in"),
                "token_type": token_data.get("token_type")
            }
        return None
    
    def create_kubeconfig(self, client_id, client_secret, output_path=None):
        """Create kubeconfig for service account"""
        if not output_path:
            output_path = f"{os.path.expanduser('~')}/.kube/config-sa-{client_id}"
        
        # Get cluster info
        try:
            cluster_url = subprocess.check_output([
                "kubectl", "config", "view", "--minify", 
                "-o", "jsonpath={.clusters[0].cluster.server}"
            ], text=True).strip()
            
            cluster_ca = subprocess.check_output([
                "kubectl", "config", "view", "--raw", "--minify", "--flatten",
                "-o", "jsonpath={.clusters[0].cluster.certificate-authority-data}"
            ], text=True).strip()
        except subprocess.CalledProcessError:
            print("❌ Failed to get cluster information")
            return None
        
        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": "kubernetes-cluster",
                "cluster": {
                    "server": cluster_url,
                    "certificate-authority-data": cluster_ca
                }
            }],
            "users": [{
                "name": f"keycloak-sa-{client_id}",
                "user": {
                    "exec": {
                        "apiVersion": "client.authentication.k8s.io/v1beta1",
                        "command": "kubelogin",
                        "args": [
                            "get-token",
                            f"--oidc-issuer-url={self.keycloak_url}/realms/{self.realm}",
                            f"--oidc-client-id={client_id}",
                            f"--oidc-client-secret={client_secret}",
                            "--grant-type=client_credentials"
                        ],
                        "env": None,
                        "provideClusterInfo": False
                    }
                }
            }],
            "contexts": [{
                "name": f"keycloak-sa-context",
                "context": {
                    "cluster": "kubernetes-cluster",
                    "user": f"keycloak-sa-{client_id}"
                }
            }],
            "current-context": f"keycloak-sa-context"
        }
        
        with open(output_path, "w") as f:
            yaml.dump(kubeconfig, f, default_flow_style=False)
        
        print(f"✅ Kubeconfig created: {output_path}")
        return output_path

def main():
    print("🔑 Keycloak Service Account Manager")
    print("=" * 50)
    
    manager = KeycloakServiceAccountManager()
    
    # Get admin credentials
    admin_user = input("Enter Keycloak admin username: ")
    admin_password = getpass.getpass("Enter Keycloak admin password: ")
    
    if not manager.get_admin_token(admin_user, admin_password):
        print("❌ Failed to authenticate as admin")
        return
    
    print("✅ Admin authentication successful")
    
    # Create service account
    client_id = input("Enter service account client ID (default: k8s-automation-sa): ").strip()
    if not client_id:
        client_id = "k8s-automation-sa"
    
    description = input("Enter description (optional): ").strip()
    if not description:
        description = f"Kubernetes automation service account - {client_id}"
    
    # Create the client
    client_info = manager.create_service_account_client(client_id, description)
    if not client_info:
        print("❌ Failed to create service account")
        return
    
    print(f"✅ Service account created!")
    print(f"   Client ID: {client_info['client_id']}")
    print(f"   Client Secret: {client_info['client_secret']}")
    
    # Add to group
    if input("Add to itl-cluster-admin group? (y/N): ").lower().startswith('y'):
        manager.add_client_to_group(client_id)
    
    # Test authentication
    print("\n🧪 Testing service account authentication...")
    token_info = manager.test_service_account(client_info['client_id'], client_info['client_secret'])
    if token_info:
        print("✅ Service account authentication successful!")
        print(f"   Token expires in: {token_info['expires_in']} seconds")
    else:
        print("❌ Service account authentication failed")
        return
    
    # Create kubeconfig
    if input("\nCreate kubeconfig file? (Y/n): ").lower() != 'n':
        config_path = manager.create_kubeconfig(client_info['client_id'], client_info['client_secret'])
        if config_path:
            print(f"\n🎉 Setup complete!")
            print(f"📁 Kubeconfig: {config_path}")
            print(f"🔧 To use: export KUBECONFIG={config_path}")
            print(f"🧪 Test: kubectl auth whoami")

if __name__ == "__main__":
    main()