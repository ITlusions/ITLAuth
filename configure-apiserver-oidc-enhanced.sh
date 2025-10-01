#!/bin/bash
# Enhanced script to add OIDC configuration to kube-apiserver
# Run this script on the control plane node (10.99.100.4)

set -e

echo "🔧 Adding enhanced OIDC configuration to kube-apiserver..."

# Backup the original file
cp /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml.backup.$(date +%Y%m%d-%H%M%S)

# Check if OIDC is already configured
if grep -q "oidc-issuer-url" /etc/kubernetes/manifests/kube-apiserver.yaml; then
    echo "⚠️ OIDC configuration already exists in kube-apiserver.yaml"
    echo "📋 Current OIDC configuration:"
    grep "oidc-" /etc/kubernetes/manifests/kube-apiserver.yaml
    exit 1
fi

# Add enhanced OIDC parameters after the --tls-private-key-file line
sed -i '/--tls-private-key-file=\/etc\/kubernetes\/pki\/apiserver.key/a\    # OIDC Authentication Configuration\n    - --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions\n    - --oidc-client-id=kubernetes-oidc\n    - --oidc-username-claim=preferred_username\n    - --oidc-groups-claim=groups\n    - --oidc-username-prefix=oidc:\n    - --oidc-groups-prefix=oidc:\n    - --oidc-signing-algs=RS256\n    - --oidc-required-claim=aud=kubernetes-oidc' /etc/kubernetes/manifests/kube-apiserver.yaml

echo "✅ Enhanced OIDC configuration added to kube-apiserver.yaml"
echo "🔄 The API server pod will restart automatically (this may take 1-2 minutes)"
echo "📋 You can monitor the restart with: watch 'kubectl get pods -n kube-system -l component=kube-apiserver'"

# Show the changes
echo ""
echo "📄 Added enhanced OIDC configuration:"
echo "    - --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions"
echo "    - --oidc-client-id=kubernetes-oidc"
echo "    - --oidc-username-claim=preferred_username"
echo "    - --oidc-groups-claim=groups"
echo "    - --oidc-username-prefix=oidc:"
echo "    - --oidc-groups-prefix=oidc:"
echo "    - --oidc-signing-algs=RS256"
echo "    - --oidc-required-claim=aud=kubernetes-oidc"
echo ""
echo "🔒 Security enhancements:"
echo "   • Explicit signing algorithm (RS256)"
echo "   • Required audience claim validation"
echo "   • Prefixed usernames/groups for security"