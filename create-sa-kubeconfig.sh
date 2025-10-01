#!/bin/bash
# Script to create kubeconfig for Keycloak service account
# Uses client credentials flow for authentication

echo "🔧 Creating kubeconfig for Keycloak Service Account"
echo "================================================="

# Configuration
KEYCLOAK_URL="https://sts.itlusions.com"
REALM="itlusions"
CLIENT_ID="kubernetes-automation-sa"

# Prompt for client secret
read -s -p "Enter the client secret for $CLIENT_ID: " CLIENT_SECRET
echo ""

# Get Kubernetes cluster info
CLUSTER_URL=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
CLUSTER_CA=$(kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')

echo "📋 Cluster URL: $CLUSTER_URL"

# Test token generation
echo "🧪 Testing service account authentication..."
TOKEN_RESPONSE=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token. Check client credentials."
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Successfully obtained access token"

# Create kubeconfig for service account
KUBECONFIG_PATH="$HOME/.kube/config-sa-keycloak"

cat > "$KUBECONFIG_PATH" <<EOF
apiVersion: v1
kind: Config
clusters:
- name: kubernetes-cluster
  cluster:
    server: $CLUSTER_URL
    certificate-authority-data: $CLUSTER_CA
users:
- name: keycloak-service-account
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: kubelogin
      args:
      - get-token
      - --oidc-issuer-url=$KEYCLOAK_URL/realms/$REALM
      - --oidc-client-id=$CLIENT_ID
      - --oidc-client-secret=$CLIENT_SECRET
      - --grant-type=client_credentials
      env: null
      provideClusterInfo: false
contexts:
- name: keycloak-sa-context
  context:
    cluster: kubernetes-cluster
    user: keycloak-service-account
current-context: keycloak-sa-context
EOF

echo "✅ Kubeconfig created: $KUBECONFIG_PATH"

# Test the configuration
echo "🧪 Testing kubeconfig..."
export KUBECONFIG="$KUBECONFIG_PATH"

if kubectl auth whoami 2>/dev/null; then
    echo "✅ Service account authentication successful!"
    kubectl get nodes 2>/dev/null && echo "✅ Cluster access confirmed!" || echo "⚠️ Limited cluster access"
else
    echo "❌ Authentication failed. Check the configuration."
fi

echo ""
echo "🎉 Keycloak Service Account Kubeconfig Ready!"
echo "============================================="
echo "Kubeconfig: $KUBECONFIG_PATH"
echo ""
echo "🔧 To use:"
echo "export KUBECONFIG=$KUBECONFIG_PATH"
echo "kubectl get nodes"
echo ""
echo "🔄 To switch back to regular OIDC:"
echo "export KUBECONFIG=$HOME/.kube/config"
echo "kubectl config use-context oidc-context"