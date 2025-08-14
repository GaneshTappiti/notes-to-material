"""
Migration script to improve embed tracking by:
1. Removing dependency on JSON tracking files
2. Adding database indexes for better performance
3. Migrating any existing JSON tracking data to database if needed
"""

from pathlib import Path
import json
from sqlalchemy import text
from ..models import get_session, PageEmbedding

def migrate_embed_tracking():
    """Migrate from JSON file tracking to pure database tracking."""

    # Check for existing JSON tracking file
    embed_track_path = Path('storage/embed_tracking.json')
    migrated_count = 0

    if embed_track_path.exists():
        try:
            with open(embed_track_path, 'r') as f:
                tracking_data = json.load(f)

            page_ids = tracking_data.get('page_ids', [])

            if page_ids:
                with get_session() as session:
                    # Check which pages don't have embeddings in DB yet
                    existing_page_ids = {pe.page_id for pe in session.query(PageEmbedding).all()}
                    missing_page_ids = set(page_ids) - existing_page_ids

                    if missing_page_ids:
                        print(f"Found {len(missing_page_ids)} pages in JSON tracking not in database")
                        # Note: We can't create PageEmbedding records without actual embeddings
                        # This is just informational for now

                    print(f"JSON tracking had {len(page_ids)} pages, DB has {len(existing_page_ids)} embeddings")

            # Backup and remove the JSON file
            backup_path = embed_track_path.with_suffix('.json.backup')
            embed_track_path.rename(backup_path)
            print(f"Backed up tracking file to {backup_path}")

        except Exception as e:
            print(f"Error migrating tracking file: {e}")

    # Ensure proper indexes exist
    with get_session() as session:
        try:
            # Add index on page_id if it doesn't exist
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_pageembedding_page_id ON pageembedding(page_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_pageembedding_file_id ON pageembedding(file_id)"))
            session.commit()
            print("Database indexes updated")
        except Exception as e:
            print(f"Error creating indexes: {e}")
            session.rollback()

    return migrated_count

if __name__ == "__main__":
    migrate_embed_tracking()
