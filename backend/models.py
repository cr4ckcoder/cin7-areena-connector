from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from .database import Base
from datetime import datetime

class Configuration(Base):
    __tablename__ = "configuration"
    id = Column(Integer, primary_key=True, index=True)
    arena_workspace_id = Column(String, default="")
    arena_email = Column(String, default="")
    arena_password = Column(String, default="")
    cin7_api_user = Column(String, default="")
    cin7_api_key = Column(String, default="")
    last_sync_time = Column(DateTime, nullable=True)
    auto_sync_enabled = Column(Boolean, default=False)
    is_arena_connected = Column(Boolean, default=False)
    is_cin7_connected = Column(Boolean, default=False)

class ArenaItem(Base):
    __tablename__ = "arena_items"
    
    guid = Column(String, primary_key=True, index=True)
    item_number = Column(String, index=True)
    item_name = Column(String)
    lifecycle_phase = Column(String)
    revision = Column(String)
    category = Column(String)
    description = Column(Text, nullable=True)
    uom = Column(String)
    
    # Custom Attributes from Arena
    costing_method = Column(String, nullable=True)
    auto_assemble = Column(String, nullable=True)
    inventory_account = Column(String, nullable=True)
    cogs_account = Column(String, nullable=True)
    sellable = Column(String, nullable=True)
    internal_note_erp = Column(Text, nullable=True)
    last_glg_co = Column(String, nullable=True)
    transfer_to_erp = Column(String, default="No")
    
    # Sourcing & BOM
    manufacturer = Column(String, nullable=True)
    manufacturer_item_number = Column(String, nullable=True)
    parent_item_number = Column(String, nullable=True)
    
    last_updated = Column(DateTime, default=datetime.utcnow)