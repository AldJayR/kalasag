"""
KALASAG - Helper Utilities
Common helper functions used across the application.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
import os


def format_date(date_str: str, output_format: str = "%B %d, %Y") -> str:
    """
    Format a date string for display.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        output_format: Desired output format
        
    Returns:
        Formatted date string or original if parsing fails
    """
    if not date_str:
        return ""
    
    try:
        date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        return date.strftime(output_format)
    except ValueError:
        return str(date_str)


def format_datetime(datetime_str: str, output_format: str = "%B %d, %Y %I:%M %p") -> str:
    """
    Format a datetime string for display.
    
    Args:
        datetime_str: Datetime string
        output_format: Desired output format
        
    Returns:
        Formatted datetime string
    """
    if not datetime_str:
        return ""
    
    try:
        # Try multiple input formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(str(datetime_str)[:19], fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue
        return str(datetime_str)
    except Exception:
        return str(datetime_str)


def format_name(first_name: str, middle_name: str = None, 
                last_name: str = None, format_type: str = "full") -> str:
    """
    Format a person's name.
    
    Args:
        first_name: First name
        middle_name: Middle name (optional)
        last_name: Last name
        format_type: 'full', 'formal' (Last, First M.), or 'short' (F. Last)
        
    Returns:
        Formatted name string
    """
    first = first_name or ""
    middle = middle_name or ""
    last = last_name or ""
    
    if format_type == "formal":
        # Last, First M.
        middle_initial = f" {middle[0]}." if middle else ""
        return f"{last}, {first}{middle_initial}".strip(", ")
    
    elif format_type == "short":
        # F. Last
        first_initial = f"{first[0]}." if first else ""
        return f"{first_initial} {last}".strip()
    
    else:  # full
        # First Middle Last
        parts = [first, middle, last]
        return " ".join(p for p in parts if p).strip()


def format_address(house_number: str = None, street_name: str = None, 
                   purok_name: str = None) -> str:
    """Format a complete address."""
    parts = []
    
    if house_number:
        parts.append(f"#{house_number}")
    if street_name:
        parts.append(street_name)
    if purok_name:
        parts.append(purok_name)
    
    return ", ".join(parts) if parts else "N/A"


def format_currency(amount: float) -> str:
    """Format amount as Philippine Peso."""
    if amount is None:
        return "₱0.00"
    return f"₱{amount:,.2f}"


def get_age_from_birthdate(birthdate: str) -> Optional[int]:
    """Calculate age from birthdate string."""
    if not birthdate:
        return None
    
    try:
        birth = datetime.strptime(str(birthdate)[:10], "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year
        
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        
        return age
    except ValueError:
        return None


def get_date_range(period: str = "month") -> tuple:
    """
    Get start and end dates for a period.
    
    Args:
        period: 'today', 'week', 'month', 'quarter', 'year'
        
    Returns:
        Tuple of (start_date, end_date) strings in YYYY-MM-DD format
    """
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    
    if period == "today":
        start_date = end_date
    elif period == "week":
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "month":
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif period == "quarter":
        start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    elif period == "year":
        start_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    else:
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    
    return start_date, end_date


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def ensure_directory(path: str) -> str:
    """Ensure a directory exists, create if not."""
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_status_color(status: str) -> str:
    """Get color code for a status value."""
    status_colors = {
        # Resident statuses
        "Active": "#27AE60",      # Green
        "Deceased": "#7F8C8D",    # Gray
        "Moved Out": "#F39C12",   # Orange
        
        # Case statuses
        "Pending": "#F39C12",           # Orange
        "Amicable Settlement": "#27AE60", # Green
        "Escalated to PNP": "#E74C3C",   # Red
        "Closed": "#7F8C8D",             # Gray
        
        # Hotspot levels
        "safe": "#27AE60",       # Green
        "caution": "#F39C12",    # Yellow
        "hotspot": "#E74C3C",    # Red
    }
    
    return status_colors.get(status, "#2C3E50")


def bool_to_yes_no(value: Any) -> str:
    """Convert boolean-like value to Yes/No string."""
    if value in (True, 1, "1", "true", "True", "yes", "Yes"):
        return "Yes"
    return "No"


def yes_no_to_bool(value: str) -> bool:
    """Convert Yes/No string to boolean."""
    return value.lower() in ("yes", "y", "true", "1")


def generate_filename(prefix: str, extension: str = "pdf") -> str:
    """Generate a timestamped filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"
