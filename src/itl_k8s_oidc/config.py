"""
Configuration management for itl-k8s-oidc.

Handles loading and saving configuration from:
- ~/.config/itl-k8s-oidc/config.json (Linux/macOS)
- %APPDATA%\\itl-k8s-oidc\\config.json (Windows)
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional

from .defaults import DEFAULT_ISSUER_URL, DEFAULT_CLIENT_ID, DEFAULT_SCOPES


def get_config_dir() -> Path:
    """Get the platform-appropriate config directory."""
    if platform.system() == "Windows":
        config_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        config_dir = Path.home() / ".config"
    
    return config_dir / "itl-k8s-oidc"


def get_config_file_path() -> Path:
    """Get the full path to the config file."""
    return get_config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from the config file."""
    config_file = get_config_file_path()
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to the config file."""
    config_file = get_config_file_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        raise RuntimeError(f"Failed to save config to {config_file}: {e}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values."""
    return {
        "issuer_url": DEFAULT_ISSUER_URL,
        "client_id": DEFAULT_CLIENT_ID,
        "scopes": DEFAULT_SCOPES,
    }


def merge_config_sources(
    cli_args: Dict[str, Any],
    env_vars: Dict[str, Any],
    config_file: Dict[str, Any],
    defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge configuration from multiple sources in order of precedence:
    1. CLI arguments (highest)
    2. Environment variables
    3. Config file
    4. Defaults (lowest)
    """
    result = {}
    
    # Start with defaults
    result.update(defaults)
    
    # Override with config file
    result.update(config_file)
    
    # Override with environment variables
    result.update(env_vars)
    
    # Override with CLI arguments (filter out None values)
    result.update({k: v for k, v in cli_args.items() if v is not None})
    
    return result


def load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    if issuer_url := os.environ.get("ITL_OIDC_ISSUER_URL"):
        config["issuer_url"] = issuer_url
    
    if client_id := os.environ.get("ITL_OIDC_CLIENT_ID"):
        config["client_id"] = client_id
    
    if scopes := os.environ.get("ITL_OIDC_SCOPES"):
        config["scopes"] = scopes
    
    return config