#!/usr/bin/env python3
"""
Bulk Data Ingestion with Client/Identity Tracking

This script ingests test data into the Control Plane API while tracking
which Keycloak client/identity created each resource for audit purposes.

Features:
- Bulk create subscriptions, resource groups, and deployments
- Extract and store Keycloak client identity (client_id, user_id, tenant)
- Create audit trail with timestamps and creator info
- Support for multiple Keycloak clients/tenants
- Dry-run mode for validation
"""

import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Add ITLAuth to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from itlc.controlplane_client import ControlPlaneClient


class ClientTrackingAuditLog:
    """Manages audit trail for resources created by specific clients"""
    
    def __init__(self, log_file: str = "resource_audit_trail.json"):
        self.log_file = Path(log_file)
        self.entries = self._load_entries()
    
    def _load_entries(self) -> List[Dict[str, Any]]:
        """Load existing audit entries"""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []
    
    def record_resource(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        client_id: str,
        user_id: Optional[str],
        tenant_id: Optional[str],
        subscription_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Record a resource creation by a specific client"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "resource": {
                "id": resource_id,
                "name": resource_name,
                "type": resource_type,
                "subscription_id": subscription_id,
            },
            "creator": {
                "client_id": client_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
            },
            "metadata": metadata or {},
        }
        self.entries.append(entry)
        self._save_entries()
    
    def _save_entries(self) -> None:
        """Save audit entries to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.entries, f, indent=2)
    
    def get_resources_by_client(self, client_id: str) -> List[Dict]:
        """Get all resources created by a specific client"""
        return [e for e in self.entries if e["creator"]["client_id"] == client_id]
    
    def get_resources_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Get all resources created by a specific tenant"""
        return [e for e in self.entries if e["creator"]["tenant_id"] == tenant_id]
    
    def get_resources_by_user(self, user_id: str) -> List[Dict]:
        """Get all resources created by a specific user"""
        return [e for e in self.entries if e["creator"]["user_id"] == user_id]


