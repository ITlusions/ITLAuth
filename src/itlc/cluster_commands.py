"""
Cluster management commands for ITL CLI
"""
import click
import sys
from .clusters import ClustersManager


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


@click.group()
def cluster():
    """
    Manage registered Kubernetes clusters.
    
    Register, list, and manage cluster configurations separate from OIDC authentication.
    Each cluster registration creates a kubeconfig context that uses one of the
    OIDC authentication methods for accessing the cluster.
    
    Commands:
      list       - List all registered clusters
      add        - Register a new cluster
      remove     - Unregister a cluster
      validate   - Check for naming conflicts
    
    Examples:
      itlc cluster list
      itlc cluster add --name my-cluster --server https://cluster-api:6443
    """
    pass


@cluster.command(name='list')
def cluster_list():
    """
    List all registered clusters.
    
    Shows all clusters registered with ITL, separated from OIDC contexts.
    """
    try:
        clusters_mgr = ClustersManager()
        clusters = clusters_mgr.list_clusters()
        
        if not clusters:
            print_info("No registered clusters yet")
            print_info("Register your first cluster with:")
            click.echo(f"  itlc cluster add --name my-cluster --server https://api.example.com:6443")
            return
        
        print_info(f"Registered Clusters ({len(clusters)}):")
        click.echo()
        
        # Display in table format
        for c in clusters:
            env = c.get('environment', 'unknown')
            loc = c.get('location', 'unknown')
            server = c['server']
            name = c['name']
            
            click.echo(f"{Colors.BOLD}{Colors.CYAN}{name:<20}{Colors.END} "
                      f"{server:<40} "
                      f"{Colors.YELLOW}[{env}]{Colors.END} "
                      f"({loc})")
        
        click.echo()
        print_info("Use with kubectl:")
        click.echo(f"  kubectl --context={clusters[0]['name']} get pods\n")
        
    except Exception as e:
        print_error(f"Failed to list clusters: {str(e)}")
        sys.exit(1)


@cluster.command(name='add')
@click.option('--name', prompt='Cluster name', help='Name for this cluster registration')
@click.option('--server', prompt='Cluster API server', help='Kubernetes API server URL (e.g., https://10.0.0.1:6443)')
@click.option('--environment', type=click.Choice(['development', 'staging', 'production']), 
              default='production', help='Cluster environment')
@click.option('--location', type=click.Choice(['local', 'remote', 'cloud']), 
              default='cloud', help='Cluster location')
def cluster_add(name: str, server: str, environment: str, location: str):
    """
    Register a new cluster.
    
    Adds a cluster configuration that can be used with kubectl.
    The cluster will use one of the OIDC authentication contexts.
    """
    try:
        clusters_mgr = ClustersManager()
        
        # Validate naming to prevent conflicts with OIDC contexts
        if name in clusters_mgr.reserved_contexts:
            print_error(f"Cluster name '{name}' conflicts with reserved OIDC context names")
            print_error(f"Reserved names: {', '.join(sorted(clusters_mgr.reserved_contexts))}")
            print_info(f"Use a different name for your cluster")
            sys.exit(1)
        
        clusters_mgr.add_cluster(name, server, environment, location)
        
        print_success(f"Cluster '{name}' registered successfully")
        print_info(f"Environment: {environment}")
        print_info(f"Server: {server}")
        print_info(f"Location: {location}")
        click.echo()
        print_info(f"Use this cluster with:")
        click.echo(f"  kubectl --context={name} get pods")
        
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to register cluster: {str(e)}")
        sys.exit(1)


@cluster.command(name='remove')
@click.option('--name', prompt='Cluster name', help='Name of cluster to unregister')
@click.confirmation_option(prompt='Are you sure you want to unregister this cluster?')
def cluster_remove(name: str):
    """
    Unregister a cluster.
    
    Removes a cluster registration from your ITL configuration.
    Note: This does NOT delete the cluster itself.
    """
    try:
        clusters_mgr = ClustersManager()
        
        if clusters_mgr.delete_cluster(name):
            print_success(f"Cluster '{name}' has been unregistered")
        else:
            print_error(f"Cluster '{name}' not found")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Failed to unregister cluster: {str(e)}")
        sys.exit(1)


@cluster.command(name='validate')
def cluster_validate():
    """
    Validate cluster naming and check for conflicts.
    
    Checks that registered cluster names don't conflict with
    reserved OIDC context names.
    """
    try:
        clusters_mgr = ClustersManager()
        clusters = clusters_mgr.list_clusters()
        
        if not clusters:
            print_success("No clusters registered (nothing to validate)")
            return
        
        print_info(f"Validating {len(clusters)} cluster(s)...")
        
        conflicts = []
        for c in clusters:
            if c['name'] in clusters_mgr.reserved_contexts:
                conflicts.append(c['name'])
        
        if conflicts:
            print_error(f"Found {len(conflicts)} naming conflict(s):")
            for name in conflicts:
                click.echo(f"  ✗ {name} (conflicts with OIDC context)")
            print_info(f"\nReserved context names: {', '.join(sorted(clusters_mgr.reserved_contexts))}")
            sys.exit(1)
        else:
            print_success(f"All {len(clusters)} cluster(s) have valid names")
            for c in clusters:
                click.echo(f"  ✓ {c['name']}")
            
    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        sys.exit(1)
