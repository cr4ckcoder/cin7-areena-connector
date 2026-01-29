"""
Database migration to add sync statistics columns.
"""

import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def migrate_add_sync_stats():
    """Add total_synced_items and last_successful_sync columns to configuration table."""
    try:
        # Get database path from environment or use default
        db_url = os.getenv("DATABASE_URL", "sqlite:///./backend/connector.db")
        # Extract file path from sqlite URL
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        
        logger.info(f"Running stats migration on database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(configuration)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add total_synced_items if it doesn't exist
        if 'total_synced_items' not in columns:
            logger.info("Adding total_synced_items column...")
            cursor.execute("ALTER TABLE configuration ADD COLUMN total_synced_items INTEGER DEFAULT 0")
            logger.info("✓ Added total_synced_items column")
        else:
            logger.debug("total_synced_items column already exists")
        
        # Add last_successful_sync if it doesn't exist
        if 'last_successful_sync' not in columns:
            logger.info("Adding last_successful_sync column...")
            cursor.execute("ALTER TABLE configuration ADD COLUMN last_successful_sync DATETIME")
            logger.info("✓ Added last_successful_sync column")
        else:
            logger.debug("last_successful_sync column already exists")
        
        conn.commit()
        conn.close()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
