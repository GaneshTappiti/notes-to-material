#!/usr/bin/env python3
"""Test script for the new exports API endpoints using urllib."""

import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def make_request(method, url, data=None):
    """Make an HTTP request using urllib."""
    if data:
        data = json.dumps(data).encode('utf-8')

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            return response.status, json.loads(response_data)
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        return e.code, {"error": error_data}
    except Exception as e:
        return 500, {"error": str(e)}

def test_exports_api():
    print("Testing Export API endpoints...")

    # Test 1: Create an export
    print("\n1. Creating an export...")
    create_payload = {
        "job_id": "test_job_api_123",
        "template": "compact",
        "title": "Test Export API"
    }

    status, response_data = make_request("POST", f"{BASE_URL}/api/exports", create_payload)
    if status == 200:
        export_id = response_data.get("export_id")
        print(f"✓ Export created successfully with ID: {export_id}")
        print(f"   Status: {response_data.get('status')}")
    else:
        print(f"✗ Failed to create export: {status} - {response_data}")
        return

    # Test 2: List exports
    print("\n2. Listing all exports...")
    status, response_data = make_request("GET", f"{BASE_URL}/api/exports")
    if status == 200:
        print(f"✓ Found {response_data.get('total')} exports")
        print(f"   Returned {len(response_data.get('exports', []))} exports in this page")
        for export in response_data.get('exports', []):
            print(f"   Export ID: {export.get('id')}, Job ID: {export.get('job_id')}, Status: {export.get('status')}")
    else:
        print(f"✗ Failed to list exports: {status} - {response_data}")

    # Test 3: Get specific export status
    print(f"\n3. Getting status of export {export_id}...")
    status, response_data = make_request("GET", f"{BASE_URL}/api/exports/{export_id}")
    if status == 200:
        print(f"✓ Export status: {response_data.get('status')}")
        print(f"   Job ID: {response_data.get('job_id')}")
        print(f"   Template: {response_data.get('template')}")
        print(f"   Created: {response_data.get('created_at')}")
    else:
        print(f"✗ Failed to get export status: {status} - {response_data}")

    # Test 4: Create another export
    print("\n4. Creating another export...")
    create_payload2 = {
        "job_id": "test_job_api_456",
        "template": "detailed",
        "title": "Second Test Export API"
    }

    status, response_data = make_request("POST", f"{BASE_URL}/api/exports", create_payload2)
    if status == 200:
        export_id2 = response_data.get("export_id")
        print(f"✓ Second export created successfully with ID: {export_id2}")
    else:
        print(f"✗ Failed to create second export: {status} - {response_data}")
        export_id2 = None

    # Test 5: List exports again (should show more)
    print("\n5. Listing exports again...")
    status, response_data = make_request("GET", f"{BASE_URL}/api/exports")
    if status == 200:
        print(f"✓ Found {response_data.get('total')} exports total")
        for export in response_data.get('exports', []):
            print(f"   Export ID: {export.get('id')}, Job ID: {export.get('job_id')}, Status: {export.get('status')}")
    else:
        print(f"✗ Failed to list exports: {status} - {response_data}")

    # Test 6: Delete the first export
    print(f"\n6. Deleting export {export_id}...")
    status, response_data = make_request("DELETE", f"{BASE_URL}/api/exports/{export_id}")
    if status == 200:
        print(f"✓ Export deleted: {response_data.get('message')}")
    else:
        print(f"✗ Failed to delete export: {status} - {response_data}")

    # Test 7: List exports again (should show one less)
    print("\n7. Listing exports after deletion...")
    status, response_data = make_request("GET", f"{BASE_URL}/api/exports")
    if status == 200:
        print(f"✓ Found {response_data.get('total')} exports total")
        for export in response_data.get('exports', []):
            print(f"   Export ID: {export.get('id')}, Job ID: {export.get('job_id')}, Status: {export.get('status')}")
    else:
        print(f"✗ Failed to list exports: {status} - {response_data}")

    # Test 8: Try to get deleted export (should fail)
    print(f"\n8. Trying to get deleted export {export_id}...")
    status, response_data = make_request("GET", f"{BASE_URL}/api/exports/{export_id}")
    if status == 404:
        print("✓ Correctly returned 404 for deleted export")
    else:
        print(f"✗ Unexpected response for deleted export: {status} - {response_data}")

    print("\n✓ All API tests completed!")

if __name__ == "__main__":
    try:
        test_exports_api()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
