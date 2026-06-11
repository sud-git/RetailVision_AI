#!/usr/bin/env python3
"""
End-to-End Test Suite for RetailVision AI
Tests all services and endpoints to validate localhost setup
"""

import sys
import time
import json
import requests
import asyncio
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
API_TIMEOUT = 10

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.response_time = 0
        self.details = {}

class EndToEndTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None

    def print_header(self, text: str) -> None:
        """Print formatted header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    def print_test(self, test_name: str) -> None:
        """Print test name."""
        print(f"{Colors.BLUE}Testing: {test_name}...{Colors.RESET}", end=" ")

    def print_result(self, result: TestResult) -> None:
        """Print test result."""
        if result.passed:
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET}")
            if result.response_time > 0:
                print(f"  Response time: {result.response_time:.2f}ms")
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET}")
            if result.error:
                print(f"  Error: {result.error}")

    async def test_backend_connectivity(self) -> TestResult:
        """Test backend connectivity."""
        result = TestResult("Backend Connectivity")
        self.print_test("Backend Connectivity")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/ping", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                result.passed = True
                result.details = response.json()
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_health_check(self) -> TestResult:
        """Test health check endpoint."""
        result = TestResult("Health Check")
        self.print_test("Health Check")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                result.details = data
                
                # Check critical services
                critical_healthy = all([
                    data.get("database", {}).get("healthy", False),
                    data.get("redis", {}).get("healthy", False),
                ])
                
                if critical_healthy:
                    result.passed = True
                else:
                    result.error = "Critical services not healthy"
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_diagnostics(self) -> TestResult:
        """Test diagnostics endpoint."""
        result = TestResult("Diagnostics Endpoint")
        self.print_test("Diagnostics Endpoint")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/api/v1/diagnostics", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                result.passed = True
                data = response.json()
                result.details = {
                    "overall_healthy": data.get("system_status", {}).get("overall_healthy"),
                    "uptime": data.get("system_status", {}).get("uptime_seconds"),
                }
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_database_service(self) -> TestResult:
        """Test database connectivity through API."""
        result = TestResult("Database Service")
        self.print_test("Database Service")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                db_status = data.get("database", {})
                
                if db_status.get("healthy"):
                    result.passed = True
                    result.details = {
                        "response_time_ms": db_status.get("response_time_ms"),
                        "message": db_status.get("message"),
                    }
                else:
                    result.error = db_status.get("message", "Database unhealthy")
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_redis_service(self) -> TestResult:
        """Test Redis connectivity through API."""
        result = TestResult("Redis Service")
        self.print_test("Redis Service")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                redis_status = data.get("redis", {})
                
                if redis_status.get("healthy"):
                    result.passed = True
                    result.details = {
                        "response_time_ms": redis_status.get("response_time_ms"),
                        "message": redis_status.get("message"),
                    }
                else:
                    result.error = redis_status.get("message", "Redis unhealthy")
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_api_docs(self) -> TestResult:
        """Test API documentation endpoint."""
        result = TestResult("API Documentation")
        self.print_test("API Documentation")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/docs", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                result.passed = True
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_frontend_connectivity(self) -> TestResult:
        """Test frontend connectivity."""
        result = TestResult("Frontend Connectivity")
        self.print_test("Frontend Connectivity")

        try:
            start = time.time()
            response = requests.get(FRONTEND_URL, timeout=API_TIMEOUT, allow_redirects=True)
            result.response_time = (time.time() - start) * 1000

            if response.status_code == 200:
                result.passed = True
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_anomalies_endpoint(self) -> TestResult:
        """Test anomalies API endpoint."""
        result = TestResult("Anomalies Endpoint")
        self.print_test("Anomalies Endpoint")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/api/v1/anomalies/active", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code in [200, 404]:
                result.passed = True
                result.details = {"status_code": response.status_code}
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    async def test_alerts_endpoint(self) -> TestResult:
        """Test alerts API endpoint."""
        result = TestResult("Alerts Endpoint")
        self.print_test("Alerts Endpoint")

        try:
            start = time.time()
            response = requests.get(f"{BACKEND_URL}/api/v1/alerts", timeout=API_TIMEOUT)
            result.response_time = (time.time() - start) * 1000

            if response.status_code in [200, 404]:
                result.passed = True
                result.details = {"status_code": response.status_code}
            else:
                result.error = f"Status code: {response.status_code}"
        except Exception as e:
            result.error = str(e)

        self.print_result(result)
        self.results.append(result)
        return result

    def print_summary(self) -> None:
        """Print test summary."""
        self.print_header("Test Summary")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        elapsed = time.time() - self.start_time

        print(f"Total Tests: {total}")
        print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
        print(f"Success Rate: {Colors.YELLOW}{(passed/total*100):.1f}%{Colors.RESET}")
        print(f"Duration: {elapsed:.2f}s")

        if failed > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
            for result in self.results:
                if not result.passed:
                    print(f"  • {result.name}: {result.error}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}Test Run Complete{Colors.RESET}")

    async def run_all_tests(self) -> bool:
        """Run all tests."""
        self.start_time = time.time()
        self.print_header("RetailVision AI - End-to-End Test Suite")

        print(f"{Colors.YELLOW}Backend URL:{Colors.RESET} {BACKEND_URL}")
        print(f"{Colors.YELLOW}Frontend URL:{Colors.RESET} {FRONTEND_URL}")
        print()

        # Core connectivity tests
        self.print_header("Core Connectivity Tests")
        await self.test_backend_connectivity()
        await self.test_frontend_connectivity()

        # Health & diagnostics tests
        self.print_header("Health & Diagnostics Tests")
        await self.test_health_check()
        await self.test_diagnostics()
        await self.test_database_service()
        await self.test_redis_service()

        # API tests
        self.print_header("API Endpoint Tests")
        await self.test_api_docs()
        await self.test_anomalies_endpoint()
        await self.test_alerts_endpoint()

        # Print summary
        self.print_summary()

        # Return success if all tests passed
        return all(r.passed for r in self.results)


async def main():
    """Main entry point."""
    tester = EndToEndTester()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
