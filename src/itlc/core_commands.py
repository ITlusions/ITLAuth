"""
ITL Core Provider CLI Commands
CRUD operations for Core resources via API Gateway
"""
import click
import json
from typing import Optional
from .controlplane_client import ControlPlaneClient


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg):
    click.echo(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg):
    click.echo(f"{Colors.RED}✗{Colors.END} {msg}", err=True)


def print_info(msg):
    click.echo(f"{Colors.CYAN}ℹ{Colors.END} {msg}")


def print_json(data):
    """Pretty print JSON data"""
    click.echo(json.dumps(data, indent=2))


def get_client(api_url: Optional[str] = None, token: Optional[str] = None) -> ControlPlaneClient:
    """Initialize ControlPlane client (always uses Gateway)"""
    return ControlPlaneClient(base_url=api_url, access_token=token)


# ==================== TENANT COMMANDS ====================

@click.group()
def tenant():
    """Manage tenants in the ITL Core Provider"""
    pass


@tenant.command('create')
@click.argument('name')
@click.option('--display-name', help='Friendly display name')
@click.option('--domain', help='Tenant domain (e.g., acme.com)')
@click.option('--location', default='westeurope', help='Azure location')
@click.option('--tag', multiple=True, help='Tags in key=value format')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'id']), default='table')
def tenant_create(name, display_name, domain, location, tag, api_url, token, output):
    """Create a new tenant"""
    client = get_client(api_url, token)
    
    tags = dict(t.split('=', 1) for t in tag) if tag else {}
    
    result = client.create_tenant(
        name=name,
        display_name=display_name or name,
        domain=domain,
        location=location,
        tags=tags
    )
    
    if result:
        print_success(f"Tenant '{name}' created successfully")
        if output == 'json':
            print_json(result)
        elif output == 'id':
            click.echo(result.get('id', ''))
        else:
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Name: {result.get('name')}")
            click.echo(f"  Domain: {result.get('properties', {}).get('domain', 'N/A')}")
    else:
        print_error("Failed to create tenant")
        raise click.Abort()


@tenant.command('list')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table')
def tenant_list(api_url, token, output):
    """List all tenants"""
    client = get_client(api_url, token)
    result = client.list_tenants()
    
    if result:
        # Support both 'value' (ARM) and 'resources' (SDK) keys
        tenants = result.get('value', result.get('resources', [])) if isinstance(result, dict) else result
        if output == 'json':
            print_json(result)
        else:
            click.echo(f"\nFound {len(tenants)} tenant(s):\n")
            for tenant in tenants:
                click.echo(f"  • {tenant.get('name')} ({tenant.get('id')})")
                props = tenant.get('properties', {})
                if 'domain' in props:
                    click.echo(f"    Domain: {props['domain']}")
                if 'display_name' in props:
                    click.echo(f"    Display Name: {props['display_name']}")
    else:
        print_error("Failed to list tenants")


@tenant.command('get')
@click.argument('tenant_id')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
def tenant_get(tenant_id, api_url, token, output):
    """Get tenant details"""
    client = get_client(api_url, token)
    result = client.get_tenant(tenant_id)
    
    if result:
        if output == 'json':
            print_json(result)
        else:
            click.echo(f"\nTenant: {result.get('name')}")
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Location: {result.get('location')}")
            if 'properties' in result:
                for key, value in result['properties'].items():
                    click.echo(f"  {key}: {value}")
    else:
        print_error(f"Tenant '{tenant_id}' not found")


@tenant.command('delete')
@click.argument('tenant_id')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def tenant_delete(tenant_id, api_url, token, yes):
    """Delete a tenant"""
    if not yes:
        click.confirm(f"Are you sure you want to delete tenant '{tenant_id}'?", abort=True)
    
    client = get_client(api_url, token)
    result = client.delete_tenant(tenant_id)
    
    if result:
        print_success(f"Tenant '{tenant_id}' deleted successfully")
    else:
        print_error("Failed to delete tenant")
        raise click.Abort()


# ==================== SUBSCRIPTION COMMANDS ====================

@click.group()
def subscription():
    """Manage subscriptions in the ITL Core Provider"""
    pass


