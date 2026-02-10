"""
Manager Portal API Test Script
===============================
Tests the Manager Portal dashboard endpoint
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_manager_dashboard():
    """Test Manager Portal dashboard endpoint"""
    print_section("TEST: Manager Portal Dashboard API")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/manager/dashboard")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - Dashboard data retrieved")
            print(f"\nTotal Audits: {data.get('total_audits', 0)}")
            print(f"Last Updated: {data.get('last_updated', 'N/A')}")
            print(f"Countries: {len(data.get('countries', []))}")

            # Print country details
            for country in data.get('countries', []):
                print(f"\n📍 {country['country_name']}")
                print(f"   Compliance: {country['compliance_percentage']}%")
                print(f"   Zones: {country['total_zones']}")
                print(f"   Facilities: {country['total_facilities']}")

                # Print zone details
                for zone in country.get('zones', [])[:2]:  # First 2 zones
                    print(f"\n   🏢 {zone['zone_name']}")
                    print(f"      Compliance: {zone['compliance_percentage']}%")
                    print(f"      Facilities: {zone['total_facilities']}")

                    # Print facility details
                    for facility in zone.get('facilities', [])[:2]:  # First 2 facilities
                        print(f"\n      🏭 {facility['facility_name']} ({facility['facility_id']})")
                        print(f"         Compliance: {facility['compliance_percentage']}%")
                        print(f"         Audits: {facility['total_audits']}")

            return True
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ FAILED - Cannot connect to backend")
        print("Make sure backend is running: python run.py")
        return False
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False

def test_zone_summary():
    """Test zone summary endpoint"""
    print_section("TEST: Zone Summary API")

    try:
        # Test with example zone
        response = requests.get(f"{BASE_URL}/api/v1/manager/zone/India/North Zone")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - Zone summary retrieved")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False

def test_facility_audits():
    """Test facility audits endpoint"""
    print_section("TEST: Facility Audits API")

    try:
        # Test with example facility
        response = requests.get(f"{BASE_URL}/api/v1/manager/facility/DEALER001/audits")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - Facility audits retrieved")
            print(f"Facility ID: {data.get('facility_id')}")
            print(f"Total Audits: {data.get('total_audits')}")
            print(f"\nFirst 3 audits:")
            for audit in data.get('audits', [])[:3]:
                print(f"  - ID {audit['id']}: {audit['compliance_status']} ({audit['confidence_level']}%)")
            return True
        elif response.status_code == 404:
            print(f"\n⚠️  No audits found for DEALER001")
            print("This is expected if no audits exist for this facility")
            return True
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False

def run_all_tests():
    """Run all Manager Portal API tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*12 + "MANAGER PORTAL API TEST SUITE" + " "*26 + "║")
    print("╚" + "="*68 + "╝")
    print(f"\nTesting API at: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Dashboard
    results.append(("Manager Dashboard", test_manager_dashboard()))

    # Test 2: Zone Summary
    results.append(("Zone Summary", test_zone_summary()))

    # Test 3: Facility Audits
    results.append(("Facility Audits", test_facility_audits()))

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
        print("\n🎉 ALL TESTS PASSED! Manager Portal API is working correctly.")
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
    print("  3. Ensure manual_audits table has some data")
    print("="*70)

    input("\nPress ENTER to start tests...")

    exit_code = run_all_tests()

    print("\n" + "="*70)
    input("\nPress ENTER to exit...")
    sys.exit(exit_code)

