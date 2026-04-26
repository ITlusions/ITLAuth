# Kubernetes API Server OIDC Configuration Guide

## Overview
This guide will help you configure the Kubernetes API server to accept OIDC tokens from ITlusions Keycloak.

## Prerequisites
- Access to the control plane node (10.99.100.4)
- Root or sudo access on the control plane node
- Current kubectl admin access working

## Step-by-Step Instructions

### Step 1: Access the Control Plane Node
```bash
# SSH to the control plane node
ssh root@10.99.100.4
# or if using a different user:
ssh your-user@10.99.100.4
```

### Step 2: Backup the Current Configuration
```bash
cd /etc/kubernetes/manifests
cp kube-apiserver.yaml kube-apiserver.yaml.backup.$(date +%Y%m%d-%H%M%S)
ls -la kube-apiserver.yaml*
```

### Step 3: Edit the API Server Manifest
```bash
nano /etc/kubernetes/manifests/kube-apiserver.yaml
```

### Step 4: Add OIDC Configuration
Find the section with the `command:` and locate the line:
```yaml
    - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
```

Add these lines immediately after it:
```yaml
    - --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions
    - --oidc-client-id=kubernetes-oidc
    - --oidc-username-claim=preferred_username
    - --oidc-groups-claim=groups
    - --oidc-username-prefix=-
    - --oidc-groups-prefix=-
```

### Step 5: Save and Wait for Restart
- Save the file (Ctrl+X, Y, Enter in nano)
- The API server pod will automatically restart (takes 1-2 minutes)
- Monitor the restart: `watch 'kubectl get pods -n kube-system -l component=kube-apiserver'`

### Step 6: Verify the Configuration
After the API server restarts, check that OIDC parameters are loaded:
```bash
kubectl get pod -n kube-system -l component=kube-apiserver -o yaml | grep oidc
```

## What Each Parameter Does

- `--oidc-issuer-url`: The URL of the OIDC issuer (ITlusions Keycloak realm)
- `--oidc-client-id`: The client ID configured in Keycloak for Kubernetes
- `--oidc-username-claim`: Which claim to use as the username (preferred_username = email)
- `--oidc-groups-claim`: Which claim contains group memberships
- `--oidc-username-prefix=-`: Remove any prefix from usernames (use - for no prefix)
- `--oidc-groups-prefix=-`: Remove any prefix from group names (use - for no prefix)

## Troubleshooting

### API Server Won't Start
If the API server fails to start after the changes:
1. Check the logs: `journalctl -u kubelet -f`
2. Restore the backup: `cp kube-apiserver.yaml.backup.* kube-apiserver.yaml`
3. Verify YAML syntax and indentation

### OIDC Still Not Working
1. Verify Keycloak is accessible from the control plane node:
   ```bash
   curl -k https://sts.itlusions.com/realms/itlusions/.well-known/openid_configuration
   ```
2. Check that the kubernetes-oidc client exists in Keycloak
3. Verify RBAC bindings are in place

## Expected Result
After successful configuration:
- API server will accept OIDC tokens
- Users with proper RBAC can authenticate using `kubectl` with OIDC
- Group memberships from Keycloak will be mapped to Kubernetes RBAC

## Testing Authentication
Once configured, test with:
```bash
kubectl config use-context oidc-context
kubectl get nodes
```

The first command should open a browser for Keycloak authentication.