@subscription.command('create')
@click.argument('name')
@click.option('--display-name', help='Friendly display name')
@click.option('--tenant-id', help='Parent tenant ID')
@click.option('--management-group-id', help='Parent management group ID')
@click.option('--state', default='Enabled', type=click.Choice(['Enabled', 'Disabled', 'Deleted']))
@click.option('--location', default='westeurope', help='Azure location')
@click.option('--tag', multiple=True, help='Tags in key=value format')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'id']), default='table')
def subscription_create(name, display_name, tenant_id, management_group_id, state, location, tag, api_url, token, output):
    """Create a new subscription"""
    client = get_client(api_url, token)
    
    tags = dict(t.split('=', 1) for t in tag) if tag else {}
    
    result = client.create_subscription(
        name=name,
        display_name=display_name or name,
        tenant_id=tenant_id,
        management_group_id=management_group_id,
        state=state,
        location=location,
        tags=tags
    )
    
    if result:
        print_success(f"Subscription '{name}' created successfully")
        if output == 'json':
            print_json(result)
        elif output == 'id':
            click.echo(result.get('id', ''))
        else:
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Display Name: {result.get('properties', {}).get('displayName', 'N/A')}")
            click.echo(f"  State: {result.get('properties', {}).get('state', 'N/A')}")
    else:
        print_error("Failed to create subscription")
        raise click.Abort()


@subscription.command('list')
@click.option('--tenant-id', help='Filter by tenant ID')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table')
def subscription_list(tenant_id, api_url, token, output):
    """List all subscriptions"""
    client = get_client(api_url, token)
    result = client.list_subscriptions(tenant_id=tenant_id)
    
    if result:
        # Support both 'value' (ARM) and 'resources' (SDK) keys
        subscriptions = result.get('value', result.get('resources', [])) if isinstance(result, dict) else result
        if output == 'json':
            print_json(result)
        else:
            click.echo(f"\nFound {len(subscriptions)} subscription(s):\n")
            for sub in subscriptions:
                props = sub.get('properties', {})
                click.echo(f"  • {sub.get('name')} ({sub.get('id')})")
                click.echo(f"    Display Name: {props.get('display_name', props.get('displayName', 'N/A'))}")
                click.echo(f"    State: {props.get('state', 'N/A')}")
    else:
        print_error("Failed to list subscriptions")


@subscription.command('get')
@click.argument('subscription_id')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
def subscription_get(subscription_id, api_url, token, output):
    """Get subscription details"""
    client = get_client(api_url, token)
    result = client.get_subscription(subscription_id)
    
    if result:
        if output == 'json':
            print_json(result)
        else:
            props = result.get('properties', {})
            click.echo(f"\nSubscription: {result.get('name')}")
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Display Name: {props.get('displayName', 'N/A')}")
            click.echo(f"  State: {props.get('state', 'N/A')}")
            click.echo(f"  Location: {result.get('location')}")
    else:
        print_error(f"Subscription '{subscription_id}' not found")


@subscription.command('delete')
@click.argument('subscription_id')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def subscription_delete(subscription_id, api_url, token, yes):
    """Delete a subscription"""
    if not yes:
        click.confirm(f"Are you sure you want to delete subscription '{subscription_id}'?", abort=True)
    
    client = get_client(api_url, token)
    result = client.delete_subscription(subscription_id)
    
    if result:
        print_success(f"Subscription '{subscription_id}' deleted successfully")
    else:
        print_error("Failed to delete subscription")
        raise click.Abort()


# ==================== RESOURCE GROUP COMMANDS ====================

@click.group()
def resourcegroup():
    """Manage resource groups in the ITL Core Provider"""
    pass


@resourcegroup.command('create')
@click.argument('name')
@click.argument('subscription_id')
@click.option('--location', default='westeurope', help='Azure location')
@click.option('--managed-by', help='Managed by resource ID')
@click.option('--tenant-id', help='Direct tenant ID for tenant linking')
@click.option('--tag', multiple=True, help='Tags in key=value format')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'id']), default='table')
def resourcegroup_create(name, subscription_id, location, managed_by, tenant_id, tag, api_url, token, output):
    """Create a new resource group"""
    client = get_client(api_url, token)
    
    tags = dict(t.split('=', 1) for t in tag) if tag else {}
    
    result = client.create_resource_group(
        name=name,
        subscription_id=subscription_id,
        location=location,
        managed_by=managed_by,
        tenant_id=tenant_id,
        tags=tags
    )
    
    if result:
        print_success(f"Resource group '{name}' created successfully")
        if output == 'json':
            print_json(result)
        elif output == 'id':
            click.echo(result.get('id', ''))
        else:
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Location: {result.get('location')}")
            click.echo(f"  Provisioning State: {result.get('properties', {}).get('provisioningState', 'N/A')}")
    else:
        print_error("Failed to create resource group")
        raise click.Abort()


