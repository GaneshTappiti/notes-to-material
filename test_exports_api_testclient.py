#!/usr/bin/env python3
"""Test the API endpoints using FastAPI TestClient."""

import sys
import os
sys.path.append('backend')

# Set test mode
os.environ['TEST_MODE'] = '1'

from fastapi.testclient import TestClient
from app.main import app

def test_exports_api():
    """Test Export API endpoints using TestClient."""
    print("Testing Export API endpoints with TestClient...")

    client = TestClient(app)

    # Test 1: Create an export
    print("\n1. Creating an export...")
    create_payload = {
        "job_id": "test_job_api_123",
        "template": "compact",
        "title": "Test Export API"
    }

    response = client.post("/api/exports", json=create_payload)
    if response.status_code == 200:
        export_data = response.json()
        export_id = export_data.get("export_id")
        print(f"✓ Export created successfully with ID: {export_id}")
        print(f"   Status: {export_data.get('status')}")
    else:
        print(f"✗ Failed to create export: {response.status_code} - {response.text}")
        return

    # Test 2: List exports
    print("\n2. Listing all exports...")
    response = client.get("/api/exports")
    if response.status_code == 200:
        exports_data = response.json()
        print(f"✓ Found {exports_data.get('total')} exports")
        print(f"   Returned {len(exports_data.get('exports', []))} exports in this page")
        for export in exports_data.get('exports', []):
            print(f"   Export ID: {export.get('id')}, Job ID: {export.get('job_id')}, Status: {export.get('status')}")
    else:
        print(f"✗ Failed to list exports: {response.status_code} - {response.text}")

    # Test 3: Get specific export status
    print(f"\n3. Getting status of export {export_id}...")
    response = client.get(f"/api/exports/{export_id}")
    if response.status_code == 200:
        export_info = response.json()
        print(f"✓ Export status: {export_info.get('status')}")
        print(f"   Job ID: {export_info.get('job_id')}")
        print(f"   Template: {export_info.get('template')}")
        print(f"   Created: {export_info.get('created_at')}")
    else:
        print(f"✗ Failed to get export status: {response.status_code} - {response.text}")

    # Test 4: Create another export
    print("\n4. Creating another export...")
    create_payload2 = {
        "job_id": "test_job_api_456",
        "template": "detailed",
        "title": "Second Test Export API"
    }

    response = client.post("/api/exports", json=create_payload2)
    if response.status_code == 200:
        export_data2 = response.json()
        export_id2 = export_data2.get("export_id")
        print(f"✓ Second export created successfully with ID: {export_id2}")
    else:
        print(f"✗ Failed to create second export: {response.status_code} - {response.text}")
        export_id2 = None

    # Test 5: List exports again (should show more)
    print("\n5. Listing exports again...")
    response = client.get("/api/exports")
    if response.status_code == 200:
        exports_data = response.json()
        print(f"✓ Found {exports_data.get('total')} exports total")
        for export in exports_data.get('exports', []):
            print(f"   Export ID: {export.get('id')}, Job ID: {export.get('job_id')}, Status: {export.get('status')}")
    else:
        print(f"✗ Failed to list exports: {response.status_code} - {response.text}")

    # Test 6: Test pagination
    print("\n6. Testing pagination...")
    response = client.get("/api/exports?limit=1&offset=0")
    if response.status_code == 200:
        exports_data = response.json()
        print(f"✓ Pagination test - Total: {exports_data.get('total')}, Returned: {len(exports_data.get('exports', []))}")
        print(f"   Limit: {exports_data.get('limit')}, Offset: {exports_data.get('offset')}")
    else:
        print(f"✗ Failed pagination test: {response.status_code} - {response.text}")

    # Test 7: Delete the first export
    print(f"\n7. Deleting export {export_id}...")
    response = client.delete(f"/api/exports/{export_id}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Export deleted: {result.get('message')}")
    else:
        print(f"✗ Failed to delete export: {response.status_code} - {response.text}")

    # Test 8: List exports again (should show one less)
    print("\n8. Listing exports after deletion...")
    response = client.get("/api/exports")
    if response.status_code == 200:
        exports_data = response.json()
        print(f"✓ Found {exports_data.get('total')} exports total")
        for export in exports_data.get('exports', []):
            print(f"   Export ID: {export.get('id')}, Job ID: {export.get('job_id')}, Status: {export.get('status')}")
    else:
        print(f"✗ Failed to list exports: {response.status_code} - {response.text}")

    # Test 9: Try to get deleted export (should fail)
    print(f"\n9. Trying to get deleted export {export_id}...")
    response = client.get(f"/api/exports/{export_id}")
    if response.status_code == 404:
        print("✓ Correctly returned 404 for deleted export")
    else:
        print(f"✗ Unexpected response for deleted export: {response.status_code} - {response.text}")

    # Test 10: Try to delete non-existent export
    print("\n10. Trying to delete non-existent export...")
    response = client.delete("/api/exports/9999")
    if response.status_code == 404:
        print("✓ Correctly returned 404 for non-existent export")
    else:
        print(f"✗ Unexpected response for non-existent export: {response.status_code} - {response.text}")

    print("\n✓ All API tests completed!")

if __name__ == "__main__":
    try:
        test_exports_api()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
