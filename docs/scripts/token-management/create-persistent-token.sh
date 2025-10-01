#!/bin/bash
# Script to create a persistent service account token for automation
# Run this with your current OIDC context

echo "🔑 Creating persistent service account token..."

# Create a service account
kubectl create serviceaccount itl-automation-sa -n default

# Create a ClusterRoleBinding for the service account
kubectl create clusterrolebinding itl-automation-binding \
  --clusterrole=cluster-admin \
  --serviceaccount=default:itl-automation-sa

# Create a secret for the service account token (Kubernetes 1.24+)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: itl-automation-token
  namespace: default
  annotations:
    kubernetes.io/service-account.name: itl-automation-sa
type: kubernetes.io/service-account-token
EOF

# Wait for token generation
echo "⏰ Waiting for token generation..."
sleep 5

# Extract the token
TOKEN=$(kubectl get secret itl-automation-token -o jsonpath='{.data.token}' | base64 -d)
CA_CERT=$(kubectl get secret itl-automation-token -o jsonpath='{.data.ca\.crt}')

# Get cluster info
CLUSTER_URL=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')

echo "✅ Service account token created!"
echo ""
echo "📋 Token details:"
echo "Service Account: itl-automation-sa"
echo "Namespace: default"
echo "Permissions: cluster-admin"
echo ""
echo "🔐 Token (save this securely):"
echo "$TOKEN"
echo ""
echo "📝 To use this token, create a kubeconfig:"
echo "kubectl config set-cluster persistent-cluster --server=$CLUSTER_URL --certificate-authority-data=$CA_CERT"
echo "kubectl config set-credentials persistent-user --token=$TOKEN"
echo "kubectl config set-context persistent-context --cluster=persistent-cluster --user=persistent-user"
echo "kubectl config use-context persistent-context"