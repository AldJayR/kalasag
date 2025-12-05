"""
KALASAG - Login View
Authentication screen with username/password login.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional

from views.theme import KalasagTheme
from controllers.admin_controller import AdminController


class LoginView(ttk.Frame):
    """Login screen with authentication."""
    
    def __init__(self, parent, on_login_success: Callable[[Dict], None]):
        super().__init__(parent, style="Main.TFrame")
        
        self.on_login_success = on_login_success
        self.admin_ctrl = AdminController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the login UI."""
        # Center container
        center_frame = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Card
        card = tk.Frame(
            center_frame,
            bg=KalasagTheme.BG_CARD,
            padx=KalasagTheme.PAD_XLARGE,
            pady=KalasagTheme.PAD_XLARGE,
            highlightbackground=KalasagTheme.BORDER_LIGHT,
            highlightthickness=1
        )
        card.pack()
        
        # Logo
        logo_label = tk.Label(
            card,
            text="🛡️",
            font=("Segoe UI", 48),
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.PRIMARY_BLUE
        )
        logo_label.pack(pady=(0, KalasagTheme.PAD_SMALL))
        
        # Title
        title = tk.Label(
            card,
            text="KALASAG",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack()
        
        # Subtitle
        subtitle = tk.Label(
            card,
            text="Barangay Information System\nwith Predictive Crime Analytics",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_SECONDARY,
            justify='center'
        )
        subtitle.pack(pady=(0, KalasagTheme.PAD_LARGE))
        
        # Form frame
        form_frame = tk.Frame(card, bg=KalasagTheme.BG_CARD)
        form_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_MEDIUM)
        
        # Username field
        username_label = tk.Label(
            form_frame,
            text="Username",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_SECONDARY,
            anchor='w'
        )
        username_label.pack(fill=tk.X)
        
        self.username_entry = ttk.Entry(
            form_frame,
            width=30,
            font=KalasagTheme.FONT_BODY
        )
        self.username_entry.pack(fill=tk.X, pady=(KalasagTheme.PAD_SMALL, KalasagTheme.PAD_MEDIUM))
        self.username_entry.focus_set()
        
        # Password field
        password_label = tk.Label(
            form_frame,
            text="Password",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_SECONDARY,
            anchor='w'
        )
        password_label.pack(fill=tk.X)
        
        self.password_entry = ttk.Entry(
            form_frame,
            width=30,
            font=KalasagTheme.FONT_BODY,
            show="•"
        )
        self.password_entry.pack(fill=tk.X, pady=(KalasagTheme.PAD_SMALL, KalasagTheme.PAD_MEDIUM))
        
        # Error label (hidden by default)
        self.error_label = tk.Label(
            form_frame,
            text="",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.DANGER_RED
        )
        self.error_label.pack(fill=tk.X)
        
        # Login button
        self.login_btn = tk.Button(
            form_frame,
            text="Login",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            activebackground=KalasagTheme.PRIMARY_LIGHT,
            activeforeground=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_XLARGE,
            pady=KalasagTheme.PAD_MEDIUM,
            cursor='hand2',
            command=self._do_login
        )
        self.login_btn.pack(fill=tk.X, pady=KalasagTheme.PAD_MEDIUM)
        
        # Bind Enter key
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus_set())
        self.password_entry.bind('<Return>', lambda e: self._do_login())
        
        # Default credentials hint
        hint = tk.Label(
            card,
            text="Default: admin / admin123",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_MUTED
        )
        hint.pack(pady=(KalasagTheme.PAD_MEDIUM, 0))
    
    def _do_login(self):
        """Handle login attempt."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Validate inputs
        if not username:
            self._show_error("Please enter your username")
            self.username_entry.focus_set()
            return
        
        if not password:
            self._show_error("Please enter your password")
            self.password_entry.focus_set()
            return
        
        # Attempt login - returns (success, message, user_data)
        success, message, user_data = self.admin_ctrl.authenticate_user(username, password)
        
        if success:
            self._clear_error()
            self.on_login_success(user_data)
        else:
            self._show_error(message)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
    
    def _show_error(self, message: str):
        """Show error message."""
        self.error_label.configure(text=message)
    
    def _clear_error(self):
        """Clear error message."""
        self.error_label.configure(text="")
