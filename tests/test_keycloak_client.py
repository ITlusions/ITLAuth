"""
Comprehensive test suite for KeycloakClient
Tests for token management, introspection, and credential discovery
"""

import unittest
from unittest.mock import patch, Mock, MagicMock, mock_open
import os
import sys
from pathlib import Path
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from itlc.keycloak_client import KeycloakClient


class TestKeycloakClientInit(unittest.TestCase):
    """Test KeycloakClient initialization"""
    
    def test_init_default_values(self):
        """Test initialization with default values"""
        client = KeycloakClient()
        self.assertEqual(client.keycloak_url, 'https://sts.itlusions.com')
        self.assertEqual(client.realm, 'itlusions')
    
    def test_init_custom_values(self):
        """Test initialization with custom values"""
        client = KeycloakClient(
            keycloak_url='https://custom.sts.com',
            realm='production'
        )
        self.assertEqual(client.keycloak_url, 'https://custom.sts.com')
        self.assertEqual(client.realm, 'production')
    
    def test_init_removes_trailing_slash(self):
        """Test that trailing slash is removed from URL"""
        client = KeycloakClient(keycloak_url='https://sts.example.com/')
        self.assertEqual(client.keycloak_url, 'https://sts.example.com')
    
    @patch.dict(os.environ, {'KEYCLOAK_URL': 'https://env.sts.com', 'KEYCLOAK_REALM': 'env-realm'})
    def test_init_from_environment(self):
        """Test initialization from environment variables"""
        client = KeycloakClient()
        self.assertEqual(client.keycloak_url, 'https://env.sts.com')
        self.assertEqual(client.realm, 'env-realm')
    
    @patch.dict(os.environ, {'KEYCLOAK_URL': 'https://env.sts.com'})
    def test_init_partial_environment(self):
        """Test initialization with partial environment variables"""
        client = KeycloakClient(realm='custom-realm')
        self.assertEqual(client.keycloak_url, 'https://env.sts.com')
        self.assertEqual(client.realm, 'custom-realm')


class TestKeycloakClientGetAccessToken(unittest.TestCase):
    """Test get_access_token method"""
    
    def setUp(self):
        """Set up test client"""
        self.client = KeycloakClient(
            keycloak_url='https://test.sts.com',
            realm='test-realm'
        )
    
    @patch('itlc.keycloak_client.requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful token acquisition"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': 'refresh_token_456',
            'scope': 'openid profile'
        }
        mock_post.return_value = mock_response
        
        result = self.client.get_access_token('test-client', 'test-secret')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], 'test_token_123')
        self.assertEqual(result['token_type'], 'Bearer')
        self.assertEqual(result['expires_in'], 3600)
        
        # Verify the correct endpoint was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('https://test.sts.com/realms/test-realm/protocol/openid-connect/token', call_args[0])
        
        # Verify correct data was sent
        self.assertEqual(call_args[1]['data']['grant_type'], 'client_credentials')
        self.assertEqual(call_args[1]['data']['client_id'], 'test-client')
        self.assertEqual(call_args[1]['data']['client_secret'], 'test-secret')
        self.assertEqual(call_args[1]['timeout'], 10)
    
    @patch('itlc.keycloak_client.requests.post')
    def test_get_access_token_failure_401(self, mock_post):
        """Test token acquisition with invalid credentials"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = self.client.get_access_token('invalid-client', 'invalid-secret')
        
        self.assertIsNone(result)
    
    @patch('itlc.keycloak_client.requests.post')
    def test_get_access_token_failure_500(self, mock_post):
        """Test token acquisition with server error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        result = self.client.get_access_token('test-client', 'test-secret')
        
        self.assertIsNone(result)
    
    @patch('itlc.keycloak_client.requests.post')
    def test_get_access_token_network_error(self, mock_post):
        """Test token acquisition with network error"""
        mock_post.side_effect = Exception('Network error')
        
        result = self.client.get_access_token('test-client', 'test-secret')
        
        self.assertIsNone(result)
    
    @patch('itlc.keycloak_client.requests.post')
    def test_get_access_token_timeout(self, mock_post):
        """Test token acquisition with timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout('Connection timeout')
        
        result = self.client.get_access_token('test-client', 'test-secret')
        
        self.assertIsNone(result)


class TestKeycloakClientIntrospectToken(unittest.TestCase):
    """Test introspect_token method"""
    
    def setUp(self):
        """Set up test client"""
        self.client = KeycloakClient(
            keycloak_url='https://test.sts.com',
            realm='test-realm'
        )
    
    @patch('itlc.keycloak_client.requests.post')
    def test_introspect_token_active(self, mock_post):
        """Test introspection of active token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': True,
            'client_id': 'test-client',
            'username': 'test-user',
            'exp': 1234567890,
            'iat': 1234564290,
            'scope': 'openid profile'
        }
        mock_post.return_value = mock_response
        
        result = self.client.introspect_token('test_token', 'test-client', 'test-secret')
        
        self.assertIsNotNone(result)
        self.assertTrue(result['active'])
        self.assertEqual(result['client_id'], 'test-client')
        
        # Verify the correct endpoint was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('https://test.sts.com/realms/test-realm/protocol/openid-connect/token/introspect', call_args[0])
        
        # Verify correct data was sent
        self.assertEqual(call_args[1]['data']['token'], 'test_token')
        self.assertEqual(call_args[1]['data']['client_id'], 'test-client')
        self.assertEqual(call_args[1]['data']['client_secret'], 'test-secret')
    
    @patch('itlc.keycloak_client.requests.post')
    def test_introspect_token_inactive(self, mock_post):
        """Test introspection of inactive/expired token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'active': False
        }
        mock_post.return_value = mock_response
        
        result = self.client.introspect_token('expired_token', 'test-client', 'test-secret')
        
        self.assertIsNotNone(result)
        self.assertFalse(result['active'])
    
    @patch('itlc.keycloak_client.requests.post')
    def test_introspect_token_unauthorized(self, mock_post):
        """Test introspection with unauthorized client"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = self.client.introspect_token('test_token', 'invalid-client', 'invalid-secret')
        
        self.assertIsNone(result)
    
    @patch('itlc.keycloak_client.requests.post')
    def test_introspect_token_error(self, mock_post):
        """Test introspection with network error"""
        mock_post.side_effect = Exception('Network error')
        
        result = self.client.introspect_token('test_token', 'test-client', 'test-secret')
        
        self.assertIsNone(result)


