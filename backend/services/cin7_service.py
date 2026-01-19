import requests
import logging

logger = logging.getLogger(__name__)

class Cin7Client:
    def __init__(self, account_id, api_key):
        # Domain confirmed via user Postman test
        self.base_url = "https://inventory.dearsystems.com/ExternalApi/v2"
        self.headers = {
            "api-auth-accountid": account_id,
            "api-auth-applicationkey": api_key,
            "Content-Type": "application/json"
        }

    def get_product_by_sku(self, sku):
        """Checks if a product exists by SKU in Cin7 Omni."""
        url = f"{self.base_url}/Product"
        params = {"SKU": sku}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                products = data.get("Products", [])
                return products[0] if products else None
            return None
        except Exception as e:
            logger.error(f"Error searching Cin7 for SKU {sku}: {e}")
            return None

    def create_or_update_product(self, product_data):
        """Creates or updates a product. POST with 'ID' triggers update."""
        sku = product_data.get("SKU")
        existing = self.get_product_by_sku(sku)
        
        if existing:
            product_data["ID"] = existing["ID"]
            logger.info(f"Updating existing SKU in Cin7: {sku}")
        else:
            logger.info(f"Creating new SKU in Cin7: {sku}")

        url = f"{self.base_url}/Product"
        try:
            response = requests.post(url, headers=self.headers, json=product_data, timeout=15)
            if response.status_code in [200, 201, 202]:
                return response.json()
            else:
                logger.error(f"Cin7 API Error for {sku}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Cin7 Exception for {sku}: {e}")
            return None


def sync_single_item(db: Session, item_number: str, dry_run: bool = True):
    # 1. Initialize Clients
    config = db.query(models.Configuration).first()
    arena = ArenaClient(config.arena_workspace_id, config.arena_email, config.arena_password)
    cin7 = Cin7Client(config.cin7_api_user, config.cin7_api_key)
    
    if not arena.login():
        return {"status": "error", "message": "Arena login failed"}

    # 2. Fetch specific item from Arena (Search by number)
    # We use list_all_items and filter or a direct search if your client supports it
    items = arena.list_all_items()
    target_summary = next((i for i in items if i['number'] == item_number), None)
    
    if not target_summary:
        return {"status": "error", "message": f"Item {item_number} not found in Arena"}

    # 3. Harvest Details
    guid = target_summary['guid']
    details = arena.get_item_details(guid)
    sourcing = arena.get_sourcing(guid)
    attrs = map_additional_attributes(details)
    
    # Extract Manufacturer info
    results = sourcing.get("results", [])
    mfr_name, mfr_num = (None, None)
    if results:
        v_item = results[0].get("vendorItem", {})
        mfr_name = v_item.get("supplier", {}).get("name")
        mfr_num = v_item.get("number")

    # 4. Create temporary ArenaItem object (don't necessarily need to save to DB)
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

    # 5. Map to Cin7
    cin7_payload = map_arena_to_cin7(temp_item)

    if dry_run:
        return {
            "status": "mock_success",
            "message": f"Prepared data for {item_number}",
            "payload": cin7_payload
        }
    
    # 6. Live Push
    response = cin7.create_or_update_product(cin7_payload)
    if response:
        return {"status": "live_success", "message": f"Item {item_number} synced to Cin7", "cin7_response": response}
    else:
        return {"status": "error", "message": f"Failed to push {item_number} to Cin7"}