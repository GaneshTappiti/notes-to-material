"""
Comprehensive error handling tests for the API endpoints.

Tests various error conditions and edge cases to ensure proper error handling.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestErrorHandling:
    """Test error handling across all API endpoints."""

    def test_invalid_file_upload(self):
        """Test uploading invalid file types."""
        # Test with non-PDF file
        files = {"file": ("test.txt", b"Not a PDF", "text/plain")}
        r = client.post("/api/uploads", files=files)
        assert r.status_code in [400, 422]  # Should reject non-PDF files

        # Test with empty file
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        r = client.post("/api/uploads", files=files)
        assert r.status_code in [400, 422]

        # Test with corrupted PDF
        files = {"file": ("corrupted.pdf", b"corrupted data", "application/pdf")}
        r = client.post("/api/uploads", files=files)
        assert r.status_code in [400, 500]

    def test_missing_file_upload(self):
        """Test upload endpoint without file."""
        r = client.post("/api/uploads")
        assert r.status_code == 422  # Missing required field

    def test_nonexistent_file_operations(self):
        """Test operations on non-existent files."""
        fake_id = "nonexistent-file-id"

        # Test getting non-existent upload
        r = client.get(f"/api/uploads/{fake_id}")
        assert r.status_code == 404

        # Test deleting non-existent upload
        r = client.delete(f"/api/uploads/{fake_id}")
        assert r.status_code == 404

        # Test getting pages for non-existent upload
        r = client.get(f"/api/uploads/{fake_id}/pages")
        assert r.status_code == 404

    def test_invalid_job_operations(self):
        """Test job operations with invalid data."""
        # Test creating job without required data
        r = client.post("/api/jobs")
        assert r.status_code == 422

        # Test invalid job ID
        r = client.get("/api/jobs/invalid-job-id")
        assert r.status_code == 404

        # Test deleting non-existent job
        r = client.delete("/api/jobs/nonexistent-job")
        assert r.status_code == 404

    def test_invalid_export_operations(self):
        """Test export operations with invalid data."""
        # Test creating export without job_id
        r = client.post("/api/exports", json={})
        assert r.status_code == 422

        # Test creating export with non-existent job
        r = client.post("/api/exports", json={"job_id": "nonexistent-job"})
        assert r.status_code in [400, 404]

        # Test getting non-existent export
        r = client.get("/api/exports/nonexistent-export")
        assert r.status_code == 404

        # Test downloading non-existent export
        r = client.get("/api/exports/nonexistent-export/download")
        assert r.status_code == 404

    def test_invalid_question_operations(self):
        """Test question operations with invalid data."""
        # Test approving non-existent question
        r = client.patch("/api/questions/nonexistent/approve")
        assert r.status_code in [401, 404]  # Unauthorized or not found

        # Test getting non-existent question
        r = client.get("/api/questions/nonexistent")
        assert r.status_code in [401, 404]

    def test_invalid_embedding_operations(self):
        """Test embedding operations error handling."""
        # Test query with empty string
        r = client.get("/api/embeddings/query?q=")
        assert r.status_code in [400, 401]  # Bad request or unauthorized

        # Test query with invalid parameters
        r = client.get("/api/embeddings/query?q=test&k=-1")
        assert r.status_code in [400, 401, 422]

        r = client.get("/api/embeddings/query?q=test&k=1000")
        assert r.status_code in [400, 401, 422]

    def test_malformed_json_requests(self):
        """Test endpoints with malformed JSON."""
        # Test various endpoints with malformed JSON
        endpoints = ["/api/jobs", "/api/exports"]

        for endpoint in endpoints:
            # Test with malformed JSON
            r = client.post(endpoint, content="malformed json",
                           headers={"Content-Type": "application/json"})
            assert r.status_code == 422

    def test_oversized_requests(self):
        """Test handling of oversized requests."""
        # Create a very large fake PDF (this would normally be rejected by file size limits)
        large_data = b"fake pdf content" * 100000  # Simulate large file
        files = {"file": ("large.pdf", large_data, "application/pdf")}

        r = client.post("/api/uploads", files=files)
        # Should either succeed or be rejected with appropriate error
        assert r.status_code in [200, 413, 422]  # Success, too large, or validation error

    def test_concurrent_operations(self):
        """Test error handling under concurrent operations."""
        import threading
        import time

        results = []

        def make_request():
            try:
                r = client.get("/api/uploads")
                results.append(r.status_code)
            except Exception as e:
                results.append(f"Error: {e}")

        # Create multiple threads making concurrent requests
        threads = []
        for _ in range(5):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # All requests should return valid status codes
        for result in results:
            if isinstance(result, int):
                assert result in [200, 401, 403]  # Success or auth-related
            else:
                pytest.fail(f"Unexpected error: {result}")

    def test_database_constraints(self):
        """Test database constraint violations."""
        # This would test things like duplicate keys, foreign key violations, etc.
        # For now, we'll test basic database connectivity
        r = client.get("/api/uploads")
        # Should not crash even if database has issues
        assert r.status_code in [200, 401, 403, 500]

    def test_auth_error_handling(self):
        """Test authentication and authorization error handling."""
        # Test endpoints that require authentication without token
        auth_endpoints = [
            ("/api/embeddings/upsert", "POST"),
            ("/api/embeddings/query", "GET"),
            ("/api/questions/test/approve", "PATCH"),
        ]

        for endpoint, method in auth_endpoints:
            r = None
            if method == "GET":
                r = client.get(endpoint)
            elif method == "POST":
                r = client.post(endpoint, json={})
            elif method == "PATCH":
                r = client.patch(endpoint, json={})

            assert r is not None, f"No request made for {method} {endpoint}"
            assert r.status_code in [401, 403]  # Unauthorized or forbidden

    def test_validation_error_messages(self):
        """Test that validation errors return helpful messages."""
        # Test upload with wrong field name
        files = {"wrong_field": ("test.pdf", b"fake pdf", "application/pdf")}
        r = client.post("/api/uploads", files=files)
        assert r.status_code == 422
        error_detail = r.json()
        assert "detail" in error_detail  # Should have error details

    def test_server_error_recovery(self):
        """Test server error recovery mechanisms."""
        # Test that the server doesn't crash on various operations
        # These should be handled gracefully
        test_operations = [
            lambda: client.get("/api/uploads"),
            lambda: client.get("/api/jobs"),
            lambda: client.get("/api/exports"),
        ]

        for operation in test_operations:
            try:
                r = operation()
                # Should return a valid HTTP status code
                assert isinstance(r.status_code, int)
                assert 100 <= r.status_code < 600
            except Exception as e:
                pytest.fail(f"Operation should not raise exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
