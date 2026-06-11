#!/usr/bin/env python3
"""
PHASE 7 Advanced Analytics Integration Tests

Tests all analytics components:
- Heatmap generation
- Journey analytics
- Zone engagement
- Business insights
- Analytics APIs
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from enum import Enum

class Colors(str, Enum):
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class TestRunner:
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = "demo-key-12345"):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(base_url=api_url, timeout=10)
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    async def run_test(self, name: str, test_fn):
        """Run a single test"""
        print(f"\n▶ Testing: {name}")
        try:
            result = await test_fn()
            if result:
                print(f"  {Colors.GREEN}✓ PASSED{Colors.END} - {name}")
                self.tests_passed += 1
                self.results.append((name, "PASSED", None))
                return True
            else:
                print(f"  {Colors.RED}✗ FAILED{Colors.END} - {name}")
                self.tests_failed += 1
                self.results.append((name, "FAILED", "Test returned False"))
                return False
        except Exception as e:
            print(f"  {Colors.RED}✗ ERROR{Colors.END} - {name}: {str(e)}")
            self.tests_failed += 1
            self.results.append((name, "ERROR", str(e)))
            return False
    
    def get_headers(self):
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}
    
    # ==================== HEATMAP TESTS ====================
    
    async def test_get_latest_heatmap(self):
        """Test GET /analytics/heatmaps/latest"""
        response = await self.client.get(
            "/api/v1/analytics/heatmaps/latest",
            headers=self.get_headers()
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        
        return True
    
    async def test_generate_realtime_heatmap(self):
        """Test POST /analytics/heatmaps/generate (real_time)"""
        response = await self.client.post(
            "/api/v1/analytics/heatmaps/generate",
            headers=self.get_headers(),
            params={"heatmap_type": "real_time"}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        assert "heatmap_id" in data["data"]
        
        print(f"    Generated heatmap ID: {data['data']['heatmap_id']}")
        return True
    
    async def test_get_daily_heatmap(self):
        """Test GET /analytics/heatmaps/daily"""
        today = datetime.utcnow().isoformat()
        response = await self.client.get(
            "/api/v1/analytics/heatmaps/daily",
            headers=self.get_headers(),
            params={"date": today}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        
        return True
    
    async def test_get_hourly_heatmap(self):
        """Test GET /analytics/heatmaps/hourly"""
        today = datetime.utcnow()
        response = await self.client.get(
            "/api/v1/analytics/heatmaps/hourly",
            headers=self.get_headers(),
            params={"date": today.isoformat(), "hour": 14}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        
        return True
    
    # ==================== JOURNEY TESTS ====================
    
    async def test_journey_analytics(self):
        """Test GET /analytics/journeys/analytics"""
        response = await self.client.get(
            "/api/v1/analytics/journeys/analytics",
            headers=self.get_headers()
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        assert "total_journeys" in data["data"]
        assert "most_common_routes" in data["data"]
        
        print(f"    Total journeys: {data['data']['total_journeys']}")
        print(f"    Unique routes: {data['data']['unique_routes']}")
        
        return True
    
    async def test_get_common_routes(self):
        """Test GET /analytics/journeys/routes"""
        response = await self.client.get(
            "/api/v1/analytics/journeys/routes",
            headers=self.get_headers(),
            params={"limit": 5}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        assert "routes" in data["data"]
        
        if data["data"]["routes"]:
            print(f"    Found {len(data['data']['routes'])} routes")
        
        return True
    
    # ==================== ZONE TESTS ====================
    
    async def test_zone_engagement(self):
        """Test GET /analytics/zones/engagement"""
        response = await self.client.get(
            "/api/v1/analytics/zones/engagement",
            headers=self.get_headers()
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        
        if data["data"].get("zones"):
            print(f"    Found {len(data['data']['zones'])} zones with engagement data")
        
        return True
    
    async def test_top_zones(self):
        """Test GET /analytics/zones/top"""
        response = await self.client.get(
            "/api/v1/analytics/zones/top",
            headers=self.get_headers(),
            params={"limit": 5}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        
        if data["data"].get("top_zones"):
            print(f"    Top zone: Zone {data['data']['top_zones'][0]['zone_id']} - Score: {data['data']['top_zones'][0]['engagement_score']:.2f}")
        
        return True
    
    async def test_underperforming_zones(self):
        """Test GET /analytics/zones/underperforming"""
        response = await self.client.get(
            "/api/v1/analytics/zones/underperforming",
            headers=self.get_headers(),
            params={"limit": 5}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        
        if data["data"].get("underperforming_zones"):
            print(f"    Found {len(data['data']['underperforming_zones'])} underperforming zones")
        
        return True
    
    # ==================== ENGAGEMENT TESTS ====================
    
    async def test_overall_engagement(self):
        """Test GET /analytics/engagement/overall"""
        response = await self.client.get(
            "/api/v1/analytics/engagement/overall",
            headers=self.get_headers()
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        
        return True
    
    # ==================== INSIGHTS TESTS ====================
    
    async def test_get_insights(self):
        """Test GET /analytics/insights"""
        response = await self.client.get(
            "/api/v1/analytics/insights",
            headers=self.get_headers(),
            params={"limit": 5}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        
        if data["data"].get("insights"):
            print(f"    Found {len(data['data']['insights'])} insights")
        
        return True
    
    async def test_generate_insights(self):
        """Test POST /analytics/insights/generate"""
        response = await self.client.post(
            "/api/v1/analytics/insights/generate",
            headers=self.get_headers(),
            params={"date": datetime.utcnow().isoformat()}
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        
        return True
    
    # ==================== REPORT TESTS ====================
    
    async def test_generate_report(self):
        """Test POST /analytics/reports/generate"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        response = await self.client.post(
            "/api/v1/analytics/reports/generate",
            headers=self.get_headers(),
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "report_type": "comprehensive"
            }
        )
        
        print(f"    Status: {response.status_code}")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert "data" in data
        
        print(f"    Report sections: {', '.join(data['data'].get('sections', {}).keys())}")
        
        return True
    
    async def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}PHASE 7: ADVANCED ANALYTICS INTEGRATION TESTS{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        print(f"\n{Colors.YELLOW}API Endpoint: {self.api_url}{Colors.END}")
        print(f"{Colors.YELLOW}API Key: {self.api_key[:10]}...{Colors.END}")
        
        # Run all tests
        print(f"\n{Colors.BLUE}1. HEATMAP TESTS{Colors.END}")
        await self.run_test("Get Latest Heatmap", self.test_get_latest_heatmap)
        await self.run_test("Generate Real-Time Heatmap", self.test_generate_realtime_heatmap)
        await self.run_test("Get Daily Heatmap", self.test_get_daily_heatmap)
        await self.run_test("Get Hourly Heatmap", self.test_get_hourly_heatmap)
        
        print(f"\n{Colors.BLUE}2. JOURNEY TESTS{Colors.END}")
        await self.run_test("Journey Analytics", self.test_journey_analytics)
        await self.run_test("Get Common Routes", self.test_get_common_routes)
        
        print(f"\n{Colors.BLUE}3. ZONE ENGAGEMENT TESTS{Colors.END}")
        await self.run_test("Zone Engagement", self.test_zone_engagement)
        await self.run_test("Top Zones", self.test_top_zones)
        await self.run_test("Underperforming Zones", self.test_underperforming_zones)
        
        print(f"\n{Colors.BLUE}4. ENGAGEMENT METRICS TESTS{Colors.END}")
        await self.run_test("Overall Engagement", self.test_overall_engagement)
        
        print(f"\n{Colors.BLUE}5. INSIGHTS TESTS{Colors.END}")
        await self.run_test("Get Insights", self.test_get_insights)
        await self.run_test("Generate Insights", self.test_generate_insights)
        
        print(f"\n{Colors.BLUE}6. REPORTS TESTS{Colors.END}")
        await self.run_test("Generate Report", self.test_generate_report)
        
        # Print summary
        total = self.tests_passed + self.tests_failed
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}TEST RESULTS SUMMARY{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        print(f"\n{Colors.GREEN}Passed: {self.tests_passed}/{total}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.tests_failed}/{total}{Colors.END}")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}✓ All tests passed!{Colors.END}")
        else:
            print(f"\n{Colors.RED}✗ Some tests failed{Colors.END}")
            print(f"\n{Colors.YELLOW}Failed Tests:{Colors.END}")
            for name, status, error in self.results:
                if status != "PASSED":
                    print(f"  - {name}: {status}")
                    if error:
                        print(f"    {error}")
        
        await self.client.aclose()
        
        return self.tests_failed == 0

async def main():
    import sys
    
    # Check backend
    print("\n⏳ Checking backend connectivity...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8000/health")
            print(f"✓ Backend is running (status: {response.status_code})\n")
    except Exception as e:
        print(f"✗ Backend not running: {e}")
        print("\nStart the backend with:")
        print("  cd backend")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    runner = TestRunner()
    success = await runner.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