class TestKeycloakClientGetCredentialsFromEnv(unittest.TestCase):
    """Test get_credentials_from_env method"""
    
    def setUp(self):
        """Set up test client"""
        self.client = KeycloakClient()
    
    @patch.dict(os.environ, {
        'KEYCLOAK_CLIENT_ID': 'keycloak-client',
        'KEYCLOAK_CLIENT_SECRET': 'keycloak-secret'
    }, clear=True)
    def test_get_credentials_keycloak_env(self):
        """Test getting credentials from KEYCLOAK_* environment variables"""
        result = self.client.get_credentials_from_env()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['client_id'], 'keycloak-client')
        self.assertEqual(result['client_secret'], 'keycloak-secret')
        self.assertEqual(result['source'], 'environment')
    
    @patch.dict(os.environ, {
        'ITL_CLIENT_ID': 'itl-client',
        'ITL_CLIENT_SECRET': 'itl-secret'
    }, clear=True)
    def test_get_credentials_itl_env(self):
        """Test getting credentials from ITL_* environment variables"""
        result = self.client.get_credentials_from_env()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['client_id'], 'itl-client')
        self.assertEqual(result['client_secret'], 'itl-secret')
        self.assertEqual(result['source'], 'environment')
    
    @patch.dict(os.environ, {
        'KEYCLOAK_CLIENT_ID': 'keycloak-client',
        'KEYCLOAK_CLIENT_SECRET': 'keycloak-secret',
        'ITL_CLIENT_ID': 'itl-client',
        'ITL_CLIENT_SECRET': 'itl-secret'
    }, clear=True)
    def test_get_credentials_priority(self):
        """Test that KEYCLOAK_* variables have priority over ITL_*"""
        result = self.client.get_credentials_from_env()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['client_id'], 'keycloak-client')
        self.assertEqual(result['client_secret'], 'keycloak-secret')
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_get_credentials_mounted_secrets(self, mock_read_text, mock_exists):
        """Test getting credentials from mounted secrets"""
        mock_exists.return_value = True
        mock_read_text.side_effect = ['mounted-client', 'mounted-secret']
        
        result = self.client.get_credentials_from_env()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['client_id'], 'mounted-client')
        self.assertEqual(result['client_secret'], 'mounted-secret')
        self.assertEqual(result['source'], 'mounted_secrets')
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('pathlib.Path.exists')
    def test_get_credentials_no_sources(self, mock_exists):
        """Test when no credential sources are available"""
        mock_exists.return_value = False
        
        result = self.client.get_credentials_from_env()
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'KEYCLOAK_CLIENT_ID': 'only-id'}, clear=True)
    def test_get_credentials_partial_keycloak_env(self):
        """Test with only partial KEYCLOAK_* credentials"""
        result = self.client.get_credentials_from_env()
        
        # Should skip incomplete credentials
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'ITL_CLIENT_SECRET': 'only-secret'}, clear=True)
    def test_get_credentials_partial_itl_env(self):
        """Test with only partial ITL_* credentials"""
        result = self.client.get_credentials_from_env()
        
        # Should skip incomplete credentials
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_get_credentials_mounted_secrets_read_error(self, mock_read_text, mock_exists):
        """Test mounted secrets with read error"""
        mock_exists.return_value = True
        mock_read_text.side_effect = Exception('Read error')
        
        result = self.client.get_credentials_from_env()
        
        self.assertIsNone(result)


