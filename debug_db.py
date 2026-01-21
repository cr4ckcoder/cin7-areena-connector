import sqlite3
import os

# Try multiple paths
possible_paths = ["connector.db", "backend/connector.db"]
db_path = None
for p in possible_paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print("❌ ERR: Database 'connector.db' not found in CWD or backend/")
    exit(1)

print(f"✅ Found DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configuration")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    print(f"\n--- Configuration Table ({len(rows)} rows) ---")
    print(f"Columns: {columns}")
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
