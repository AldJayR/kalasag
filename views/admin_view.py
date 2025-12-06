"""
KALASAG - Admin View
System Administration interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, Optional, List
from datetime import datetime

from views.theme import KalasagTheme
from views.components import SearchFrame, DataTable, CardWidget, ConfirmDialog
from controllers.admin_controller import AdminController


class AdminView(ttk.Frame):
    """System administration view."""
    
    def __init__(self, parent, current_user: Dict, status_callback: Callable):
        super().__init__(parent, style="Main.TFrame")
        
        self.current_user = current_user
        self.status_callback = status_callback
        self.admin_ctrl = AdminController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the admin UI."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky='nsew')
        
        # Create tabs
        self._create_users_tab()
        self._create_audit_tab()
        self._create_backup_tab()
        self._create_settings_tab()
    
    def _create_header(self):
        """Create header."""
        header = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        title = tk.Label(
            header,
            text="System Administration",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)
    
    def _create_users_tab(self):
        """Create user management tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  👤 Users  ")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header
        header = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        tk.Button(
            header, text="➕ Add User", font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._add_user
        ).pack(side=tk.RIGHT)
        
        # Users table
        columns = [
            ('user_id', 'ID', 50),
            ('username', 'Username', 150),
            ('full_name', 'Full Name', 200),
            ('role', 'Role', 100),
            ('is_active', 'Status', 80),
            ('last_login', 'Last Login', 150),
        ]
        
        self.users_table = DataTable(
            tab, columns,
            on_select=self._on_user_select,
            on_double_click=self._edit_user
        )
        self.users_table.grid(row=1, column=0, sticky='nsew')
        
        # Action buttons
        btn_frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        btn_frame.grid(row=2, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        self.edit_user_btn = tk.Button(
            btn_frame, text="✏️ Edit", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.WARNING_ORANGE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._edit_user, state='disabled'
        )
        self.edit_user_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.reset_pwd_btn = tk.Button(
            btn_frame, text="🔑 Reset Password", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.INFO_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._reset_password, state='disabled'
        )
        self.reset_pwd_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.toggle_status_btn = tk.Button(
            btn_frame, text="🔄 Toggle Status", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._toggle_user_status, state='disabled'
        )
        self.toggle_status_btn.pack(side=tk.LEFT)
    
    def _create_audit_tab(self):
        """Create audit log tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  📜 Audit Log  ")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Filter bar
        filter_frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        filter_frame.grid(row=0, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        tk.Label(filter_frame, text="Action:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_MAIN).pack(side=tk.LEFT)
        self.action_filter = ttk.Combobox(
            filter_frame,
            values=['All', 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT'],
            state='readonly',
            width=12
        )
        self.action_filter.current(0)
        self.action_filter.pack(side=tk.LEFT, padx=KalasagTheme.PAD_SMALL)
        self.action_filter.bind('<<ComboboxSelected>>', lambda e: self._filter_audit())
        
        search_frame = SearchFrame(filter_frame, placeholder="Search audit...", on_search=self._search_audit)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=KalasagTheme.PAD_MEDIUM)
        
        tk.Button(
            filter_frame, text="📊 Export", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, command=self._export_audit
        ).pack(side=tk.RIGHT)
        
        # Audit table
        columns = [
            ('log_id', 'ID', 50),
            ('timestamp', 'Timestamp', 150),
            ('username', 'User', 120),
            ('action', 'Action', 100),
            ('table_name', 'Table', 100),
            ('record_id', 'Record', 80),
        ]
        
        self.audit_table = DataTable(tab, columns, on_double_click=self._view_audit_detail)
        self.audit_table.grid(row=1, column=0, sticky='nsew')
    
    def _create_backup_tab(self):
        """Create backup/restore tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  💾 Backup  ")
        
        frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Backup section
        backup_card = tk.Frame(frame, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        backup_card.pack(fill=tk.X, pady=KalasagTheme.PAD_MEDIUM)
        
        tk.Label(
            backup_card, text="💾 Create Backup", font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w')
        
        tk.Label(
            backup_card, text="Create a backup copy of the database.",
            font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY
        ).pack(anchor='w', pady=(KalasagTheme.PAD_SMALL, KalasagTheme.PAD_MEDIUM))
        
        tk.Button(
            backup_card, text="Create Backup", font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_SMALL,
            command=self._create_backup
        ).pack(anchor='w')
        
        # Export section
        export_card = tk.Frame(frame, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        export_card.pack(fill=tk.X, pady=KalasagTheme.PAD_MEDIUM)
        
        tk.Label(
            export_card, text="📤 Export Data", font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w')
        
        tk.Label(
            export_card, text="Export tables to CSV format.",
            font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY
        ).pack(anchor='w', pady=(KalasagTheme.PAD_SMALL, KalasagTheme.PAD_MEDIUM))
        
        btn_row = tk.Frame(export_card, bg=KalasagTheme.BG_CARD)
        btn_row.pack(fill=tk.X)
        
        tables = ['resident', 'household', 'blotter_case', 'doc_log', 'user']
        for table in tables:
            tk.Button(
                btn_row, text=table.replace('_', ' ').title(),
                font=KalasagTheme.FONT_SMALL,
                bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
                bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
                command=lambda t=table: self._export_table(t)
            ).pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        # Backup history
        history_card = tk.Frame(frame, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        history_card.pack(fill=tk.BOTH, expand=True, pady=KalasagTheme.PAD_MEDIUM)
        
        tk.Label(
            history_card, text="📋 Backup History", font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w')
        
        self.backup_list = tk.Listbox(
            history_card, font=KalasagTheme.FONT_BODY, height=8,
            bg=KalasagTheme.BG_MAIN, bd=0
        )
        self.backup_list.pack(fill=tk.BOTH, expand=True, pady=KalasagTheme.PAD_SMALL)
    
    def _create_settings_tab(self):
        """Create settings tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  ⚙️ Settings  ")
        
        frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            frame, text="System Settings", font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_MAIN, fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w', pady=(0, KalasagTheme.PAD_LARGE))
        
        # Barangay Info
        info_card = tk.Frame(frame, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        info_card.pack(fill=tk.X, pady=KalasagTheme.PAD_SMALL)
        
        tk.Label(info_card, text="Barangay Information", font=KalasagTheme.FONT_H3, bg=KalasagTheme.BG_CARD).pack(anchor='w')
        
        # Barangay Name
        row1 = tk.Frame(info_card, bg=KalasagTheme.BG_CARD)
        row1.pack(fill=tk.X, pady=KalasagTheme.PAD_SMALL)
        tk.Label(row1, text="Barangay Name:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, width=15, anchor='w').pack(side=tk.LEFT)
        self.brgy_name_entry = ttk.Entry(row1, font=KalasagTheme.FONT_BODY)
        self.brgy_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Municipality
        row2 = tk.Frame(info_card, bg=KalasagTheme.BG_CARD)
        row2.pack(fill=tk.X, pady=KalasagTheme.PAD_SMALL)
        tk.Label(row2, text="Municipality:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, width=15, anchor='w').pack(side=tk.LEFT)
        self.municipality_entry = ttk.Entry(row2, font=KalasagTheme.FONT_BODY)
        self.municipality_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Province
        row3 = tk.Frame(info_card, bg=KalasagTheme.BG_CARD)
        row3.pack(fill=tk.X, pady=KalasagTheme.PAD_SMALL)
        tk.Label(row3, text="Province:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, width=15, anchor='w').pack(side=tk.LEFT)
        self.province_entry = ttk.Entry(row3, font=KalasagTheme.FONT_BODY)
        self.province_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Save button
        tk.Button(
            info_card, text="Save Settings", font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_SMALL,
            command=self._save_settings
        ).pack(anchor='w', pady=KalasagTheme.PAD_MEDIUM)
    
    def refresh(self):
        """Refresh all admin data."""
        self._load_users()
        self._load_audit()
        self._load_backups()
        self._load_settings()
    
    def _load_users(self):
        """Load users into table."""
        try:
            users = self.admin_ctrl.get_all_users()
            
            data = []
            for u in users:
                data.append({
                    'user_id': u.get('user_id'),
                    'username': u.get('username'),
                    'full_name': u.get('full_name', ''),
                    'role': u.get('role', 'Staff'),
                    'is_active': 'Active' if u.get('is_active') else 'Inactive',
                    'last_login': u.get('last_login', 'Never'),
                })
            
            self.users_table.load_data(data)
        except Exception as e:
            self.status_callback(f"Error loading users: {str(e)}", 'error')
    
    def _load_audit(self):
        """Load audit log."""
        try:
            logs = self.admin_ctrl.get_audit_logs(limit=100)
            
            data = []
            for l in logs:
                data.append({
                    'log_id': l.get('log_id'),
                    'timestamp': l.get('timestamp', ''),
                    'username': l.get('username') or 'System',
                    'action': l.get('action', ''),
                    'table_name': l.get('table_name', ''),
                    'record_id': l.get('record_id', ''),
                })
            
            self.audit_table.load_data(data)
        except Exception as e:
            self.status_callback(f"Error loading audit log: {str(e)}", 'error')
    
    def _load_backups(self):
        """Load backup history."""
        self.backup_list.delete(0, tk.END)
        
        try:
            backups = self.admin_ctrl.get_backup_history()
            
            for b in backups:
                timestamp = b.get('timestamp', 'Unknown')
                filename = b.get('filename', 'Unknown')
                self.backup_list.insert(tk.END, f"{timestamp} - {filename}")
            
            if not backups:
                self.backup_list.insert(tk.END, "No backups found")
        except Exception as e:
            self.backup_list.insert(tk.END, f"Error loading backups")
    
    def _load_settings(self):
        """Load system settings."""
        try:
            settings = self.admin_ctrl.get_settings()
            
            self.brgy_name_entry.delete(0, tk.END)
            self.brgy_name_entry.insert(0, settings.get('barangay_name', ''))
            
            self.municipality_entry.delete(0, tk.END)
            self.municipality_entry.insert(0, settings.get('municipality', ''))
            
            self.province_entry.delete(0, tk.END)
            self.province_entry.insert(0, settings.get('province', ''))
        except Exception as e:
            self.status_callback(f"Error loading settings: {str(e)}", 'error')
    
    def _on_user_select(self, item: Dict):
        """Handle user selection."""
        state = 'normal' if item else 'disabled'
        self.edit_user_btn.configure(state=state)
        self.reset_pwd_btn.configure(state=state)
        self.toggle_status_btn.configure(state=state)
    
    def _add_user(self):
        """Add new user."""
        dialog = UserFormDialog(self, "Add User", self.admin_ctrl, self.current_user)
        if dialog.show():
            self._load_users()
            self.status_callback("User added successfully", 'success')
    
    def _edit_user(self, event=None):
        """Edit selected user."""
        selected = self.users_table.get_selected()
        if selected:
            user = self.admin_ctrl.get_user(selected['user_id'])
            if user:
                dialog = UserFormDialog(self, "Edit User", self.admin_ctrl, self.current_user, user)
                if dialog.show():
                    self._load_users()
                    self.status_callback("User updated successfully", 'success')
    
    def _reset_password(self):
        """Reset user password."""
        selected = self.users_table.get_selected()
        if selected:
            dialog = ResetPasswordDialog(self, self.admin_ctrl, selected['user_id'], self.current_user)
            if dialog.show():
                self.status_callback("Password reset successfully", 'success')
    
    def _toggle_user_status(self):
        """Toggle user active status."""
        selected = self.users_table.get_selected()
        if not selected:
            return
        
        current_status = selected['is_active'] == 'Active'
        new_status = not current_status
        action = "deactivate" if current_status else "activate"
        
        dialog = ConfirmDialog(
            self,
            f"Confirm {action.title()}",
            f"Are you sure you want to {action} user '{selected['username']}'?",
            confirm_text=action.title()
        )
        
        if dialog.show():
            if current_status:
                success, msg = self.admin_ctrl.deactivate_user(
                    selected['user_id'],
                    self.current_user['user_id']
                )
            else:
                success, msg = self.admin_ctrl.activate_user(selected['user_id'])
            
            if success:
                self._load_users()
                self.status_callback(f"User {action}d successfully", 'success')
            else:
                self.status_callback(f"Failed to {action} user: {msg}", 'error')
    
    def _filter_audit(self):
        """Filter audit log."""
        action = self.action_filter.get()
        
        try:
            if action == 'All':
                logs = self.admin_ctrl.get_audit_logs(limit=100)
            else:
                from models.admin import AuditLogModel
                logs = AuditLogModel.search(action)
            
            data = []
            for l in logs:
                data.append({
                    'log_id': l.get('log_id'),
                    'timestamp': l.get('timestamp', ''),
                    'username': l.get('username', 'System'),
                    'action': l.get('action', ''),
                    'table_name': l.get('table_name', ''),
                    'record_id': l.get('record_id', ''),
                })
            
            self.audit_table.load_data(data)
        except Exception as e:
            self.status_callback(f"Filter error: {str(e)}", 'error')
    
    def _search_audit(self, query: str):
        """Search audit log."""
        if not query:
            self._load_audit()
            return
        
        try:
            from models.admin import AuditLogModel
            logs = AuditLogModel.search(query)
            
            data = []
            for l in logs:
                data.append({
                    'log_id': l.get('log_id'),
                    'timestamp': l.get('timestamp', ''),
                    'username': l.get('username', 'System'),
                    'action': l.get('action', ''),
                    'table_name': l.get('table_name', ''),
                    'record_id': l.get('record_id', ''),
                })
            
            self.audit_table.load_data(data)
            self.status_callback(f"Found {len(data)} audit entries", 'info')
        except Exception as e:
            self.status_callback(f"Search error: {str(e)}", 'error')
    
    def _view_audit_detail(self, event=None):
        """View audit detail."""
        selected = self.audit_table.get_selected()
        if selected:
            from models.admin import AuditLogModel
            logs = AuditLogModel.get_all(limit=1000)
            
            for log in logs:
                if log.get('log_id') == selected['log_id']:
                    AuditDetailDialog(self, log)
                    break
    
    def _export_audit(self):
        """Export audit log."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"audit_log_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                from database import export_to_csv
                export_to_csv('audit_log', filename)
                self.status_callback(f"Audit log exported to {filename}", 'success')
        except Exception as e:
            self.status_callback(f"Export error: {str(e)}", 'error')
    
    def _create_backup(self):
        """Create database backup."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                initialfile=f"kalasag_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if filename:
                success, msg = self.admin_ctrl.create_backup(filename)
                
                if success:
                    self._load_backups()
                    self.status_callback(f"Backup created: {filename}", 'success')
                    messagebox.showinfo("Success", f"Backup created:\n{filename}")
                else:
                    self.status_callback(f"Backup failed: {msg}", 'error')
        except Exception as e:
            self.status_callback(f"Backup error: {str(e)}", 'error')
    
    def _export_table(self, table_name: str):
        """Export a table to CSV."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"{table_name}_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                from database import export_to_csv
                export_to_csv(table_name, filename)
                self.status_callback(f"Exported {table_name} to {filename}", 'success')
        except Exception as e:
            self.status_callback(f"Export error: {str(e)}", 'error')
    
    def _save_settings(self):
        """Save system settings."""
        try:
            settings = {
                'barangay_name': self.brgy_name_entry.get().strip(),
                'municipality': self.municipality_entry.get().strip(),
                'province': self.province_entry.get().strip(),
            }
            
            success, msg = self.admin_ctrl.save_settings(settings)
            
            if success:
                self.status_callback("Settings saved successfully", 'success')
            else:
                self.status_callback(f"Failed to save settings: {msg}", 'error')
        except Exception as e:
            self.status_callback(f"Save error: {str(e)}", 'error')


class UserFormDialog(tk.Toplevel):
    """Dialog for adding/editing users."""
    
    def __init__(self, parent, title: str, controller: AdminController, current_user: Dict, user: Dict = None):
        super().__init__(parent)
        
        self.controller = controller
        self.current_user = current_user
        self.user = user
        self.result = False
        
        self.title(title)
        self.geometry("400x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        self._build_form()
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _build_form(self):
        """Build the form."""
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        tk.Label(frame, text="Username *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.username_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.username_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Password (only for new users)
        if not self.user:
            tk.Label(frame, text="Password *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
            self.password_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY, show="•")
            self.password_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Full Name
        tk.Label(frame, text="Full Name *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.fullname_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.fullname_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Role
        tk.Label(frame, text="Role *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.role_combo = ttk.Combobox(
            frame,
            values=['Admin', 'Captain', 'Secretary', 'Kagawad', 'Staff'],
            state='readonly',
            font=KalasagTheme.FONT_BODY
        )
        self.role_combo.current(4)  # Default to Staff
        self.role_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Populate if editing
        if self.user:
            self.username_entry.insert(0, self.user.get('username', ''))
            self.fullname_entry.insert(0, self.user.get('full_name', ''))
            
            role = self.user.get('role', 'Staff')
            roles = ['Admin', 'Captain', 'Secretary', 'Kagawad', 'Staff']
            if role in roles:
                self.role_combo.current(roles.index(role))
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Save", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._save).pack(side=tk.RIGHT)
    
    def _save(self):
        """Save the user."""
        username = self.username_entry.get().strip()
        fullname = self.fullname_entry.get().strip()
        role = self.role_combo.get()
        
        if not username:
            messagebox.showerror("Error", "Username is required")
            return
        
        if not fullname:
            messagebox.showerror("Error", "Full name is required")
            return
        
        if self.user:
            # Update existing user
            success, msg, _ = self.controller.update_user(
                user_id=self.user['user_id'],
                full_name=fullname,
                role=role
            )
        else:
            # Create new user
            password = self.password_entry.get()
            if not password:
                messagebox.showerror("Error", "Password is required")
                return
            
            success, msg, _ = self.controller.create_user(
                username=username,
                password=password,
                full_name=fullname,
                role=role
            )
        
        if success:
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result


class ResetPasswordDialog(tk.Toplevel):
    """Dialog for resetting user password."""
    
    def __init__(self, parent, controller: AdminController, user_id: int, current_user: Dict):
        super().__init__(parent)
        
        self.controller = controller
        self.user_id = user_id
        self.current_user = current_user
        self.result = False
        
        self.title("Reset Password")
        self.geometry("350x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="New Password *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.new_pwd_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY, show="•")
        self.new_pwd_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        tk.Label(frame, text="Confirm Password *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.confirm_pwd_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY, show="•")
        self.confirm_pwd_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        btn_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Reset", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.WARNING_ORANGE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._reset).pack(side=tk.RIGHT)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _reset(self):
        new_pwd = self.new_pwd_entry.get()
        confirm_pwd = self.confirm_pwd_entry.get()
        
        if not new_pwd:
            messagebox.showerror("Error", "New password is required")
            return
        
        if new_pwd != confirm_pwd:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(new_pwd) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        success, msg = self.controller.change_password(
            self.user_id,
            new_pwd,
            self.current_user['user_id']
        )
        
        if success:
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result


class AuditDetailDialog(tk.Toplevel):
    """Dialog to view audit detail."""
    
    def __init__(self, parent, log: Dict):
        super().__init__(parent)
        
        self.title("Audit Log Detail")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Audit Log Entry", font=KalasagTheme.FONT_H2, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY).pack(anchor='w')
        
        details = [
            ('ID', log.get('log_id')),
            ('Timestamp', log.get('timestamp')),
            ('User', log.get('username') or 'System'),
            ('Action', log.get('action')),
            ('Table', log.get('table_name')),
            ('Record ID', log.get('record_id')),
        ]
        
        for label, value in details:
            row = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"{label}:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY, width=12, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY).pack(side=tk.LEFT)
        
        # Old/New values
        if log.get('old_values'):
            tk.Label(frame, text="Old Values:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w', pady=(KalasagTheme.PAD_MEDIUM, 2))
            old_text = tk.Text(frame, height=4, font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.BG_MAIN, bd=0)
            old_text.insert('1.0', str(log.get('old_values')))
            old_text.configure(state='disabled')
            old_text.pack(fill=tk.X)
        
        if log.get('new_values'):
            tk.Label(frame, text="New Values:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w', pady=(KalasagTheme.PAD_MEDIUM, 2))
            new_text = tk.Text(frame, height=4, font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.BG_MAIN, bd=0)
            new_text.insert('1.0', str(log.get('new_values')))
            new_text.configure(state='disabled')
            new_text.pack(fill=tk.X)
        
        tk.Button(frame, text="Close", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self.destroy).pack(pady=KalasagTheme.PAD_LARGE)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
