import requests
import logging

logger = logging.getLogger(__name__)

class ArenaClient:
    def __init__(self, workspace_id, email, password):
        self.base_url = "https://api.arenasolutions.com/v1"
        self.workspace_id = workspace_id
        self.email = email
        self.password = password
        self.session_id = None
        # Headers initialized with the format Arena requested in your test
        self.headers = {
            "Content-Type": "application/json",
            "Arena-Usage-Reason": "JobinAndJismi Cin7-Connector/1.0 Initial-Harvest"
        }

    def login(self):
        url = f"{self.base_url}/login"
        payload = {
            "workspaceId": self.workspace_id, 
            "email": self.email, 
            "password": self.password
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Use the verified key 'arenaSessionId' from your test login output
                self.session_id = data.get("arenaSessionId")
                
                if not self.session_id:
                    logger.error("Login successful but arenaSessionId missing in response.")
                    return False

                # Apply the session ID to the Cookie header exactly as validated
                self.headers["Cookie"] = f"arena_session_id={self.session_id}"
                # Redundancy: Some endpoints also look for the direct header
                self.headers["arena_session_id"] = self.session_id
                
                logger.info(f"Arena Login Successful. Workspace: {data.get('workspaceName')}")
                return True
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("note") or error_data.get("reason") or response.text
                logger.error(f"Arena login failed: {response.status_code} - {error_msg}")
                self.last_error = f"Arena Login Error ({response.status_code}): {error_msg}"
                return False
        except Exception as e:
            logger.error(f"Arena login exception: {str(e)}")
            return False

    def list_all_items(self):
        """Fetches all item summaries using pagination."""
        if not self.session_id:
            return []
            
        all_items = []
        offset = 0
        limit = 400
        
        while True:
            url = f"{self.base_url}/items?offset={offset}&limit={limit}&number=TEST-*"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("results", [])
                all_items.extend(items)
                
                if len(items) < limit:
                    break
                offset += limit
            else:
                logger.error(f"Failed to list items at offset {offset}: {response.text}")
                break
        return all_items

    def get_item_details(self, guid):
        """Retrieves detailed information of an item by its GUID."""
        url = f"{self.base_url}/items/{guid}"
        response = requests.get(url, headers=self.headers, timeout=10)
        return response.json() if response.status_code == 200 else None

    def get_sourcing(self, guid):
        """Retrieves sourcing (manufacturer) information for an item."""
        url = f"{self.base_url}/items/{guid}/sourcing"
        response = requests.get(url, headers=self.headers, timeout=10)
        return response.json() if response.status_code == 200 else {}