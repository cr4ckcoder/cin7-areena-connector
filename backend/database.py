from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/connector.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
    },
    pool_pre_ping=True,
    echo=False
)

# Configure SQLite for immediate writes and disable WAL mode
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=DELETE")
    cursor.execute("PRAGMA synchronous=FULL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Initialize database and run auto-migration for encryption."""
    from . import models
    
    # Run migration for sync stats columns FIRST (before creating tables)
    # This ensures the columns exist when SQLAlchemy tries to query the table
    try:
        from .migrate_stats import migrate_add_sync_stats
        migrate_add_sync_stats()
    except Exception as e:
        logger.warning(f"Stats migration skipped: {e}")
    
    # Create tables (will use existing table if it exists)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
    
    # Run auto-migration for credentials
    try:
        from .migrate_encryption import migrate_credentials_to_encrypted
        db = SessionLocal()
        try:
            results = migrate_credentials_to_encrypted(db)
            if results["migrated"] > 0:
                logger.info(f"Auto-migration: Encrypted {results['migrated']} credential fields")
            elif results["already_encrypted"] > 0:
                logger.debug("Auto-migration: All credentials already encrypted")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Auto-migration skipped: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
