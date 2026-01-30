"""
Initialize default admin user on first run.
"""

from sqlalchemy.orm import Session
from . import models
from .database import SessionLocal
from .auth_utils import hash_password
import logging

logger = logging.getLogger(__name__)


def init_default_admin():
    """
    Create default admin user if no users exist.
    
    Default credentials:
    - Username: admin
    - Password: admin
    
    IMPORTANT: Change the default password immediately after first login!
    """
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(models.User).count()
        
        if user_count == 0:
            logger.info("No users found. Creating default admin user...")
            
            # Create default admin user
            admin = models.User(
                username="admin",
                hashed_password=hash_password("admin"),
                is_active=True
            )
            
            db.add(admin)
            db.commit()
            
            logger.warning("=" * 60)
            logger.warning("DEFAULT ADMIN USER CREATED")
            logger.warning("Username: admin")
            logger.warning("Password: admin")
            logger.warning("IMPORTANT: Change the default password immediately!")
            logger.warning("=" * 60)
        else:
            logger.debug(f"Users already exist ({user_count} users)")
            
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        db.rollback()
    finally:
        db.close()
