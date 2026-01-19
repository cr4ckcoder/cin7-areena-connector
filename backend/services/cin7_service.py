import requests
import logging

logger = logging.getLogger(__name__)

class Cin7Client:
    def __init__(self, account_id, api_key):
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
        """Creates or updates a product with descriptive error handling."""
        sku = product_data.get("SKU")
        
        # Check if the product already exists to determine if we are updating
        existing = self.get_product_by_sku(sku)
        
        if existing:
            # Map the Cin7 Internal ID to the payload to prevent 409 Conflict errors
            product_data["ID"] = existing["ID"]
            logger.info(f"Updating existing SKU in Cin7: {sku}")
        else:
            logger.info(f"Creating new SKU in Cin7: {sku}")

        url = f"{self.base_url}/Product"
        try:
            response = requests.post(url, headers=self.headers, json=product_data, timeout=15)
            
            if response.status_code in [200, 201, 202]:
                return {"status": "success", "data": response.json()}
            else:
                # Parse descriptive error messages from the Cin7 response
                try:
                    error_list = response.json()
                    # Cin7 returns a list of error objects
                    error_msg = "; ".join([f"{e.get('Exception')}" for e in error_list])
                except:
                    error_msg = response.text

                logger.error(f"Cin7 API Error for {sku}: {response.status_code} - {error_msg}")
                return {
                    "status": "error", 
                    "message": f"Cin7 Error ({response.status_code}): {error_msg}"
                }
        except Exception as e:
            logger.error(f"Cin7 Exception for {sku}: {e}")
            return {"status": "error", "message": f"Connection Exception: {str(e)}"}