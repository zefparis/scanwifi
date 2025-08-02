import hashlib
import os
from datetime import datetime, timezone, timedelta

def get_daily_salt():
    """
    Generate a daily salt value based on the current date and a fixed secret.
    This ensures the same MAC address will hash to the same value within a day,
    but differently on subsequent days.
    """
    # Use a fixed secret (could be loaded from config in production)
    secret = os.getenv('HASH_SALT_PREFIX', 'BeNx-Salt')
    
    # Get current UTC date as string (YYYY-MM-DD)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Combine and hash
    salt = f"{secret}-{today}"
    return salt.encode('utf-8')

def hash_mac_address(mac_address):
    """
    Hash a MAC address using SHA-256 with a daily salt.
    
    Args:
        mac_address (str): The MAC address to hash (format: '00:11:22:33:44:55' or '00-11-22-33-44-55')
        
    Returns:
        str: A hashed version of the MAC address as a hex string
    """
    if not mac_address:
        return None
        
    # Normalize the MAC address (remove any non-hex characters and make lowercase)
    normalized_mac = ''.join(c.lower() for c in mac_address if c.isalnum())
    
    if not all(c in '0123456789abcdef' for c in normalized_mac) or len(normalized_mac) != 12:
        raise ValueError("Invalid MAC address format")
    
    # Get the daily salt
    salt = get_daily_salt()
    
    # Create a SHA-256 hash of the salt + MAC address
    hasher = hashlib.sha256()
    hasher.update(salt)
    hasher.update(normalized_mac.encode('utf-8'))
    
    # Return the first 12 characters of the hash (48 bits, same as a MAC address)
    return hasher.hexdigest()[:12]

def is_hashed_mac(mac):
    """
    Check if a string appears to be a hashed MAC address.
    
    Args:
        mac (str): The string to check
        
    Returns:
        bool: True if the string looks like a hashed MAC address
    """
    if not mac or not isinstance(mac, str):
        return False
    return len(mac) == 12 and all(c in '0123456789abcdef' for c in mac)
