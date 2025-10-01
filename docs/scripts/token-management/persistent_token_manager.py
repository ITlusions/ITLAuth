#!/usr/bin/env python3
"""
Persistent Kubernetes Token Manager
Creates and manages long-lived tokens for automation
"""
import json
import subprocess
import base64
import yaml
import os
from datetime import datetime, timedelta

class KubernetesTokenManager:
    def __init__(self):
        self.kubeconfig_path = os.path.expanduser("~/.kube/config")
        
    def create_service_account_token(self, sa_name="itl-automation-sa", namespace="default"):
        """Create a persistent service account with token"""
        print(f"🔑 Creating service account: {sa_name}")
        
        # Create service account
        subprocess.run([
            "kubectl", "create", "serviceaccount", sa_name, "-n", namespace
        ], check=True)
        
        # Create cluster role binding
        subprocess.run([
            "kubectl", "create", "clusterrolebinding", f"{sa_name}-binding",
            "--clusterrole=cluster-admin",
            f"--serviceaccount={namespace}:{sa_name}"
        ], check=True)
        
        # Create token secret
        secret_yaml = f"""
apiVersion: v1
kind: Secret
metadata:
  name: {sa_name}-token
  namespace: {namespace}
  annotations:
    kubernetes.io/service-account.name: {sa_name}
type: kubernetes.io/service-account-token
"""
        
        with open("/tmp/token-secret.yaml", "w") as f:
            f.write(secret_yaml)
        
        subprocess.run(["kubectl", "apply", "-f", "/tmp/token-secret.yaml"], check=True)
        
        # Wait and extract token
        import time
        time.sleep(5)
        
        token_result = subprocess.run([
            "kubectl", "get", "secret", f"{sa_name}-token", "-n", namespace,
            "-o", "jsonpath={.data.token}"
        ], capture_output=True, text=True, check=True)
        
        token = base64.b64decode(token_result.stdout).decode('utf-8')
        
        ca_result = subprocess.run([
            "kubectl", "get", "secret", f"{sa_name}-token", "-n", namespace,
            "-o", "jsonpath={.data.ca\\.crt}"
        ], capture_output=True, text=True, check=True)
        
        ca_cert = ca_result.stdout
        
        cluster_result = subprocess.run([
            "kubectl", "config", "view", "--minify",
            "-o", "jsonpath={.clusters[0].cluster.server}"
        ], capture_output=True, text=True, check=True)
        
        cluster_url = cluster_result.stdout
        
        return {
            "token": token,
            "ca_cert": ca_cert,
            "cluster_url": cluster_url,
            "service_account": sa_name,
            "namespace": namespace
        }
    
    def create_persistent_kubeconfig(self, token_info, context_name="persistent-context"):
        """Create a kubeconfig file with persistent token"""
        
        config = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": "persistent-cluster",
                "cluster": {
                    "server": token_info["cluster_url"],
                    "certificate-authority-data": token_info["ca_cert"]
                }
            }],
            "users": [{
                "name": "persistent-user",
                "user": {
                    "token": token_info["token"]
                }
            }],
            "contexts": [{
                "name": context_name,
                "context": {
                    "cluster": "persistent-cluster",
                    "user": "persistent-user"
                }
            }],
            "current-context": context_name
        }
        
        config_path = f"{os.path.expanduser('~')}/.kube/config-persistent"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"✅ Persistent kubeconfig created: {config_path}")
        print(f"🔧 To use: export KUBECONFIG={config_path}")
        return config_path
    
    def get_oidc_token_info(self):
        """Extract OIDC token information from current kubeconfig"""
        try:
            result = subprocess.run([
                "kubectl", "config", "view", "--context=oidc-context", "--raw"
            ], capture_output=True, text=True, check=True)
            
            config = yaml.safe_load(result.stdout)
            
            for user in config.get("users", []):
                if user["name"] == "oidc-user":
                    auth_provider = user.get("user", {}).get("auth-provider", {})
                    if auth_provider:
                        return auth_provider.get("config", {})
            
            # Try exec-based auth (kubelogin)
            for user in config.get("users", []):
                if user["name"] == "oidc-user":
                    exec_config = user.get("user", {}).get("exec", {})
                    if exec_config:
                        return {"exec": exec_config}
            
            return {}
        except Exception as e:
            print(f"⚠️ Could not extract OIDC token info: {e}")
            return {}

def main():
    manager = KubernetesTokenManager()
    
    print("🔑 Kubernetes Persistent Token Manager")
    print("=" * 50)
    
    choice = input("""
Choose token type:
1. Service Account Token (recommended for automation)
2. OIDC Token Information
3. Both

Enter choice (1-3): """).strip()
    
    if choice in ["1", "3"]:
        print("\n📝 Creating Service Account Token...")
        try:
            token_info = manager.create_service_account_token()
            config_path = manager.create_persistent_kubeconfig(token_info)
            
            print("\n✅ Service Account Token Created!")
            print(f"🔐 Token: {token_info['token'][:50]}...")
            print(f"📁 Config: {config_path}")
            print(f"🧪 Test: KUBECONFIG={config_path} kubectl get nodes")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating service account token: {e}")
    
    if choice in ["2", "3"]:
        print("\n📝 OIDC Token Information...")
        oidc_info = manager.get_oidc_token_info()
        
        if oidc_info:
            print("✅ OIDC configuration found:")
            print(json.dumps(oidc_info, indent=2))
            
            if "refresh-token" in oidc_info:
                print(f"\n🔄 Refresh Token: {oidc_info['refresh-token'][:50]}...")
                print("💾 Save this refresh token for automation!")
        else:
            print("⚠️ No OIDC token information found")

if __name__ == "__main__":
    main()