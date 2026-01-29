from sqlalchemy.orm import Session
from .. import models
from .arena_service import ArenaClient
from .cin7_service import Cin7Client
import logging
from datetime import datetime

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

def _ensure_product_exists(db: Session, sku: str, arena_client: ArenaClient, cin7_client: Cin7Client, dry_run: bool = False):
    """
    Ensures a product exists in Cin7. If not, fetches from Arena (including BOM checks) and creates it.
    This is used for recursive BOM component syncing.
    
    Args:
        db: Database session
        sku: Product SKU to ensure exists
        arena_client: Arena API client
        cin7_client: Cin7 API client
        dry_run: If True, skip actual Cin7 API calls (for testing)
    
    Returns:
        Product ID if successful, None if component should be excluded (Transfer to ERP = No)
    """
    # 1. Check if exists in Cin7 (skip in dry run)
    if not dry_run:
        existing = cin7_client.get_product_by_sku(sku)
        if existing:
            return existing["ID"]
    else:
        # In dry run, assume product doesn't exist to test full flow
        logger.info(f"[DRY RUN] Skipping Cin7 check for {sku}")

    # 2. If not, we need to fetch it from Arena
    # Check if we have it in our local DB first (Harvested)
    db_item = db.query(models.ArenaItem).filter(models.ArenaItem.item_number == sku).first()
    
    target_item = None
    bom_items = []
    transfer_to_erp = None
    
    if db_item:
        target_item = db_item
        transfer_to_erp = db_item.transfer_to_erp
        # Fetch BOM from Arena using GUID from DB
        try:
            bom_items = arena_client.get_bom(db_item.guid)
        except Exception as e:
            logger.warning(f"Failed to fetch BOM for component {sku}: {e}")
    else:
        # Not in DB, fetch from Arena API
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
            transfer_to_erp = attrs.get("Transfer Data to ERP?")
            
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
                manufacturer_item_number=mfr_num,
                transfer_to_erp=transfer_to_erp
            )
            # Fetch BOM
            try:
                bom_items = arena_client.get_bom(guid)
            except:
                pass

    if not target_item:
        return None
    
    # BOM Exception Rule: If component has "Transfer to ERP?" = "No", exclude it from BOM
    if transfer_to_erp and transfer_to_erp != "Yes":
        logger.warning(f"Component {sku} has 'Transfer to ERP?' = '{transfer_to_erp}' - excluding from BOM")
        return None

    # 3. Recursive Check for this component's components
    if bom_items:
        # Resolve sub-components first, filtering out excluded items
        sub_bom_resolved = []
        for line in bom_items:
            comp_sku = line.get("item", {}).get("number")
            qty = line.get("quantity", 0)
            if comp_sku:
                # Recursion with dry_run flag
                c_id = _ensure_product_exists(db, comp_sku, arena_client, cin7_client, dry_run)
                # Only add to BOM if component was successfully resolved (not excluded)
                # In dry run, c_id will be None, but we still check if it was excluded (function returned None due to filter)
                # We need to differentiate between "excluded" and "would be created in dry run"
                # If the function returns None and it's NOT because of dry_run, it means excluded
                if c_id is not None:
                    # Component exists or was created
                    sub_bom_resolved.append({"sku": comp_sku, "qty": qty, "cin7_id": c_id})
                elif dry_run:
                    # In dry run, check if component would be excluded by re-checking the filter
                    # We can do this by checking the database or Arena for the transfer_to_erp field
                    db_check = db.query(models.ArenaItem).filter(models.ArenaItem.item_number == comp_sku).first()
                    if db_check and db_check.transfer_to_erp and db_check.transfer_to_erp != "Yes":
                        logger.info(f"Skipping excluded component {comp_sku} from BOM of {sku} (Transfer to ERP = {db_check.transfer_to_erp})")
                    else:
                        # Would be created in dry run
                        sub_bom_resolved.append({"sku": comp_sku, "qty": qty, "cin7_id": None})
                else:
                    logger.info(f"Skipping excluded component {comp_sku} from BOM of {sku}")
                
        # 4. Map and Create with BOM info
        payload = map_arena_to_cin7(target_item, db, sub_bom_resolved)
    else:
        payload = map_arena_to_cin7(target_item, db)

    # Skip actual Cin7 API calls in dry run mode
    if dry_run:
        logger.info(f"[DRY RUN] Would create product {sku} in Cin7")
        return None  # Return None in dry run since no real ID is created
    
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
        if prod_id and bom_items and sub_bom_resolved:
             # Logic to upload BOM for component
             # Reuse resolved list
             bom_payload = []
             for entry in sub_bom_resolved:
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
    """
    Bulk pushes filtered items from SQLite to Cin7 using two-phase processing.
    
    Phase 1: Process simple items (no BOM) in parallel for performance
    Phase 2: Process assembly items (with BOM) sequentially with dependency resolution
    
    This ensures BOM components are created before parent assemblies.
    """
    config = db.query(models.Configuration).first()
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    
    # Needs Arena login for fetching BOMs even in dry run
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}
    
    # Fetch items that match the current dynamic prefix
    query = db.query(models.ArenaItem)
    if config.item_prefix_filter and config.item_prefix_filter != "*":
        query = query.filter(
            models.ArenaItem.item_number.like(f"{config.item_prefix_filter}%")
        )
    items = query.all()
    
    results = []
    summary = {"success": 0, "failed": 0, "mocked": 0}
    
    logger.info(f"Starting two-phase sync for {len(items)} items (dry_run={dry_run})")
    
    # ========== PHASE 1: Separate items into simple and assembly groups ==========
    simple_items = []  # Items without BOM
    assembly_items = []  # Items with BOM
    
    logger.info("Phase 1: Categorizing items by BOM presence...")
    for item in items:
        try:
            bom_items = arena.get_bom(item.guid)
            if bom_items and len(bom_items) > 0:
                assembly_items.append(item)
                logger.info(f"  Assembly: {item.item_number} (has {len(bom_items)} components)")
            else:
                simple_items.append(item)
                logger.info(f"  Simple: {item.item_number} (no BOM)")
        except Exception as e:
            logger.warning(f"Failed to check BOM for {item.item_number}, treating as simple: {e}")
            simple_items.append(item)
    
    logger.info(f"Categorization complete: {len(simple_items)} simple, {len(assembly_items)} assemblies")
    
    # ========== PHASE 2: Process simple items in parallel ==========
    if simple_items:
        logger.info(f"Phase 2: Processing {len(simple_items)} simple items in parallel...")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_simple_item(item):
            """Process a simple item (no BOM) for parallel execution."""
            try:
                payload = map_arena_to_cin7(item, db, bom_resolved_list=None)
                return {
                    "status": "success", 
                    "payload": payload, 
                    "sku": item.item_number, 
                    "mode": "DRY_RUN" if dry_run else "LIVE",
                    "type": "simple"
                }
            except Exception as e:
                return {"status": "error", "message": str(e), "sku": item.item_number}
        
        # Parallel execution for simple items
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {executor.submit(process_simple_item, item): item for item in simple_items}
            
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    if result["status"] == "success":
                        if dry_run:
                            summary["mocked"] += 1
                            results.append({
                                "SKU": result["sku"], 
                                "Mode": result["mode"], 
                                "Type": "Simple",
                                "Payload": result["payload"]
                            })
                        else:
                            response = cin7.create_or_update_product(result["payload"])
                            if response.get("status") == "success":
                                summary["success"] += 1
                                logger.info(f"✓ Created simple item: {result['sku']}")
                            else:
                                summary["failed"] += 1
                                results.append({
                                    "SKU": result["sku"], 
                                    "Type": "Simple",
                                    "Error": response.get("message")
                                })
                                logger.error(f"✗ Failed simple item: {result['sku']} - {response.get('message')}")
                    else:
                        summary["failed"] += 1
                        results.append({"SKU": result["sku"], "Type": "Simple", "Error": result["message"]})
                        logger.error(f"✗ Error processing simple item: {result['sku']} - {result['message']}")
                except Exception as exc:
                    logger.error(f"Item {item.item_number} generated an exception: {exc}")
                    summary["failed"] += 1
                    results.append({"SKU": item.item_number, "Type": "Simple", "Error": str(exc)})
    
    # ========== PHASE 3: Process assembly items sequentially ==========
    if assembly_items:
        logger.info(f"Phase 3: Processing {len(assembly_items)} assembly items sequentially...")
        
        for item in assembly_items:
            try:
                logger.info(f"Processing assembly: {item.item_number}")
                
                # Fetch BOM
                bom_items = []
                try:
                    bom_items = arena.get_bom(item.guid)
                    logger.info(f"  Found {len(bom_items)} BOM components")
                except Exception as e:
                    logger.error(f"Failed to fetch BOM for {item.item_number}: {e}")
                
                # Resolve Components using _ensure_product_exists
                # This recursively creates missing components and filters excluded ones
                bom_resolved_list = []
                for line in bom_items:
                    comp_sku = line.get("item", {}).get("number")
                    qty = line.get("quantity", 0)
                    
                    if comp_sku:
                        logger.info(f"  Ensuring component exists: {comp_sku}")
                        cin7_id = _ensure_product_exists(db, comp_sku, arena, cin7, dry_run)
                        
                        # Only add to BOM if component was successfully resolved (not excluded)
                        if cin7_id is not None:
                            # Component exists or was created
                            bom_resolved_list.append({
                                "sku": comp_sku,
                                "qty": qty,
                                "cin7_id": cin7_id
                            })
                            logger.info(f"    ✓ Component {comp_sku} ensured (ID: {cin7_id})")
                        elif dry_run:
                            # In dry run, check if component would be excluded
                            db_check = db.query(models.ArenaItem).filter(models.ArenaItem.item_number == comp_sku).first()
                            if db_check and db_check.transfer_to_erp and db_check.transfer_to_erp != "Yes":
                                logger.info(f"    ⊘ Component {comp_sku} excluded (Transfer to ERP = {db_check.transfer_to_erp})")
                            else:
                                # Would be created in dry run
                                bom_resolved_list.append({
                                    "sku": comp_sku,
                                    "qty": qty,
                                    "cin7_id": None
                                })
                                logger.info(f"    [DRY RUN] Component {comp_sku} would be ensured")
                        else:
                            logger.info(f"    ⊘ Component {comp_sku} excluded (Transfer to ERP = No)")
                
                # Build payload with resolved BOM
                payload = map_arena_to_cin7(item, db, bom_resolved_list)
                
                if dry_run:
                    summary["mocked"] += 1
                    results.append({
                        "SKU": item.item_number, 
                        "Mode": "DRY_RUN",
                        "Type": "Assembly",
                        "Payload": payload
                    })
                    logger.info(f"[DRY RUN] Assembly {item.item_number} payload prepared")
                else:
                    # Create/update the assembly in Cin7
                    response = cin7.create_or_update_product(payload)
                    if response.get("status") == "success":
                        summary["success"] += 1
                        logger.info(f"✓ Created assembly: {item.item_number}")
                    else:
                        summary["failed"] += 1
                        results.append({
                            "SKU": item.item_number,
                            "Type": "Assembly", 
                            "Error": response.get("message")
                        })
                        logger.error(f"✗ Failed assembly: {item.item_number} - {response.get('message')}")
                        
            except Exception as e:
                logger.error(f"Exception processing assembly {item.item_number}: {e}")
                summary["failed"] += 1
                results.append({"SKU": item.item_number, "Type": "Assembly", "Error": str(e)})
    
    # Update sync statistics (only for live syncs, not dry runs)
    if not dry_run and summary["success"] > 0:
        config.total_synced_items = (config.total_synced_items or 0) + summary["success"]
        config.last_successful_sync = datetime.utcnow()
        config.last_sync_time = datetime.utcnow()
        db.commit()
        logger.info(f"Updated sync stats: total={config.total_synced_items}, last_sync={config.last_successful_sync}")
    
    logger.info(f"Sync complete: {summary}")
    return {"status": "complete", "dry_run": dry_run, "push_summary": summary, "details": results}

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
            # Always ensure product exists, passing dry_run flag
            cin7_id = _ensure_product_exists(db, comp_sku, arena, cin7, dry_run)
            
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