#!/bin/bash
# Script to check API server manifest and validate OIDC configuration
# Run this on the control plane node (10.99.100.4)

echo "🔍 Checking API server manifest for OIDC configuration..."

if [ ! -f "/etc/kubernetes/manifests/kube-apiserver.yaml" ]; then
    echo "❌ API server manifest not found!"
    exit 1
fi

echo "📄 Current OIDC configuration in manifest:"
grep -A 10 -B 2 "oidc-" /etc/kubernetes/manifests/kube-apiserver.yaml || echo "❌ No OIDC configuration found in manifest"

echo ""
echo "🔍 Checking for syntax errors..."
kubectl apply --dry-run=client -f /etc/kubernetes/manifests/kube-apiserver.yaml

echo ""
echo "📋 Checking kubelet logs for API server errors..."
journalctl -u kubelet --since "10 minutes ago" | grep -i "apiserver\|error\|failed" | tail -10

echo ""
echo "🔍 Current running API server configuration:"
kubectl get pod -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.containers[0].command}' | grep -E "(oidc|tls-private-key-file)"