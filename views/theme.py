"""
KALASAG - Theme Configuration
Defines consistent visual styling for the application.
NFR-1: UI/UX Design Standards
"""

import tkinter as tk
from tkinter import ttk


class KalasagTheme:
    """
    Central theme configuration for KALASAG application.
    Implements NFR-1: Visual Consistency using ttk styling.
    """
    
    # ==========================================
    # COLOR PALETTE (Corporate Blue/Slate Gray)
    # ==========================================
    
    # Primary Colors
    PRIMARY_BLUE = "#1a5276"      # Dark corporate blue
    PRIMARY_LIGHT = "#2980b9"     # Lighter blue for hover
    PRIMARY_DARK = "#154360"      # Darker blue for pressed
    
    # Secondary Colors
    SECONDARY_GRAY = "#5d6d7e"    # Slate gray
    SECONDARY_LIGHT = "#85929e"   # Light gray
    
    # Background Colors
    BG_MAIN = "#ecf0f1"           # Light gray background
    BG_SIDEBAR = "#2c3e50"        # Dark sidebar
    BG_CARD = "#ffffff"           # White card background
    BG_INPUT = "#ffffff"          # Input background
    
    # Text Colors
    TEXT_PRIMARY = "#2c3e50"      # Dark text
    TEXT_SECONDARY = "#7f8c8d"    # Gray text
    TEXT_LIGHT = "#ffffff"        # White text (on dark bg)
    TEXT_MUTED = "#95a5a6"        # Muted text
    
    # Status Colors
    SUCCESS_GREEN = "#27ae60"     # Green (Safe)
    WARNING_YELLOW = "#f39c12"    # Yellow (Caution)
    WARNING_ORANGE = "#f39c12"    # Orange (Warning) - alias
    DANGER_RED = "#e74c3c"        # Red (Hotspot/Alert)
    INFO_BLUE = "#3498db"         # Info blue
    
    # Border Colors
    BORDER_LIGHT = "#bdc3c7"
    BORDER_DARK = "#95a5a6"
    
    # ==========================================
    # FONTS (Arial/Helvetica family)
    # ==========================================
    
    FONT_FAMILY = "Segoe UI"      # Windows-friendly font
    FONT_FAMILY_ALT = "Arial"     # Fallback
    
    # Font Sizes
    FONT_SIZE_H1 = 24             # Main headers
    FONT_SIZE_H2 = 18             # Section headers
    FONT_SIZE_H3 = 14             # Sub-headers
    FONT_SIZE_BODY = 11           # Body text
    FONT_SIZE_SMALL = 9           # Small text
    
    # Font Tuples
    FONT_H1 = (FONT_FAMILY, FONT_SIZE_H1, "bold")
    FONT_H2 = (FONT_FAMILY, FONT_SIZE_H2, "bold")
    FONT_H3 = (FONT_FAMILY, FONT_SIZE_H3, "bold")
    FONT_BODY = (FONT_FAMILY, FONT_SIZE_BODY)
    FONT_BODY_BOLD = (FONT_FAMILY, FONT_SIZE_BODY, "bold")
    FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SMALL)
    FONT_BUTTON = (FONT_FAMILY, FONT_SIZE_BODY, "bold")
    
    # ==========================================
    # SPACING (Padding/Margins)
    # ==========================================
    
    PAD_SMALL = 5
    PAD_MEDIUM = 10
    PAD_LARGE = 20
    PAD_XLARGE = 30
    
    # ==========================================
    # WIDGET SIZES
    # ==========================================
    
    ENTRY_WIDTH = 30
    BUTTON_WIDTH = 15
    SIDEBAR_WIDTH = 220
    
    @classmethod
    def apply_theme(cls, root: tk.Tk):
        """Apply the KALASAG theme to the application."""
        style = ttk.Style(root)
        
        # Use clam as base theme (more customizable)
        style.theme_use('clam')
        
        # ==========================================
        # CONFIGURE TTK STYLES
        # ==========================================
        
        # Frame styles
        style.configure(
            "Card.TFrame",
            background=cls.BG_CARD,
            relief="flat"
        )
        
        style.configure(
            "Sidebar.TFrame",
            background=cls.BG_SIDEBAR
        )
        
        style.configure(
            "Main.TFrame",
            background=cls.BG_MAIN
        )
        
        # Label styles
        style.configure(
            "TLabel",
            background=cls.BG_MAIN,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_BODY
        )
        
        style.configure(
            "Header.TLabel",
            background=cls.BG_MAIN,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_H1
        )
        
        style.configure(
            "SubHeader.TLabel",
            background=cls.BG_MAIN,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_H2
        )
        
        style.configure(
            "Card.TLabel",
            background=cls.BG_CARD,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_BODY
        )
        
        style.configure(
            "CardHeader.TLabel",
            background=cls.BG_CARD,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_H3
        )
        
        style.configure(
            "Sidebar.TLabel",
            background=cls.BG_SIDEBAR,
            foreground=cls.TEXT_LIGHT,
            font=cls.FONT_BODY
        )
        
        style.configure(
            "SidebarHeader.TLabel",
            background=cls.BG_SIDEBAR,
            foreground=cls.TEXT_LIGHT,
            font=cls.FONT_H2
        )
        
        # Status labels
        style.configure(
            "Success.TLabel",
            foreground=cls.SUCCESS_GREEN,
            font=cls.FONT_BODY_BOLD
        )
        
        style.configure(
            "Warning.TLabel",
            foreground=cls.WARNING_YELLOW,
            font=cls.FONT_BODY_BOLD
        )
        
        style.configure(
            "Danger.TLabel",
            foreground=cls.DANGER_RED,
            font=cls.FONT_BODY_BOLD
        )
        
        # Button styles
        style.configure(
            "TButton",
            background=cls.PRIMARY_BLUE,
            foreground=cls.TEXT_LIGHT,
            font=cls.FONT_BUTTON,
            padding=(cls.PAD_MEDIUM, cls.PAD_SMALL)
        )
        
        style.map(
            "TButton",
            background=[
                ("active", cls.PRIMARY_LIGHT),
                ("pressed", cls.PRIMARY_DARK),
                ("disabled", cls.SECONDARY_LIGHT)
            ],
            foreground=[
                ("disabled", cls.TEXT_MUTED)
            ]
        )
        
        style.configure(
            "Primary.TButton",
            background=cls.PRIMARY_BLUE,
            foreground=cls.TEXT_LIGHT
        )
        
        style.configure(
            "Success.TButton",
            background=cls.SUCCESS_GREEN,
            foreground=cls.TEXT_LIGHT
        )
        
        style.map(
            "Success.TButton",
            background=[
                ("active", "#2ecc71"),
                ("pressed", "#229954")
            ]
        )
        
        style.configure(
            "Danger.TButton",
            background=cls.DANGER_RED,
            foreground=cls.TEXT_LIGHT
        )
        
        style.map(
            "Danger.TButton",
            background=[
                ("active", "#ec7063"),
                ("pressed", "#c0392b")
            ]
        )
        
        style.configure(
            "Sidebar.TButton",
            background=cls.BG_SIDEBAR,
            foreground=cls.TEXT_LIGHT,
            font=cls.FONT_BODY,
            padding=(cls.PAD_LARGE, cls.PAD_MEDIUM),
            anchor="w"
        )
        
        style.map(
            "Sidebar.TButton",
            background=[
                ("active", cls.PRIMARY_BLUE),
                ("selected", cls.PRIMARY_BLUE)
            ]
        )
        
        # Entry styles
        style.configure(
            "TEntry",
            fieldbackground=cls.BG_INPUT,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_BODY,
            padding=cls.PAD_SMALL
        )
        
        style.map(
            "TEntry",
            fieldbackground=[
                ("focus", cls.BG_CARD),
                ("disabled", cls.BG_MAIN)
            ],
            bordercolor=[
                ("focus", cls.PRIMARY_BLUE)
            ]
        )
        
        # Combobox styles
        style.configure(
            "TCombobox",
            fieldbackground=cls.BG_INPUT,
            background=cls.BG_INPUT,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_BODY
        )
        
        # Treeview (Table) styles
        style.configure(
            "Treeview",
            background=cls.BG_CARD,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.BG_CARD,
            font=cls.FONT_BODY,
            rowheight=28
        )
        
        style.configure(
            "Treeview.Heading",
            background=cls.PRIMARY_BLUE,
            foreground=cls.TEXT_LIGHT,
            font=cls.FONT_BODY_BOLD
        )
        
        style.map(
            "Treeview",
            background=[
                ("selected", cls.PRIMARY_LIGHT)
            ],
            foreground=[
                ("selected", cls.TEXT_LIGHT)
            ]
        )
        
        # Notebook (Tabs) styles
        style.configure(
            "TNotebook",
            background=cls.BG_MAIN,
            tabmargins=[2, 5, 2, 0]
        )
        
        style.configure(
            "TNotebook.Tab",
            background=cls.SECONDARY_LIGHT,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_BODY,
            padding=[cls.PAD_LARGE, cls.PAD_SMALL]
        )
        
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", cls.BG_CARD),
                ("active", cls.BG_MAIN)
            ]
        )
        
        # Progressbar styles
        style.configure(
            "TProgressbar",
            background=cls.PRIMARY_BLUE,
            troughcolor=cls.BG_MAIN
        )
        
        # Scrollbar styles
        style.configure(
            "TScrollbar",
            background=cls.SECONDARY_LIGHT,
            troughcolor=cls.BG_MAIN,
            arrowcolor=cls.TEXT_PRIMARY
        )
        
        # LabelFrame styles
        style.configure(
            "TLabelframe",
            background=cls.BG_CARD,
            foreground=cls.TEXT_PRIMARY
        )
        
        style.configure(
            "TLabelframe.Label",
            background=cls.BG_CARD,
            foreground=cls.TEXT_PRIMARY,
            font=cls.FONT_H3
        )
        
        # Separator
        style.configure(
            "TSeparator",
            background=cls.BORDER_LIGHT
        )
    
    @classmethod
    def get_status_color(cls, level: str) -> str:
        """Get color based on status/severity level."""
        level = level.lower()
        if level in ('safe', 'green', 'success', 'low'):
            return cls.SUCCESS_GREEN
        elif level in ('caution', 'yellow', 'warning', 'medium'):
            return cls.WARNING_YELLOW
        elif level in ('hotspot', 'red', 'danger', 'high'):
            return cls.DANGER_RED
        else:
            return cls.INFO_BLUE
