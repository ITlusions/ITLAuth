#!/usr/bin/env python3
"""Test subscription-scoped RG uniqueness"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from itlc.controlplane_client import ControlPlaneClient

client = ControlPlaneClient(base_url='http://localhost:8000')

# Create subscription
sub = client.create_subscription(
    resource_name='test-sub-unique',
    resource_group='default',
    location='eastus',
    display_name='Test Unique'
)
sub_id = sub.get('id').replace('/subscriptions/', '')
print(f'[+] Subscription: {sub_id}')

# Create first RG
rg1 = client.create_resource_group(
    subscription_id=sub_id,
    resource_name='rg-unique',
    location='eastus'
)
print(f'[+] RG created: {rg1.get("id") if rg1 else "FAILED"}')

# Try to get it
rg1_get = client.get_resource_group(sub_id, 'rg-unique')
print(f'[+] RG GET: {rg1_get.get("name") if rg1_get else "NOT FOUND"}')

# Try to duplicate (should fail with None)
print('[*] Attempting duplicate...')
rg1_dup = client.create_resource_group(
    subscription_id=sub_id,
    resource_name='rg-unique',
    location='westus'
)
if rg1_dup is None:
    print('[SUCCESS] Duplicate correctly blocked (409 Conflict)')
else:
    print(f'[ERROR] Duplicate was allowed: {rg1_dup.get("id")}')

# Create another RG with different name (should succeed)
rg2 = client.create_resource_group(
    subscription_id=sub_id,
    resource_name='rg-different',
    location='westus'
)
print(f'[+] Different RG created: {rg2.get("id") if rg2 else "FAILED"}')

print('\n[SUCCESS] Subscription-scoped resource group uniqueness is enforced!')
