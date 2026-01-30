from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from .database import Base
from datetime import datetime

class Configuration(Base):
    __tablename__ = "configuration"
    id = Column(Integer, primary_key=True, index=True)
    
    # Non-sensitive fields (plaintext)
    arena_workspace_id = Column(String, default="")
    last_sync_time = Column(DateTime, nullable=True)
    auto_sync_enabled = Column(Boolean, default=False)
    is_arena_connected = Column(Boolean, default=False)
    is_cin7_connected = Column(Boolean, default=False)
    item_prefix_filter = Column(String, default="*")
    
    # Sync statistics
    total_synced_items = Column(Integer, default=0)
    last_successful_sync = Column(DateTime, nullable=True)
    
    # Encrypted fields (stored encrypted, accessed as plaintext via properties)
    _arena_email = Column("arena_email", String, default="")
    _arena_password = Column("arena_password", String, default="")
    _cin7_api_user = Column("cin7_api_user", String, default="")
    _cin7_api_key = Column("cin7_api_key", String, default="")
    
    # Properties for transparent encryption/decryption
    @property
    def arena_email(self) -> str:
        """Get decrypted arena email."""
        from .encryption import decrypt_value, migrate_to_encrypted
        if not self._arena_email:
            return ""
        # Auto-migrate if plaintext
        if not self._arena_email.startswith('gAAAAA'):
            self._arena_email = migrate_to_encrypted(self._arena_email)
        return decrypt_value(self._arena_email)
    
    @arena_email.setter
    def arena_email(self, value: str):
        """Set arena email (encrypts automatically)."""
        from .encryption import encrypt_value
        self._arena_email = encrypt_value(value) if value else ""
    
    @property
    def arena_password(self) -> str:
        """Get decrypted arena password."""
        from .encryption import decrypt_value, migrate_to_encrypted
        if not self._arena_password:
            return ""
        # Auto-migrate if plaintext
        if not self._arena_password.startswith('gAAAAA'):
            self._arena_password = migrate_to_encrypted(self._arena_password)
        return decrypt_value(self._arena_password)
    
    @arena_password.setter
    def arena_password(self, value: str):
        """Set arena password (encrypts automatically)."""
        from .encryption import encrypt_value
        self._arena_password = encrypt_value(value) if value else ""
    
    @property
    def cin7_api_user(self) -> str:
        """Get decrypted Cin7 API user."""
        from .encryption import decrypt_value, migrate_to_encrypted
        if not self._cin7_api_user:
            return ""
        # Auto-migrate if plaintext
        if not self._cin7_api_user.startswith('gAAAAA'):
            self._cin7_api_user = migrate_to_encrypted(self._cin7_api_user)
        return decrypt_value(self._cin7_api_user)
    
    @cin7_api_user.setter
    def cin7_api_user(self, value: str):
        """Set Cin7 API user (encrypts automatically)."""
        from .encryption import encrypt_value
        self._cin7_api_user = encrypt_value(value) if value else ""
    
    @property
    def cin7_api_key(self) -> str:
        """Get decrypted Cin7 API key."""
        from .encryption import decrypt_value, migrate_to_encrypted
        if not self._cin7_api_key:
            return ""
        # Auto-migrate if plaintext
        if not self._cin7_api_key.startswith('gAAAAA'):
            self._cin7_api_key = migrate_to_encrypted(self._cin7_api_key)
        return decrypt_value(self._cin7_api_key)
    
    @cin7_api_key.setter
    def cin7_api_key(self, value: str):
        """Set Cin7 API key (encrypts automatically)."""
        from .encryption import encrypt_value
        self._cin7_api_key = encrypt_value(value) if value else ""

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


class SyncRule(Base):
    __tablename__ = "sync_rules"
    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String, unique=True)  # e.g., "RevenueAccount"
    rule_name = Column(String)              # e.g., "Default Product Revenue Account"
    rule_value = Column(String)             # e.g., "4001: OEM Product"
    is_enabled = Column(Boolean, default=True)


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
