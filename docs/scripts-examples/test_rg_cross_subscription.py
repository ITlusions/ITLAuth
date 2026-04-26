#!/usr/bin/env python3
"""Test that resource groups can have same name in different subscriptions"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from itlc.controlplane_client import ControlPlaneClient

client = ControlPlaneClient(base_url='http://localhost:8000')

# Create two subscriptions
print('[*] Creating first subscription...')
sub1 = client.create_subscription(
    resource_name='subscription-one',
    resource_group='default',
    location='eastus',
    display_name='Subscription One'
)
sub1_id = sub1.get('id').replace('/subscriptions/', '')
print(f'[+] Subscription 1: {sub1_id}')

print('[*] Creating second subscription...')
sub2 = client.create_subscription(
    resource_name='subscription-two',
    resource_group='default',
    location='westus',
    display_name='Subscription Two'
)
sub2_id = sub2.get('id').replace('/subscriptions/', '')
print(f'[+] Subscription 2: {sub2_id}')

# Create RG with same name in both subscriptions (should work)
print('\n[*] Creating RG "shared-name" in subscription 1...')
rg1 = client.create_resource_group(
    subscription_id=sub1_id,
    resource_name='shared-name',
    location='eastus'
)
print(f'[+] RG1 created: {rg1.get("id")}')

print('[*] Creating RG "shared-name" in subscription 2...')
rg2 = client.create_resource_group(
    subscription_id=sub2_id,
    resource_name='shared-name',
    location='westus'
)
print(f'[+] RG2 created: {rg2.get("id")}')

# Verify they're different resources
if rg1.get('id') == rg2.get('id'):
    print('[ERROR] Both RGs have the same ID! Cross-subscription isolation failed.')
    sys.exit(1)

# List RGs in each subscription
print('\n[*] Listing RGs in subscription 1...')
rgs1 = client.list_resource_groups(subscription_id=sub1_id)
rg1_count = rgs1.get("count", 0)
print(f'[+] Found {rg1_count} RG(s) in subscription 1')

print('[*] Listing RGs in subscription 2...')
rgs2 = client.list_resource_groups(subscription_id=sub2_id)
rg2_count = rgs2.get("count", 0)
print(f'[+] Found {rg2_count} RG(s) in subscription 2')

# Verify each subscription sees only its own RGs
if rg1_count != 1 or rg2_count != 1:
    print(f'[ERROR] Expected 1 RG per subscription, got {rg1_count} and {rg2_count}')
    sys.exit(1)

# Attempt to create "shared-name" again in subscription 1 (should fail)
print('\n[*] Attempting duplicate in subscription 1...')
rg_dup = client.create_resource_group(
    subscription_id=sub1_id,
    resource_name='shared-name',
    location='northeurope'
)
if rg_dup and not isinstance(rg_dup, type(None)):
    print('[ERROR] Duplicate was allowed in subscription 1!')
    sys.exit(1)
print('[+] Duplicate correctly blocked')

# Attempt to create "shared-name" again in subscription 2 (should fail)
print('[*] Attempting duplicate in subscription 2...')
rg_dup2 = client.create_resource_group(
    subscription_id=sub2_id,
    resource_name='shared-name',
    location='northeurope'
)
if rg_dup2 and not isinstance(rg_dup2, type(None)):
    print('[ERROR] Duplicate was allowed in subscription 2!')
    sys.exit(1)
print('[+] Duplicate correctly blocked')

# Get each RG by name from its subscription
print('\n[*] Getting shared-name from subscription 1...')
rg1_get = client.get_resource_group(subscription_id=sub1_id, resource_name='shared-name')
print(f'[+] Retrieved from sub1: {rg1_get.get("id")}')

print('[*] Getting shared-name from subscription 2...')
rg2_get = client.get_resource_group(subscription_id=sub2_id, resource_name='shared-name')
print(f'[+] Retrieved from sub2: {rg2_get.get("id")}')

# Verify the IDs match what we created
if rg1_get.get('id') != rg1.get('id'):
    print('[ERROR] RG1 IDs do not match!')
    sys.exit(1)

if rg2_get.get('id') != rg2.get('id'):
    print('[ERROR] RG2 IDs do not match!')
    sys.exit(1)

print('\n[SUCCESS] Cross-subscription resource group naming is fully isolated!')
