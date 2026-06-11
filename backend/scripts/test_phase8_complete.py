"""
Phase 8: Complete Anomaly Detection & Alert System Tests

Comprehensive testing for:
- Anomaly detection
- Risk scoring  
- Alert generation
- API endpoints
- Alert management
"""

import asyncio
import json
from datetime import datetime, timedelta
import requests
import time


BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "X-API-Key": "test-key"}


# ==================== TEST DATA ====================

def get_sample_customers():
    """Sample customer data for testing"""
    return [
        {
            "customer_id": "cust_001",
            "zone_id": 1,
            "dwell_time": 400000,  # 400 seconds - will trigger loitering
            "interaction_count": 8,
            "zones_visited": [1, 2, 1, 3, 1]
        },
        {
            "customer_id": "cust_002",
            "zone_id": 2,
            "dwell_time": 50000,  # Normal
            "interaction_count": 2,
            "zones_visited": [2, 3]
        }
    ]


def get_sample_zone_occupancies():
    """Sample zone occupancy data"""
    return {
        1: 25,  # Exceeds threshold of 20
        2: 15,  # Normal
        3: 18   # Normal
    }


def get_sample_objects():
    """Sample object data for abandoned object detection"""
    return [
        {
            "object_id": "obj_001",
            "zone_id": 1,
            "x": 100.0,
            "y": 150.0,
            "timestamp": datetime.utcnow() - timedelta(seconds=35)
        }
    ]


# ==================== ANOMALY DETECTION TESTS ====================

