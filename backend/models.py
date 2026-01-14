from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .database import Base
from datetime import datetime

class Configuration(Base):
    __tablename__ = "configuration"

    id = Column(Integer, primary_key=True, index=True)
    # Arena Credentials
    arena_workspace_id = Column(String, default="")
    arena_email = Column(String, default="")
    arena_password = Column(String, default="") # In a real app, encrypt this!
    
    # Cin7 Credentials
    cin7_api_user = Column(String, default="")
    cin7_api_key = Column(String, default="")
    
    # Sync Settings
    last_sync_time = Column(DateTime, nullable=True)
    auto_sync_enabled = Column(Boolean, default=False)
    
    # Validation flags
    is_arena_connected = Column(Boolean, default=False)
    is_cin7_connected = Column(Boolean, default=False)
