"""
ITL Control Plane API Client

Communicates EXCLUSIVELY with the ITL ControlPlane API Gateway.
The Gateway handles provider discovery, routing, and load balancing.

Uses ARM-style resource URLs as defined by Azure Resource Manager patterns.
Never connect directly to resource providers.
"""
import requests
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
import os


class ControlPlaneClient:
    """
    Client for ITL ControlPlane API Gateway.
    
    The CLI communicates exclusively through the API Gateway.
    ARM-style URLs are used:
        /subscriptions/{sub}/resourceGroups/{rg}/providers/{namespace}/{type}/{name}
    
    For global resources (tenants, locations), a placeholder subscription is used.
    """
    
    def __init__(self, base_url: str = None, access_token: str = None):
        """
        Initialize ControlPlaneClient.
        
        Args:
            base_url: API Gateway URL (default: http://localhost:8081)
            access_token: Bearer token for authentication (from OIDC)
        """
        # ALWAYS use Gateway - no direct provider communication
        self.base_url = (base_url or os.getenv('CONTROLPLANE_API_URL', 'http://localhost:8081')).rstrip('/')
        self.access_token = access_token or os.getenv('CONTROLPLANE_TOKEN')
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.access_token:
            self.headers['Authorization'] = f'Bearer {self.access_token}'
        
        # Placeholder for global resources (tenants, subscriptions, locations)
        self.default_subscription = 'default'
        self.default_resource_group = 'default'
    
    def set_token(self, access_token: str):
        """Update the authorization token"""
        self.access_token = access_token
        if access_token:
            self.headers['Authorization'] = f'Bearer {self.access_token}'
    
    # ==================== HEALTH & INFO ====================
    
    def health(self) -> bool:
        """Check API health"""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_openapi_spec(self) -> Optional[Dict]:
        """Get OpenAPI specification"""
        try:
            response = requests.get(f"{self.base_url}/openapi.json", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting OpenAPI spec: {e}")
            return None
    
    # ==================== TENANTS ====================
    
    def create_tenant(self,
                     name: str,
                     display_name: str = None,
                     domain: str = None,
                     location: str = 'global',
                     tags: Dict[str, str] = None,
                     properties: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Create a tenant via API Gateway (ARM-style endpoint).
        
        Tenants are global resources, so we use placeholder subscription/resourceGroup.
        
        Args:
            name: Tenant name (unique identifier)
            display_name: User-friendly display name
            domain: Tenant domain
            location: Location (defaults to 'global')
            tags: Optional tags dictionary
            properties: Optional additional properties
            
        Returns:
            Created tenant object or None on failure
        """
        try:
            # ARM-style URL for Gateway:
            # PUT /subscriptions/{sub}/resourceGroups/{rg}/providers/ITL.Core/tenants/{name}
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/tenants/{name}")
            
            payload = {
                'name': name,
                'location': location,
                'properties': {}
            }
            
            if display_name:
                payload['properties']['displayName'] = display_name
            if domain:
                payload['properties']['domain'] = domain
            if properties:
                payload['properties'].update(properties)
            if tags:
                payload['tags'] = tags
            
            response = requests.put(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error creating tenant: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def list_tenants(self) -> Optional[Dict]:
        """List all tenants via API Gateway"""
        try:
            # ARM-style URL: GET /subscriptions/{sub}/resourceGroups/{rg}/providers/ITL.Core/tenants
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/tenants")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get specific tenant via API Gateway"""
        try:
            # ARM-style URL: GET /{...}/providers/ITL.Core/tenants/{name}
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/tenants/{tenant_id}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Tenant '{tenant_id}' not found")
                return None
            else:
                print(f"Error getting tenant: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant via API Gateway"""
        try:
            # ARM-style URL: DELETE /{...}/providers/ITL.Core/tenants/{name}
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/tenants/{tenant_id}")
            
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=30
            )
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    # ==================== SUBSCRIPTIONS ====================
    
    def create_subscription(self,
                          name: str,
                          display_name: str = None,
                          tenant_id: str = None,
                          management_group_id: str = None,
                          state: str = 'Enabled',
                          location: str = 'westeurope',
                          tags: Dict[str, str] = None,
                          properties: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Create a subscription via API Gateway (ARM-style endpoint).
        
        Args:
            name: Subscription name (unique identifier)
            display_name: User-friendly display name
            tenant_id: Parent tenant ID (optional)
            management_group_id: Parent management group ID (optional)
            state: Subscription state (Enabled, Disabled, Deleted)
            location: Azure location
            tags: Optional tags dictionary
            properties: Optional additional properties
            
        Returns:
            Created subscription object or None on failure
        """
        try:
            # ARM-style URL: PUT /{...}/providers/ITL.Core/subscriptions/{name}
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/subscriptions/{name}")
            
            payload = {
                'name': name,
                'location': location,
                'properties': {}
            }
            
            if display_name:
                payload['properties']['displayName'] = display_name
            if tenant_id:
                payload['properties']['tenantId'] = tenant_id
            if management_group_id:
                payload['properties']['managementGroupId'] = management_group_id
            
            payload['properties']['state'] = state
            
            if properties:
                payload['properties'].update(properties)
            if tags:
                payload['tags'] = tags
            
            response = requests.put(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error creating subscription: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def list_subscriptions(self, tenant_id: str = None) -> Optional[Dict]:
        """List all subscriptions, optionally filtered by tenant"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/subscriptions")
            
            params = {}
            if tenant_id:
                params['tenantId'] = tenant_id
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Get specific subscription"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/subscriptions/{subscription_id}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Subscription '{subscription_id}' not found")
                return None
            else:
                print(f"Error getting subscription: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete subscription"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/subscriptions/{subscription_id}")
            
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=30
            )
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    # ==================== LOCATIONS ====================
    
    def list_locations(self) -> Optional[Dict]:
        """List available locations via API Gateway"""
        try:
            # ARM-style URL for locations
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/locations")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_location(self, location_name: str) -> Optional[Dict]:
        """Get specific location details"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/locations/{location_name}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Location '{location_name}' not found")
                return None
            else:
                print(f"Error getting location: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_location(self,
                       name: str,
                       display_name: str = None,
                       region: str = None,
                       location_type: str = 'Region',
                       latitude: str = None,
                       longitude: str = None,
                       properties: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Create a new location.
        
        Args:
            name: Location name (e.g., 'apeldoorn', 'kpn-dc01')
            display_name: User-friendly display name
            region: Region name (e.g., 'Netherlands')
            location_type: Type of location ('Region', 'EdgeZone', 'DataCenter')
            latitude: Geographic latitude
            longitude: Geographic longitude
            properties: Additional properties
            
        Returns:
            Created location object or None on failure
        """
        try:
            # POST to collection URL (without resource name in URL)
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/locations")
            
            # Build body properties
            body_props = properties.copy() if properties else {}
            if display_name:
                body_props['display_name'] = display_name
            if region:
                body_props['region'] = region
            if location_type:
                body_props['location_type'] = location_type
            if latitude:
                body_props['latitude'] = latitude
            if longitude:
                body_props['longitude'] = longitude
            
            # ResourceRequest requires these fields
            payload = {
                'subscription_id': self.default_subscription,
                'resource_group': self.default_resource_group,
                'resource_type': 'locations',
                'resource_name': name,
                'location': 'global',
                'body': body_props
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 409:
                print(f"Location '{name}' already exists")
                return None
            else:
                print(f"Error creating location: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_location(self, location_name: str) -> bool:
        """Delete a location"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/locations/{location_name}")
            
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=30
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    # ==================== MANAGEMENT GROUPS ====================
    
    def create_management_group(self,
                               name: str,
                               display_name: str = None,
                               parent_id: str = None,
                               tenant_id: str = None,
                               properties: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Create a management group.
        
        Args:
            name: Management group name
            display_name: User-friendly display name
            parent_id: Parent management group ID
            tenant_id: Associated tenant ID
            properties: Additional properties
            
        Returns:
            Created management group object or None on failure
        """
        try:
            # POST to collection URL (without resource name in URL)
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/managementgroups")
            
            # Build body properties
            body_props = properties.copy() if properties else {}
            if display_name:
                body_props['displayName'] = display_name
            if parent_id:
                body_props['parent_id'] = parent_id
            if tenant_id:
                body_props['tenant_id'] = tenant_id
            
            # ResourceRequest requires these fields
            payload = {
                'subscription_id': self.default_subscription,
                'resource_group': self.default_resource_group,
                'resource_type': 'managementgroups',
                'resource_name': name,
                'location': 'global',
                'body': body_props
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 409:
                print(f"Management group '{name}' already exists")
                return None
            else:
                print(f"Error creating management group: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def list_management_groups(self, tenant_id: str = None) -> Optional[Dict]:
        """List management groups"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/managementgroups")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_management_group(self, name: str) -> Optional[Dict]:
        """Get specific management group"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/managementgroups/{name}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Management group '{name}' not found")
                return None
            else:
                print(f"Error getting management group: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_management_group(self, name: str) -> bool:
        """Delete a management group"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/managementgroups/{name}")
            
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=30
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def list_extended_locations(self) -> Optional[Dict]:
        """List extended locations (custom locations)"""
        try:
            url = (f"{self.base_url}/subscriptions/{self.default_subscription}/"
                   f"resourceGroups/{self.default_resource_group}/"
                   f"providers/ITL.Core/extendedlocations")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    # ==================== RESOURCE GROUPS ====================
    
    def create_resource_group(self,
                            name: str,
                            subscription_id: str,
                            location: str,
                            managed_by: str = None,
                            tenant_id: str = None,
                            tags: Dict[str, str] = None,
                            properties: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Create a resource group via ARM-style endpoint.
        
        Args:
            name: Resource group name (unique within subscription)
            subscription_id: Parent subscription ID
            location: Azure location
            managed_by: Managed by resource ID (optional)
            tenant_id: Direct tenant ID for tenant linking (optional)
            tags: Optional tags dictionary
            properties: Optional additional properties
            
        Returns:
            Created resource group object or None on failure
        """
        try:
            payload = {
                'name': name,
                'location': location,
                'properties': properties or {}
            }
            
            if managed_by:
                payload['properties']['managedBy'] = managed_by
            if tenant_id:
                payload['properties']['tenant_id'] = tenant_id
            if tags:
                payload['tags'] = tags
            
            # ARM-style endpoint: /subscriptions/{id}/resourceGroups/{name}
            response = requests.put(
                f"{self.base_url}/subscriptions/{subscription_id}/resourceGroups/{name}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 409:
                print(f"Resource group '{name}' already exists in subscription {subscription_id}")
                return None
            else:
                print(f"Error creating resource group: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_resource_group(self, subscription_id: str, name: str) -> Optional[Dict]:
        """Get a resource group from a subscription"""
        try:
            response = requests.get(
                f"{self.base_url}/subscriptions/{subscription_id}/resourceGroups/{name}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Resource group '{name}' not found in subscription {subscription_id}")
                return None
            else:
                print(f"Error getting resource group: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def list_resource_groups(self, subscription_id: str = None) -> Optional[Dict]:
        """
        List resource groups, optionally filtered by subscription.
        
        Args:
            subscription_id: Optional subscription ID to filter by
            
        Returns:
            Dictionary with resource groups list
        """
        try:
            if subscription_id:
                url = f"{self.base_url}/subscriptions/{subscription_id}/resourceGroups"
            else:
                url = f"{self.base_url}/providers/ITL.Core/resourcegroups"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error listing resource groups: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_resource_group(self, subscription_id: str, name: str) -> bool:
        """
        Delete a resource group from a subscription.
        
        Args:
            subscription_id: Subscription ID
            name: Resource group name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.base_url}/subscriptions/{subscription_id}/resourceGroups/{name}",
                headers=self.headers,
                timeout=30
            )
            
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    # ==================== DEPLOYMENTS ====================
    
    def list_deployments(self, subscription_id: str = None, resource_group: str = None) -> Optional[Dict]:
        """List deployments"""
        try:
            url = f"{self.base_url}/deployments"
            params = []
            if subscription_id:
                params.append(f"subscription_id={subscription_id}")
            if resource_group:
                params.append(f"resource_group={resource_group}")
            
            if params:
                url += "?" + "&".join(params)
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_deployment(self,
                         subscription_id: str,
                         resource_group: str,
                         resource_name: str,
                         deployment_body: Dict[str, Any],
                         location: str = 'global') -> Optional[Dict]:
        """Create a deployment"""
        try:
            payload = {
                'subscription_id': subscription_id,
                'resource_group': resource_group,
                'resource_name': resource_name,
                'resource_type': 'deployments',
                'location': location,
                'body': deployment_body
            }
            
            response = requests.post(
                f"{self.base_url}/deployments",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error creating deployment: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_deployment(self, deployment_name: str, subscription_id: str = None, resource_group: str = None) -> Optional[Dict]:
        """Get specific deployment"""
        try:
            url = f"{self.base_url}/deployments/{deployment_name}"
            params = []
            if subscription_id:
                params.append(f"subscription_id={subscription_id}")
            if resource_group:
                params.append(f"resource_group={resource_group}")
            
            if params:
                url += "?" + "&".join(params)
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def delete_deployment(self, deployment_name: str, subscription_id: str = None, resource_group: str = None) -> bool:
        """Delete deployment"""
        try:
            url = f"{self.base_url}/deployments/{deployment_name}"
            params = []
            if subscription_id:
                params.append(f"subscription_id={subscription_id}")
            if resource_group:
                params.append(f"resource_group={resource_group}")
            
            if params:
                url += "?" + "&".join(params)
            
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=30
            )
            return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"Error: {e}")
            return False
