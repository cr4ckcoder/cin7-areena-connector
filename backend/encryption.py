"""
Encryption utilities for securing sensitive data at rest.

Uses Fernet symmetric encryption from the cryptography library.
Encryption key is stored in environment variable for security.
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to store encryption key if not in environment
KEY_FILE = Path(__file__).parent / '.encryption_key'


def generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key()


def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable or key file.
    
    Priority:
    1. ENCRYPTION_KEY environment variable
    2. .encryption_key file (auto-generated on first run)
    
    Returns:
        bytes: Fernet encryption key
    """
    # Try environment variable first
    key = os.getenv('ENCRYPTION_KEY')
    
    if key:
        logger.info("Using encryption key from environment variable")
        return key.encode() if isinstance(key, str) else key
    
    # Try key file
    if KEY_FILE.exists():
        logger.info("Using encryption key from key file")
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    
    # Generate new key and save to file
    logger.warning("No encryption key found. Generating new key...")
    new_key = generate_key()
    
    try:
        with open(KEY_FILE, 'wb') as f:
            f.write(new_key)
        logger.info(f"Encryption key saved to {KEY_FILE}")
        logger.warning("IMPORTANT: Backup this key file! Losing it means losing access to encrypted credentials.")
    except Exception as e:
        logger.error(f"Failed to save encryption key: {e}")
    
    return new_key


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a string value using Fernet encryption.
    
    Args:
        plaintext: String to encrypt
        
    Returns:
        str: Base64-encoded encrypted string
    """
    if not plaintext:
        return ""
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(plaintext.encode())
        return encrypted.decode()  # Store as string in DB
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_value(encrypted: str) -> str:
    """
    Decrypt an encrypted value.
    
    Args:
        encrypted: Base64-encoded encrypted string
        
    Returns:
        str: Decrypted plaintext string
    """
    if not encrypted:
        return ""
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted.encode())
        return decrypted.decode()
    except InvalidToken:
        logger.error("Decryption failed: Invalid token or wrong encryption key")
        return ""
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return ""


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted.
    
    Fernet encrypted values are base64-encoded and typically start with 'gAAAAA'.
    
    Args:
        value: String to check
        
    Returns:
        bool: True if value appears encrypted, False otherwise
    """
    if not value:
        return False
    
    try:
        # Fernet tokens start with version byte (0x80) which encodes to 'gA' in base64
        # Full prefix is usually 'gAAAAA' (version + timestamp)
        return value.startswith('gAAAAA')
    except:
        return False


def migrate_to_encrypted(plaintext: str) -> str:
    """
    Migrate a plaintext value to encrypted format.
    
    If value is already encrypted, returns it unchanged.
    If plaintext, encrypts and returns encrypted value.
    
    Args:
        plaintext: Value to migrate
        
    Returns:
        str: Encrypted value
    """
    if not plaintext:
        return ""
    
    if is_encrypted(plaintext):
        logger.debug("Value already encrypted, skipping migration")
        return plaintext
    
    logger.info("Migrating plaintext value to encrypted format")
    return encrypt_value(plaintext)
