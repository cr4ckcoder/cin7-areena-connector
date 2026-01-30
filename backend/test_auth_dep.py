from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

print("Testing dependencies...")
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash = pwd_context.hash("test")
    print(f"Hashing successful: {hash}")
    verify = pwd_context.verify("test", hash)
    print(f"Verification successful: {verify}")
    
    token = jwt.encode({"sub": "test"}, "secret", algorithm="HS256")
    print(f"JWT generation successful: {token}")
except Exception as e:
    print(f"ERROR: {e}")
