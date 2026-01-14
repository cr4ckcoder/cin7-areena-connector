from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ConfigurationBase(BaseModel):
    arena_workspace_id: str = ""
    arena_email: str = ""
    arena_password: str = ""
    cin7_api_user: str = ""
    cin7_api_key: str = ""
    auto_sync_enabled: bool = False

class ConfigurationCreate(ConfigurationBase):
    pass

class Configuration(ConfigurationBase):
    id: int
    last_sync_time: Optional[datetime] = None
    is_arena_connected: bool
    is_cin7_connected: bool

    class Config:
        from_attributes = True

class SyncResult(BaseModel):
    status: str
    message: str
    processed_items: int = 0
    errors: list[str] = []
