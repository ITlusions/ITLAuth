"""
Cluster Configuration Distribution API

A simple Flask API that serves the latest Kubernetes cluster configuration
with up-to-date certificates for ITlusions OIDC setup.
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from pathlib import Path
import yaml
import os
import logging
from datetime import datetime
import base64
import subprocess
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for browser access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CLUSTER_CONFIG_DIR = Path(__file__).parent / "configs"
CLUSTER_CONFIG_FILE = CLUSTER_CONFIG_DIR / "cluster.yaml"
API_KEY = os.environ.get("API_KEY", None)  # Optional API key for authentication
AUTO_REFRESH = os.environ.get("AUTO_REFRESH", "false").lower() == "true"
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "3600"))  # 1 hour default

def fetch_cluster_config_from_k8s():
    """Fetch the current cluster configuration from kubectl."""
    try:
        logger.info("Fetching latest cluster configuration from kubectl...")
        
        # Run kubectl config view to get current cluster config
        result = subprocess.run(
            ['kubectl', 'config', 'view', '--flatten', '--minify'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to fetch cluster config: {result.stderr}")
            return None
        
        # Parse the config
        config = yaml.safe_load(result.stdout)
        
        # Get the cluster info
        clusters = config.get('clusters', [])
        contexts = config.get('contexts', [])
        current_context = config.get('current-context', '')
        
        # Replace users with OIDC configuration
        config['users'] = [{
            'name': 'oidc-user',
            'user': {
                'exec': {
                    'apiVersion': 'client.authentication.k8s.io/v1beta1',
                    'args': [
                        'get-token',
                        '--oidc-issuer-url=https://sts.itlusions.com/realms/itlusions',
                        '--oidc-client-id=kubernetes-oidc'
                    ],
                    'command': 'kubectl-oidc_login',
                    'env': None,
                    'interactiveMode': 'IfAvailable',
                    'provideClusterInfo': False
                }
            }
        }]
        
        # Update context to use oidc-user
        if contexts:
            for context in contexts:
                if 'context' in context:
                    context['context']['user'] = 'oidc-user'
        
        # Update context name to 'itl' if there's a context
        if contexts:
            contexts[0]['name'] = 'itl'
            if 'context' in contexts[0]:
                contexts[0]['context']['user'] = 'oidc-user'
        
        config['current-context'] = 'itl'
        
        logger.info("Successfully fetched and configured cluster configuration with OIDC")
        return config
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout fetching cluster config")
        return None
    except Exception as e:
        logger.error(f"Error fetching cluster config: {e}")
        return None

def update_cluster_config_file():
    """Update the cluster config file with latest from cluster."""
    try:
        config = fetch_cluster_config_from_k8s()
        if not config:
            return False
        
        # Backup existing file
        if CLUSTER_CONFIG_FILE.exists():
            backup_path = CLUSTER_CONFIG_FILE.with_suffix('.yaml.backup')
            import shutil
            shutil.copy2(CLUSTER_CONFIG_FILE, backup_path)
        
        # Write new config
        CLUSTER_CONFIG_DIR.mkdir(exist_ok=True)
        with open(CLUSTER_CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Updated cluster config file: {CLUSTER_CONFIG_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update cluster config file: {e}")
        return False

def load_cluster_config():
    """Load the cluster configuration from file."""
    try:
        if not CLUSTER_CONFIG_FILE.exists():
            logger.error(f"Cluster config file not found: {CLUSTER_CONFIG_FILE}")
            return None
        
        with open(CLUSTER_CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    except Exception as e:
        logger.error(f"Failed to load cluster config: {e}")
        return None

def verify_api_key():
    """Verify API key if configured."""
    if not API_KEY:
        return True  # No auth required
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return token == API_KEY
    
    return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/cluster-config', methods=['GET'])
def get_cluster_config():
    """
    Get the latest cluster configuration.
    
    Returns:
        YAML content with cluster configuration
    """
    # Verify API key if configured
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    config = load_cluster_config()
    if not config:
        return jsonify({"error": "Cluster configuration not found"}), 404
    
    # Log access
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.info(f"Cluster config accessed by {client_ip}")
    
    # Return as YAML file
    return send_file(
        CLUSTER_CONFIG_FILE,
        mimetype='application/x-yaml',
        as_attachment=True,
        download_name='cluster.yaml'
    )

@app.route('/api/v1/cluster-config/json', methods=['GET'])
def get_cluster_config_json():
    """
    Get the cluster configuration as JSON.
    
    Returns:
        JSON representation of cluster config
    """
    # Verify API key if configured
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    config = load_cluster_config()
    if not config:
        return jsonify({"error": "Cluster configuration not found"}), 404
    
    # Log access
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.info(f"Cluster config (JSON) accessed by {client_ip}")
    
    return jsonify(config)

@app.route('/api/v1/cluster-config/info', methods=['GET'])
def get_cluster_info():
    """
    Get metadata about the cluster configuration.
    
    Returns:
        JSON with cluster metadata
    """
    config = load_cluster_config()
    if not config:
        return jsonify({"error": "Cluster configuration not found"}), 404
    
    # Extract cluster information
    clusters = config.get('clusters', [])
    contexts = config.get('contexts', [])
    current_context = config.get('current-context', '')
    
    cluster_names = [c['name'] for c in clusters]
    context_names = [c['name'] for c in contexts]
    
    # Get file modification time
    mod_time = datetime.fromtimestamp(CLUSTER_CONFIG_FILE.stat().st_mtime)
    
    return jsonify({
        "clusters": cluster_names,
        "contexts": context_names,
        "current_context": current_context,
        "last_updated": mod_time.isoformat(),
        "api_version": "v1",
        "auto_refresh": AUTO_REFRESH
    })

@app.route('/api/v1/cluster-config/refresh', methods=['POST'])
def refresh_cluster_config():
    """
    Manually trigger a refresh of cluster configuration from kubectl.
    
    Returns:
        JSON with status
    """
    # Verify API key if configured
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    logger.info("Manual refresh triggered")
    
    success = update_cluster_config_file()
    
    if success:
        return jsonify({
            "status": "success",
            "message": "Cluster configuration refreshed",
            "timestamp": datetime.utcnow().isoformat()
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to refresh cluster configuration"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Create config directory if it doesn't exist
    CLUSTER_CONFIG_DIR.mkdir(exist_ok=True)
    
    # Check if config file exists or if auto-refresh is enabled
    if not CLUSTER_CONFIG_FILE.exists() or AUTO_REFRESH:
        logger.info("Fetching initial cluster configuration...")
        if update_cluster_config_file():
            logger.info("Initial cluster configuration loaded successfully")
        else:
            logger.warning("Failed to fetch cluster configuration")
            if not CLUSTER_CONFIG_FILE.exists():
                logger.error("No cluster config available. Please ensure kubectl is configured.")
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Cluster Config API on port {port}")
    logger.info(f"Config file: {CLUSTER_CONFIG_FILE}")
    logger.info(f"Auto-refresh: {AUTO_REFRESH} (interval: {REFRESH_INTERVAL}s)")
    if API_KEY:
        logger.info("API key authentication enabled")
    
    # Schedule periodic refresh if enabled
    if AUTO_REFRESH:
        import threading
        import time
        
        def refresh_worker():
            while True:
                time.sleep(REFRESH_INTERVAL)
                logger.info("Auto-refresh triggered")
                update_cluster_config_file()
        
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
        logger.info(f"Auto-refresh thread started (interval: {REFRESH_INTERVAL}s)")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