@resourcegroup.command('list')
@click.option('--subscription-id', help='Filter by subscription ID')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table')
def resourcegroup_list(subscription_id, api_url, token, output):
    """List all resource groups"""
    client = get_client(api_url, token)
    result = client.list_resource_groups(subscription_id=subscription_id)
    
    if result:
        # Support both 'value' (ARM) and 'resources' (SDK) keys
        groups = result.get('value', result.get('resources', [])) if isinstance(result, dict) else result
        if output == 'json':
            print_json(result)
        else:
            click.echo(f"\nFound {len(groups)} resource group(s):\n")
            for rg in groups:
                click.echo(f"  • {rg.get('name')} ({rg.get('location')})")
                click.echo(f"    ID: {rg.get('id')}")
    else:
        print_error("Failed to list resource groups")


@resourcegroup.command('get')
@click.argument('subscription_id')
@click.argument('name')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
def resourcegroup_get(subscription_id, name, api_url, token, output):
    """Get resource group details"""
    client = get_client(api_url, token)
    result = client.get_resource_group(subscription_id, name)
    
    if result:
        if output == 'json':
            print_json(result)
        else:
            props = result.get('properties', {})
            click.echo(f"\nResource Group: {result.get('name')}")
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Location: {result.get('location')}")
            click.echo(f"  Provisioning State: {props.get('provisioningState', 'N/A')}")
            if tags := result.get('tags'):
                click.echo("  Tags:")
                for key, value in tags.items():
                    click.echo(f"    {key}: {value}")
    else:
        print_error(f"Resource group '{name}' not found")


@resourcegroup.command('delete')
@click.argument('subscription_id')
@click.argument('name')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def resourcegroup_delete(subscription_id, name, api_url, token, yes):
    """Delete a resource group"""
    if not yes:
        click.confirm(f"Are you sure you want to delete resource group '{name}'?", abort=True)
    
    client = get_client(api_url, token)
    result = client.delete_resource_group(subscription_id, name)
    
    if result:
        print_success(f"Resource group '{name}' deleted successfully")
    else:
        print_error("Failed to delete resource group")
        raise click.Abort()


# ==================== LOCATION COMMANDS ====================

@click.group()
def location():
    """Manage locations in the ITL Core Provider"""
    pass


@location.command('list')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table')
def location_list(api_url, token, output):
    """List all available locations"""
    client = get_client(api_url, token)
    result = client.list_locations()
    
    if result:
        # Handle both 'resources' and 'value' keys for backward compatibility
        locations = result.get('resources', result.get('value', []))
        if output == 'json':
            print_json(locations)
        else:
            click.echo(f"\nFound {len(locations)} location(s):\n")
            for loc in locations:
                props = loc.get('properties', {})
                click.echo(f"  • {loc.get('name')}")
                click.echo(f"    Display Name: {props.get('display_name', 'N/A')}")
                click.echo(f"    Region: {props.get('region', 'N/A')}")
    else:
        print_error("Failed to list locations")


@location.command('get')
@click.argument('location_name')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
def location_get(location_name, api_url, token, output):
    """Get location details"""
    client = get_client(api_url, token)
    result = client.get_location(location_name)
    
    if result:
        if output == 'json':
            print_json(result)
        else:
            props = result.get('properties', {})
            click.echo(f"\nLocation: {result.get('name')}")
            click.echo(f"  Display Name: {props.get('display_name', 'N/A')}")
            click.echo(f"  Region: {props.get('region', 'N/A')}")
            click.echo(f"  Type: {props.get('location_type', 'N/A')}")
            if coords := props.get('latitude'):
                click.echo(f"  Coordinates: {coords}, {props.get('longitude', 'N/A')}")
    else:
        print_error(f"Location '{location_name}' not found")


@location.command('create')
@click.argument('name')
@click.option('--display-name', help='Friendly display name')
@click.option('--region', help='Region name (e.g., Netherlands)')
@click.option('--location-type', default='Region', type=click.Choice(['Region', 'EdgeZone', 'DataCenter']), help='Location type')
@click.option('--latitude', help='Geographic latitude')
@click.option('--longitude', help='Geographic longitude')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'id']), default='table')
def location_create(name, display_name, region, location_type, latitude, longitude, api_url, token, output):
    """Create a new location"""
    client = get_client(api_url, token)
    
    result = client.create_location(
        name=name,
        display_name=display_name or name,
        region=region,
        location_type=location_type,
        latitude=latitude,
        longitude=longitude
    )
    
    if result:
        print_success(f"Location '{name}' created successfully")
        if output == 'json':
            print_json(result)
        elif output == 'id':
            click.echo(result.get('id', ''))
        else:
            props = result.get('properties', {})
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Name: {result.get('name')}")
            click.echo(f"  Display Name: {props.get('display_name', 'N/A')}")
            click.echo(f"  Region: {props.get('region', 'N/A')}")
    else:
        print_error("Failed to create location")
        raise click.Abort()


