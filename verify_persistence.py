import requests
import sqlite3
import time
import os

API_URL = "http://localhost:8000/settings"
DB_PATH = "backend/connector.db"

def check_db_directly():
    if not os.path.exists(DB_PATH):
        print("❌ DB file not found on host!")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_prefix_filter FROM configuration")
        rows = cursor.fetchall()
        conn.close()
        print(f"📁 DB Direct Read: {rows}")
        return rows
    except Exception as e:
        print(f"❌ DB Read Error: {e}")

def run_test():
    print("--- Starting Persistence Test ---")
    
    # 1. Check Initial State
    print("\n1. Initial DB State:")
    check_db_directly()
    
    # 2. Update via API
    print("\n2. Updating via API to 'MY_TEST_123'...")
    try:
        new_config = {
            "arena_workspace_id": "901439761",
            "arena_email": "development@jobinandjismi.com",
            "arena_password": "AJILsiva007@",
            "cin7_api_user": "0a5bc857-f37a-4abc-a52d-97859cd88aba", # Req fields
            "cin7_api_key": "cd6194d6-64ad-4b1f-68bd-b1823caa1661",
            "auto_sync_enabled": True,
            "item_prefix_filter": "MY_TEST_123"
        }
        res = requests.post(API_URL, json=new_config)
        print(f"API Status: {res.status_code}")
        print(f"API Response: {res.json()}")
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return

    # 3. Check DB immediately
    print("\n3. DB State after Update:")
    check_db_directly()

    # 4. GET via API
    print("\n4. Reading via API:")
    try:
        res = requests.get(API_URL)
        print(f"API GET Response: {res.json()}")
        if res.json().get("item_prefix_filter") == "MY_TEST_123":
            print("✅ SUCCESS: API reflects update.")
        else:
            print("❌ FAILURE: API returns stale/wrong data.")
    except Exception as e:
        print(f"❌ API GET Failed: {e}")

if __name__ == "__main__":
    run_test()
