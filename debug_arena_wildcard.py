import os
import sys

# Add backend to path so we can import modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Configuration
from backend.services.arena_service import ArenaClient

# Setup DB connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/connector.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def test_arena_wildcard():
    print("--- Testing Arena API Wildcard Handling ---")
    config = db.query(Configuration).order_by(Configuration.id).first()
    if not config:
        print("❌ No config")
        return

    client = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    if not client.login():
        print("❌ Login Failed")
        return

    print("✅ Login Successful")

    # Test passing "*" explicitly
    print("\n1. Calling list_all_items('*')")
    try:
        items = client.list_all_items("*")
        print(f"   Count: {len(items)}")
        if len(items) > 0:
            print(f"   First item: {items[0].get('number')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test passing "" explicitly (Control)
    print("\n2. Calling list_all_items('')")
    try:
        items = client.list_all_items("")
        print(f"   Count: {len(items)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_arena_wildcard()
