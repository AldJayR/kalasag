"""
KALASAG - Input Validators
Validation functions for user input.
"""

import re
from datetime import datetime
from typing import Tuple, Optional


def validate_required(value: str, field_name: str) -> Tuple[bool, Optional[str]]:
    """Validate that a required field is not empty."""
    if not value or not value.strip():
        return False, f"{field_name} is required"
    return True, None


def validate_name(value: str, field_name: str = "Name") -> Tuple[bool, Optional[str]]:
    """Validate a name field (letters, spaces, hyphens, apostrophes only)."""
    if not value or not value.strip():
        return False, f"{field_name} is required"
    
    # Allow letters (including accented), spaces, hyphens, apostrophes, and ñ/Ñ
    pattern = r"^[A-Za-zÀ-ÿÑñ\s\-'\.]+$"
    if not re.match(pattern, value.strip()):
        return False, f"{field_name} contains invalid characters"
    
    if len(value.strip()) < 2:
        return False, f"{field_name} must be at least 2 characters"
    
    return True, None


def validate_date(value: str, field_name: str = "Date") -> Tuple[bool, Optional[str]]:
    """Validate a date in YYYY-MM-DD format."""
    if not value:
        return True, None  # Allow empty dates
    
    try:
        date = datetime.strptime(value, "%Y-%m-%d")
        
        # Check if date is not in the future (for birthdate)
        if date > datetime.now():
            return False, f"{field_name} cannot be in the future"
        
        # Check if date is reasonable (not before 1900)
        if date.year < 1900:
            return False, f"{field_name} year must be 1900 or later"
        
        return True, None
    except ValueError:
        return False, f"{field_name} must be in YYYY-MM-DD format"


def validate_birthdate(value: str) -> Tuple[bool, Optional[str]]:
    """Validate birthdate specifically."""
    valid, error = validate_date(value, "Birthdate")
    if not valid:
        return valid, error
    
    if value:
        birthdate = datetime.strptime(value, "%Y-%m-%d")
        age = (datetime.now() - birthdate).days / 365.25
        
        if age < 0:
            return False, "Birthdate cannot be in the future"
        if age > 150:
            return False, "Invalid birthdate (age > 150 years)"
    
    return True, None


def validate_sex(value: str) -> Tuple[bool, Optional[str]]:
    """Validate sex field."""
    if not value:
        return True, None  # Allow empty
    
    if value not in ("Male", "Female"):
        return False, "Sex must be 'Male' or 'Female'"
    
    return True, None


def validate_civil_status(value: str) -> Tuple[bool, Optional[str]]:
    """Validate civil status field."""
    if not value:
        return True, None  # Allow empty
    
    valid_statuses = ("Single", "Married", "Widowed", "Separated", "Divorced")
    if value not in valid_statuses:
        return False, f"Civil status must be one of: {', '.join(valid_statuses)}"
    
    return True, None


def validate_contact_number(value: str) -> Tuple[bool, Optional[str]]:
    """Validate Philippine contact number format."""
    if not value:
        return True, None  # Allow empty
    
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s\-]', '', value)
    
    # Accept formats: 09XXXXXXXXX, +639XXXXXXXXX, or landline 0XXXXXXX
    patterns = [
        r'^09\d{9}$',           # 09XXXXXXXXX (11 digits)
        r'^\+639\d{9}$',        # +639XXXXXXXXX
        r'^639\d{9}$',          # 639XXXXXXXXX
        r'^0\d{7,10}$',         # Landline
    ]
    
    if not any(re.match(p, cleaned) for p in patterns):
        return False, "Invalid contact number format"
    
    return True, None


def validate_username(value: str) -> Tuple[bool, Optional[str]]:
    """Validate username."""
    if not value or not value.strip():
        return False, "Username is required"
    
    if len(value) < 4:
        return False, "Username must be at least 4 characters"
    
    if len(value) > 50:
        return False, "Username must be less than 50 characters"
    
    # Alphanumeric and underscore only
    if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', value):
        return False, "Username must start with a letter and contain only letters, numbers, and underscores"
    
    return True, None


def validate_password(value: str, min_length: int = 6) -> Tuple[bool, Optional[str]]:
    """Validate password strength."""
    if not value:
        return False, "Password is required"
    
    if len(value) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    return True, None


def validate_amount(value: str) -> Tuple[bool, Optional[str]]:
    """Validate monetary amount."""
    if not value:
        return True, None  # Allow empty (0)
    
    try:
        amount = float(value)
        if amount < 0:
            return False, "Amount cannot be negative"
        return True, None
    except ValueError:
        return False, "Invalid amount format"


def validate_or_number(value: str) -> Tuple[bool, Optional[str]]:
    """Validate Official Receipt number."""
    if not value:
        return True, None  # Allow empty
    
    # Alphanumeric with dashes
    if not re.match(r'^[A-Za-z0-9\-]+$', value):
        return False, "O.R. Number contains invalid characters"
    
    return True, None


def validate_narrative(value: str, min_length: int = 10) -> Tuple[bool, Optional[str]]:
    """Validate blotter narrative."""
    if not value or not value.strip():
        return False, "Narrative is required"
    
    if len(value.strip()) < min_length:
        return False, f"Narrative must be at least {min_length} characters"
    
    return True, None


def sanitize_input(value: str) -> str:
    """Sanitize input to prevent basic injection attacks."""
    if not value:
        return value
    
    # Strip whitespace
    value = value.strip()
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    return value


def calculate_age(birthdate: str) -> Optional[int]:
    """Calculate age from birthdate string."""
    if not birthdate:
        return None
    
    try:
        birth = datetime.strptime(birthdate, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        
        return age
    except ValueError:
        return None
