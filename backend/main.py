from fastapi import FastAPI, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from . import models, schemas, database
from .services import sync_service
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from datetime import datetime

# Configure Logging
# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('app.log')
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(log_format)
f_handler.setFormatter(log_format)

# Add handlers to the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(c_handler)
logger.addHandler(f_handler)

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

@app.get("/admin/logs")
def get_system_logs(lines: int = 100):
    """Retrieve the last N lines of the system log."""
    try:
        with open("app.log", "r") as f:
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except FileNotFoundError:
        return {"logs": ["Log file not found."]}

# Scheduler Setup
scheduler = BackgroundScheduler()

def run_auto_sync():
    """Background job for auto-syncing Arena changes."""
    print(">>> SCHEDULER: EXECUTING RUN_AUTO_SYNC <<<")
    logger.info("Scheduler: Running Auto-Sync Job...")
    db = database.SessionLocal()
    try:
        sync_service.process_completed_changes(db)
    except Exception as e:
        logger.error(f"Scheduler Error: {e}")
    finally:
        db.close()

@app.on_event("startup")
def start_scheduler():
    print(">>> SCHEDULER STARTUP EVENT FIRED - INITIALIZING JOB <<<")
    config_db = database.SessionLocal()
    try:
        config = config_db.query(models.Configuration).first()
        # Default to every 5 minutes (300 seconds)
        # In production, we might read this interval from config
        # next_run_time=datetime.now() makes it run immediately upon adding
        scheduler.add_job(run_auto_sync, 'interval', minutes=5, id='arena_sync_job', next_run_time=datetime.now())
        scheduler.start()
        logger.info("Scheduler started. Running 'arena_sync_job' every 5 minutes.")
    finally:
        config_db.close()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down.")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()


@app.get("/settings", response_model=schemas.Configuration)
def get_settings(response: Response, db: Session = Depends(get_db)):
    # Prevent browser caching of settings
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    
    # Deterministic fetch: Order by ID to ensure we always get the first created row (Singleton pattern)
    config = db.query(models.Configuration).order_by(models.Configuration.id).first()
    if not config:
        # Create default config if not exists
        config = models.Configuration()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@app.post("/settings", response_model=schemas.Configuration)
def save_settings(settings: schemas.ConfigurationCreate, db: Session = Depends(get_db)):
    config = db.query(models.Configuration).order_by(models.Configuration.id).first()
    if not config:
        config = models.Configuration()
        db.add(config)
    
    config.arena_workspace_id = settings.arena_workspace_id
    config.arena_email = settings.arena_email
    config.arena_password = settings.arena_password
    config.cin7_api_user = settings.cin7_api_user
    config.cin7_api_key = settings.cin7_api_key
    config.auto_sync_enabled = settings.auto_sync_enabled
    config.item_prefix_filter = settings.item_prefix_filter
    
    # Reset connection flags on update (they will be re-verified)
    # config.is_arena_connected = False
    # config.is_cin7_connected = False
    
    db.commit()
    db.refresh(config)
    return config


@app.get("/test/arena/item/{guid}")

@app.post("/sync/arena")
def trigger_arena_harvest(db: Session = Depends(get_db)):
    return sync_service.perform_sync(db)

@app.post("/sync/cin7")
def trigger_cin7_push(dry_run: bool = True, db: Session = Depends(get_db)):
    """Triggers Full Sync (Harvest + Push). Use ?dry_run=false for live sync."""
    return sync_service.perform_full_sync(db, dry_run=dry_run)

@app.post("/sync/auto-process")
def trigger_auto_process(dry_run: bool = False, db: Session = Depends(get_db)):
    """Manually triggers the 'Completed Changes' poller logic."""
    return sync_service.process_completed_changes(db, dry_run=dry_run)

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

@app.get("/rules", response_model=list[schemas.SyncRule])
def read_rules(db: Session = Depends(get_db)):
    return db.query(models.SyncRule).all()

@app.post("/rules", response_model=schemas.SyncRule)
def create_rule(rule: schemas.SyncRuleCreate, db: Session = Depends(get_db)):
    db_rule = models.SyncRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@app.put("/rules/{rule_id}", response_model=schemas.SyncRule)
def update_rule(rule_id: int, rule_update: schemas.SyncRuleUpdate, db: Session = Depends(get_db)):
    db_rule = db.query(models.SyncRule).filter(models.SyncRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    for key, value in rule_update.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule