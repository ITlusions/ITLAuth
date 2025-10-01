#!/usr/bin/env python3
"""
Generate OIDC Token for Current User
Creates a fresh token using your current OIDC session
"""
import subprocess
import json
import yaml
import os
import base64
from datetime import datetime

def get_current_oidc_token():
    """Extract or generate a fresh OIDC token for the current user"""
    print("🔑 Getting Current User OIDC Token")
    print("=" * 40)
    
    # Check current authentication
    print("👤 Current user:")
    try:
        whoami_result = subprocess.run(["kubectl", "auth", "whoami"], 
                                     capture_output=True, text=True, check=True)
        print(whoami_result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking current user: {e}")
        return None
    
    # Get kubeconfig info
    try:
        config_result = subprocess.run([
            "kubectl", "config", "view", "--raw", "--minify"
        ], capture_output=True, text=True, check=True)
        
        config = yaml.safe_load(config_result.stdout)
        current_context = config.get("current-context")
        
        # Find current user
        current_user = None
        for context in config.get("contexts", []):
            if context["name"] == current_context:
                user_name = context["context"]["user"]
                for user in config.get("users", []):
                    if user["name"] == user_name:
                        current_user = user
                        break
                break
        
        if not current_user:
            print("❌ Could not find current user configuration")
            return None
        
        print(f"📋 Current user: {current_user['name']}")
        
        # Check user configuration type
        user_config = current_user["user"]
        
        if "exec" in user_config:
            print("✅ Using exec-based authentication (kubelogin)")
            return get_token_with_kubelogin()
        elif "auth-provider" in user_config:
            print("✅ Using auth-provider (legacy)")
            return extract_auth_provider_token(user_config["auth-provider"])
        elif "token" in user_config:
            print("✅ Using direct token")
            return {
                "access_token": user_config["token"],
                "token_type": "Bearer",
                "source": "direct"
            }
        else:
            print("❌ Unknown authentication method")
            return None
            
    except Exception as e:
        print(f"❌ Error reading kubeconfig: {e}")
        return None

def get_token_with_kubelogin():
    """Get fresh token using kubelogin"""
    print("🔄 Getting fresh token with kubelogin...")
    
    try:
        # Run kubelogin get-token
        result = subprocess.run([
            "kubelogin", "get-token",
            "--login", "devicecode",
            "--server-id", "kubernetes-oidc",
            "--client-id", "kubernetes-oidc",
            "--tenant-id", "itlusions"
        ], capture_output=True, text=True, check=True)
        
        token_data = json.loads(result.stdout)
        
        if "status" in token_data and "token" in token_data["status"]:
            return {
                "access_token": token_data["status"]["token"],
                "expiration": token_data["status"].get("expirationTimestamp"),
                "token_type": "Bearer",
                "source": "kubelogin"
            }
        else:
            print("❌ Unexpected token format from kubelogin")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ kubelogin failed: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse kubelogin output: {e}")
        return None

def extract_auth_provider_token(auth_provider):
    """Extract token from auth-provider configuration"""
    config = auth_provider.get("config", {})
    
    token_info = {}
    if "id-token" in config:
        token_info["id_token"] = config["id-token"]
    if "refresh-token" in config:
        token_info["refresh_token"] = config["refresh-token"]
    if "access-token" in config:
        token_info["access_token"] = config["access-token"]
    
    token_info["source"] = "auth-provider"
    return token_info if token_info else None

def save_token_info(token_info):
    """Save token information to files"""
    if not token_info:
        return
    
    print("\n💾 Saving token information...")
    
    # Save raw token
    if "access_token" in token_info:
        token_file = os.path.expanduser("~/.kube/current-token.txt")
        with open(token_file, "w") as f:
            f.write(token_info["access_token"])
        print(f"📁 Access token saved: {token_file}")
    
    # Save full token info as JSON
    info_file = os.path.expanduser("~/.kube/current-token-info.json")
    with open(info_file, "w") as f:
        # Don't save the actual tokens in the info file for security
        safe_info = {k: v for k, v in token_info.items() if "token" not in k.lower()}
        safe_info["token_length"] = len(token_info.get("access_token", ""))
        safe_info["has_refresh_token"] = "refresh_token" in token_info
        json.dump(safe_info, f, indent=2, default=str)
    print(f"📁 Token info saved: {info_file}")

def create_bearer_token_kubeconfig(token_info):
    """Create a kubeconfig using the bearer token"""
    if not token_info or "access_token" not in token_info:
        return None
    
    try:
        # Get cluster info
        cluster_url = subprocess.check_output([
            "kubectl", "config", "view", "--minify",
            "-o", "jsonpath={.clusters[0].cluster.server}"
        ], text=True).strip()
        
        cluster_ca = subprocess.check_output([
            "kubectl", "config", "view", "--raw", "--minify", "--flatten",
            "-o", "jsonpath={.clusters[0].cluster.certificate-authority-data}"
        ], text=True).strip()
        
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
                "name": "current-token-user",
                "user": {
                    "token": token_info["access_token"]
                }
            }],
            "contexts": [{
                "name": "current-token-context",
                "context": {
                    "cluster": "kubernetes-cluster",
                    "user": "current-token-user"
                }
            }],
            "current-context": "current-token-context"
        }
        
        config_path = os.path.expanduser("~/.kube/config-current-token")
        with open(config_path, "w") as f:
            yaml.dump(kubeconfig, f, default_flow_style=False)
        
        print(f"📁 Bearer token kubeconfig created: {config_path}")
        return config_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get cluster info: {e}")
        return None

def test_token(token_info):
    """Test the token by making a simple API call"""
    if not token_info or "access_token" not in token_info:
        return False
    
    try:
        # Get API server URL
        api_server = subprocess.check_output([
            "kubectl", "config", "view", "--minify",
            "-o", "jsonpath={.clusters[0].cluster.server}"
        ], text=True).strip()
        
        import requests
        headers = {
            "Authorization": f"Bearer {token_info['access_token']}",
            "Accept": "application/json"
        }
        
        # Test with /api/v1/namespaces (should be accessible to most users)
        response = requests.get(f"{api_server}/api/v1/namespaces", 
                              headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            print("✅ Token test successful!")
            namespaces = response.json().get("items", [])
            print(f"   Found {len(namespaces)} namespaces")
            return True
        else:
            print(f"❌ Token test failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Token test error: {e}")
        return False

def main():
    print("🔑 Current User OIDC Token Generator")
    print("=" * 50)
    
    # Get current token
    token_info = get_current_oidc_token()
    
    if not token_info:
        print("❌ Failed to get token information")
        return
    
    print(f"\n✅ Token obtained!")
    print(f"   Source: {token_info.get('source', 'unknown')}")
    print(f"   Type: {token_info.get('token_type', 'Bearer')}")
    
    if "expiration" in token_info:
        print(f"   Expires: {token_info['expiration']}")
    
    if "access_token" in token_info:
        print(f"   Token length: {len(token_info['access_token'])} characters")
    
    # Save token information
    save_token_info(token_info)
    
    # Create kubeconfig
    config_path = create_bearer_token_kubeconfig(token_info)
    
    # Test token
    print("\n🧪 Testing token...")
    test_token(token_info)
    
    print("\n🎉 Token extraction complete!")
    print("\n📋 Usage examples:")
    print(f"   # Use with curl:")
    print(f"   curl -H 'Authorization: Bearer <token>' <k8s-api-url>/api/v1/nodes")
    print(f"   # Use with kubeconfig:")
    if config_path:
        print(f"   export KUBECONFIG={config_path}")
        print(f"   kubectl get nodes")

if __name__ == "__main__":
    main()