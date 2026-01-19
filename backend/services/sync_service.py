from sqlalchemy.orm import Session
from .. import models
from .arena_service import ArenaClient
from .cin7_service import Cin7Client
import logging

logger = logging.getLogger(__name__)

def map_additional_attributes(item_json):
    """Helper to extract custom fields from the additionalAttributes array."""
    attrs = item_json.get("additionalAttributes", [])
    return {a.get("name"): a.get("value") for a in attrs}

def map_arena_to_cin7(arena_item):
    """Maps ArenaItem to Cin7 structure with required PriceTiers and account text."""
    
    # Combined Mfr String: [manufacturer] [manufacturer_item_number]
    mfr_info = f"{arena_item.manufacturer or ''} {arena_item.manufacturer_item_number or ''}".strip()
    
    return {
        "SKU": arena_item.item_number,
        "Name": arena_item.item_name,
        "Category": arena_item.category or "Fabricated Metal",
        "Description": arena_item.description or "",
        "UOM": arena_item.uom or "EA",
        "CostingMethod": arena_item.costing_method or "FIFO - Batch",
        
        # Updated Account Formats with descriptive text
        "InventoryAccount": "1402: Raw Materials",
        "COGSAccount": "4100: Cost of Sales",
        "RevenueAccount": "4001: Sales", 
        
        "DefaultLocation": "Main Warehouse",
        "Type": "Stock",
        "Sellable": True if arena_item.sellable == "Yes" else False,
        "Status": "Active",
        "InternalNote": arena_item.internal_note_erp or "",
        "AdditionalAttribute1": arena_item.revision,
        "AdditionalAttribute2": arena_item.last_glg_co,
        "AdditionalAttribute4": mfr_info,
        "AttributeSet": "Item",
        
        # Mandatory PriceTiers object to resolve Error 400
        "PriceTiers": {
            "Standard": 0.0000,
            "Tier 2": 0.0000,
            "Tier 3": 0.0000,
            "Tier 4": 0.0000,
            "Tier 5": 0.0000,
            "Tier 6": 0.0000,
            "Tier 7": 0.0000,
            "Tier 8": 0.0000,
            "Tier 9": 0.0000,
            "Tier 10": 0.0000
        }
    }



# ... keep your existing perform_sync and push_to_cin7 functions ...

def sync_single_item(db: Session, item_number: str, dry_run: bool = True):
    """Fetches a specific item from Arena and prepares/pushes it to Cin7."""
    config = db.query(models.Configuration).first()
    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}

    items = arena.list_all_items()
    target_summary = next((i for i in items if i['number'] == item_number), None)
    
    if not target_summary:
        return {"status": "error", "message": f"Item {item_number} not found in Arena"}

    guid = target_summary['guid']
    details = arena.get_item_details(guid)
    sourcing = arena.get_sourcing(guid)
    attrs = map_additional_attributes(details)
    
    results = sourcing.get("results", [])
    mfr_name, mfr_num = (None, None)
    if results:
        v_item = results[0].get("vendorItem", {})
        mfr_name = v_item.get("supplier", {}).get("name")
        mfr_num = v_item.get("number")

    temp_item = models.ArenaItem(
        item_number=item_number,
        item_name=details.get("name"),
        revision=details.get("revisionNumber"),
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

    cin7_payload = map_arena_to_cin7(temp_item)

    if dry_run:
        return {
            "status": "mock_success",
            "message": f"Prepared data for {item_number}",
            "payload": cin7_payload
        }
    
    response = cin7.create_or_update_product(cin7_payload)
    if response:
        return {"status": "live_success", "message": f"Item {item_number} synced to Cin7", "cin7_response": response}
    else:
        return {"status": "error", "message": f"Failed to push {item_number} to Cin7"}