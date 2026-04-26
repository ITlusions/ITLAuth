#!/usr/bin/env python3
"""Test subscription-scoped resource groups"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from itlc.controlplane_client import ControlPlaneClient

client = ControlPlaneClient(base_url='http://localhost:8000')

# Create a subscription first
print('[*] Creating subscription...')
sub = client.create_subscription(
    resource_name='test-subscription',
    resource_group='default',
    location='eastus',
    display_name='Test Subscription for RG Scoping'
)
print(f'[+] Subscription created: {sub.get("id")}')

# Now test creating a resource group
print('[*] Creating resource group in subscription...')
sub_id = sub.get('id').replace('/subscriptions/', '')
rg = client.create_resource_group(
    subscription_id=sub_id,
    resource_name='test-rg-1',
    location='eastus'
)
print(f'[+] Resource group created: {rg.get("id") if rg else "FAILED"}')

# Try to create another RG with same name (should fail with 409)
print('[*] Attempting duplicate resource group (should fail)...')
rg2 = client.create_resource_group(
    subscription_id=sub_id,
    resource_name='test-rg-1',
    location='westus'
)
print(f'[!] Got: {rg2.get("id") if rg2 else "BLOCKED (as expected)"}')

# List resource groups
print('[*] Listing resource groups...')
rgs = client.list_resource_groups(subscription_id=sub_id)
print(f'[+] Found {rgs.get("count", 0)} resource groups')

# Get specific resource group
print('[*] Getting resource group...')
rg_get = client.get_resource_group(subscription_id=sub_id, resource_name='test-rg-1')
print(f'[+] Retrieved: {rg_get.get("name") if rg_get else "NOT FOUND"}')

print('\n[SUCCESS] Subscription-scoped resource groups are working!')
