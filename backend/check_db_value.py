import sqlite3
import os

def check_db():
    db_path = "connector.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, item_prefix_filter FROM configuration")
        rows = cursor.fetchall()
        
        print("Configuration Table Content:")
        if not rows:
            print("No rows found.")
        for row in rows:
            print(f"ID: {row[0]}, Filter: '{row[1]}'")
            
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")

if __name__ == "__main__":
    check_db()
