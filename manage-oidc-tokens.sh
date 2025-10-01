#!/bin/bash
# Script to extract and manage OIDC refresh tokens
# This creates a persistent OIDC session

echo "🔄 Managing OIDC refresh tokens for persistence..."

# Check current OIDC token info
echo "📋 Current OIDC authentication:"
kubectl auth whoami

# Extract current token information from kubeconfig
KUBECONFIG_FILE="$HOME/.kube/config"
OIDC_CONTEXT="oidc-context"

echo ""
echo "🔍 Current OIDC configuration:"
kubectl config view --context=$OIDC_CONTEXT --minify

# Get the refresh token from kubeconfig (if available)
REFRESH_TOKEN=$(kubectl config view --context=$OIDC_CONTEXT --raw -o jsonpath='{.users[?(@.name=="oidc-user")].user.auth-provider.config.refresh-token}' 2>/dev/null || echo "Not found in kubeconfig")

if [ "$REFRESH_TOKEN" != "Not found in kubeconfig" ] && [ -n "$REFRESH_TOKEN" ]; then
    echo ""
    echo "✅ Refresh token found in kubeconfig"
    echo "🔐 Refresh token: $REFRESH_TOKEN"
    echo ""
    echo "📝 This refresh token can be used to get new access tokens"
    echo "💡 Save this refresh token securely for automation"
else
    echo ""
    echo "⚠️ No refresh token found in kubeconfig"
    echo "🔄 You may need to re-authenticate to get a refresh token"
    echo ""
    echo "💡 To get a refresh token, run:"
    echo "kubelogin get-token --login devicecode --server-id kubernetes-oidc --client-id kubernetes-oidc --tenant-id itlusions"
fi

# Show token info if available
echo ""
echo "🔍 Current token information:"
kubectl config view --context=$OIDC_CONTEXT --raw -o jsonpath='{.users[?(@.name=="oidc-user")].user}' | jq . 2>/dev/null || echo "No detailed token info available"