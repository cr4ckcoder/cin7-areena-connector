from sqlalchemy.orm import Session
from .. import models
from .arena_service import ArenaClient
from .cin7_service import Cin7Client
import logging

logger = logging.getLogger(__name__)

def get_rule_value(db: Session, key: str, default: str):
    """Helper to fetch dynamic sync rules from the database."""
    rule = db.query(models.SyncRule).filter(
        models.SyncRule.rule_key == key, 
        models.SyncRule.is_enabled == True
    ).first()
    return rule.rule_value if rule else default

def map_additional_attributes(item_json):
    """Helper to extract custom fields from the additionalAttributes array."""
    attrs = item_json.get("additionalAttributes", [])
    return {a.get("name"): a.get("value") for a in attrs}

def map_arena_to_cin7(arena_item, db: Session, bom_resolved_list=None):
    """Maps ArenaItem to Cin7 structure enforcing sync rules for accounts and defaults."""
    
    # Combined Mfr String: [manufacturer] [manufacturer_item_number]
    mfr_info = f"{arena_item.manufacturer or ''} {arena_item.manufacturer_item_number or ''}".strip()
    
    payload = {
        "SKU": arena_item.item_number,
        "Name": arena_item.item_name,
        "Category": arena_item.category or "Fabricated Metal",
        "Description": arena_item.description or "",
        "UOM": arena_item.uom or "EA",
        "CostingMethod": arena_item.costing_method or "FIFO - Batch",
        
        # Rules #2, #3, #4: Dynamic defaults from DB
        "RevenueAccount": get_rule_value(db, "RevenueAccount", "4001: OEM Product"),
        "InventoryAccount": get_rule_value(db, "InventoryAccount", "1402: Raw Materials"),
        "COGSAccount": get_rule_value(db, "COGSAccount", "4100: Cost of Sales"),
        "DefaultLocation": get_rule_value(db, "DefaultLocation", "Main Warehouse"),
        "Type": get_rule_value(db, "ProductType", "Stock"),
        
        "Sellable": True if arena_item.sellable == "Yes" else False,
        "Status": "Active",
        "InternalNote": arena_item.internal_note_erp or "",
        "AdditionalAttribute1": arena_item.revision,
        "AdditionalAttribute2": arena_item.last_glg_co,
        "AdditionalAttribute4": mfr_info,
        "AttributeSet": "Item",
        
        # Mandatory PriceTiers object to resolve Cin7 Error 400
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

    if bom_resolved_list:
        payload["AssemblyBOM"] = True
        payload["BillOfMaterial"] = True 
        payload["QuantityToProduce"] = 1.0
        payload["AssemblyCostEstimationMethod"] = "Average Cost" # Changed from "Total" to valid enum
        
        bom_products = []
        for item in bom_resolved_list:
            entry = {
                "Quantity": item.get("qty", 0)
            }
            if item.get("cin7_id"):
                entry["ComponentProductID"] = item.get("cin7_id")
            else:
                entry["ProductCode"] = item.get("sku")
                
            bom_products.append(entry)
        
        payload["BillOfMaterialsProducts"] = bom_products
    else:
        payload["AssemblyBOM"] = False
        payload["BillOfMaterial"] = False
        
    return payload

def perform_sync(db: Session):
    """Harvests items from Arena to SQLite, enforcing sync filters."""
    config = db.query(models.Configuration).first()
    if not config or not config.arena_workspace_id:
        return {"status": "error", "message": "Arena configuration missing"}

    # Rule #7: Allowed production stage lifecycle statuses
    # Rule #7: Allowed production stage lifecycle statuses
    allowed_lifecycles = ["In Production", "Deprecated", "Obsolete", "Production"]

    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}

    try:
        # Pass the prefix filter to the service method for server-side filtering
        items_summary = arena.list_all_items(config.item_prefix_filter)
        count = 0
        skipped_lifecycle = 0
        skipped_transfer_erp = 0

        for summary in items_summary:
            # Client-side filter removed as it is now handled by the API query
            
            guid = summary['guid']
            details = arena.get_item_details(guid)
            if not details:
                continue
                
            # Rule #7: Lifecycle Status Filter
            lifecycle = details.get("lifecyclePhase", {}).get("name")
            if lifecycle not in allowed_lifecycles:
                skipped_lifecycle += 1
                continue

            attrs = map_additional_attributes(details)
            
            # Rule #1: Sync Filter based on "Transfer Data to ERP?" field
            if attrs.get("Transfer Data to ERP?") != "Yes":
                skipped_transfer_erp += 1
                continue
            
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
                lifecycle_phase=lifecycle,
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
        return {
            "status": "success", 
            "items_harvested": count, 
            "skipped_lifecycle": skipped_lifecycle,
            "skipped_transfer_erp": skipped_transfer_erp,
            "item-prefix": config.item_prefix_filter,
            "raw_data": items_summary
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {str(e)}")
        return {"status": "error", "message": str(e)}

def _ensure_product_exists(db: Session, sku: str, arena_client: ArenaClient, cin7_client: Cin7Client):
    """
    Ensures a product exists in Cin7. If not, fetches from Arena (including BOM checks) and creates it.
    This is used for recursive BOM component syncing.
    """
    # 1. Check if exists in Cin7
    existing = cin7_client.get_product_by_sku(sku)
    if existing:
        return existing["ID"]

    # 2. If not, we need to fetch it from Arena
    # Check if we have it in our local DB first (Harvested)
    db_item = db.query(models.ArenaItem).filter(models.ArenaItem.item_number == sku).first()
    
    target_item = None
    bom_items = []
    
    if db_item:
        target_item = db_item
        # Fetch BOM from Arena using GUID from DB
        try:
            bom_items = arena_client.get_bom(db_item.guid)
        except Exception as e:
            logger.warning(f"Failed to fetch BOM for component {sku}: {e}")
    else:
        # Not in DB, fetch from Arena API
        # logger.info(f"Component {sku} missing in Cin7 and DB. Fetching from Arena...")
        items = arena_client.list_all_items(sku)
        summary = next((i for i in items if i['number'] == sku), None)
        
        if not summary:
            logger.error(f"Component {sku} not found in Arena. Cannot sync.")
            return None
            
        guid = summary['guid']
        details = arena_client.get_item_details(guid)
        sourcing = arena_client.get_sourcing(guid)
        if details:
            attrs = map_additional_attributes(details)
            results = sourcing.get("results", [])
            mfr_name, mfr_num = None, None
            if results:
                v_item = results[0].get("vendorItem", {})
                mfr_name = v_item.get("supplier", {}).get("name")
                mfr_num = v_item.get("number")
                
            # Create transient object for mapping
            target_item = models.ArenaItem(
                guid=guid,
                item_number=details.get("number"),
                item_name=details.get("name"),
                revision=details.get("revisionNumber"),
                # lifecycle_phase=details.get("lifecyclePhase", {}).get("name"), # Might be missing in details if not queried?
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
            # Fetch BOM
            try:
                bom_items = arena_client.get_bom(guid)
            except:
                pass

    if not target_item:
        return None

    # 3. Recursive Check for this component's components
    if bom_items:
        # Resolve sub-components first
        sub_bom_resolved = []
        for line in bom_items:
            comp_sku = line.get("item", {}).get("number")
            qty = line.get("quantity", 0)
            if comp_sku:
                # Recursion
                c_id = _ensure_product_exists(db, comp_sku, arena_client, cin7_client)
                sub_bom_resolved.append({"sku": comp_sku, "qty": qty, "cin7_id": c_id})
                
        # 4. Map and Create with BOM info
        payload = map_arena_to_cin7(target_item, db, sub_bom_resolved)
    else:
        payload = map_arena_to_cin7(target_item, db)

    response = cin7_client.create_or_update_product(payload)
    
    if response.get("status") == "success":
        data = response.get("data", {})
        # handle case where list is returned
        prod_id = None
        if isinstance(data, list) and data:
            prod_id = data[0].get("ID")
        else:
            prod_id = data.get("ID")
            
        # If we created it and it had a BOM, we must upload it now
        if prod_id and bom_items:
             # Logic to upload BOM for component
             # Reuse resolved list
             bom_payload = []
             for entry in sub_bom_resolved: # defined above if bom_items was true
                 line = {"Quantity": entry["qty"]}
                 if entry.get("cin7_id"):
                     line["ComponentProductID"] = entry["cin7_id"]
                 else:
                     line["ProductCode"] = entry["sku"]
                 bom_payload.append(line)
             
             cin7_client.upload_bill_of_materials(prod_id, bom_payload)
             
        return prod_id
        
    return None

def push_to_cin7(db: Session, dry_run: bool = True):
    """Bulk pushes filtered items from SQLite to Cin7."""
    config = db.query(models.Configuration).first()
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    
    # Needs Arena login for fetching BOMs even in dry run
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}
    
    # Fetch items that match the current dynamic prefix
    # Fetch items that match the current dynamic prefix
    query = db.query(models.ArenaItem)
    if config.item_prefix_filter and config.item_prefix_filter != "*":
        query = query.filter(
            models.ArenaItem.item_number.like(f"{config.item_prefix_filter}%")
        )
    items = query.all()
    
    results = []
    summary = {"success": 0, "failed": 0, "mocked": 0}

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_item_payload(item):
        """Helper to process a single item for parallel execution."""
        try:
            bom_items = []
            try:
                bom_items = arena.get_bom(item.guid)
            except Exception as e:
                logger.error(f"Failed to fetch BOM for {item.item_number}: {e}")
            
            # Resolve Components
            bom_resolved_list = []
            for line in bom_items:
                comp_sku = line.get("item", {}).get("number")
                qty = line.get("quantity", 0)
                
                if comp_sku:
                    cin7_id = None
                    if not dry_run:
                        cin7_id = _ensure_product_exists(db, comp_sku, arena, cin7)
                    
                    bom_resolved_list.append({
                        "sku": comp_sku,
                        "qty": qty,
                        "cin7_id": cin7_id
                    })

            payload = map_arena_to_cin7(item, db, bom_resolved_list)
            return {"status": "success", "payload": payload, "sku": item.item_number, "mode": "DRY_RUN" if dry_run else "LIVE"}
            
        except Exception as e:
            return {"status": "error", "message": str(e), "sku": item.item_number}

    # Parallel Execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_item_payload, item): item for item in items}
        
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                if result["status"] == "success":
                    if dry_run:
                        summary["mocked"] += 1
                        results.append({"SKU": result["sku"], "Mode": result["mode"], "Payload": result["payload"]})
                    else:
                        response = cin7.create_or_update_product(result["payload"])
                        if response.get("status") == "success":
                            summary["success"] += 1
                        else:
                            summary["failed"] += 1
                            results.append({"SKU": result["sku"], "Error": response.get("message")})
                else:
                    summary["failed"] += 1
                    results.append({"SKU": result["sku"], "Error": result["message"]})
            except Exception as exc:
                logger.error(f"Item {item.item_number} generated an exception: {exc}")
                summary["failed"] += 1
                results.append({"SKU": item.item_number, "Error": str(exc)})
            
    return {"status": "complete", "dry_run": dry_run, "summary": summary, "details": results}

def sync_single_item(db: Session, item_number: str, dry_run: bool = True):
    """On-demand sync for a specific SKU."""
    config = db.query(models.Configuration).first()
    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}

    # Use the item number as filter to find the specific item efficiently
    items = arena.list_all_items(item_number)
    target = next((i for i in items if i['number'] == item_number), None)
    
    if not target:
        return {"status": "error", "message": f"Item {item_number} not found in Arena"}

    guid = target['guid']
    details = arena.get_item_details(guid)
    sourcing = arena.get_sourcing(guid)
    attrs = map_additional_attributes(details)
    
    results = sourcing.get("results", [])
    mfr_name, mfr_num = None, None
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

    bom_items = []
    try:
       bom_items = arena.get_bom(guid)
    except Exception as e:
       logger.warning(f"Failed to fetch BOM for single sync {item_number}: {e}")

    # Prepare resolved list
    bom_resolved_list = []
    for line in bom_items:
        comp_sku = line.get("item", {}).get("number")
        qty = line.get("quantity", 0)
        
        if comp_sku:
            cin7_id = None
            if not dry_run:
                cin7_id = _ensure_product_exists(db, comp_sku, arena, cin7)
            
            bom_resolved_list.append({
                "sku": comp_sku,
                "qty": qty,
                "cin7_id": cin7_id
            })

    cin7_payload = map_arena_to_cin7(temp_item, db, bom_resolved_list)

    if dry_run:
        return {"status": "mock_success", "payload": cin7_payload}
    
    response = cin7.create_or_update_product(cin7_payload)
    return response

