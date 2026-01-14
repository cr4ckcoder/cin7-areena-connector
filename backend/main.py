from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, database
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for Docker/Host networking simplicity, or restrict to ["http://localhost", "http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/settings", response_model=schemas.Configuration)
def get_settings(db: Session = Depends(get_db)):
    config = db.query(models.Configuration).first()
    if not config:
        # Create default config if not exists
        config = models.Configuration()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@app.post("/settings", response_model=schemas.Configuration)
def save_settings(settings: schemas.ConfigurationCreate, db: Session = Depends(get_db)):
    config = db.query(models.Configuration).first()
    if not config:
        config = models.Configuration()
        db.add(config)
    
    config.arena_workspace_id = settings.arena_workspace_id
    config.arena_email = settings.arena_email
    config.arena_password = settings.arena_password
    config.cin7_api_user = settings.cin7_api_user
    config.cin7_api_key = settings.cin7_api_key
    config.auto_sync_enabled = settings.auto_sync_enabled
    
    # Reset connection flags on update (they will be re-verified)
    # config.is_arena_connected = False
    # config.is_cin7_connected = False
    
    db.commit()
    db.refresh(config)
    return config

@app.post("/sync", response_model=schemas.SyncResult)
def trigger_sync(db: Session = Depends(get_db)):
    from .services import sync_service
    return sync_service.perform_sync(db)

@app.get("/test/arena/item/{guid}")
def test_arena_item(guid: str, db: Session = Depends(get_db)):
    config = db.query(models.Configuration).first()
    if not config:
        raise HTTPException(status_code=400, detail="Configuration not found")
        
    from .services.arena_service import ArenaClient
    client = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    
    if not client.login():
        raise HTTPException(status_code=400, detail="Failed to login to Arena")
        
    item_details = client.get_item_details(guid)
    bom = client.get_item_bom(guid)
    
    return {
        "item": item_details,
        "bom": bom
    }
