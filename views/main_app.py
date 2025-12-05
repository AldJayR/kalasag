"""
KALASAG - Main Application Window
The primary application container with navigation sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable, Optional

from views.theme import KalasagTheme
from views.components import StatusBar, ConfirmDialog
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.resident_view import ResidentView
from views.blotter_view import BlotterView
from views.document_view import DocumentView
from views.analytics_view import AnalyticsView
from views.admin_view import AdminView
from controllers.admin_controller import AdminController


class MainApplication(tk.Tk):
    """Main application window with sidebar navigation."""
    
    def __init__(self):
        super().__init__()
        
        # Application state
        self.current_user = None
        self.current_view = None
        
        # Configure window
        self.title("KALASAG - Barangay Information System")
        self.geometry("1280x720")
        self.minsize(1024, 600)
        
        # Apply theme
        KalasagTheme.apply_theme(self)
        
        # Configure root background
        self.configure(bg=KalasagTheme.BG_MAIN)
        
        # Initialize database and seed default data
        from database import init_database, seed_default_data
        init_database()
        seed_default_data()
        
        # Show login first
        self._show_login()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _show_login(self):
        """Show the login screen."""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create login view
        self.login_view = LoginView(self, self._on_login_success)
        self.login_view.pack(fill=tk.BOTH, expand=True)
    
    def _on_login_success(self, user: Dict):
        """Handle successful login."""
        self.current_user = user
        self._build_main_ui()
        self.status_bar.set_user(user['username'], user['role'])
        self.status_bar.set_message(f"Welcome, {user['full_name']}!", 'success')
        
        # Show dashboard by default
        self._show_view('dashboard')
    
    def _build_main_ui(self):
        """Build the main application UI with sidebar."""
        # Clear login view
        for widget in self.winfo_children():
            widget.destroy()
        
        # Main container
        self.main_container = ttk.Frame(self, style="Main.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self._create_sidebar()
        
        # Content area
        self.content_frame = ttk.Frame(self.main_container, style="Main.TFrame")
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # View container
        self.view_container = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.view_container.pack(fill=tk.BOTH, expand=True, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_MEDIUM)
        
        # Store views
        self.views: Dict[str, ttk.Frame] = {}
    
    def _create_sidebar(self):
        """Create the navigation sidebar."""
        sidebar = tk.Frame(
            self.main_container,
            bg=KalasagTheme.BG_SIDEBAR,
            width=KalasagTheme.SIDEBAR_WIDTH
        )
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Logo/Header
        header_frame = tk.Frame(sidebar, bg=KalasagTheme.BG_SIDEBAR)
        header_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        logo_label = tk.Label(
            header_frame,
            text="🛡️ KALASAG",
            font=KalasagTheme.FONT_H2,
            fg=KalasagTheme.TEXT_LIGHT,
            bg=KalasagTheme.BG_SIDEBAR
        )
        logo_label.pack()
        
        subtitle = tk.Label(
            header_frame,
            text="Barangay Information System",
            font=KalasagTheme.FONT_SMALL,
            fg=KalasagTheme.TEXT_MUTED,
            bg=KalasagTheme.BG_SIDEBAR
        )
        subtitle.pack()
        
        # Separator
        tk.Frame(sidebar, bg=KalasagTheme.BORDER_DARK, height=1).pack(fill=tk.X, padx=10, pady=10)
        
        # Navigation buttons
        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("👥", "Residents", "residents"),
            ("📋", "E-Blotter", "blotter"),
            ("📄", "Documents", "documents"),
            ("📈", "Analytics", "analytics"),
        ]
        
        # Add admin option for appropriate roles
        if self.current_user and self.current_user.get('role') in ('Admin', 'Captain'):
            nav_items.append(("⚙️", "Administration", "admin"))
        
        self.nav_buttons: Dict[str, tk.Button] = {}
        
        for icon, text, view_name in nav_items:
            btn = tk.Button(
                sidebar,
                text=f"  {icon}  {text}",
                font=KalasagTheme.FONT_BODY,
                fg=KalasagTheme.TEXT_LIGHT,
                bg=KalasagTheme.BG_SIDEBAR,
                activebackground=KalasagTheme.PRIMARY_BLUE,
                activeforeground=KalasagTheme.TEXT_LIGHT,
                bd=0,
                anchor='w',
                padx=KalasagTheme.PAD_LARGE,
                pady=KalasagTheme.PAD_MEDIUM,
                cursor='hand2',
                command=lambda v=view_name: self._show_view(v)
            )
            btn.pack(fill=tk.X)
            
            # Hover effects
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=KalasagTheme.PRIMARY_LIGHT))
            btn.bind('<Leave>', lambda e, b=btn, v=view_name: self._update_nav_highlight(b, v))
            
            self.nav_buttons[view_name] = btn
        
        # Spacer
        tk.Frame(sidebar, bg=KalasagTheme.BG_SIDEBAR).pack(fill=tk.BOTH, expand=True)
        
        # Bottom section - Logout
        tk.Frame(sidebar, bg=KalasagTheme.BORDER_DARK, height=1).pack(fill=tk.X, padx=10, pady=10)
        
        logout_btn = tk.Button(
            sidebar,
            text="  🚪  Logout",
            font=KalasagTheme.FONT_BODY,
            fg=KalasagTheme.TEXT_LIGHT,
            bg=KalasagTheme.BG_SIDEBAR,
            activebackground=KalasagTheme.DANGER_RED,
            activeforeground=KalasagTheme.TEXT_LIGHT,
            bd=0,
            anchor='w',
            padx=KalasagTheme.PAD_LARGE,
            pady=KalasagTheme.PAD_MEDIUM,
            cursor='hand2',
            command=self._logout
        )
        logout_btn.pack(fill=tk.X, pady=(0, KalasagTheme.PAD_MEDIUM))
        
        logout_btn.bind('<Enter>', lambda e: logout_btn.configure(bg=KalasagTheme.DANGER_RED))
        logout_btn.bind('<Leave>', lambda e: logout_btn.configure(bg=KalasagTheme.BG_SIDEBAR))
    
    def _update_nav_highlight(self, button: tk.Button, view_name: str):
        """Update navigation button highlighting."""
        if self.current_view == view_name:
            button.configure(bg=KalasagTheme.PRIMARY_BLUE)
        else:
            button.configure(bg=KalasagTheme.BG_SIDEBAR)
    
    def _show_view(self, view_name: str):
        """Show a specific view."""
        # Update current view tracking
        old_view = self.current_view
        self.current_view = view_name
        
        # Update nav button highlights
        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(bg=KalasagTheme.PRIMARY_BLUE)
            else:
                btn.configure(bg=KalasagTheme.BG_SIDEBAR)
        
        # Clear view container
        for widget in self.view_container.winfo_children():
            widget.pack_forget()
        
        # Create or show view
        if view_name not in self.views:
            self._create_view(view_name)
        
        if view_name in self.views:
            self.views[view_name].pack(fill=tk.BOTH, expand=True)
            
            # Refresh view data
            if hasattr(self.views[view_name], 'refresh'):
                self.views[view_name].refresh()
    
    def _create_view(self, view_name: str):
        """Create a view instance."""
        view_classes = {
            'dashboard': DashboardView,
            'residents': ResidentView,
            'blotter': BlotterView,
            'documents': DocumentView,
            'analytics': AnalyticsView,
            'admin': AdminView,
        }
        
        if view_name in view_classes:
            # Pass navigate callback for dashboard
            if view_name == 'dashboard':
                view = view_classes[view_name](
                    self.view_container,
                    current_user=self.current_user,
                    status_callback=self.status_bar.set_message,
                    navigate_callback=self._show_view
                )
            else:
                view = view_classes[view_name](
                    self.view_container,
                    current_user=self.current_user,
                    status_callback=self.status_bar.set_message
                )
            self.views[view_name] = view
    
    def _logout(self):
        """Handle logout."""
        dialog = ConfirmDialog(
            self,
            "Logout",
            "Are you sure you want to logout?",
            confirm_text="Logout",
            confirm_style="Danger"
        )
        
        if dialog.show():
            # Log audit
            if self.current_user:
                from database import log_audit
                log_audit(
                    self.current_user.get('user_id'),
                    'LOGOUT',
                    'user',
                    self.current_user.get('user_id')
                )
            
            self.current_user = None
            self.views = {}
            self._show_login()
    
    def _on_close(self):
        """Handle window close."""
        dialog = ConfirmDialog(
            self,
            "Exit",
            "Are you sure you want to exit KALASAG?",
            confirm_text="Exit",
            confirm_style="Danger"
        )
        
        if dialog.show():
            self.destroy()
    
    def show_message(self, title: str, message: str, message_type: str = 'info'):
        """Show a message dialog."""
        if message_type == 'error':
            messagebox.showerror(title, message)
        elif message_type == 'warning':
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)


def run_application():
    """Entry point to run the application."""
    app = MainApplication()
    app.mainloop()


if __name__ == "__main__":
    run_application()
