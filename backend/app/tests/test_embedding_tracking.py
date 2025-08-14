"""
Tests for the new embedding tracking system.

Tests the EmbeddingTracker service and related functionality.
"""
import pytest
from app.models import get_session, Page, PageEmbedding, create_db
from app.services.embedding_tracker import EmbeddingTracker
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestEmbeddingTracker:
    """Test the EmbeddingTracker service functionality."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up clean database for each test."""
        create_db()
        # Clean up any existing data
        with get_session() as session:
            session.query(PageEmbedding).delete()
            session.query(Page).delete()
            session.commit()

    def test_get_embedding_status_empty(self):
        """Test getting embedding status with no pages."""
        status = EmbeddingTracker.get_embedding_status()

        assert status["total_pages"] == 0
        assert status["embedded_pages"] == 0
        assert status["pending_pages"] == 0
        assert status["completion_percentage"] == 100.0
        assert status["files"] == []

    def test_get_embedding_status_with_data(self):
        """Test getting embedding status with some pages."""
        # Create test pages
        with get_session() as session:
            page1 = Page(
                file_name="test1.pdf",
                page_no=1,
                text="Test content 1",
                file_id="test-file-1"
            )
            page2 = Page(
                file_name="test1.pdf",
                page_no=2,
                text="Test content 2",
                file_id="test-file-1"
            )
            page3 = Page(
                file_name="test2.pdf",
                page_no=1,
                text="Test content 3",
                file_id="test-file-2"
            )
            session.add(page1)
            session.add(page2)
            session.add(page3)
            session.commit()

            # Add embedding for only one page
            embedding = PageEmbedding(
                page_id=page1.id,
                file_id="test-file-1",
                page_no=1,
                embedding=[0.1, 0.2, 0.3]
            )
            session.add(embedding)
            session.commit()

        status = EmbeddingTracker.get_embedding_status()

        assert status["total_pages"] == 3
        assert status["embedded_pages"] == 1
        assert status["pending_pages"] == 2
        assert abs(status["completion_percentage"] - 33.33) < 0.1
        assert len(status["files"]) == 2

    def test_get_pending_pages(self):
        """Test getting pages that need embedding."""
        # Create test pages
        with get_session() as session:
            page1 = Page(
                file_name="test.pdf",
                page_no=1,
                text="Test content 1",
                file_id="test-file"
            )
            page2 = Page(
                file_name="test.pdf",
                page_no=2,
                text="Test content 2",
                file_id="test-file"
            )
            session.add(page1)
            session.add(page2)
            session.commit()

            # Mark one page as embedded
            embedding = PageEmbedding(
                page_id=page1.id,
                file_id="test-file",
                page_no=1,
                embedding=[0.1, 0.2, 0.3]
            )
            session.add(embedding)
            session.commit()

        pending = EmbeddingTracker.get_pending_pages()
        assert len(pending) == 1
        assert pending[0].page_no == 2

        # Test with limit
        pending_limited = EmbeddingTracker.get_pending_pages(limit=0)
        assert len(pending_limited) == 0

    def test_mark_page_embedded(self):
        """Test marking a page as embedded."""
        # Create test page
        with get_session() as session:
            page = Page(
                file_name="test.pdf",
                page_no=1,
                text="Test content",
                file_id="test-file"
            )
            session.add(page)
            session.commit()
            page_id = page.id

        # Mark as embedded
        success = EmbeddingTracker.mark_page_embedded(
            page_id, [0.1, 0.2, 0.3], "test-file", 1
        )
        assert success is True

        # Try to mark again (should return False)
        success = EmbeddingTracker.mark_page_embedded(
            page_id, [0.1, 0.2, 0.3], "test-file", 1
        )
        assert success is False

        # Verify embedding exists
        with get_session() as session:
            embedding = session.query(PageEmbedding).filter(
                PageEmbedding.page_id == page_id
            ).first()
            assert embedding is not None
            assert embedding.embedding == [0.1, 0.2, 0.3]

    def test_bulk_mark_embedded(self):
        """Test bulk marking pages as embedded."""
        # Create test pages
        with get_session() as session:
            page1 = Page(
                file_name="test.pdf",
                page_no=1,
                text="Test content 1",
                file_id="test-file"
            )
            page2 = Page(
                file_name="test.pdf",
                page_no=2,
                text="Test content 2",
                file_id="test-file"
            )
            session.add(page1)
            session.add(page2)
            session.commit()

            page_embeddings = [
                {
                    "page_id": page1.id,
                    "file_id": "test-file",
                    "page_no": 1,
                    "embedding": [0.1, 0.2, 0.3]
                },
                {
                    "page_id": page2.id,
                    "file_id": "test-file",
                    "page_no": 2,
                    "embedding": [0.4, 0.5, 0.6]
                }
            ]

        created_count = EmbeddingTracker.bulk_mark_embedded(page_embeddings)
        assert created_count == 2

        # Verify embeddings exist
        with get_session() as session:
            embeddings = session.query(PageEmbedding).all()
            assert len(embeddings) == 2

    def test_remove_page_embedding(self):
        """Test removing page embedding."""
        # Create test page and embedding
        with get_session() as session:
            page = Page(
                file_name="test.pdf",
                page_no=1,
                text="Test content",
                file_id="test-file"
            )
            session.add(page)
            session.commit()

            embedding = PageEmbedding(
                page_id=page.id,
                file_id="test-file",
                page_no=1,
                embedding=[0.1, 0.2, 0.3]
            )
            session.add(embedding)
            session.commit()
            page_id = page.id

        # Remove embedding
        success = EmbeddingTracker.remove_page_embedding(page_id)
        assert success is True

        # Try to remove again (should return False)
        success = EmbeddingTracker.remove_page_embedding(page_id)
        assert success is False

        # Verify embedding is gone
        with get_session() as session:
            embedding = session.query(PageEmbedding).filter(
                PageEmbedding.page_id == page_id
            ).first()
            assert embedding is None

    def test_cleanup_orphaned_embeddings(self):
        """Test cleaning up orphaned embeddings."""
        # Create embedding without corresponding page
        with get_session() as session:
            # Create a page first to get a valid ID
            page = Page(
                file_name="test.pdf",
                page_no=1,
                text="Test content",
                file_id="test-file"
            )
            session.add(page)
            session.commit()
            page_id = page.id

            # Create embedding
            embedding = PageEmbedding(
                page_id=page_id,
                file_id="test-file",
                page_no=1,
                embedding=[0.1, 0.2, 0.3]
            )
            session.add(embedding)
            session.commit()

            # Now delete the page to create orphaned embedding
            session.delete(page)
            session.commit()

        # Clean up orphaned embeddings
        cleaned_count = EmbeddingTracker.cleanup_orphaned_embeddings()
        assert cleaned_count == 1

        # Verify embedding is gone
        with get_session() as session:
            embeddings = session.query(PageEmbedding).all()
            assert len(embeddings) == 0

    def test_reset_all_embeddings(self):
        """Test resetting all embeddings."""
        # Create test embeddings
        with get_session() as session:
            page = Page(
                file_name="test.pdf",
                page_no=1,
                text="Test content",
                file_id="test-file"
            )
            session.add(page)
            session.commit()

            embedding1 = PageEmbedding(
                page_id=page.id,
                file_id="test-file",
                page_no=1,
                embedding=[0.1, 0.2, 0.3]
            )
            embedding2 = PageEmbedding(
                page_id=page.id + 1000,  # Fake ID
                file_id="test-file",
                page_no=2,
                embedding=[0.4, 0.5, 0.6]
            )
            session.add(embedding1)
            session.add(embedding2)
            session.commit()

        # Reset all embeddings
        deleted_count = EmbeddingTracker.reset_all_embeddings()
        assert deleted_count == 2

        # Verify all embeddings are gone
        with get_session() as session:
            embeddings = session.query(PageEmbedding).all()
            assert len(embeddings) == 0

    def test_embedding_api_endpoints(self):
        """Test the new embedding API endpoints."""
        # Test status endpoint
        r = client.get("/api/embeddings/status")
        assert r.status_code in [200, 401]  # Success or auth required

        if r.status_code == 200:
            data = r.json()
            assert "total_pages" in data
            assert "embedded_pages" in data
            assert "pending_pages" in data
            assert "completion_percentage" in data

        # Test cleanup endpoint
        r = client.post("/api/embeddings/cleanup")
        assert r.status_code in [200, 401]  # Success or auth required

        # Test reset endpoint
        r = client.delete("/api/embeddings/reset")
        assert r.status_code in [200, 401]  # Success or auth required


if __name__ == "__main__":
    pytest.main([__file__])
