
from services.sync_service import process_completed_changes
from database import SessionLocal

db = SessionLocal()
process_completed_changes(db)
print("Check logs")
