#!/usr/bin/env python3
"""
Test CLI integration with Control Plane API
This script tests the CLI commands without requiring full Keycloak authentication
"""

import json
import sys
import os

# Add the ITLAuth module to path
sys.path.insert(0, 'd:\\repos\\ITLAuth\\src')

from itlc.controlplane_client import ControlPlaneClient

def test_subscription_workflow():
    """Test creating, listing, and deleting subscriptions"""
    print("\n" + "="*60)
    print("ITL Control Plane CLI - Integration Test")
    print("="*60 + "\n")
    
    # Create client (no auth token needed for direct communication with local API)
    api_url = "http://localhost:8000"
    client = ControlPlaneClient(base_url=api_url, use_gateway=False)
    
    # Check health
    print("[1] Checking API health...")
    if client.health():
        print("✓ API is healthy\n")
    else:
        print("✗ API is not responding")
        return False
    
    # List locations
    print("[2] Listing available locations...")
    locations = client.list_locations()
    if locations and 'locations' in locations:
        loc_list = locations['locations']
        print(f"✓ Found {len(loc_list)} locations")
        for loc in loc_list[:3]:
            print(f"  - {loc.get('name', 'N/A')} ({loc.get('shortname', 'N/A')})")
        if len(loc_list) > 3:
            print(f"  ... and {len(loc_list) - 3} more")
        print()
    else:
        print("✗ Failed to list locations\n")
        return False
    
    # Create subscription
    print("[3] Creating subscription...")
    sub_name = "cli-test-sub-01"
    result = client.create_subscription(
        resource_name=sub_name,
        resource_group="cli-test-rg",
        location="westeurope",
        display_name="CLI Test Subscription",
        state="Enabled"
    )
    
    if result:
        print(f"✓ Subscription created successfully")
        print(f"  Name: {result.get('name', 'N/A')}")
        print(f"  ID: {result.get('id', 'N/A')}")
        print(f"  GUID: {result.get('resource_guid', 'N/A')}")
        print()
    else:
        print(f"✗ Failed to create subscription\n")
        return False
    
    # List subscriptions
    print("[4] Listing subscriptions...")
    subs = client.list_subscriptions()
    if subs and 'resources' in subs:
        sub_list = subs['resources']
        print(f"✓ Found {len(sub_list)} subscription(s)")
        for sub in sub_list[:3]:
            print(f"  - {sub.get('name', 'N/A')} ({sub.get('id', 'N/A')})")
        if len(sub_list) > 3:
            print(f"  ... and {len(sub_list) - 3} more")
        print()
    else:
        print("✗ Failed to list subscriptions\n")
        return False
    
    # Get specific subscription
    print(f"[5] Getting subscription '{sub_name}'...")
    sub = client.get_subscription(sub_name)
    if sub:
        print(f"✓ Subscription retrieved")
        print(f"  Properties: {json.dumps(sub.get('properties', {}), indent=4)}")
        print()
    else:
        print(f"✗ Failed to get subscription\n")
        return False
    
    # Create resource group
    print("[6] Creating resource group...")
    rg_name = "cli-test-rg-01"
    rg_result = client.create_resource_group(
        subscription_id=sub_name,
        resource_name=rg_name,
        location="westeurope",
        display_name="CLI Test Resource Group"
    )
    
    if rg_result:
        print(f"✓ Resource group created successfully")
        print(f"  Name: {rg_result.get('name', 'N/A')}")
        print(f"  ID: {rg_result.get('id', 'N/A')}")
        print()
    else:
        print(f"✗ Failed to create resource group\n")
        return False
    
    # List resource groups
    print("[7] Listing resource groups...")
    rgs = client.list_resource_groups(subscription_id=sub_name)
    if rgs and 'resources' in rgs:
        rg_list = rgs['resources']
        print(f"✓ Found {len(rg_list)} resource group(s)")
        for rg in rg_list:
            print(f"  - {rg.get('name', 'N/A')} ({rg.get('id', 'N/A')})")
        print()
    else:
        print("✗ Failed to list resource groups\n")
        return False
    
    # Cleanup - Delete resource group
    print("[8] Cleaning up - deleting resource group...")
    if client.delete_resource_group(rg_name, subscription_id=sub_name):
        print(f"✓ Resource group deleted\n")
    else:
        print(f"✗ Failed to delete resource group\n")
    
    # Cleanup - Delete subscription
    print("[9] Cleaning up - deleting subscription...")
    if client.delete_subscription(sub_name):
        print(f"✓ Subscription deleted\n")
    else:
        print(f"✗ Failed to delete subscription\n")
    
    print("="*60)
    print("✓ All tests passed!")
    print("="*60 + "\n")
    return True

if __name__ == '__main__':
    success = test_subscription_workflow()
    sys.exit(0 if success else 1)