def process_completed_changes(db: Session, dry_run: bool = False):
    """
    Poller function to check for 'Completed' changes in Arena and sync affected items.
    Example usage: Scheduled every X minutes.
    """
    logger.info("Starting Polling for Completed Changes...")
    config = db.query(models.Configuration).first()
    if not config or not config.auto_sync_enabled:
        logger.info("Auto-sync disabled or config missing. Skipping.")
        return

    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    if not arena.login():
        logger.error("Arena login failed during polling.")
        return

    # Fetch recent changes
    changes = arena.get_changes() 
    # Logic: Look for changes with status 'Completed' (or Effective).
    # In a real impl, we'd filter by 'processed_after' date or similar to avoid re-syncing old ones.
    # For MVP: We will iterate and sync. (Constraint: this might re-sync items often if not filtered)
    
    # TODO: Implement "High Water Mark" or "Last Sync Timestamp" in DB to filter old changes.
    # For now, we'll process the recent ones found.
    
    synced_count = 0
    errors = []

    for change in changes:
        # Check status options. Usually 'Completed' or 'Effective'.
        status = change.get("status", {}).get("name")
        if status in ["Completed", "Effective"]: 
            change_number = change.get("number")
            logger.info(f"Processing Change {change_number} ({status})")
            
            # Fetch affected items
            items = arena.get_change_items(change.get("guid"))
            for line in items:
                # Structure might be line['item']['number']
                item_ref = line.get("item", {})
                sku = item_ref.get("number")
                
                if sku:
                    action = "Dry-Run Syncing" if dry_run else "Auto-Syncing"
                    logger.info(f"{action} Item {sku} from Change {change_number}")
                    # Trigger the existing single item sync
                    result = sync_single_item(db, sku, dry_run=dry_run)
                    
                    if result.get("status") == "success":
                        synced_count += 1
                    elif result.get("status") == "mock_success":
                         # Dry run success
                         synced_count += 1
                         # Store payload for review if needed, but summary is enough for now
                    else:
                        errors.append(f"{sku}: {result.get('message')}")
    
    logger.info(f"Polling Complete. Processed {synced_count} items. Errors: {len(errors)}")
    return {"synced": synced_count, "errors": errors, "dry_run": dry_run}

def perform_full_sync(db: Session, dry_run: bool = True):
    """
    Orchestrates the full sync process:
    1. Harvests items from Arena to Local DB.
    2. Pushes items from Local DB to Cin7 (or mocks it if dry_run).
    """
    # Step 1: Harvest
    harvest_result = perform_sync(db)
    if harvest_result.get("status") == "error":
        return {
            "status": "error",
            "message": f"Harvest Failed: {harvest_result.get('message')}",
            "harvest_details": harvest_result
        }
    
    # Step 2: Push (or Dry Run Push)
    push_result = push_to_cin7(db, dry_run=dry_run)
    
    # Combine results
    return {
        "status": push_result.get("status"),
        "dry_run": dry_run,
        "harvest_summary": {
            "items_harvested": harvest_result.get("items_harvested"),
            "skipped_lifecycle": harvest_result.get("skipped_lifecycle"),
            "skipped_transfer_erp": harvest_result.get("skipped_transfer_erp")
        },
        "push_summary": push_result.get("summary"),
        "details": push_result.get("details")
    }