#!/usr/bin/env python3
"""
Example: Core Resources Management via ITLC CLI

Demonstrates creating tenants, subscriptions, resource groups, and querying locations
using the ITL Control Plane API Gateway.
"""
import subprocess
import json
import os
import sys
from typing import Optional


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_step(msg: str):
    print(f"{Colors.CYAN}==>{Colors.END} {Colors.BOLD}{msg}{Colors.END}")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.END} {msg}", file=sys.stderr)


def run_command(cmd: list, capture_output: bool = True) -> Optional[str]:
    """Run CLI command and return output"""
    try:
        print(f"  $ {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr)
        return None


def main():
    """Main workflow: Setup and manage Core resources"""
    
    print(f"\n{Colors.BOLD}ITL Core Resources Management Demo{Colors.END}\n")
    
    # Step 1: Verify environment
    print_step("Step 1: Verify environment")
    api_url = os.getenv('CONTROLPLANE_API_URL')
    token = os.getenv('CONTROLPLANE_TOKEN')
    
    if not api_url:
        print_error("CONTROLPLANE_API_URL not set")
        print("  Set it: export CONTROLPLANE_API_URL='http://localhost:8080'")
        sys.exit(1)
    
    print_success(f"API Gateway URL: {api_url}")
    
    if not token:
        print("  No CONTROLPLANE_TOKEN set, attempting to get token...")
        # Try to get token (requires service account credentials)
        client_id = os.getenv('KEYCLOAK_CLIENT_ID')
        client_secret = os.getenv('KEYCLOAK_CLIENT_SECRET')
        
        if client_id and client_secret:
            token = run_command([
                'itlc', 'get-token',
                '--client-id', client_id,
                '--client-secret', client_secret,
                '--output', 'token'
            ])
            if token:
                os.environ['CONTROLPLANE_TOKEN'] = token
                print_success("Token obtained successfully")
            else:
                print_error("Failed to get token")
                sys.exit(1)
        else:
            print_error("No authentication available")
            print("  Either set CONTROLPLANE_TOKEN or provide KEYCLOAK credentials")
            sys.exit(1)
    else:
        print_success("Token found in environment")
    
    # Step 2: List available locations
    print_step("Step 2: List available locations")
    locations_json = run_command(['itlc', 'location', 'list', '--output', 'json'])
    if locations_json:
        locations = json.loads(locations_json)
        location_list = locations.get('value', [])
        print_success(f"Found {len(location_list)} locations")
        for loc in location_list[:3]:  # Show first 3
            print(f"  • {loc.get('name')} - {loc.get('properties', {}).get('displayName', 'N/A')}")
    else:
        print_error("Failed to list locations")
    
    # Step 3: Create a tenant
    print_step("Step 3: Create tenant")
    tenant_name = "demo-tenant-001"
    tenant_json = run_command([
        'itlc', 'tenant', 'create', tenant_name,
        '--display-name', 'Demo Tenant',
        '--domain', 'demo.example.com',
        '--location', 'westeurope',
        '--tag', 'environment=demo',
        '--tag', 'purpose=testing',
        '--output', 'json'
    ])
    
    if tenant_json:
        tenant = json.loads(tenant_json)
        tenant_id = tenant.get('id')
        print_success(f"Tenant created: {tenant_id}")
    else:
        print_error("Failed to create tenant")
        sys.exit(1)
    
    # Step 4: Create a subscription
    print_step("Step 4: Create subscription")
    subscription_name = "demo-subscription-001"
    subscription_json = run_command([
        'itlc', 'subscription', 'create', subscription_name,
        '--display-name', 'Demo Subscription',
        '--tenant-id', tenant_id,
        '--state', 'Enabled',
        '--location', 'westeurope',
        '--tag', 'tier=standard',
        '--output', 'json'
    ])
    
    if subscription_json:
        subscription = json.loads(subscription_json)
        subscription_id = subscription.get('name')  # Use name as ID
        print_success(f"Subscription created: {subscription.get('id')}")
    else:
        print_error("Failed to create subscription")
        sys.exit(1)
    
    # Step 5: Create resource groups
    print_step("Step 5: Create resource groups")
    resource_groups = [
        ('app-rg', 'Application Resources'),
        ('data-rg', 'Data Resources'),
        ('network-rg', 'Network Resources')
    ]
    
    created_rgs = []
    for rg_name, description in resource_groups:
        rg_json = run_command([
            'itlc', 'resourcegroup', 'create', rg_name, subscription_id,
            '--location', 'westeurope',
            '--tag', f'description={description}',
            '--tag', 'managed-by=itlc',
            '--output', 'json'
        ])
        
        if rg_json:
            rg = json.loads(rg_json)
            created_rgs.append(rg)
            print_success(f"Resource group created: {rg_name}")
        else:
            print_error(f"Failed to create resource group: {rg_name}")
    
    # Step 6: List created resources
    print_step("Step 6: List created resources")
    
    print("\n  Tenants:")
    run_command(['itlc', 'tenant', 'list', '--output', 'table'], capture_output=False)
    
    print("\n  Subscriptions:")
    run_command(['itlc', 'subscription', 'list', '--output', 'table'], capture_output=False)
    
    print(f"\n  Resource Groups in {subscription_id}:")
    run_command([
        'itlc', 'resourcegroup', 'list',
        '--subscription-id', subscription_id,
        '--output', 'table'
    ], capture_output=False)
    
    # Step 7: Get details
    print_step("Step 7: Get resource details")
    
    print("\n  Tenant details:")
    run_command(['itlc', 'tenant', 'get', tenant_name], capture_output=False)
    
    print("\n  Subscription details:")
    run_command(['itlc', 'subscription', 'get', subscription_id], capture_output=False)
    
    if created_rgs:
        print(f"\n  Resource group details ({created_rgs[0].get('name')}):")
        run_command([
            'itlc', 'resourcegroup', 'get',
            subscription_id,
            created_rgs[0].get('name')
        ], capture_output=False)
    
    # Step 8: Cleanup (optional)
    print_step("Step 8: Cleanup (optional)")
    print("\n  To cleanup created resources, run:")
    print(f"    itlc tenant delete {tenant_name} --yes")
    print(f"    itlc subscription delete {subscription_id} --yes")
    for rg_name, _ in resource_groups:
        print(f"    itlc resourcegroup delete {subscription_id} {rg_name} --yes")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Demo completed successfully!{Colors.END}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
