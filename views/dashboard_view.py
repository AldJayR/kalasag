"""
KALASAG - Dashboard View
Main dashboard with statistics and quick access.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional
from datetime import datetime

from views.theme import KalasagTheme
from views.components import DashboardCard, CardWidget
from controllers.resident_controller import ResidentController
from controllers.blotter_controller import BlotterController
from controllers.document_controller import DocumentController
from controllers.analytics_controller import AnalyticsController


class DashboardView(ttk.Frame):
    """Dashboard view with system overview."""
    
    def __init__(self, parent, current_user: Dict, status_callback: Callable, navigate_callback: Callable = None):
        super().__init__(parent, style="Main.TFrame")
        
        self.current_user = current_user
        self.status_callback = status_callback
        self.navigate_callback = navigate_callback
        
        # Controllers
        self.resident_ctrl = ResidentController()
        self.blotter_ctrl = BlotterController()
        self.document_ctrl = DocumentController()
        self.analytics_ctrl = AnalyticsController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dashboard UI."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Stats cards
        self._create_stats_section()
        
        # Main content area
        self._create_content_section()
    
    def _create_header(self):
        """Create dashboard header."""
        header_frame = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        # Title
        title = tk.Label(
            header_frame,
            text="Dashboard",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)
        
        # Date/time
        self.datetime_label = tk.Label(
            header_frame,
            text="",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_SECONDARY
        )
        self.datetime_label.pack(side=tk.RIGHT)
        self._update_datetime()
    
    def _update_datetime(self):
        """Update the datetime display."""
        now = datetime.now()
        self.datetime_label.configure(text=now.strftime("%A, %B %d, %Y  %I:%M %p"))
        self.after(60000, self._update_datetime)  # Update every minute
    
    def _create_stats_section(self):
        """Create statistics cards section."""
        stats_frame = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        stats_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=KalasagTheme.PAD_MEDIUM)
        
        # Configure grid for cards
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1, uniform='stats')
        
        # Create stat cards
        self.residents_card = DashboardCard(
            stats_frame, "👥", "Total Residents", "0",
            color=KalasagTheme.PRIMARY_BLUE
        )
        self.residents_card.grid(row=0, column=0, sticky='ew', padx=(0, KalasagTheme.PAD_SMALL))
        
        self.households_card = DashboardCard(
            stats_frame, "🏠", "Households", "0",
            color=KalasagTheme.SUCCESS_GREEN
        )
        self.households_card.grid(row=0, column=1, sticky='ew', padx=KalasagTheme.PAD_SMALL)
        
        self.cases_card = DashboardCard(
            stats_frame, "📋", "Active Cases", "0",
            color=KalasagTheme.WARNING_ORANGE
        )
        self.cases_card.grid(row=0, column=2, sticky='ew', padx=KalasagTheme.PAD_SMALL)
        
        self.documents_card = DashboardCard(
            stats_frame, "📄", "Documents (Month)", "0",
            color=KalasagTheme.INFO_BLUE
        )
        self.documents_card.grid(row=0, column=3, sticky='ew', padx=(KalasagTheme.PAD_SMALL, 0))
    
    def _create_content_section(self):
        """Create main content section."""
        content_frame = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        content_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=KalasagTheme.PAD_MEDIUM)
        content_frame.columnconfigure(0, weight=2)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Left: Recent Activity
        activity_card = CardWidget(content_frame, "Recent Activity")
        activity_card.grid(row=0, column=0, sticky='nsew', padx=(0, KalasagTheme.PAD_SMALL))
        
        # Activity list
        self.activity_list = tk.Listbox(
            activity_card.content_frame,
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY,
            selectbackground=KalasagTheme.PRIMARY_LIGHT,
            selectforeground=KalasagTheme.TEXT_LIGHT,
            bd=0,
            highlightthickness=0,
            activestyle='none'
        )
        self.activity_list.pack(fill=tk.BOTH, expand=True)
        
        # Right: Quick Actions
        actions_card = CardWidget(content_frame, "Quick Actions")
        actions_card.grid(row=0, column=1, sticky='nsew', padx=(KalasagTheme.PAD_SMALL, 0))
        
        quick_actions = [
            ("➕ Register New Resident", self._quick_add_resident),
            ("📋 New Blotter Entry", self._quick_add_blotter),
            ("📄 Issue Document", self._quick_issue_document),
            ("📊 View Reports", self._quick_view_reports),
        ]
        
        for text, command in quick_actions:
            btn = tk.Button(
                actions_card.content_frame,
                text=text,
                font=KalasagTheme.FONT_BODY,
                bg=KalasagTheme.BG_CARD,
                fg=KalasagTheme.TEXT_PRIMARY,
                activebackground=KalasagTheme.PRIMARY_LIGHT,
                activeforeground=KalasagTheme.TEXT_LIGHT,
                bd=1,
                relief='solid',
                anchor='w',
                padx=KalasagTheme.PAD_MEDIUM,
                pady=KalasagTheme.PAD_MEDIUM,
                cursor='hand2',
                command=command
            )
            btn.pack(fill=tk.X, pady=(0, KalasagTheme.PAD_SMALL))
            
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=KalasagTheme.PRIMARY_LIGHT, fg=KalasagTheme.TEXT_LIGHT))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY))
    
    def refresh(self):
        """Refresh dashboard data."""
        try:
            # Update stats
            residents = self.resident_ctrl.get_all_residents()
            self.residents_card.update_value(str(len(residents)))
            
            households = self.resident_ctrl.get_all_households()
            self.households_card.update_value(str(len(households)))
            
            cases = self.blotter_ctrl.get_all_cases()
            active_cases = [c for c in cases if c.get('status') in ('Filed', 'Under Investigation', 'Scheduled')]
            self.cases_card.update_value(str(len(active_cases)))
            
            # Get documents for current month
            from datetime import datetime
            now = datetime.now()
            month_start = now.replace(day=1).strftime("%Y-%m-%d")
            month_end = now.strftime("%Y-%m-%d")
            documents = self.document_ctrl.get_documents_by_date_range(month_start, month_end)
            self.documents_card.update_value(str(len(documents)))
            
            # Update activity list
            self._update_activity_list()
            
            self.status_callback("Dashboard refreshed", 'success')
        except Exception as e:
            self.status_callback(f"Error refreshing dashboard: {str(e)}", 'error')
    
    def _update_activity_list(self):
        """Update the recent activity list."""
        self.activity_list.delete(0, tk.END)
        
        try:
            # Get recent activities from audit log
            from models.admin import AuditLogModel
            logs = AuditLogModel.get_all(limit=20)
            
            for log in logs:
                timestamp = log.get('timestamp', '')[:16]
                action = log.get('action', 'Unknown')
                table = log.get('table_name', '')
                username = log.get('username', 'System')
                
                activity_text = f"{timestamp} | {username} - {action} ({table})"
                self.activity_list.insert(tk.END, activity_text)
        except Exception:
            self.activity_list.insert(tk.END, "No recent activity")
    
    def _quick_add_resident(self):
        """Quick action: Add resident."""
        if self.navigate_callback:
            self.navigate_callback('residents')
    
    def _quick_add_blotter(self):
        """Quick action: Add blotter."""
        if self.navigate_callback:
            self.navigate_callback('blotter')
    
    def _quick_issue_document(self):
        """Quick action: Issue document."""
        if self.navigate_callback:
            self.navigate_callback('documents')
    
    def _quick_view_reports(self):
        """Quick action: View reports."""
        if self.navigate_callback:
            self.navigate_callback('analytics')
