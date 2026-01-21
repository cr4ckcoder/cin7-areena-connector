import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Attempting to import sync_service...")
try:
    from backend.services import sync_service
    print("✅ Import successful. Syntax looks good.")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
