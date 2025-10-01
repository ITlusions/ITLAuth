#!/bin/bash
# Script to create Keycloak service account clients for centralized management
# This creates OIDC service accounts instead of Kubernetes service accounts

KEYCLOAK_URL="https://sts.itlusions.com"
REALM="itlusions"
ADMIN_CLI_CLIENT="admin-cli"

echo "🔧 Creating Keycloak Service Account for Kubernetes Access"
echo "========================================================"

# Check if we have admin access or credentials
echo "📋 You'll need Keycloak admin credentials or a management token"
echo ""

read -p "Enter Keycloak admin username: " ADMIN_USER
read -s -p "Enter Keycloak admin password: " ADMIN_PASSWORD
echo ""

# Get admin token
echo "🔑 Getting admin access token..."
ADMIN_TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=$ADMIN_CLI_CLIENT" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token. Check credentials."
    exit 1
fi

echo "✅ Admin token obtained"

# Create service account client
SERVICE_ACCOUNT_ID="kubernetes-automation-sa"
echo "🔧 Creating service account client: $SERVICE_ACCOUNT_ID"

CLIENT_JSON=$(cat <<EOF
{
  "clientId": "$SERVICE_ACCOUNT_ID",
  "name": "Kubernetes Automation Service Account",
  "description": "Service account for Kubernetes cluster automation",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "serviceAccountsEnabled": true,
  "standardFlowEnabled": false,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "publicClient": false,
  "protocol": "openid-connect",
  "attributes": {
    "access.token.lifespan": "3600",
    "client.session.idle.timeout": "1800",
    "client.session.max.lifespan": "36000"
  }
}
EOF
)

# Create the client
RESPONSE=$(curl -s -X POST \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$CLIENT_JSON")

# Get the created client's internal ID
CLIENT_UUID=$(curl -s -X GET \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients?clientId=$SERVICE_ACCOUNT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')

if [ "$CLIENT_UUID" = "null" ] || [ -z "$CLIENT_UUID" ]; then
    echo "❌ Failed to create or find client"
    exit 1
fi

echo "✅ Service account client created with ID: $CLIENT_UUID"

# Get client secret
CLIENT_SECRET=$(curl -s -X GET \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID/client-secret" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.value')

echo "✅ Client secret generated"

# Add client to cluster admin group
echo "🔧 Adding service account to itl-cluster-admin group..."

# Get service account user ID
SA_USER_ID=$(curl -s -X GET \
  "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID/service-account-user" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

# Get cluster admin group ID
GROUP_ID=$(curl -s -X GET \
  "$KEYCLOAK_URL/admin/realms/$REALM/groups?search=itl-cluster-admin" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')

if [ "$GROUP_ID" != "null" ] && [ -n "$GROUP_ID" ]; then
    # Add user to group
    curl -s -X PUT \
      "$KEYCLOAK_URL/admin/realms/$REALM/users/$SA_USER_ID/groups/$GROUP_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN"
    echo "✅ Service account added to itl-cluster-admin group"
else
    echo "⚠️ itl-cluster-admin group not found. You may need to add permissions manually."
fi

echo ""
echo "🎉 Keycloak Service Account Created Successfully!"
echo "=============================================="
echo "Client ID: $SERVICE_ACCOUNT_ID"
echo "Client Secret: $CLIENT_SECRET"
echo "Realm: $REALM"
echo "Issuer URL: $KEYCLOAK_URL/realms/$REALM"
echo ""
echo "📝 Save these credentials securely!"
echo ""
echo "🔧 To use this service account for kubectl:"
echo "1. Create a kubeconfig with these credentials"
echo "2. Use client_credentials grant type"
echo "3. Set up automated token refresh"
echo ""
echo "🚀 Next: Run create-sa-kubeconfig.sh to create the kubeconfig"