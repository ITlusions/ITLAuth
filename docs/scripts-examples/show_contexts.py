#!/usr/bin/env python3
"""Show OIDC contexts and registered clusters"""
from src.itlc.clusters import OIDC_CONTEXTS, ClustersManager

print('\n' + '='*80)
print('OIDC AUTHENTICATION CONTEXTS (4 fixed authentication patterns)')
print('='*80 + '\n')

for ctx in OIDC_CONTEXTS:
    print(f"{ctx['name']:<25} | {ctx['auth_method']:<30} | {ctx['best_for']}")

print('\n' + '='*80)
print('REGISTERED CLUSTERS')
print('='*80 + '\n')

mgr = ClustersManager()
clusters = mgr.list_clusters()

if clusters:
    for c in clusters:
        print(f"{c['name']:<25} | {c['server']:<40} | [{c.get('environment', 'unknown')}]")
else:
    print('(No clusters registered yet)')

print('\n' + '='*80)
print('NAMING RULES')
print('='*80)
print(f'Reserved OIDC context names: {sorted(mgr.reserved_contexts)}')
print('Cluster names: Use your own identifiers (avoid reserved names above)')
print()
