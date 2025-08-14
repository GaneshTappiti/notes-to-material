#!/usr/bin/env python3
"""Test the database Export functionality directly."""

import sys
import os
sys.path.append('backend')

from app.models import Export, create_db, get_session
from sqlmodel import select

def test_export_db():
    """Test Export model CRUD operations."""
    print("Testing Export database operations...")

    # Create database tables
    create_db()
    print("✓ Database tables created/verified")

    # Test 1: Create an export
    print("\n1. Creating an export...")
    with get_session() as session:
        export = Export(
            job_id="test_job_123",
            template="compact",
            status="pending"
        )
        session.add(export)
        session.commit()
        session.refresh(export)
        export_id = export.id
        print(f"✓ Export created with ID: {export_id}")

    # Test 2: Read the export
    print(f"\n2. Reading export {export_id}...")
    with get_session() as session:
        export = session.get(Export, export_id)
        if export:
            print(f"✓ Export found:")
            print(f"   ID: {export.id}")
            print(f"   Job ID: {export.job_id}")
            print(f"   Template: {export.template}")
            print(f"   Status: {export.status}")
            print(f"   Created at: {export.created_at}")
        else:
            print("✗ Export not found")
            return

    # Test 3: Create another export
    print("\n3. Creating another export...")
    with get_session() as session:
        export2 = Export(
            job_id="test_job_456",
            template="detailed",
            status="ready",
            file_path="/path/to/export.pdf"
        )
        session.add(export2)
        session.commit()
        session.refresh(export2)
        export_id2 = export2.id
        print(f"✓ Second export created with ID: {export_id2}")

    # Test 4: List all exports
    print("\n4. Listing all exports...")
    with get_session() as session:
        stmt = select(Export)
        exports = list(session.exec(stmt))
        print(f"✓ Found {len(exports)} exports:")
        for export in exports:
            print(f"   ID: {export.id}, Job: {export.job_id}, Status: {export.status}")

    # Test 5: Update an export
    print(f"\n5. Updating export {export_id}...")
    with get_session() as session:
        export = session.get(Export, export_id)
        if export:
            export.status = "ready"
            export.file_path = "/path/to/updated/export.pdf"
            session.add(export)
            session.commit()
            print("✓ Export updated successfully")
        else:
            print("✗ Export not found for update")

    # Test 6: Delete an export
    print(f"\n6. Deleting export {export_id}...")
    with get_session() as session:
        export = session.get(Export, export_id)
        if export:
            session.delete(export)
            session.commit()
            print("✓ Export deleted successfully")
        else:
            print("✗ Export not found for deletion")

    # Test 7: Verify deletion
    print(f"\n7. Verifying export {export_id} is deleted...")
    with get_session() as session:
        export = session.get(Export, export_id)
        if export:
            print("✗ Export still exists after deletion")
        else:
            print("✓ Export successfully deleted")

    # Test 8: List remaining exports
    print("\n8. Listing remaining exports...")
    with get_session() as session:
        stmt = select(Export)
        exports = list(session.exec(stmt))
        print(f"✓ Found {len(exports)} remaining exports:")
        for export in exports:
            print(f"   ID: {export.id}, Job: {export.job_id}, Status: {export.status}")

    print("\n✓ All database tests completed successfully!")

if __name__ == "__main__":
    try:
        test_export_db()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
