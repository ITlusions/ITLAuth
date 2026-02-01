"""
Cluster Management for ITL CLI

Manages registered clusters separate from OIDC authentication contexts.
"""
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


class ClustersManager:
    """Manages registered ITL clusters"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.itl' / 'clusters'
        self.clusters_file = self.config_dir / 'clusters.yaml'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Reserved context names that should not be used for cluster names
        self.reserved_contexts = {
            'itl',
            'itl-python',
            'itl-ssh-tunnel',
            'itl-ssh-tunnel-python',
            'kubernetes',
            'kubernetes-ssh-tunnel'
        }
    
    def load_clusters(self) -> Dict[str, Any]:
        """Load clusters from configuration file"""
        if not self.clusters_file.exists():
            return {'clusters': {}}
        
        with open(self.clusters_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                return data if data else {'clusters': {}}
            except Exception:
                return {'clusters': {}}
    
    def save_clusters(self, data: Dict[str, Any]) -> None:
        """Save clusters to configuration file"""
        with open(self.clusters_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def add_cluster(self, name: str, server: str, environment: str = 'production',
                   location: str = 'cloud', metadata: Optional[Dict] = None) -> None:
        """Register a new cluster"""
        if name in self.reserved_contexts:
            raise ValueError(
                f"Cluster name '{name}' conflicts with reserved OIDC context names. "
                f"Avoid: {', '.join(sorted(self.reserved_contexts))}"
            )
        
        clusters = self.load_clusters()
        
        clusters['clusters'][name] = {
            'server': server,
            'environment': environment,
            'location': location,
            'registered_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self.save_clusters(clusters)
    
    def get_cluster(self, name: str) -> Optional[Dict]:
        """Get a specific cluster"""
        clusters = self.load_clusters()
        return clusters.get('clusters', {}).get(name)
    
    def list_clusters(self) -> List[Dict]:
        """List all registered clusters"""
        clusters = self.load_clusters()
        result = []
        
        for name, config in clusters.get('clusters', {}).items():
            result.append({
                'name': name,
                **config
            })
        
        return sorted(result, key=lambda x: x['name'])
    
    def delete_cluster(self, name: str) -> bool:
        """Delete a registered cluster"""
        clusters = self.load_clusters()
        
        if name in clusters.get('clusters', {}):
            del clusters['clusters'][name]
            self.save_clusters(clusters)
            return True
        
        return False
    
    def get_context_naming_recommendation(self, cluster_name: str) -> str:
        """Get kubectl context name recommendation for a cluster"""
        # Remove reserved prefix if user accidentally included it
        clean_name = cluster_name.lower()
        for reserved in self.reserved_contexts:
            if clean_name.startswith(reserved + '-'):
                clean_name = clean_name[len(reserved)+1:]
        
        return clean_name if clean_name else cluster_name


# OIDC Contexts metadata (the fixed authentication substrate)
OIDC_CONTEXTS = [
    {
        'name': 'itl',
        'category': 'OIDC Authentication',
        'auth_method': 'Binary (kubelogin)',
        'access_mode': 'Direct to cluster',
        'best_for': 'Standard kubectl access with kubelogin plugin',
        'usage': 'kubectl --context=itl get pods',
        'description': 'Direct access using the kubelogin binary plugin for OIDC authentication'
    },
    {
        'name': 'itl-python',
        'category': 'OIDC Authentication',
        'auth_method': 'Python (built-in)',
        'access_mode': 'Direct to cluster',
        'best_for': 'Minimal dependencies, development, debugging',
        'usage': 'kubectl --context=itl-python get pods',
        'description': 'Direct access using Python-based OIDC authentication (no external binaries)'
    },
    {
        'name': 'itl-ssh-tunnel',
        'category': 'OIDC Authentication (via SSH Tunnel)',
        'auth_method': 'Binary (kubelogin) + SSH tunnel',
        'access_mode': 'SSH tunnel to cluster (127.0.0.1:16643)',
        'best_for': 'Remote/restricted networks, firewall bypass',
        'usage': 'kubectl --context=itl-ssh-tunnel get pods',
        'description': 'Tunneled access via SSH with kubelogin plugin (requires SSH setup)'
    },
    {
        'name': 'itl-ssh-tunnel-python',
        'category': 'OIDC Authentication (via SSH Tunnel)',
        'auth_method': 'Python (built-in) + SSH tunnel',
        'access_mode': 'SSH tunnel to cluster (127.0.0.1:16643)',
        'best_for': 'Remote access with minimal dependencies',
        'usage': 'kubectl --context=itl-ssh-tunnel-python get pods',
        'description': 'Tunneled access via SSH with Python-based authentication'
    }
]
