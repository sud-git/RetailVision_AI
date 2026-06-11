#!/usr/bin/env python3
"""
PHASE 5 Backend Platform - Integration Test Suite

Tests all Phase 5 components:
- Database models and repositories
- REST APIs
- Redis consumer
- WebSocket
- Security
"""

import asyncio
import json
import sys
from datetime import datetime
import uuid
from typing import Dict, Any

import httpx
import websockets


# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "demo-key-12345"
WS_URL = "ws://localhost:8000/ws"

# Test results
TESTS_PASSED = 0
TESTS_FAILED = 0


def print_header(text: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test(name: str, status: bool, details: str = ""):
    """Print test result."""
    global TESTS_PASSED, TESTS_FAILED
    
    status_str = "✓ PASS" if status else "✗ FAIL"
    color = "\033[92m" if status else "\033[91m"  # Green or Red
    reset = "\033[0m"
    
    print(f"{color}[{status_str}]{reset} {name}")
    if details:
        print(f"       {details}")
    
    if status:
        TESTS_PASSED += 1
    else:
        TESTS_FAILED += 1


def headers() -> Dict[str, str]:
    """Get request headers with API key."""
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}


async def test_health_check():
    """Test health check endpoint."""
    print_header("Testing Health Check")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_test(
                    "Health Check",
                    True,
                    f"Status: {data.get('status')}, Redis: {data.get('redis')}"
                )
                return True
            else:
                print_test("Health Check", False, f"Status code: {response.status_code}")
                return False
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False


async def test_analytics_api():
    """Test analytics API endpoints."""
    print_header("Testing Analytics API")
    
    async with httpx.AsyncClient() as client:
        # Test overview
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/analytics/overview",
                headers=headers()
            )
            print_test(
                "GET /api/v1/analytics/overview",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/analytics/overview", False, str(e))
        
        # Test interactions
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/analytics/interactions",
                headers=headers()
            )
            print_test(
                "GET /api/v1/analytics/interactions",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/analytics/interactions", False, str(e))


async def test_events_api():
    """Test events API endpoints."""
    print_header("Testing Events API")
    
    async with httpx.AsyncClient() as client:
        # Test recent events
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/events/recent",
                headers=headers()
            )
            print_test(
                "GET /api/v1/events/recent",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/events/recent", False, str(e))
        
        # Test all events
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/events?hours=24",
                headers=headers()
            )
            print_test(
                "GET /api/v1/events?hours=24",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/events?hours=24", False, str(e))


async def test_system_api():
    """Test system API endpoints."""
    print_header("Testing System API")
    
    async with httpx.AsyncClient() as client:
        # Test health
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/system/health",
                headers=headers()
            )
            print_test(
                "GET /api/v1/system/health",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/system/health", False, str(e))
        
        # Test metrics
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/system/metrics",
                headers=headers()
            )
            print_test(
                "GET /api/v1/system/metrics",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/system/metrics", False, str(e))
        
        # Test status
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/system/status",
                headers=headers()
            )
            print_test(
                "GET /api/v1/system/status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/system/status", False, str(e))


async def test_customers_api():
    """Test customers API endpoints."""
    print_header("Testing Customers API")
    
    async with httpx.AsyncClient() as client:
        # Test list customers
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/customers",
                headers=headers()
            )
            print_test(
                "GET /api/v1/customers",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/customers", False, str(e))
        
        # Test create customer
        try:
            customer_data = {
                "first_name": "John",
                "last_name": "Doe",
                "email": f"test{uuid.uuid4()}@example.com",
                "external_id": f"ext_{uuid.uuid4()}"
            }
            response = await client.post(
                f"{BASE_URL}/api/v1/customers",
                json=customer_data,
                headers=headers()
            )
            print_test(
                "POST /api/v1/customers",
                response.status_code in [200, 201],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("POST /api/v1/customers", False, str(e))


async def test_alerts_api():
    """Test alerts API endpoints."""
    print_header("Testing Alerts API")
    
    async with httpx.AsyncClient() as client:
        # Test list alerts
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/alerts",
                headers=headers()
            )
            print_test(
                "GET /api/v1/alerts",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/alerts", False, str(e))
        
        # Test critical alerts
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/alerts/critical",
                headers=headers()
            )
            print_test(
                "GET /api/v1/alerts/critical",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("GET /api/v1/alerts/critical", False, str(e))


async def test_security():
    """Test security features."""
    print_header("Testing Security")
    
    async with httpx.AsyncClient() as client:
        # Test missing API key
        try:
            response = await client.get(f"{BASE_URL}/api/v1/analytics/overview")
            print_test(
                "Missing API Key (should be 401)",
                response.status_code == 401,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("Missing API Key", False, str(e))
        
        # Test invalid API key
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/analytics/overview",
                headers={"X-API-Key": "invalid-key"}
            )
            print_test(
                "Invalid API Key (should be 403)",
                response.status_code == 403,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            print_test("Invalid API Key", False, str(e))


async def test_websocket():
    """Test WebSocket connection."""
    print_header("Testing WebSocket")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Send ping
            await websocket.send("ping")
            
            # Receive pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            print_test(
                "WebSocket Connection",
                data.get("type") == "pong",
                f"Received: {data}"
            )
            
            # Test subscription
            await websocket.send("subscribe:events")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            print_test(
                "WebSocket Subscription",
                data.get("channel") == "events",
                f"Channel: {data.get('channel')}"
            )
    
    except Exception as e:
        print_test("WebSocket Connection", False, str(e))


async def test_cors():
    """Test CORS headers."""
    print_header("Testing CORS")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.options(
                f"{BASE_URL}/api/v1/analytics/overview",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            has_cors = "access-control-allow-origin" in response.headers
            print_test(
                "CORS Headers",
                has_cors,
                f"CORS enabled: {has_cors}"
            )
    except Exception as e:
        print_test("CORS Headers", False, str(e))


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  RetailVision AI - PHASE 5 Backend Integration Tests")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"WebSocket URL: {WS_URL}")
    print(f"Test API Key: {API_KEY}")
    
    # Run all tests
    await test_health_check()
    await test_analytics_api()
    await test_events_api()
    await test_system_api()
    await test_customers_api()
    await test_alerts_api()
    await test_security()
    await test_cors()
    await test_websocket()
    
    # Summary
    print_header("Test Summary")
    total = TESTS_PASSED + TESTS_FAILED
    percentage = (TESTS_PASSED / total * 100) if total > 0 else 0
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {TESTS_PASSED}")
    print(f"Failed: {TESTS_FAILED}")
    print(f"Success Rate: {percentage:.1f}%")
    
    if TESTS_FAILED == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {TESTS_FAILED} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