def test_get_active_anomalies():
    """Test: Get active anomalies"""
    print("\n📋 TEST: Get Active Anomalies")
    try:
        response = requests.get(
            f"{BASE_URL}/anomalies/active",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Active anomalies: {data.get('data', {}).get('count', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_get_anomaly_history():
    """Test: Get anomaly history"""
    print("\n📋 TEST: Get Anomaly History")
    try:
        now = datetime.utcnow()
        start_date = (now - timedelta(hours=24)).isoformat()
        end_date = now.isoformat()
        
        response = requests.get(
            f"{BASE_URL}/anomalies/history",
            params={
                "start_date": start_date,
                "end_date": end_date
            },
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Historical anomalies: {data.get('data', {}).get('total', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_anomaly_by_type():
    """Test: Get anomalies by type"""
    print("\n📋 TEST: Anomalies by Type")
    try:
        response = requests.get(
            f"{BASE_URL}/anomalies/by-type/loitering",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Loitering anomalies: {data.get('data', {}).get('count', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


# ==================== ALERT TESTS ====================

def test_get_active_alerts():
    """Test: Get active alerts"""
    print("\n📋 TEST: Get Active Alerts")
    try:
        response = requests.get(
            f"{BASE_URL}/alerts/active",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Active alerts: {data.get('data', {}).get('total', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_get_all_alerts():
    """Test: Get all alerts"""
    print("\n📋 TEST: Get All Alerts")
    try:
        response = requests.get(
            f"{BASE_URL}/alerts",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Total alerts: {data.get('data', {}).get('total', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_alert_acknowledgment():
    """Test: Acknowledge alert"""
    print("\n📋 TEST: Acknowledge Alert")
    try:
        # First get an alert
        response = requests.get(
            f"{BASE_URL}/alerts/active",
            headers=HEADERS
        )
        
        if response.status_code != 200:
            print("✗ Could not retrieve alerts")
            return False
        
        alerts = response.json().get('data', {}).get('alerts', [])
        if not alerts:
            print("⚠ No active alerts to acknowledge")
            return True
        
        alert_id = alerts[0]['id']
        
        # Acknowledge the alert
        ack_response = requests.post(
            f"{BASE_URL}/alerts/{alert_id}/acknowledge",
            json={
                "acknowledged_by": "test_user",
                "action_taken": "Investigated and resolved",
                "notes": "Customer issue addressed"
            },
            headers=HEADERS
        )
        
        print(f"✓ Status: {ack_response.status_code}")
        print(f"✓ Alert acknowledged: {alert_id}")
        return ack_response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_get_alert_history():
    """Test: Get alert history"""
    print("\n📋 TEST: Get Alert History")
    try:
        response = requests.get(
            f"{BASE_URL}/alerts/history",
            params={"limit": 10},
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Historical alerts: {data.get('data', {}).get('total', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


# ==================== RISK SCORING TESTS ====================

def test_customer_risk_score():
    """Test: Get customer risk score"""
    print("\n📋 TEST: Customer Risk Score")
    try:
        response = requests.get(
            f"{BASE_URL}/risk-scores/customer/cust_001",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        risk_data = data.get('data', {})
        print(f"✓ Customer risk score: {risk_data.get('risk_score', 0):.2f}")
        print(f"✓ Risk level: {risk_data.get('risk_level', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_zone_risk_score():
    """Test: Get zone risk score"""
    print("\n📋 TEST: Zone Risk Score")
    try:
        response = requests.get(
            f"{BASE_URL}/risk-scores/zone/1",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        risk_data = data.get('data', {})
        print(f"✓ Zone risk score: {risk_data.get('risk_score', 0):.2f}")
        print(f"✓ Zone risk level: {risk_data.get('risk_level', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_top_risk_zones():
    """Test: Get top risk zones"""
    print("\n📋 TEST: Top Risk Zones")
    try:
        response = requests.get(
            f"{BASE_URL}/risk-scores/top-zones",
            params={"limit": 5},
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        zones = data.get('data', {}).get('zones', [])
        print(f"✓ Top risk zones count: {len(zones)}")
        for zone in zones[:3]:
            print(f"  - Zone {zone.get('zone_id')}: risk={zone.get('risk_score', 0):.2f}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


# ==================== STATISTICS TESTS ====================

def test_alert_statistics():
    """Test: Get alert statistics"""
    print("\n📋 TEST: Alert Statistics")
    try:
        response = requests.get(
            f"{BASE_URL}/statistics/alerts",
            params={"days": 1},
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json().get('data', {})
        print(f"✓ Total alerts (24h): {data.get('total_alerts', 0)}")
        print(f"✓ Critical alerts: {data.get('critical_alerts', 0)}")
        print(f"✓ High alerts: {data.get('high_alerts', 0)}")
        print(f"✓ Acknowledged: {data.get('acknowledged_count', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_anomaly_statistics():
    """Test: Get anomaly statistics"""
    print("\n📋 TEST: Anomaly Statistics")
    try:
        response = requests.get(
            f"{BASE_URL}/statistics/anomalies",
            params={"days": 1},
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json().get('data', {})
        print(f"✓ Total anomalies: {data.get('total_anomalies', 0)}")
        print(f"✓ Loitering: {data.get('loitering_count', 0)}")
        print(f"✓ Crowd: {data.get('crowd_count', 0)}")
        print(f"✓ Suspicious: {data.get('suspicious_count', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_dashboard_summary():
    """Test: Get dashboard summary"""
    print("\n📋 TEST: Dashboard Summary")
    try:
        response = requests.get(
            f"{BASE_URL}/statistics/dashboard",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json().get('data', {})
        print(f"✓ Active alerts: {data.get('active_alerts_count', 0)}")
        print(f"✓ Critical alerts: {data.get('critical_alerts_count', 0)}")
        print(f"✓ Zones affected: {data.get('alert_statistics', {}).get('zones_affected', 0)}")
        print(f"✓ Customers involved: {data.get('alert_statistics', {}).get('customers_involved', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


# ==================== ZONE PROFILE TESTS ====================

def test_create_zone_profile():
    """Test: Create/update zone profile"""
    print("\n📋 TEST: Create Zone Profile")
    try:
        response = requests.post(
            f"{BASE_URL}/zones/1/profile",
            json={
                "zone_id": 1,
                "zone_type": "high_value",
                "is_restricted": False,
                "max_occupancy": 25,
                "normal_occupancy": 8,
                "loitering_threshold": 300,
                "interaction_threshold": 5
            },
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Zone profile configured")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_get_zone_profile():
    """Test: Get zone profile"""
    print("\n📋 TEST: Get Zone Profile")
    try:
        response = requests.get(
            f"{BASE_URL}/zones/1/profile",
            headers=HEADERS
        )
        print(f"✓ Status: {response.status_code}")
        data = response.json().get('data', {})
        print(f"✓ Zone type: {data.get('zone_type', 'N/A')}")
        print(f"✓ Max occupancy: {data.get('max_occupancy', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    """Run all Phase 8 tests"""
    print("\n" + "="*60)
    print("PHASE 8: ANOMALY DETECTION & ALERT SYSTEM")
    print("Comprehensive Testing Suite")
    print("="*60)
    
    tests = [
        # Anomaly tests
        ("Active Anomalies", test_get_active_anomalies),
        ("Anomaly History", test_get_anomaly_history),
        ("Anomalies by Type", test_anomaly_by_type),
        
        # Alert tests
        ("Active Alerts", test_get_active_alerts),
        ("All Alerts", test_get_all_alerts),
        ("Alert Acknowledgment", test_alert_acknowledgment),
        ("Alert History", test_get_alert_history),
        
        # Risk scoring tests
        ("Customer Risk Score", test_customer_risk_score),
        ("Zone Risk Score", test_zone_risk_score),
        ("Top Risk Zones", test_top_risk_zones),
        
        # Statistics tests
        ("Alert Statistics", test_alert_statistics),
        ("Anomaly Statistics", test_anomaly_statistics),
        ("Dashboard Summary", test_dashboard_summary),
        
        # Zone profile tests
        ("Create Zone Profile", test_create_zone_profile),
        ("Get Zone Profile", test_get_zone_profile),
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "PASSED" if result else "FAILED"
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Exception in {test_name}: {str(e)}")
            results[test_name] = "ERROR"
            failed += 1
        
        time.sleep(0.5)  # Rate limiting
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"Total: {passed + failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✓" if result == "PASSED" else "✗"
        print(f"{status} {test_name}: {result}")
    
    return results


if __name__ == "__main__":
    print("\nWaiting for backend to be ready...")
    time.sleep(2)
    
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", headers=HEADERS)
        if response.status_code == 200:
            print("✓ Backend is ready!")
            run_all_tests()
        else:
            print("✗ Backend is not responding correctly")
    except:
        print("✗ Could not connect to backend. Make sure it's running on localhost:8000")
