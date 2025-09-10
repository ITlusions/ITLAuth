"""
Configuration management for ITL Kubernetes OIDC setup.

Handles configuration from CLI arguments, environment variables, and config files.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class OIDCConfig:
    """Configuration class for OIDC setup."""
    
    # Default issuer URL for ITlusions realm
    DEFAULT_ISSUER_URL = "https://auth.itlusions.com/realms/itlusions"
    
    def __init__(self):
        self.issuer_url: str = self.DEFAULT_ISSUER_URL
        self.client_id: str = "kubernetes"
        self.use_device_code: bool = False
        self.custom_ca_path: Optional[str] = None
        self.kubeconfig_path: Optional[str] = None
        self.verify_auth: bool = False
        self.config_file_path: Optional[str] = None
        
    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        if issuer_env := os.getenv("OIDC_ISSUER_URL"):
            self.issuer_url = issuer_env
            
        if client_id_env := os.getenv("OIDC_CLIENT_ID"):
            self.client_id = client_id_env
            
        if device_code_env := os.getenv("OIDC_USE_DEVICE_CODE"):
            self.use_device_code = device_code_env.lower() in ("true", "1", "yes")
            
        if ca_path_env := os.getenv("OIDC_CA_PATH"):
            self.custom_ca_path = ca_path_env
            
        if kubeconfig_env := os.getenv("KUBECONFIG"):
            self.kubeconfig_path = kubeconfig_env
            
        if verify_env := os.getenv("OIDC_VERIFY_AUTH"):
            self.verify_auth = verify_env.lower() in ("true", "1", "yes")
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from YAML config file."""
        config_file = Path(config_path)
        if not config_file.exists():
            return
            
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            if not config_data:
                return
                
            if 'oidc' in config_data:
                oidc_config = config_data['oidc']
                
                if 'issuer_url' in oidc_config:
                    self.issuer_url = oidc_config['issuer_url']
                    
                if 'client_id' in oidc_config:
                    self.client_id = oidc_config['client_id']
                    
                if 'use_device_code' in oidc_config:
                    self.use_device_code = oidc_config['use_device_code']
                    
                if 'custom_ca_path' in oidc_config:
                    self.custom_ca_path = oidc_config['custom_ca_path']
                    
                if 'kubeconfig_path' in oidc_config:
                    self.kubeconfig_path = oidc_config['kubeconfig_path']
                    
                if 'verify_auth' in oidc_config:
                    self.verify_auth = oidc_config['verify_auth']
                    
        except (yaml.YAMLError, IOError) as e:
            raise RuntimeError(f"Failed to load config file {config_path}: {e}")
    
    def update_from_cli_args(self, **kwargs) -> None:
        """Update configuration from CLI arguments."""
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)
    
    def get_default_config_paths(self) -> list[str]:
        """Get list of default configuration file paths to check."""
        home = Path.home()
        return [
            str(home / ".itl-oidc.yaml"),
            str(home / ".itl-oidc.yml"),
            str(home / ".config" / "itl-oidc" / "config.yaml"),
            str(home / ".config" / "itl-oidc" / "config.yml"),
            "./itl-oidc.yaml",
            "./itl-oidc.yml",
        ]
    
    def load_default_config(self) -> None:
        """Load configuration from default locations."""
        for config_path in self.get_default_config_paths():
            if Path(config_path).exists():
                self.load_from_file(config_path)
                self.config_file_path = config_path
                break
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'issuer_url': self.issuer_url,
            'client_id': self.client_id,
            'use_device_code': self.use_device_code,
            'custom_ca_path': self.custom_ca_path,
            'kubeconfig_path': self.kubeconfig_path,
            'verify_auth': self.verify_auth,
            'config_file_path': self.config_file_path,
        }