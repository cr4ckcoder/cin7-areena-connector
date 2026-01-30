"""
Database migration utility to encrypt existing plaintext credentials.

This script can be run manually or is automatically triggered on application startup.
"""

import logging
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from .encryption import migrate_to_encrypted, is_encrypted

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_credentials_to_encrypted(db: Session) -> dict:
    """
    Migrate plaintext credentials to encrypted format.
    
    Args:
        db: Database session
        
    Returns:
        dict: Migration results with counts
    """
    results = {
        "migrated": 0,
        "already_encrypted": 0,
        "errors": 0,
        "fields_migrated": []
    }
    
    try:
        config = db.query(models.Configuration).first()
        
        if not config:
            logger.info("No configuration found, skipping migration")
            return results
        
        logger.info("Checking credentials for encryption migration...")
        
        # Check and migrate each sensitive field
        fields_to_check = [
            ('_arena_email', 'arena_email'),
            ('_arena_password', 'arena_password'),
            ('_cin7_api_user', 'cin7_api_user'),
            ('_cin7_api_key', 'cin7_api_key')
        ]
        
        for db_field, display_name in fields_to_check:
            value = getattr(config, db_field, "")
            
            if not value:
                logger.debug(f"{display_name}: Empty, skipping")
                continue
            
            if is_encrypted(value):
                logger.info(f"{display_name}: Already encrypted ✓")
                results["already_encrypted"] += 1
            else:
                logger.info(f"{display_name}: Plaintext detected, migrating...")
                try:
                    encrypted_value = migrate_to_encrypted(value)
                    setattr(config, db_field, encrypted_value)
                    results["migrated"] += 1
                    results["fields_migrated"].append(display_name)
                    logger.info(f"{display_name}: Migrated to encrypted ✓")
                except Exception as e:
                    logger.error(f"{display_name}: Migration failed - {e}")
                    results["errors"] += 1
        
        # Commit changes if any migrations occurred
        if results["migrated"] > 0:
            db.commit()
            logger.info(f"Migration complete: {results['migrated']} fields encrypted")
        else:
            logger.info("No migration needed - all credentials already encrypted")
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        db.rollback()
        results["errors"] += 1
    
    return results


def run_migration():
    """Run migration as standalone script."""
    logger.info("=== Starting Credential Encryption Migration ===")
    
    # Create tables if they don't exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        results = migrate_credentials_to_encrypted(db)
        
        logger.info("\n=== Migration Results ===")
        logger.info(f"Fields migrated: {results['migrated']}")
        logger.info(f"Already encrypted: {results['already_encrypted']}")
        logger.info(f"Errors: {results['errors']}")
        
        if results['fields_migrated']:
            logger.info(f"Migrated fields: {', '.join(results['fields_migrated'])}")
        
        if results['errors'] > 0:
            logger.warning("Migration completed with errors!")
            return False
        else:
            logger.info("Migration completed successfully! ✓")
            return True
            
    finally:
        db.close()


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
