"""
Phase 8: Setup Zone Profiles Script
Initialize retail zones with anomaly detection thresholds
"""

import asyncio
import json
from datetime import datetime
import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Default zone profiles for different types
ZONE_TEMPLATES = {
    "high_value": {
        "zone_type": "high_value",
        "is_restricted": False,
        "max_occupancy": 15,
        "normal_occupancy": 5,
        "loitering_threshold": 180,  # 3 minutes - more strict for valuable areas
        "interaction_threshold": 3,  # Fewer interactions tolerated
        "rapid_switch_threshold": 2,
        "occupancy_weight": 0.40,
        "interaction_weight": 0.35,
        "anomaly_weight": 0.25
    },
    "general": {
        "zone_type": "general",
        "is_restricted": False,
        "max_occupancy": 25,
        "normal_occupancy": 10,
        "loitering_threshold": 300,  # 5 minutes - normal threshold
        "interaction_threshold": 5,
        "rapid_switch_threshold": 3,
        "occupancy_weight": 0.35,
        "interaction_weight": 0.25,
        "anomaly_weight": 0.40
    },
    "checkout": {
        "zone_type": "checkout",
        "is_restricted": False,
        "max_occupancy": 30,
        "normal_occupancy": 8,
        "loitering_threshold": 120,  # 2 minutes - short, it's checkout
        "interaction_threshold": 2,
        "rapid_switch_threshold": 4,
        "occupancy_weight": 0.30,
        "interaction_weight": 0.20,
        "anomaly_weight": 0.50
    },
    "entrance": {
        "zone_type": "entrance",
        "is_restricted": False,
        "max_occupancy": 20,
        "normal_occupancy": 5,
        "loitering_threshold": 60,  # 1 minute - people shouldn't linger at entrance
        "interaction_threshold": 1,
        "rapid_switch_threshold": 2,
        "occupancy_weight": 0.30,
        "interaction_weight": 0.15,
        "anomaly_weight": 0.55
    },
    "restricted": {
        "zone_type": "restricted",
        "is_restricted": True,
        "max_occupancy": 5,
        "normal_occupancy": 1,
        "loitering_threshold": 30,  # Very strict - should be empty
        "interaction_threshold": 1,
        "rapid_switch_threshold": 1,
        "occupancy_weight": 0.50,
        "interaction_weight": 0.30,
        "anomaly_weight": 0.20
    }
}

async def setup_zone_profiles():
    """Setup default zone profiles"""
    
    print("\n" + "="*60)
    print("PHASE 8: ZONE PROFILE SETUP")
    print("Initialize retail zones with anomaly detection")
    print("="*60)
    
    async with httpx.AsyncClient(headers=HEADERS) as client:
        # Define zones for typical retail store
        zones_config = [
            # Electronics (high-value zone)
            {"zone_id": 1, "template": "high_value", "name": "Electronics"},
            
            # Produce (general shopping)
            {"zone_id": 2, "template": "general", "name": "Produce"},
            
            # Dairy (general shopping)
            {"zone_id": 3, "template": "general", "name": "Dairy"},
            
            # Jewelry (high-value zone)
            {"zone_id": 4, "template": "high_value", "name": "Jewelry"},
            
            # Checkout (checkout zone)
            {"zone_id": 5, "template": "checkout", "name": "Checkout"},
            
            # Entrance/Exit (entrance zone)
            {"zone_id": 6, "template": "entrance", "name": "Entrance"},
            
            # Stockroom (restricted)
            {"zone_id": 10, "template": "restricted", "name": "Stockroom"},
            
            # Manager Office (restricted)
            {"zone_id": 11, "template": "restricted", "name": "Manager Office"},
        ]
        
        created = 0
        failed = 0
        
        for zone_config in zones_config:
            zone_id = zone_config["zone_id"]
            template = zone_config["template"]
            name = zone_config["name"]
            
            # Get template configuration
            profile = ZONE_TEMPLATES[template].copy()
            profile["zone_id"] = zone_id
            
            try:
                print(f"\n📍 Setting up Zone {zone_id} ({name}, type: {template})...")
                
                # Create/update zone profile
                response = await client.post(
                    f"{BASE_URL}/zones/{zone_id}/profile",
                    json=profile
                )
                
                if response.status_code in [200, 201]:
                    print(f"✓ Zone {zone_id} configured:")
                    print(f"  - Max occupancy: {profile['max_occupancy']}")
                    print(f"  - Loitering threshold: {profile['loitering_threshold']}s")
                    print(f"  - Interaction threshold: {profile['interaction_threshold']}")
                    created += 1
                else:
                    print(f"✗ Failed to configure zone {zone_id}: {response.text}")
                    failed += 1
                    
            except Exception as e:
                print(f"✗ Error configuring zone {zone_id}: {str(e)}")
                failed += 1
        
        # Summary
        print("\n" + "="*60)
        print("SETUP SUMMARY")
        print("="*60)
        print(f"✓ Created: {created} zones")
        print(f"✗ Failed: {failed} zones")
        print(f"Total: {created + failed} zones")
        
        if failed == 0:
            print("\n✨ All zones configured successfully!")
            print("\nZone Configuration Reference:")
            print("-" * 60)
            for zone_config in zones_config:
                zone_id = zone_config["zone_id"]
                template = zone_config["template"]
                name = zone_config["name"]
                profile = ZONE_TEMPLATES[template]
                
                print(f"\nZone {zone_id}: {name} ({profile['zone_type']})")
                print(f"  Occupancy: {profile['normal_occupancy']}/{profile['max_occupancy']}")
                print(f"  Loitering: {profile['loitering_threshold']}s")
                print(f"  Interaction: {profile['interaction_threshold']}")
        
        return failed == 0


if __name__ == "__main__":
    try:
        result = asyncio.run(setup_zone_profiles())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Setup failed: {str(e)}")
        sys.exit(1)
