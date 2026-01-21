import sys
import os

# Ensure we can import from the current directory if run as script
sys.path.append(os.getcwd())

try:
    from backend.database import SessionLocal
    from backend.models import Configuration
except ImportError:
    from database import SessionLocal
    from models import Configuration
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enable_auto_sync():
    db = SessionLocal()
    try:
        config = db.query(Configuration).first()
        if not config:
            logger.info("Creating new configuration...")
            config = Configuration()
            db.add(config)
        
        logger.info(f"Current Auto-Sync Status: {config.auto_sync_enabled}")
        
        if not config.auto_sync_enabled:
            config.auto_sync_enabled = True
            db.commit()
            logger.info("Successfully ENABLED Auto-Sync.")
        else:
            logger.info("Auto-Sync is already enabled.")
            
        # Verify
        db.refresh(config)
        logger.info(f"Verified Status: {config.auto_sync_enabled}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    enable_auto_sync()