class BulkDataIngestion:
    """Bulk data ingestion with client tracking"""
    
    def __init__(self, api_url: str, token: Optional[str] = None, dry_run: bool = False):
        self.client = ControlPlaneClient(base_url=api_url, access_token=token)
        self.audit_log = ClientTrackingAuditLog()
        self.dry_run = dry_run
        self.created_resources = []
    
    def ingest_subscriptions(
        self,
        client_id: str,
        subscription_specs: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[str]:
        """Ingest multiple subscriptions for a client"""
        subscription_ids = []
        
        for spec in subscription_specs:
            name = spec.get("name", f"sub-{uuid.uuid4().hex[:8]}")
            display_name = spec.get("display_name", name)
            
            print(f"  Creating subscription: {name} (client: {client_id})")
            
            if not self.dry_run:
                try:
                    response = self.client.create_subscription(
                        resource_name=name,
                        resource_group="default",
                        location="eastus",
                        display_name=display_name
                    )
                    
                    sub_id = response.get("id", "")
                    resource_guid = response.get("resource_guid", "")
                    
                    # Record in audit log
                    self.audit_log.record_resource(
                        resource_id=sub_id,
                        resource_name=name,
                        resource_type="subscription",
                        client_id=client_id,
                        user_id=user_id,
                        tenant_id=tenant_id,
                        metadata={
                            "display_name": display_name,
                            "resource_guid": resource_guid,
                        }
                    )
                    
                    subscription_ids.append(sub_id)
                    self.created_resources.append({
                        "type": "subscription",
                        "id": sub_id,
                        "name": name,
                        "client_id": client_id,
                    })
                    print(f"    [+] Created: {sub_id}")
                
                except Exception as e:
                    print(f"    [ERROR] {str(e)}")
            else:
                print(f"    [DRY RUN] Would create subscription: {name}")
                subscription_ids.append(f"/subscriptions/{name}")
        
        return subscription_ids
    
    def ingest_resource_groups(
        self,
        client_id: str,
        subscription_id: str,
        rg_specs: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[str]:
        """Ingest resource groups for a subscription by a specific client"""
        rg_ids = []
        
        for spec in rg_specs:
            name = spec.get("name", f"rg-{uuid.uuid4().hex[:8]}")
            location = spec.get("location", "eastus")
            
            print(f"  Creating resource group: {name} (client: {client_id})")
            
            if not self.dry_run:
                try:
                    response = self.client.create_resource_group(
                        subscription_id=subscription_id,
                        resource_name=name,
                        location=location
                    )
                    
                    rg_id = response.get("id", "")
                    
                    # Record in audit log
                    self.audit_log.record_resource(
                        resource_id=rg_id,
                        resource_name=name,
                        resource_type="resourcegroup",
                        client_id=client_id,
                        user_id=user_id,
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        metadata={"location": location}
                    )
                    
                    rg_ids.append(rg_id)
                    self.created_resources.append({
                        "type": "resourcegroup",
                        "id": rg_id,
                        "name": name,
                        "client_id": client_id,
                        "subscription_id": subscription_id,
                    })
                    print(f"    [+] Created: {rg_id}")
                
                except Exception as e:
                    print(f"    [ERROR] {str(e)}")
            else:
                print(f"    [DRY RUN] Would create resource group: {name}")
                rg_ids.append(f"{subscription_id}/resourceGroups/{name}")
        
        return rg_ids
    
    def print_summary(self) -> None:
        """Print ingestion summary"""
        print("\n" + "="*60)
        print("BULK INGESTION SUMMARY")
        print("="*60 + "\n")
        
        if self.dry_run:
            print("[DRY RUN MODE] No resources were actually created\n")
        
        print(f"Total Resources Processed: {len(self.created_resources)}")
        
        # Group by type
        by_type = {}
        for resource in self.created_resources:
            rtype = resource["type"]
            if rtype not in by_type:
                by_type[rtype] = []
            by_type[rtype].append(resource)
        
        for rtype, resources in sorted(by_type.items()):
            print(f"\n{rtype.upper()} ({len(resources)})")
            for resource in resources:
                client = resource.get("client_id", "N/A")
                print(f"  - {resource['name']:<30} [client: {client}]")
        
        # Show audit trail
        if not self.dry_run and self.created_resources:
            print("\n=== Resource Audit Trail ===\n")
            by_client = {}
            for entry in self.audit_log.entries:
                client = entry["creator"]["client_id"]
                if client not in by_client:
                    by_client[client] = []
                by_client[client].append(entry)
            
            for client_id in sorted(by_client.keys()):
                resources = by_client[client_id]
                print(f"Client: {client_id}")
                print(f"  Total Resources: {len(resources)}")
                for r in resources:
                    print(f"    - {r['resource']['type']}: {r['resource']['name']} ({r['timestamp']})")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Bulk ingest test data with client tracking"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Control Plane API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--token",
        help="Bearer token for authentication (optional)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't create resources"
    )
    parser.add_argument(
        "--scenario",
        choices=["simple", "multi-tenant", "load-test"],
        default="simple",
        help="Ingestion scenario (default: simple)"
    )
    
    args = parser.parse_args()
    
    ingestion = BulkDataIngestion(
        api_url=args.api_url,
        token=args.token,
        dry_run=args.dry_run
    )
    
    print("\n" + "="*60)
    print("BULK DATA INGESTION WITH CLIENT TRACKING")
    print("="*60 + "\n")
    
    if args.scenario == "simple":
        print("Scenario: Simple ingestion (1 client, 2 subscriptions, 2 RGs each)\n")
        print("Client: frontend-app (tenant: acme)")
        sub_ids = ingestion.ingest_subscriptions(
            client_id="frontend-app",
            tenant_id="acme",
            user_id="alice@acme.com",
            subscription_specs=[
                {"name": "frontend-prod", "display_name": "Frontend Production"},
                {"name": "frontend-dev", "display_name": "Frontend Development"},
            ]
        )
        
        for sub_id in sub_ids:
            ingestion.ingest_resource_groups(
                client_id="frontend-app",
                tenant_id="acme",
                user_id="alice@acme.com",
                subscription_id=sub_id,
                rg_specs=[
                    {"name": "compute", "location": "eastus"},
                    {"name": "storage", "location": "eastus"},
                ]
            )
    
    elif args.scenario == "multi-tenant":
        print("Scenario: Multi-tenant ingestion (3 clients, 2 tenants)\n")
        print("Tenant: acme\n")
        
        print("  Client: api-gateway (user: bob@acme.com)")
        sub_ids_1 = ingestion.ingest_subscriptions(
            client_id="api-gateway",
            tenant_id="acme",
            user_id="bob@acme.com",
            subscription_specs=[
                {"name": "api-prod", "display_name": "API Production"},
                {"name": "api-staging", "display_name": "API Staging"},
            ]
        )
        
        for sub_id in sub_ids_1:
            ingestion.ingest_resource_groups(
                client_id="api-gateway",
                tenant_id="acme",
                user_id="bob@acme.com",
                subscription_id=sub_id,
                rg_specs=[
                    {"name": "gateway", "location": "westeurope"},
                    {"name": "integration", "location": "westeurope"},
                ]
            )
        
        print("\n  Client: db-manager (user: charlie@acme.com)")
        sub_ids_2 = ingestion.ingest_subscriptions(
            client_id="db-manager",
            tenant_id="acme",
            user_id="charlie@acme.com",
            subscription_specs=[
                {"name": "db-prod", "display_name": "Database Production"},
            ]
        )
        
        for sub_id in sub_ids_2:
            ingestion.ingest_resource_groups(
                client_id="db-manager",
                tenant_id="acme",
                user_id="charlie@acme.com",
                subscription_id=sub_id,
                rg_specs=[
                    {"name": "primary", "location": "eastus"},
                    {"name": "replica", "location": "westeurope"},
                ]
            )
        
        print("\nTenant: global-systems\n")
        print("  Client: platform-admin (user: diana@global-systems.com)")
        sub_ids_3 = ingestion.ingest_subscriptions(
            client_id="platform-admin",
            tenant_id="global-systems",
            user_id="diana@global-systems.com",
            subscription_specs=[
                {"name": "platform-core", "display_name": "Platform Core"},
            ]
        )
        
        for sub_id in sub_ids_3:
            ingestion.ingest_resource_groups(
                client_id="platform-admin",
                tenant_id="global-systems",
                user_id="diana@global-systems.com",
                subscription_id=sub_id,
                rg_specs=[
                    {"name": "infrastructure", "location": "centralus"},
                    {"name": "monitoring", "location": "centralus"},
                ]
            )
    
    elif args.scenario == "load-test":
        print("Scenario: Load test (10 clients, 5 subscriptions each)\n")
        
        for client_num in range(1, 11):
            client_id = f"service-client-{client_num:02d}"
            tenant_id = "load-test-tenant"
            user_id = f"user{client_num}@load-test.com"
            
            print(f"Client: {client_id} (user: {user_id})")
            
            sub_ids = ingestion.ingest_subscriptions(
                client_id=client_id,
                tenant_id=tenant_id,
                user_id=user_id,
                subscription_specs=[
                    {
                        "name": f"{client_id}-sub-{i}",
                        "display_name": f"Subscription {i+1} for {client_id}"
                    }
                    for i in range(5)
                ]
            )
            
            for i, sub_id in enumerate(sub_ids):
                ingestion.ingest_resource_groups(
                    client_id=client_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    subscription_id=sub_id,
                    rg_specs=[
                        {
                            "name": f"rg-{j}",
                            "location": ["eastus", "westus", "centralus", "northeurope"][j % 4]
                        }
                        for j in range(3)
                    ]
                )
            print()
    
    ingestion.print_summary()


if __name__ == "__main__":
    main()
