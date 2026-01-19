from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, database
from .services import sync_service

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/sync/arena")
def trigger_arena_harvest(db: Session = Depends(get_db)):
    return sync_service.perform_sync(db)

@app.post("/sync/cin7")
def trigger_cin7_push(dry_run: bool = True, db: Session = Depends(get_db)):
    """Triggers push to Cin7. Use ?dry_run=false for live sync."""
    return sync_service.push_to_cin7(db, dry_run=dry_run)

@app.post("/test/cin7/connection")
def test_cin7_connection(db: Session = Depends(get_db)):
    config = db.query(models.Configuration).first()
    if not config or not config.cin7_api_user:
        return {"status": "error", "message": "Credentials missing"}
    
    from .services.cin7_service import Cin7Client
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    product = cin7.get_product_by_sku("06-03416")
    return {"status": "success", "found": product is not None}


@app.post("/sync/on-demand")
def sync_on_demand_item(item_number: str, dry_run: bool = True, db: Session = Depends(get_db)):
    """
    Fetches a specific item from Arena and prepares/pushes it to Cin7.
    """
    from .services import sync_service
    return sync_service.sync_single_item(db, item_number, dry_run)