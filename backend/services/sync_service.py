from sqlalchemy.orm import Session
from .. import models
from .arena_service import ArenaClient
from .cin7_service import Cin7Client
import datetime

def perform_sync(db: Session):
    config = db.query(models.Configuration).first()
    if not config:
        return {"status": "error", "message": "Configuration not found"}

    # Initialize Clients
    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)

    # 1. Verify Connections
    if not arena.verify_connection():
         return {"status": "error", "message": "Failed to connect to Arena PLM"}
    if not cin7.verify_connection():
         return {"status": "error", "message": "Failed to connect to Cin7 Omni"}

    # 2. Fetch Data (Mocked for now as we agreed)
    # In reality: changes = arena.get_completed_changes()
    # For logic verification, we simulate a fetched item
    
    simulated_items = [
        {
            "guid": "item_guid_1",
            "item_number": "PRD-001",
            "item_name": "Pro Widget",
            "revision": "A",
            "item_category": "Finished Goods",
            "description": "High quality widget",
            "unit_of_measure": "Each",
            "transfer_data_to_erp": "Yes", # Filter Check
            "manufacturer": "Acme Corp",
            "manufacturer_item_number": "WID-99",
            # ... other fields
        },
        {
            "guid": "item_guid_2",
            "item_number": "PRD-002",
            "transfer_data_to_erp": "No", # Should be skipped
        }
    ]

    processed_count = 0
    errors = []

    for item in simulated_items:
        # 3. Filtering Logic
        if item.get("transfer_data_to_erp") != "Yes":
            print(f"Skipping {item.get('item_number')} due to filter.")
            continue

        # 4. Mapping Logic
        cin7_data = map_item_to_cin7(item)

        # 5. Sync to Cin7
        try:
            existing = cin7.get_product_by_code(cin7_data["ProductCode"])
            if existing:
                cin7.update_product(existing["id"], cin7_data)
            else:
                cin7.create_product(cin7_data)
            
            # BOM Handling (Mocked)
            # bom = arena.get_item_bom(item["guid"])
            # Filter BOM children
            # valid_bom = [child for child in bom if child.get("transfer_data_to_erp") == "Yes"]
            # cin7.update_bom(...)
            
            processed_count += 1
        except Exception as e:
            errors.append(f"Failed to sync {item.get('item_number')}: {str(e)}")

    # Update Last Sync Time
    config.last_sync_time = datetime.datetime.utcnow()
    db.commit()

    return {
        "status": "success",
        "message": "Sync completed successfully",
        "processed_items": processed_count,
        "errors": errors
    }

def map_item_to_cin7(arena_item):
    return {
        "ProductCode": arena_item.get("item_number"),
        "Name": arena_item.get("item_name"),
        "AdditionalAttribute1": arena_item.get("revision"), # Revision
        "Category": arena_item.get("item_category"),
        "Description": arena_item.get("description"),
        "DefaultUnitOfMeasure": arena_item.get("unit_of_measure"),
        "StockControl": "FIFO", # Default
        "OrderType": "Stock", # Product Type default
        "AdditionalAttribute4": f"{arena_item.get('manufacturer', '')} {arena_item.get('manufacturer_item_number', '')}".strip()
    }