class TestKeycloakClientIntegration(unittest.TestCase):
    """Integration tests for KeycloakClient"""
    
    @patch('itlc.keycloak_client.requests.post')
    def test_full_token_workflow(self, mock_post):
        """Test complete workflow: get token -> introspect token"""
        client = KeycloakClient(
            keycloak_url='https://test.sts.com',
            realm='test-realm'
        )
        
        # Mock token acquisition
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            'access_token': 'workflow_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        # Mock token introspection
        introspect_response = Mock()
        introspect_response.status_code = 200
        introspect_response.json.return_value = {
            'active': True,
            'client_id': 'test-client'
        }
        
        mock_post.side_effect = [token_response, introspect_response]
        
        # Get token
        token_result = client.get_access_token('test-client', 'test-secret')
        self.assertIsNotNone(token_result)
        self.assertEqual(token_result['access_token'], 'workflow_token')
        
        # Introspect token
        introspect_result = client.introspect_token(
            token_result['access_token'],
            'test-client',
            'test-secret'
        )
        self.assertIsNotNone(introspect_result)
        self.assertTrue(introspect_result['active'])
    
    @patch.dict(os.environ, {
        'KEYCLOAK_CLIENT_ID': 'env-client',
        'KEYCLOAK_CLIENT_SECRET': 'env-secret'
    })
    @patch('itlc.keycloak_client.requests.post')
    def test_token_acquisition_with_env_credentials(self, mock_post):
        """Test token acquisition using environment credentials"""
        client = KeycloakClient()
        
        # Get credentials from environment
        creds = client.get_credentials_from_env()
        self.assertIsNotNone(creds)
        
        # Mock token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'env_token',
            'token_type': 'Bearer'
        }
        mock_post.return_value = mock_response
        
        # Use credentials to get token
        result = client.get_access_token(creds['client_id'], creds['client_secret'])
        
        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], 'env_token')


class TestKeycloakClientEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_url(self):
        """Test with empty URL (should use default)"""
        client = KeycloakClient(keycloak_url='')
        # Empty string is falsy, so it falls back to default
        self.assertEqual(client.keycloak_url, 'https://sts.itlusions.com')
    
    def test_none_values_explicitly(self):
        """Test with explicit None values"""
        client = KeycloakClient(keycloak_url=None, realm=None)
        self.assertEqual(client.keycloak_url, 'https://sts.itlusions.com')
        self.assertEqual(client.realm, 'itlusions')
    
    @patch('itlc.keycloak_client.requests.post')
    def test_malformed_json_response(self, mock_post):
        """Test handling of malformed JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_post.return_value = mock_response
        
        client = KeycloakClient()
        result = client.get_access_token('test-client', 'test-secret')
        
        self.assertIsNone(result)
    
    def test_multiple_trailing_slashes(self):
        """Test URL with multiple trailing slashes"""
        client = KeycloakClient(keycloak_url='https://test.sts.com///')
        self.assertEqual(client.keycloak_url, 'https://test.sts.com')


if __name__ == '__main__':
    unittest.main()
