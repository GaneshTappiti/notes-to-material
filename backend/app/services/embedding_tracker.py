"""
Embedding tracking service that uses the database as the single source of truth.

This replaces the previous JSON file-based tracking system with a more robust
database-centric approach.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import func, text
from sqlmodel import Session, select
from ..models import get_session, Page, PageEmbedding


class EmbeddingTracker:
    """Service for tracking which pages have been embedded."""

    @staticmethod
    def get_embedding_status() -> Dict[str, Any]:
        """Get comprehensive embedding status statistics."""
        with get_session() as session:
            # Get total counts using SQLModel select
            all_pages = session.exec(select(Page)).all()
            all_embeddings = session.exec(select(PageEmbedding)).all()

            total_pages = len(all_pages)
            embedded_pages = len(all_embeddings)
            pending_pages = total_pages - embedded_pages

            # Build file-level statistics manually
            file_stats = {}
            for page in all_pages:
                if page.file_name not in file_stats:
                    file_stats[page.file_name] = {'total': 0, 'embedded': 0}
                file_stats[page.file_name]['total'] += 1

            # Count embedded pages per file
            embedded_by_page_id = {e.page_id for e in all_embeddings}
            for page in all_pages:
                if page.id and page.id in embedded_by_page_id:
                    file_stats[page.file_name]['embedded'] += 1

            file_breakdown = []
            for file_name, stats in file_stats.items():
                total = stats['total']
                embedded = stats['embedded']
                file_breakdown.append({
                    'file_name': file_name,
                    'total_pages': total,
                    'embedded_pages': embedded,
                    'pending_pages': total - embedded,
                    'completion_percentage': (embedded / total * 100) if total > 0 else 0
                })

            return {
                'total_pages': total_pages,
                'embedded_pages': embedded_pages,
                'pending_pages': pending_pages,
                'completion_percentage': (embedded_pages / total_pages * 100) if total_pages > 0 else 100.0,
                'files': file_breakdown
            }

    @staticmethod
    def get_pending_pages(limit: Optional[int] = None) -> List[Page]:
        """Get pages that need embedding (don't have PageEmbedding records)."""
        with get_session() as session:
            # Get all pages and all embeddings
            all_pages = session.exec(select(Page)).all()
            all_embeddings = session.exec(select(PageEmbedding)).all()

            # Get set of page IDs that are already embedded
            embedded_page_ids = {e.page_id for e in all_embeddings}

            # Filter pages that don't have embeddings
            pending_pages = [p for p in all_pages if p.id not in embedded_page_ids]

            # Sort by ID for consistency
            pending_pages.sort(key=lambda x: x.id or 0)

            # Apply limit if specified
            if limit is not None:
                pending_pages = pending_pages[:limit]

            return pending_pages

    @staticmethod
    def mark_page_embedded(page_id: int, embedding: List[float],
                          file_id: Optional[str] = None, page_no: Optional[int] = None) -> bool:
        """Mark a page as embedded by creating a PageEmbedding record."""
        try:
            with get_session() as session:
                # Check if already exists using SQLModel select
                existing = session.exec(
                    select(PageEmbedding).where(PageEmbedding.page_id == page_id)
                ).first()

                if existing:
                    return False  # Already embedded

                # Create new embedding record
                pe = PageEmbedding(
                    page_id=page_id,
                    file_id=file_id,
                    page_no=page_no or 0,
                    embedding=embedding
                )
                session.add(pe)
                session.commit()
                return True
        except Exception:
            return False

    @staticmethod
    def bulk_mark_embedded(page_embeddings: List[Dict[str, Any]]) -> int:
        """Bulk mark multiple pages as embedded."""
        created_count = 0

        try:
            with get_session() as session:
                for pe_data in page_embeddings:
                    # Check if already exists using SQLModel select
                    existing = session.exec(
                        select(PageEmbedding).where(PageEmbedding.page_id == pe_data['page_id'])
                    ).first()

                    if not existing:
                        pe = PageEmbedding(**pe_data)
                        session.add(pe)
                        created_count += 1

                session.commit()
        except Exception:
            pass

        return created_count

    @staticmethod
    def remove_page_embedding(page_id: int) -> bool:
        """Remove embedding record for a page."""
        try:
            with get_session() as session:
                # Find and delete the embedding using SQLModel
                embedding = session.exec(
                    select(PageEmbedding).where(PageEmbedding.page_id == page_id)
                ).first()

                if embedding:
                    session.delete(embedding)
                    session.commit()
                    return True
                return False
        except Exception:
            return False

    @staticmethod
    def cleanup_orphaned_embeddings() -> int:
        """Remove PageEmbedding records for pages that no longer exist."""
        try:
            with get_session() as session:
                # Get all page IDs and embedding page IDs
                all_pages = session.exec(select(Page)).all()
                all_embeddings = session.exec(select(PageEmbedding)).all()

                valid_page_ids = {p.id for p in all_pages if p.id is not None}

                # Find orphaned embeddings
                orphaned = [e for e in all_embeddings if e.page_id not in valid_page_ids]

                count = len(orphaned)

                for pe in orphaned:
                    session.delete(pe)

                session.commit()
                return count
        except Exception:
            return 0

    @staticmethod
    def reset_all_embeddings() -> int:
        """Reset all embedding records. Returns count of deleted records."""
        try:
            with get_session() as session:
                # Get all embeddings to count them
                all_embeddings = session.exec(select(PageEmbedding)).all()
                count = len(all_embeddings)

                # Delete all embeddings
                for embedding in all_embeddings:
                    session.delete(embedding)

                session.commit()
                return count
        except Exception:
            return 0
