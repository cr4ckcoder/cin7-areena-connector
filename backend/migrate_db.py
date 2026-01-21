import sqlite3

def migrate_db():
    try:
        conn = sqlite3.connect("connector.db")
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(configuration)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "item_prefix_filter" not in columns:
            print("Adding 'item_prefix_filter' column to 'configuration' table...")
            cursor.execute("ALTER TABLE configuration ADD COLUMN item_prefix_filter TEXT DEFAULT '06-'")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'item_prefix_filter' already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_db()
