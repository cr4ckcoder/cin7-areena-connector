import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os

# Add parent dir to sys.path to allow package imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import models, database

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./connector.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_rules():
    db = SessionLocal()
    
    # Define rules from the CSV file
    rules = [
        {
            "rule_key": "TransferFilter",
            "rule_name": "Sync Filter (Transfer Data to ERP?)",
            "rule_value": "Yes",
            "is_enabled": True
        },
        {
            "rule_key": "RevenueAccount",
            "rule_name": "Default Product Revenue Account",
            "rule_value": "4001: OEM Product", # Rule #2
            "is_enabled": True
        },
        {
            "rule_key": "DefaultLocation",
            "rule_name": "Default Product Location",
            "rule_value": "Main Warehouse", # Rule #3
            "is_enabled": True
        },
        {
            "rule_key": "ProductType",
            "rule_name": "Default Product Type",
            "rule_value": "Stock", # Rule #4
            "is_enabled": True
        },
        {
            "rule_key": "AllowedLifecycles",
            "rule_name": "Arena Item Status Filter",
            "rule_value": "In Production, Deprecated, Obsolete", # Rule #7
            "is_enabled": True
        },
        {
            "rule_key": "AssemblyBOM",
            "rule_name": "Add BOMs to applicable NEW products",
            "rule_value": "Yes", # Rule #5
            "is_enabled": True
        }
    ]

    try:
        # Ensure tables are created before seeding
        database.Base.metadata.create_all(bind=engine)
        
        print("Seeding synchronization rules...")
        for rule_data in rules:
            # Check if rule already exists to avoid duplicates
            exists = db.query(models.SyncRule).filter(models.SyncRule.rule_key == rule_data["rule_key"]).first()
            if not exists:
                new_rule = models.SyncRule(**rule_data)
                db.add(new_rule)
                print(f"Added rule: {rule_data['rule_name']}")
            else:
                print(f"Rule already exists: {rule_data['rule_name']}")
        
        db.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding rules: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_rules()