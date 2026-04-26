#!/usr/bin/env python3
"""Display built-in kubectl contexts"""
import yaml
import sys
sys.path.insert(0, '.')

from src.itlc.kubectl_oidc_setup import KubectlOIDCSetup

setup = KubectlOIDCSetup()
config = yaml.safe_load(setup.DEFAULT_CLUSTER_CONFIG)

print()
print('='*90)
print('BUILT-IN KUBECTL CONTEXTS (defined in DEFAULT_CLUSTER_CONFIG)')
print('='*90)
print()

print('CLUSTERS:')
print('-' * 90)
for cluster in config['clusters']:
    name = cluster['name']
    server = cluster['cluster']['server']
    insecure = cluster['cluster'].get('insecure-skip-tls-verify', False)
    print(f"  {name:<25} {server:<40} [insecure={insecure}]")

print()
print('CONTEXTS (kubectl context name -> cluster + user):')
print('-' * 90)
for context in config['contexts']:
    name = context['name']
    ctx = context['context']
    cluster = ctx['cluster']
    user = ctx['user']
    print(f"  {name:<25} -> {cluster:<25} + {user}")

print()
print('USERS (Authentication Methods):')
print('-' * 90)
for user in config['users']:
    name = user['name']
    exec_cfg = user['user']['exec']
    cmd = exec_cfg['command']
    
    if cmd == 'kubectl-oidc_login':
        method = "Binary (kubelogin plugin)"
    else:
        method = "Python (built-in)"
    
    print(f"  {name:<25} {method:<30} command={cmd}")

print()
print('='*90)
print('CONTEXT MAPPING')
print('='*90)
print()
print("  itl                     = kubernetes cluster + oidc-user (kubelogin binary)")
print("  itl-python              = kubernetes cluster + oidc-user-python (Python auth)")
print("  itl-ssh-tunnel          = kubernetes-ssh-tunnel + oidc-user (kubelogin)")
print("  itl-ssh-tunnel-python   = kubernetes-ssh-tunnel + oidc-user-python (Python)")
print()
print("Created by: itlc oidc-setup full")
print("Location: ~/.kube/config")
print()
