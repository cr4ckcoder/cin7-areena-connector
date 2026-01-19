from sqlalchemy.orm import Session
from .. import models
from .arena_service import ArenaClient
from .cin7_service import Cin7Client
import logging

logger = logging.getLogger(__name__)

def map_additional_attributes(item_json):
    attrs = item_json.get("additionalAttributes", [])
    return {a.get("name"): a.get("value") for a in attrs}

def map_arena_to_cin7(arena_item):
    """Maps ArenaItem to Cin7 structure with required defaults."""
    # Combined Mfr String: [manufacturer] [manufacturer_item_number]
    mfr_info = f"{arena_item.manufacturer or ''} {arena_item.manufacturer_item_number or ''}".strip()
    
    return {
        "SKU": arena_item.item_number,
        "Name": arena_item.item_name,
        "Category": arena_item.category or "Fabricated Metal",
        "Description": arena_item.description,
        "UOM": arena_item.uom or "EA",
        "CostingMethod": arena_item.costing_method or "FIFO - Batch",
        "InventoryAccount": arena_item.inventory_account or "1402",
        "COGSAccount": arena_item.cogs_account or "4100",
        "RevenueAccount": "4001", # System Default
        "DefaultLocation": "Main Warehouse", # System Default
        "Type": "Stock", # System Default
        "Sellable": True if arena_item.sellable == "Yes" else False,
        "Status": "Active",
        "InternalNote": arena_item.internal_note_erp,
        "AdditionalAttribute1": arena_item.revision, #
        "AdditionalAttribute2": arena_item.last_glg_co,
        "AdditionalAttribute4": mfr_info, # Combined Mfr Info
        "AttributeSet": "Item"
    }

def perform_sync(db: Session):
    config = db.query(models.Configuration).first()
    if not config or not config.arena_workspace_id:
        return {"status": "error", "message": "Arena configuration missing"}

    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}

    try:
        items_summary = arena.list_all_items()
        count = 0
        for summary in items_summary:
            guid = summary['guid']
            details = arena.get_item_details(guid)
            if not details: continue
                
            attrs = map_additional_attributes(details)
            sourcing = arena.get_sourcing(guid)
            results = sourcing.get("results", [])
            mfr_name, mfr_num = None, None
            
            if results:
                v_item = results[0].get("vendorItem", {})
                mfr_name = v_item.get("supplier", {}).get("name")
                mfr_num = v_item.get("number")

            db_item = models.ArenaItem(
                guid=guid,
                item_number=details.get("number"),
                item_name=details.get("name"),
                revision=details.get("revisionNumber"),
                lifecycle_phase=details.get("lifecyclePhase", {}).get("name"),
                category=details.get("category", {}).get("name"),
                description=details.get("description"),
                uom=details.get("uom"),
                costing_method=attrs.get("Costing Method"),
                inventory_account=attrs.get("Inventory Account"),
                cogs_account=attrs.get("COGS Account"),
                sellable=attrs.get("Sellable"),
                internal_note_erp=attrs.get("Internal Note for ERP"),
                last_glg_co=attrs.get("Last GLG CO"),
                manufacturer=mfr_name,
                manufacturer_item_number=mfr_num
            )
            db.merge(db_item)
            count += 1
        db.commit()
        return {"status": "success", "items_harvested": count}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

def push_to_cin7(db: Session, dry_run: bool = True):
    """Pushes '06-' items to Cin7 with a dry-run flag."""
    config = db.query(models.Configuration).first()
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    
    test_items = db.query(models.ArenaItem).filter(models.ArenaItem.item_number.like("06-%")).all()
    
    output = []
    summary = {"success": 0, "failed": 0, "mocked": 0}

    for item in test_items:
        payload = map_arena_to_cin7(item)
        
        if dry_run:
            summary["mocked"] += 1
            output.append({"SKU": item.item_number, "Mode": "DRY_RUN", "Payload": payload})
        else:
            response = cin7.create_or_update_product(payload)
            if response:
                summary["success"] += 1
                output.append({"SKU": item.item_number, "Status": "Synced"})
            else:
                summary["failed"] += 1
                output.append({"SKU": item.item_number, "Status": "Failed"})
            
    return {"status": "complete", "dry_run": dry_run, "summary": summary, "details": output}