"""
Token Cache Manager
Azure-style token caching for Keycloak tokens
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class TokenCache:
    """
    Token cache manager with automatic expiry handling.
    Similar to Azure's ~/.kube/cache/
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = Path.home() / '.itl' / 'token-cache'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_file(self, client_id: str) -> Path:
        """Get cache file path for client ID"""
        # Hash client_id for filename
        hashed = hashlib.md5(client_id.encode()).hexdigest()
        return self.cache_dir / f"{hashed}.json"
    
    def save_token(self, client_id: str, token_data: Dict):
        """
        Save token to cache with metadata.
        
        Args:
            client_id: Service account client ID
            token_data: Token response from Keycloak
        """
        try:
            cache_file = self._get_cache_file(client_id)
            
            # Calculate expiry
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            cache_entry = {
                'client_id': client_id,
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_in': expires_in,
                'expires_at': expires_at.isoformat(),
                'cached_at': datetime.now().isoformat(),
                'scope': token_data.get('scope', '')
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
        except Exception as e:
            print(f"Warning: Failed to cache token: {e}")
    
    def get_token(self, client_id: str) -> Optional[Dict]:
        """
        Get token from cache if not expired.
        
        Args:
            client_id: Service account client ID
            
        Returns:
            Token data if valid, None if expired or not found
        """
        try:
            cache_file = self._get_cache_file(client_id)
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r') as f:
                cache_entry = json.load(f)
            
            # Check expiry
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            now = datetime.now()
            
            # Refresh 5 minutes before expiry
            refresh_threshold = expires_at - timedelta(minutes=5)
            
            if now >= expires_at:
                cache_file.unlink()  # Delete expired cache
                return None
            
            if now >= refresh_threshold:
                # Near expiry but still valid
                pass
            
            return cache_entry
            
        except Exception:
            return None
    
    def delete_token(self, client_id: str):
        """Delete cached token for client ID"""
        try:
            cache_file = self._get_cache_file(client_id)
            if cache_file.exists():
                cache_file.unlink()
        except Exception:
            pass
    
    def clear_all(self):
        """Clear all cached tokens"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
        except Exception as e:
            print(f"Warning: Failed to clear cache: {e}")
    
    def list_cached(self) -> list:
        """List all cached tokens"""
        cached_tokens = []
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                    cached_tokens.append({
                        'client_id': cache_entry['client_id'],
                        'expires_at': cache_entry['expires_at'],
                        'cached_at': cache_entry['cached_at']
                    })
        except Exception:
            pass
        
        return cached_tokens


# Global instance
token_cache = TokenCache()
