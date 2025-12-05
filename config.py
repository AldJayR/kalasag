"""
KALASAG - Configuration Settings
Application constants and configuration.
"""

import os

# Application Info
APP_NAME = "KALASAG"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Barangay Information System with Predictive Crime Analytics"

# Database
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "kalasag.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")

# UI Theme Colors (Corporate Blue/Slate Gray)
COLORS = {
    "primary": "#2C3E50",       # Dark blue-gray (headers, nav)
    "secondary": "#34495E",     # Slate gray
    "accent": "#3498DB",        # Bright blue (buttons, links)
    "success": "#27AE60",       # Green
    "warning": "#F39C12",       # Yellow/Orange
    "danger": "#E74C3C",        # Red
    "light": "#ECF0F1",         # Light gray (backgrounds)
    "white": "#FFFFFF",
    "text": "#2C3E50",          # Dark text
    "text_light": "#7F8C8D",    # Muted text
}

# Hotspot Thresholds (for BI Analytics)
HOTSPOT_THRESHOLDS = {
    "safe": 0,          # Green: 0 incidents
    "caution": 3,       # Yellow: 1-3 incidents
    # Red: > 3 incidents
}

# Hotspot Colors
HOTSPOT_COLORS = {
    "safe": "#27AE60",      # Green
    "caution": "#F39C12",   # Yellow
    "hotspot": "#E74C3C",   # Red
}

# Analytics Period (in days)
ANALYTICS_PERIOD_DAYS = 30

# Document Types
DOCUMENT_TYPES = [
    "Clearance",
    "Indigency",
    "Permit",
    "Residency",
    "Business Permit"
]

# Case Statuses
CASE_STATUSES = [
    "Pending",
    "Amicable Settlement",
    "Escalated to PNP",
    "Closed"
]

# Resident Statuses
RESIDENT_STATUSES = [
    "Active",
    "Deceased",
    "Moved Out"
]

# Civil Status Options
CIVIL_STATUS_OPTIONS = [
    "Single",
    "Married",
    "Widowed",
    "Separated",
    "Divorced"
]

# Sex Options
SEX_OPTIONS = ["Male", "Female"]

# User Roles
USER_ROLES = [
    "Captain",
    "Secretary",
    "Tanod",
    "Admin"
]

# Role Permissions
ROLE_PERMISSIONS = {
    "Admin": ["all"],
    "Captain": ["view_all", "view_analytics", "generate_reports", "manage_users"],
    "Secretary": ["manage_residents", "manage_blotter", "issue_documents", "view_analytics"],
    "Tanod": ["view_residents", "view_blotter", "view_patrol"]
}

# UI Fonts
FONTS = {
    "heading": ("Arial", 18, "bold"),
    "subheading": ("Arial", 14, "bold"),
    "body": ("Arial", 11),
    "small": ("Arial", 9),
    "button": ("Arial", 10, "bold"),
}

# Window Sizes
WINDOW_SIZES = {
    "main": (1200, 700),
    "dialog": (500, 400),
    "small_dialog": (350, 250),
}

# Table Settings
TABLE_SETTINGS = {
    "rows_per_page": 25,
    "max_search_results": 100,
}
