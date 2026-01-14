import requests
import json
from datetime import datetime

class ArenaClient:
    def __init__(self, workspace_id, email, password):
        self.base_url = "https://api.arena.com/v1" # Placeholder URL
        self.workspace_id = workspace_id
        self.email = email
        self.password = password
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json"
        }

    def login(self):
        """
        Authenticate with Arena PLM API. 
        Updates self.session_id and self.headers.
        """
        url = f"{self.base_url}/login"
        payload = {
            "workspaceId": self.workspace_id,
            "email": self.email,
            "password": self.password
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                self.session_id = response.json().get("sessionId")
                self.headers["arena_session_id"] = self.session_id
                print(f"Login to Arena Workspace {self.workspace_id} successful.")
                return True
            else:
                print(f"Arena Login Failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Arena Connection Exception: {e}")
            return False

    def get_completed_changes(self):
        """
        Fetch Change Objects with status 'Completed'.
        """
        if not self.session_id:
            self.login()
        
        # Placeholder
        print("Fetching completed changes from Arena...")
        return []

    def get_item_details(self, item_guid):
        """
        Fetch details for a specific item.
        """
        if not self.session_id:
            self.login()
        
        url = f"{self.base_url}/items/{item_guid}"
        print(f"Fetching item details from {url}...")
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
             return {"error": "Item not found"}
        else:
             print(f"Error fetching item: {response.status_code} - {response.text}")
             return {"error": f"API Error: {response.status_code}"}

    def get_item_bom(self, item_guid):
        """
        Fetch Bill of Materials for a specific item.
        """
        if not self.session_id:
            self.login()
        
        url = f"{self.base_url}/items/{item_guid}/bom"
        print(f"Fetching BOM from {url}...")
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
             print(f"Error fetching BOM: {response.status_code} - {response.text}")
             return []

    def verify_connection(self):
        try:
            return self.login()
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
