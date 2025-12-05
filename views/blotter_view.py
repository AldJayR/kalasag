"""
KALASAG - Blotter View
E-Blotter and Case Management interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Optional, List
from datetime import datetime

from views.theme import KalasagTheme
from views.components import SearchFrame, DataTable, CardWidget, ConfirmDialog, StatusBadge
from controllers.blotter_controller import BlotterController
from controllers.resident_controller import ResidentController


class BlotterView(ttk.Frame):
    """E-Blotter and Case Management view."""
    
    def __init__(self, parent, current_user: Dict, status_callback: Callable):
        super().__init__(parent, style="Main.TFrame")
        
        self.current_user = current_user
        self.status_callback = status_callback
        self.blotter_ctrl = BlotterController()
        self.resident_ctrl = ResidentController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the blotter management UI."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Main content
        self._create_content()
    
    def _create_header(self):
        """Create header."""
        header = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        title = tk.Label(
            header,
            text="E-Blotter & Case Management",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)
        
        # Add case button
        add_btn = tk.Button(
            header,
            text="📋 New Case",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            activebackground=KalasagTheme.PRIMARY_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._add_case
        )
        add_btn.pack(side=tk.RIGHT)
    
    def _create_content(self):
        """Create main content area."""
        content = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        content.grid(row=1, column=0, sticky='nsew')
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        
        # Filter/Search bar
        filter_frame = tk.Frame(content, bg=KalasagTheme.BG_MAIN)
        filter_frame.grid(row=0, column=0, sticky='ew', pady=(0, KalasagTheme.PAD_SMALL))
        
        # Status filter
        tk.Label(filter_frame, text="Status:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_MAIN).pack(side=tk.LEFT)
        
        self.status_filter = ttk.Combobox(
            filter_frame,
            values=['All', 'Filed', 'Under Investigation', 'Scheduled', 'Resolved', 'Dismissed'],
            state='readonly',
            width=15
        )
        self.status_filter.current(0)
        self.status_filter.pack(side=tk.LEFT, padx=KalasagTheme.PAD_SMALL)
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self._filter_cases())
        
        # Search
        search_frame = SearchFrame(filter_frame, placeholder="Search cases...", on_search=self._search_cases)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=KalasagTheme.PAD_MEDIUM)
        
        # Cases table
        columns = [
            ('case_id', 'Case #', 60),
            ('case_number', 'Reference', 120),
            ('incident_type', 'Type', 120),
            ('date_time', 'Date/Time', 140),
            ('location', 'Location', 150),
            ('status', 'Status', 100),
            ('priority', 'Priority', 80),
        ]
        
        self.cases_table = DataTable(
            content, columns,
            on_select=self._on_case_select,
            on_double_click=self._view_case
        )
        self.cases_table.grid(row=1, column=0, sticky='nsew')
        
        # Action buttons
        btn_frame = tk.Frame(content, bg=KalasagTheme.BG_MAIN)
        btn_frame.grid(row=2, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        self.view_btn = tk.Button(
            btn_frame, text="👁️ View", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.INFO_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._view_case, state='disabled'
        )
        self.view_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.edit_btn = tk.Button(
            btn_frame, text="✏️ Edit", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.WARNING_ORANGE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._edit_case, state='disabled'
        )
        self.edit_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.status_btn = tk.Button(
            btn_frame, text="🔄 Update Status", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._update_status, state='disabled'
        )
        self.status_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.persons_btn = tk.Button(
            btn_frame, text="👥 Persons Involved", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._manage_persons, state='disabled'
        )
        self.persons_btn.pack(side=tk.LEFT)
    
    def refresh(self):
        """Refresh case data."""
        self._load_cases()
    
    def _load_cases(self):
        """Load cases into table."""
        try:
            cases = self.blotter_ctrl.get_all_cases()
            
            data = []
            for c in cases:
                data.append({
                    'case_id': c.get('case_id'),
                    'case_number': c.get('case_number', 'N/A'),
                    'incident_type': c.get('incident_type', c.get('name', 'N/A')),
                    'date_time': c.get('date_time', ''),
                    'location': c.get('location', ''),
                    'status': c.get('status', 'Filed'),
                    'priority': c.get('priority', 'Normal'),
                })
            
            self.cases_table.load_data(data)
            self.status_callback(f"Loaded {len(data)} cases", 'success')
        except Exception as e:
            self.status_callback(f"Error loading cases: {str(e)}", 'error')
    
    def _filter_cases(self):
        """Filter cases by status."""
        status = self.status_filter.get()
        
        try:
            if status == 'All':
                cases = self.blotter_ctrl.get_all_cases()
            else:
                cases = self.blotter_ctrl.get_cases_by_status(status)
            
            data = []
            for c in cases:
                data.append({
                    'case_id': c.get('case_id'),
                    'case_number': c.get('case_number', 'N/A'),
                    'incident_type': c.get('incident_type', c.get('name', 'N/A')),
                    'date_time': c.get('date_time', ''),
                    'location': c.get('location', ''),
                    'status': c.get('status', 'Filed'),
                    'priority': c.get('priority', 'Normal'),
                })
            
            self.cases_table.load_data(data)
        except Exception as e:
            self.status_callback(f"Error filtering: {str(e)}", 'error')
    
    def _search_cases(self, query: str):
        """Search cases."""
        if not query:
            self._load_cases()
            return
        
        try:
            cases = self.blotter_ctrl.search_cases(query)
            
            data = []
            for c in cases:
                data.append({
                    'case_id': c.get('case_id'),
                    'case_number': c.get('case_number', 'N/A'),
                    'incident_type': c.get('incident_type', c.get('name', 'N/A')),
                    'date_time': c.get('date_time', ''),
                    'location': c.get('location', ''),
                    'status': c.get('status', 'Filed'),
                    'priority': c.get('priority', 'Normal'),
                })
            
            self.cases_table.load_data(data)
            self.status_callback(f"Found {len(data)} cases", 'info')
        except Exception as e:
            self.status_callback(f"Search error: {str(e)}", 'error')
    
    def _on_case_select(self, item: Dict):
        """Handle case selection."""
        state = 'normal' if item else 'disabled'
        self.view_btn.configure(state=state)
        self.edit_btn.configure(state=state)
        self.status_btn.configure(state=state)
        self.persons_btn.configure(state=state)
    
    def _add_case(self):
        """Add new case."""
        dialog = CaseFormDialog(self, "New Case", self.blotter_ctrl, self.current_user)
        if dialog.show():
            self._load_cases()
            self.status_callback("Case created successfully", 'success')
    
    def _view_case(self, event=None):
        """View selected case."""
        selected = self.cases_table.get_selected()
        if selected:
            case = self.blotter_ctrl.get_case(selected['case_id'])
            if case:
                CaseDetailDialog(self, case, self.blotter_ctrl)
    
    def _edit_case(self):
        """Edit selected case."""
        selected = self.cases_table.get_selected()
        if selected:
            case = self.blotter_ctrl.get_case(selected['case_id'])
            if case:
                dialog = CaseFormDialog(self, "Edit Case", self.blotter_ctrl, self.current_user, case)
                if dialog.show():
                    self._load_cases()
                    self.status_callback("Case updated successfully", 'success')
    
    def _update_status(self):
        """Update case status."""
        selected = self.cases_table.get_selected()
        if selected:
            dialog = StatusUpdateDialog(self, self.blotter_ctrl, selected['case_id'], selected['status'])
            if dialog.show():
                self._load_cases()
                self.status_callback("Status updated successfully", 'success')
    
    def _manage_persons(self):
        """Manage persons involved."""
        selected = self.cases_table.get_selected()
        if selected:
            PersonsInvolvedDialog(self, self.blotter_ctrl, self.resident_ctrl, selected['case_id'])


class CaseFormDialog(tk.Toplevel):
    """Dialog for adding/editing cases."""
    
    def __init__(self, parent, title: str, controller: BlotterController, current_user: Dict, case: Dict = None):
        super().__init__(parent)
        
        self.controller = controller
        self.current_user = current_user
        self.case = case
        self.result = False
        
        self.title(title)
        self.geometry("550x600")
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
        # Scrollable frame
        canvas = tk.Canvas(self, bg=KalasagTheme.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Incident Type
        tk.Label(form, text="Incident Type *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        
        types = self.controller.get_incident_types()
        self.type_values = [f"{t['type_id']} - {t['name']}" for t in types]
        
        self.type_combo = ttk.Combobox(form, values=self.type_values, state='readonly', font=KalasagTheme.FONT_BODY)
        self.type_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Date/Time
        tk.Label(form, text="Date/Time *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.datetime_entry = ttk.Entry(form, font=KalasagTheme.FONT_BODY)
        self.datetime_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        self.datetime_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # Location (Purok)
        tk.Label(form, text="Location (Purok) *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        
        puroks = self.controller.get_puroks()
        self.purok_values = [f"{p['purok_id']} - {p['purok_name']}" for p in puroks]
        
        self.purok_combo = ttk.Combobox(form, values=self.purok_values, state='readonly', font=KalasagTheme.FONT_BODY)
        self.purok_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Narrative
        tk.Label(form, text="Narrative *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.narrative_text = tk.Text(form, height=6, font=KalasagTheme.FONT_BODY)
        self.narrative_text.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Status (only for editing)
        if self.case:
            tk.Label(form, text="Status", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
            self.status_combo = ttk.Combobox(
                form,
                values=['Pending', 'Amicable Settlement', 'Escalated to PNP', 'Closed'],
                state='readonly',
                font=KalasagTheme.FONT_BODY
            )
            self.status_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Populate if editing
        if self.case:
            self._populate_form()
        
        # Buttons
        btn_frame = tk.Frame(form, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Save", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._save).pack(side=tk.RIGHT)
    
    def _populate_form(self):
        """Populate form with existing data."""
        # Set incident type
        type_id = self.case.get('type_id')
        if type_id:
            for i, val in enumerate(self.type_combo['values']):
                if val.startswith(f"{type_id} - "):
                    self.type_combo.current(i)
                    break
        
        self.datetime_entry.delete(0, tk.END)
        self.datetime_entry.insert(0, self.case.get('date_time', ''))
        
        # Set purok
        purok_id = self.case.get('purok_id')
        if purok_id:
            for i, val in enumerate(self.purok_combo['values']):
                if val.startswith(f"{purok_id} - "):
                    self.purok_combo.current(i)
                    break
        
        self.narrative_text.insert('1.0', self.case.get('narrative', ''))
        
        if hasattr(self, 'status_combo'):
            self.status_combo.set(self.case.get('status', 'Pending'))
    
    def _save(self):
        """Save the case."""
        type_selection = self.type_combo.get()
        datetime_val = self.datetime_entry.get().strip()
        purok_selection = self.purok_combo.get()
        narrative = self.narrative_text.get('1.0', tk.END).strip()
        
        if not type_selection:
            messagebox.showerror("Error", "Incident type is required")
            return
        
        if not datetime_val:
            messagebox.showerror("Error", "Date/Time is required")
            return
        
        if not purok_selection:
            messagebox.showerror("Error", "Location (Purok) is required")
            return
        
        if not narrative:
            messagebox.showerror("Error", "Narrative is required")
            return
        
        type_id = int(type_selection.split(' - ')[0])
        purok_id = int(purok_selection.split(' - ')[0])
        
        data = {
            'type_id': type_id,
            'date_time': datetime_val,
            'purok_id': purok_id,
            'narrative': narrative,
            'reported_by': self.current_user.get('user_id'),
        }
        
        if self.case and hasattr(self, 'status_combo'):
            data['status'] = self.status_combo.get()
        
        if self.case:
            success, msg = self.controller.update_case(self.case['case_id'], data)
        else:
            success, msg = self.controller.create_case(data)
        
        if success:
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result


class CaseDetailDialog(tk.Toplevel):
    """Dialog to view case details."""
    
    def __init__(self, parent, case: Dict, controller: BlotterController):
        super().__init__(parent)
        
        self.title(f"Case Details - {case.get('case_number', 'N/A')}")
        self.geometry("550x500")
        self.resizable(False, False)
        self.transient(parent)
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        # Content
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        header.pack(fill=tk.X, pady=(0, KalasagTheme.PAD_MEDIUM))
        
        tk.Label(
            header,
            text=case.get('case_number', 'N/A'),
            font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT)
        
        # Status badge
        status = case.get('status', 'Filed')
        status_colors = {
            'Filed': KalasagTheme.INFO_BLUE,
            'Under Investigation': KalasagTheme.WARNING_ORANGE,
            'Scheduled': KalasagTheme.PRIMARY_BLUE,
            'Resolved': KalasagTheme.SUCCESS_GREEN,
            'Dismissed': KalasagTheme.TEXT_MUTED,
        }
        
        tk.Label(
            header,
            text=status,
            font=KalasagTheme.FONT_SMALL,
            bg=status_colors.get(status, KalasagTheme.TEXT_MUTED),
            fg=KalasagTheme.TEXT_LIGHT,
            padx=8,
            pady=2
        ).pack(side=tk.RIGHT)
        
        # Details
        details = [
            ('Type', case.get('incident_type', case.get('name', 'N/A'))),
            ('Date/Time', case.get('date_time', 'N/A')),
            ('Location', case.get('location', 'N/A')),
            ('Priority', case.get('priority', 'Normal')),
            ('Reported By', case.get('reporter_name', 'N/A')),
        ]
        
        for label, value in details:
            row = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{label}:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY, width=15, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY, anchor='w').pack(side=tk.LEFT, fill=tk.X)
        
        # Narrative
        tk.Label(frame, text="Narrative:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY, anchor='w').pack(fill=tk.X, pady=(KalasagTheme.PAD_MEDIUM, 2))
        
        narrative_frame = tk.Frame(frame, bg=KalasagTheme.BG_MAIN, padx=KalasagTheme.PAD_SMALL, pady=KalasagTheme.PAD_SMALL)
        narrative_frame.pack(fill=tk.BOTH, expand=True)
        
        narrative_text = tk.Text(narrative_frame, font=KalasagTheme.FONT_BODY, wrap=tk.WORD, height=8, bd=0, bg=KalasagTheme.BG_MAIN)
        narrative_text.insert('1.0', case.get('narrative', 'No narrative provided.'))
        narrative_text.configure(state='disabled')
        narrative_text.pack(fill=tk.BOTH, expand=True)
        
        # Persons involved
        tk.Label(frame, text="Persons Involved:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY, anchor='w').pack(fill=tk.X, pady=(KalasagTheme.PAD_MEDIUM, 2))
        
        persons = controller.get_case_involvements(case['case_id'])
        persons_frame = tk.Frame(frame, bg=KalasagTheme.BG_MAIN, padx=KalasagTheme.PAD_SMALL, pady=KalasagTheme.PAD_SMALL)
        persons_frame.pack(fill=tk.X)
        
        if persons:
            for p in persons:
                name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or 'Unknown'
                role = p.get('role', 'Unknown')
                tk.Label(persons_frame, text=f"• {name} ({role})", font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.BG_MAIN, fg=KalasagTheme.TEXT_PRIMARY, anchor='w').pack(fill=tk.X)
        else:
            tk.Label(persons_frame, text="No persons recorded", font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.BG_MAIN, fg=KalasagTheme.TEXT_MUTED).pack()
        
        # Close button
        tk.Button(
            frame, text="Close", font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_SMALL,
            command=self.destroy
        ).pack(pady=KalasagTheme.PAD_MEDIUM)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class StatusUpdateDialog(tk.Toplevel):
    """Dialog for updating case status."""
    
    def __init__(self, parent, controller: BlotterController, case_id: int, current_status: str):
        super().__init__(parent)
        
        self.controller = controller
        self.case_id = case_id
        self.result = False
        
        self.title("Update Status")
        self.geometry("350x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Current Status:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        tk.Label(frame, text=current_status, font=KalasagTheme.FONT_H3, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY).pack(anchor='w', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        tk.Label(frame, text="New Status:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.status_combo = ttk.Combobox(
            frame,
            values=['Filed', 'Under Investigation', 'Scheduled', 'Resolved', 'Dismissed'],
            state='readonly',
            font=KalasagTheme.FONT_BODY
        )
        self.status_combo.set(current_status)
        self.status_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        btn_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_MEDIUM)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Update", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._update).pack(side=tk.RIGHT)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _update(self):
        new_status = self.status_combo.get()
        success, msg = self.controller.update_case(self.case_id, {'status': new_status})
        
        if success:
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result


class PersonsInvolvedDialog(tk.Toplevel):
    """Dialog for managing persons involved in a case."""
    
    def __init__(self, parent, blotter_ctrl: BlotterController, resident_ctrl: ResidentController, case_id: int):
        super().__init__(parent)
        
        self.blotter_ctrl = blotter_ctrl
        self.resident_ctrl = resident_ctrl
        self.case_id = case_id
        
        self.title("Persons Involved")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        self._build_ui()
        self._load_persons()
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Build the UI."""
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add person section
        add_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        add_frame.pack(fill=tk.X, pady=(0, KalasagTheme.PAD_MEDIUM))
        
        tk.Label(add_frame, text="Add Person:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        
        row = tk.Frame(add_frame, bg=KalasagTheme.BG_CARD)
        row.pack(fill=tk.X)
        
        # Resident selection
        residents = self.resident_ctrl.get_all_residents()
        res_values = [f"{r['resident_id']} - {r.get('first_name', '')} {r.get('last_name', '')}".strip() for r in residents]
        
        self.resident_combo = ttk.Combobox(row, values=res_values, font=KalasagTheme.FONT_BODY, width=25)
        self.resident_combo.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        # Role selection
        self.role_combo = ttk.Combobox(row, values=['Complainant', 'Respondent', 'Witness', 'Victim', 'Suspect'], state='readonly', font=KalasagTheme.FONT_BODY, width=12)
        self.role_combo.current(0)
        self.role_combo.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        tk.Button(row, text="Add", font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._add_person).pack(side=tk.LEFT)
        
        # List
        tk.Label(frame, text="Current Persons:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w', pady=(KalasagTheme.PAD_MEDIUM, 2))
        
        self.persons_list = tk.Listbox(frame, font=KalasagTheme.FONT_BODY, height=10)
        self.persons_list.pack(fill=tk.BOTH, expand=True)
        
        # Remove button
        tk.Button(frame, text="Remove Selected", font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.DANGER_RED, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._remove_person).pack(anchor='w', pady=KalasagTheme.PAD_SMALL)
        
        # Close
        tk.Button(frame, text="Close", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self.destroy).pack(pady=KalasagTheme.PAD_MEDIUM)
    
    def _load_persons(self):
        """Load persons involved."""
        self.persons_list.delete(0, tk.END)
        
        persons = self.blotter_ctrl.get_case_involvements(self.case_id)
        self.persons_data = persons
        
        for p in persons:
            name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or 'Unknown'
            role = p.get('role', 'Unknown')
            self.persons_list.insert(tk.END, f"{name} - {role}")
    
    def _add_person(self):
        """Add person to case."""
        resident_sel = self.resident_combo.get()
        role = self.role_combo.get()
        
        if not resident_sel:
            messagebox.showwarning("Warning", "Please select a resident")
            return
        
        resident_id = int(resident_sel.split(' - ')[0])
        
        success, msg = self.blotter_ctrl.add_involvement(self.case_id, resident_id, role)
        
        if success:
            self._load_persons()
            self.resident_combo.set('')
        else:
            messagebox.showerror("Error", msg)
    
    def _remove_person(self):
        """Remove selected person from case."""
        selection = self.persons_list.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx < len(self.persons_data):
            person = self.persons_data[idx]
            involvement_id = person.get('involvement_id')
            
            if involvement_id:
                success, msg = self.blotter_ctrl.remove_involvement(involvement_id)
                if success:
                    self._load_persons()
                else:
                    messagebox.showerror("Error", msg)
