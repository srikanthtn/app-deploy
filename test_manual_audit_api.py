"""
Manual Audit API Test Script
=============================
Tests all manual audit endpoints to verify functionality
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_health_check():
    """Test health check endpoint"""
    print_section("TEST 1: Health Check")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200, "Health check failed"
        print("✅ Health check PASSED")
        return True
    except Exception as e:
        print(f"❌ Health check FAILED: {e}")
        return False

def test_create_manual_audit():
    """Test creating a new manual audit"""
    print_section("TEST 2: Create Manual Audit")

    # Sample audit data
    audit_data = {
        "dealer_id": "DEALER001",
        "dealer_name": "Downtown Stellantis Showroom",
        "dealer_details": "Premium dealership location in downtown area",
        "dealer_consolidated_summary": "All checkpoints passed with excellent hygiene standards",
        "date": "2026-02-10",
        "month": "February",
        "time": datetime.now().isoformat(),
        "shift": "Morning Shift",
        "compliance_status": "Compliant",
        "level_1": "Level 1 - Critical",
        "sub_category": "Cleanliness",
        "checkpoint": "Surface Sanitation",
        "photo_url": "https://example.com/photo.jpg",
        "confidence_level": 95.5,
        "feedback": "Excellent hygiene maintained across all checkpoints. All surfaces are clean and sanitized.",
        "language": "English",
        "country": "India",
        "zone": "North Zone",
        "email": "dealer@stellantis.com",
        "password": "test123"
    }

    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/manual-audit",
            json=audit_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        audit_id = response.json()["id"]
        print(f"✅ Manual audit created successfully with ID: {audit_id}")
        return audit_id
    except Exception as e:
        print(f"❌ Create manual audit FAILED: {e}")
        return None

def test_get_manual_audit(audit_id):
    """Test getting a specific manual audit by ID"""
    print_section(f"TEST 3: Get Manual Audit by ID ({audit_id})")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/manual-audit/{audit_id}")

        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["id"] == audit_id, "Audit ID mismatch"

        print("✅ Get manual audit by ID PASSED")
        return True
    except Exception as e:
        print(f"❌ Get manual audit FAILED: {e}")
        return False

def test_list_manual_audits():
    """Test listing all manual audits"""
    print_section("TEST 4: List All Manual Audits")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/manual-audits?skip=0&limit=10")

        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Total Audits: {data['total']}")
        print(f"Retrieved: {len(data['audits'])} audits")

        if data['audits']:
            print("\nFirst audit:")
            print(json.dumps(data['audits'][0], indent=2))

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'total' in data, "Missing 'total' field"
        assert 'audits' in data, "Missing 'audits' field"

        print("✅ List manual audits PASSED")
        return True
    except Exception as e:
        print(f"❌ List manual audits FAILED: {e}")
        return False

def test_get_audits_by_dealer(dealer_id):
    """Test getting audits by dealer ID"""
    print_section(f"TEST 5: Get Audits by Dealer ({dealer_id})")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/manual-audits/dealer/{dealer_id}")

        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Total Audits for {dealer_id}: {data['total']}")
        print(f"Retrieved: {len(data['audits'])} audits")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify all audits belong to the dealer
        for audit in data['audits']:
            assert audit['dealer_id'] == dealer_id, f"Dealer ID mismatch: expected {dealer_id}, got {audit['dealer_id']}"

        print("✅ Get audits by dealer PASSED")
        return True
    except Exception as e:
        print(f"❌ Get audits by dealer FAILED: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "MANUAL AUDIT API TEST SUITE" + " "*26 + "║")
    print("╚" + "="*68 + "╝")
    print(f"\nTesting API at: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))

    # Test 2: Create Manual Audit
    audit_id = test_create_manual_audit()
    results.append(("Create Manual Audit", audit_id is not None))

    if audit_id:
        # Test 3: Get Manual Audit by ID
        results.append(("Get Manual Audit by ID", test_get_manual_audit(audit_id)))

        # Test 4: List All Manual Audits
        results.append(("List All Manual Audits", test_list_manual_audits()))

        # Test 5: Get Audits by Dealer
        results.append(("Get Audits by Dealer", test_get_audits_by_dealer("DEALER001")))

    # Print Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\nResults:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:.<40} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! API is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("  PREREQUISITES:")
    print("  1. Ensure PostgreSQL is running")
    print("  2. Ensure backend is running on http://localhost:8000")
    print("  3. Database tables should be created automatically")
    print("="*70)

    input("\nPress ENTER to start tests...")

    exit_code = run_all_tests()

    print("\n" + "="*70)
    input("\nPress ENTER to exit...")
    sys.exit(exit_code)

