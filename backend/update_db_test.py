import sqlite3

def update_db():
    try:
        conn = sqlite3.connect("connector.db")
        cursor = conn.cursor()
        
        print("Updating item_prefix_filter to 'TEST'...")
        cursor.execute("UPDATE configuration SET item_prefix_filter = 'TEST' WHERE id = 1")
        conn.commit()
        
        # Verify
        cursor.execute("SELECT item_prefix_filter FROM configuration WHERE id = 1")
        row = cursor.fetchone()
        print(f"New value: '{row[0]}'")
            
        conn.close()
    except Exception as e:
        print(f"Update failed: {e}")

if __name__ == "__main__":
    update_db()
