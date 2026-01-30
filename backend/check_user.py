import sqlite3
import os

# DB path from docker-compose
db_path = "/data/connector.db"

print(f"Checking DB at {db_path}")

if not os.path.exists(db_path):
    print(f"DB NOT FOUND at {db_path}")
    # Try default location just in case
    if os.path.exists("connector.db"):
        print("Found connector.db in current dir")
        db_path = "connector.db"
    else:
        exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} users")
    for row in rows:
        print(f"User ID: {row[0]}, Email: {row[1]}, Hash: {row[2]}")
except Exception as e:
    print(f"Error querying users table: {e}")
    # List tables
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Tables found:", cursor.fetchall())
    except:
        pass
conn.close()
