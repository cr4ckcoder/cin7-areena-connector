from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Configuration Schemas
class ConfigurationBase(BaseModel):
    arena_workspace_id: str = ""
    arena_email: str = ""
    arena_password: str = ""
    cin7_api_user: str = ""
    cin7_api_key: str = ""
    auto_sync_enabled: bool = False
    item_prefix_filter: str = "*" # Added to match new model field

class ConfigurationCreate(ConfigurationBase):
    pass

class Configuration(ConfigurationBase):
    id: int
    last_sync_time: Optional[datetime] = None
    is_arena_connected: bool
    is_cin7_connected: bool

    class Config:
        from_attributes = True

# Sync Rule Schemas (Required for the current error)
class SyncRuleBase(BaseModel):
    rule_key: str
    rule_name: str
    rule_value: str
    is_enabled: bool = True

class SyncRuleCreate(SyncRuleBase):
    pass

class SyncRuleUpdate(BaseModel):
    rule_value: Optional[str] = None
    is_enabled: Optional[bool] = None

class SyncRule(SyncRuleBase):
    id: int

    class Config:
        from_attributes = True

# Result Schemas
class SyncResult(BaseModel):
    status: str
    message: str
    processed_items: int = 0
    errors: list[str] = []