@location.command('delete')
@click.argument('location_name')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def location_delete(location_name, api_url, token, yes):
    """Delete a location"""
    if not yes:
        click.confirm(f"Are you sure you want to delete location '{location_name}'?", abort=True)
    
    client = get_client(api_url, token)
    result = client.delete_location(location_name)
    
    if result:
        print_success(f"Location '{location_name}' deleted successfully")
    else:
        print_error("Failed to delete location")
        raise click.Abort()


# ==================== MANAGEMENT GROUP COMMANDS ====================

@click.group()
def managementgroup():
    """Manage management groups in the ITL Core Provider"""
    pass


@managementgroup.command('create')
@click.argument('name')
@click.option('--display-name', help='Friendly display name')
@click.option('--parent-id', help='Parent management group ID')
@click.option('--tenant-id', help='Associated tenant ID')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'id']), default='table')
def managementgroup_create(name, display_name, parent_id, tenant_id, api_url, token, output):
    """Create a new management group"""
    client = get_client(api_url, token)
    
    result = client.create_management_group(
        name=name,
        display_name=display_name or name,
        parent_id=parent_id,
        tenant_id=tenant_id
    )
    
    if result:
        print_success(f"Management group '{name}' created successfully")
        if output == 'json':
            print_json(result)
        elif output == 'id':
            click.echo(result.get('id', ''))
        else:
            props = result.get('properties', {})
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Name: {result.get('name')}")
            click.echo(f"  Display Name: {props.get('displayName', 'N/A')}")
            click.echo(f"  Parent: {props.get('parent_id', 'N/A')}")
    else:
        print_error("Failed to create management group")
        raise click.Abort()


@managementgroup.command('list')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table')
def managementgroup_list(api_url, token, output):
    """List all management groups"""
    client = get_client(api_url, token)
    result = client.list_management_groups()
    
    if result:
        # Support both 'value' (ARM) and 'resources' (SDK) keys
        groups = result.get('value', result.get('resources', [])) if isinstance(result, dict) else result
        if output == 'json':
            print_json(result)
        else:
            click.echo(f"\nFound {len(groups)} management group(s):\n")
            for mg in groups:
                props = mg.get('properties', {})
                click.echo(f"  • {mg.get('name')}")
                click.echo(f"    Display Name: {props.get('displayName', 'N/A')}")
                if props.get('parent_id'):
                    click.echo(f"    Parent: {props.get('parent_id')}")
    else:
        print_error("Failed to list management groups")


@managementgroup.command('get')
@click.argument('name')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
def managementgroup_get(name, api_url, token, output):
    """Get management group details"""
    client = get_client(api_url, token)
    result = client.get_management_group(name)
    
    if result:
        if output == 'json':
            print_json(result)
        else:
            props = result.get('properties', {})
            click.echo(f"\nManagement Group: {result.get('name')}")
            click.echo(f"  ID: {result.get('id')}")
            click.echo(f"  Display Name: {props.get('displayName', 'N/A')}")
            if props.get('parent_id'):
                click.echo(f"  Parent: {props.get('parent_id')}")
            if props.get('tenant_id'):
                click.echo(f"  Tenant: {props.get('tenant_id')}")
    else:
        print_error(f"Management group '{name}' not found")


@managementgroup.command('delete')
@click.argument('name')
@click.option('--api-url', envvar='CONTROLPLANE_API_URL', help='API Gateway URL')
@click.option('--token', envvar='CONTROLPLANE_TOKEN', help='Authentication token')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def managementgroup_delete(name, api_url, token, yes):
    """Delete a management group"""
    if not yes:
        click.confirm(f"Are you sure you want to delete management group '{name}'?", abort=True)
    
    client = get_client(api_url, token)
    result = client.delete_management_group(name)
    
    if result:
        print_success(f"Management group '{name}' deleted successfully")
    else:
        print_error("Failed to delete management group")
        raise click.Abort()

