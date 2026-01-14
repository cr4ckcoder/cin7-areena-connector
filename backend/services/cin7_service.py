import requests
import json
from base64 import b64encode

class Cin7Client:
    def __init__(self, api_user, api_key):
        self.base_url = "https://api.cin7.com/api/v1" # Standard Cin7 API URL
        self.api_user = api_user
        self.api_key = api_key
        self.auth_header = self._get_auth_header()

    def _get_auth_header(self):
        credentials = f"{self.api_user}:{self.api_key}"
        encoded_credentials = b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}", "Content-Type": "application/json"}

    def verify_connection(self):
        """
        Verify credentials by making a lightweight call, e.g., fetching 1 product.
        """
        # Placeholder
        print(f"Verifying Cin7 connection for user {self.api_user}...")
        # response = requests.get(f"{self.base_url}/Products?rows=1", headers=self.auth_header)
        # return response.status_code == 200
        return True

    def get_product_by_code(self, product_code):
        """
        Check if a product exists by code/SKU.
        """
        print(f"Searching for Cin7 product {product_code}...")
        # response = requests.get(f"{self.base_url}/Products?where=code='{product_code}'", headers=self.auth_header)
        return None # Return None if not found, or dict if found

    def create_product(self, product_data):
        """
        Create a new product in Cin7.
        """
        print(f"Creating product {product_data.get('ProductCode')} in Cin7...")
        # response = requests.post(f"{self.base_url}/Products", json=[product_data], headers=self.auth_header)
        return {"id": "mock_id_123"}

    def update_product(self, cin7_id, product_data):
        """
        Update an existing product.
        """
        print(f"Updating product {cin7_id} in Cin7...")
        # product_data['id'] = cin7_id
        # response = requests.put(f"{self.base_url}/Products", json=[product_data], headers=self.auth_header)
        return True

    def update_bom(self, parent_id, bom_items):
        """
        Update Bill of Materials for a product.
        Cin7 usually handles BOMs as 'BillOfMaterials' endpoint or nested.
        """
        print(f"Updating BOM for parent {parent_id} with {len(bom_items)} items...")
        return True
