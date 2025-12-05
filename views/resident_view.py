"""
KALASAG - Resident View
Resident Information System (RIS) management interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Optional, List

from views.theme import KalasagTheme
from views.components import SearchFrame, DataTable, CardWidget, ConfirmDialog, FormDialog
from controllers.resident_controller import ResidentController


class ResidentView(ttk.Frame):
    """Resident management view."""
    
    def __init__(self, parent, current_user: Dict, status_callback: Callable):
        super().__init__(parent, style="Main.TFrame")
        
        self.current_user = current_user
        self.status_callback = status_callback
        self.resident_ctrl = ResidentController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the resident management UI."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header with actions
        self._create_header()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky='nsew')
        
        # Create tabs
        self._create_residents_tab()
        self._create_households_tab()
        self._create_puroks_tab()
    
    def _create_header(self):
        """Create header with title and action buttons."""
        header = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        # Title
        title = tk.Label(
            header,
            text="Resident Information System",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = tk.Frame(header, bg=KalasagTheme.BG_MAIN)
        btn_frame.pack(side=tk.RIGHT)
        
        add_btn = tk.Button(
            btn_frame,
            text="➕ Add Resident",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            activebackground=KalasagTheme.PRIMARY_LIGHT,
            activeforeground=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._add_resident
        )
        add_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
    
    def _create_residents_tab(self):
        """Create residents list tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  👥 Residents  ")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Search bar
        search_frame = SearchFrame(
            tab,
            placeholder="Search residents by name, address...",
            on_search=self._search_residents
        )
        search_frame.grid(row=0, column=0, sticky='ew', pady=(KalasagTheme.PAD_MEDIUM, KalasagTheme.PAD_SMALL))
        
        # Data table
        columns = [
            ('resident_id', 'ID', 50),
            ('full_name', 'Full Name', 200),
            ('birthdate', 'Birthdate', 100),
            ('gender', 'Gender', 80),
            ('civil_status', 'Civil Status', 100),
            ('purok_name', 'Purok', 100),
            ('voter_status', 'Voter', 80),
        ]
        
        self.residents_table = DataTable(
            tab, columns,
            on_select=self._on_resident_select,
            on_double_click=self._edit_resident
        )
        self.residents_table.grid(row=1, column=0, sticky='nsew')
        
        # Context buttons
        ctx_frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        ctx_frame.grid(row=2, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        self.view_btn = tk.Button(
            ctx_frame,
            text="👁️ View",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.INFO_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._view_resident,
            state='disabled'
        )
        self.view_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.edit_btn = tk.Button(
            ctx_frame,
            text="✏️ Edit",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.WARNING_ORANGE,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._edit_resident,
            state='disabled'
        )
        self.edit_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.delete_btn = tk.Button(
            ctx_frame,
            text="🗑️ Delete",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.DANGER_RED,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._delete_resident,
            state='disabled'
        )
        self.delete_btn.pack(side=tk.LEFT)
    
    def _create_households_tab(self):
        """Create households list tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  🏠 Households  ")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header with add button
        header = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        add_hh_btn = tk.Button(
            header,
            text="➕ Add Household",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.SUCCESS_GREEN,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._add_household
        )
        add_hh_btn.pack(side=tk.RIGHT)
        
        # Data table
        columns = [
            ('household_id', 'ID', 50),
            ('household_head', 'Household Head', 200),
            ('address', 'Address', 250),
            ('purok_name', 'Purok', 100),
            ('member_count', 'Members', 80),
        ]
        
        self.households_table = DataTable(tab, columns)
        self.households_table.grid(row=1, column=0, sticky='nsew')
    
    def _create_puroks_tab(self):
        """Create puroks list tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  📍 Puroks  ")
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Header with add button
        header = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        add_purok_btn = tk.Button(
            header,
            text="➕ Add Purok",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.SUCCESS_GREEN,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_MEDIUM,
            pady=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._add_purok
        )
        add_purok_btn.pack(side=tk.RIGHT)
        
        # Data table
        columns = [
            ('purok_id', 'ID', 50),
            ('purok_name', 'Purok Name', 200),
            ('assigned_tanod_leader', 'Assigned Tanod Leader', 300),
        ]
        
        self.puroks_table = DataTable(tab, columns)
        self.puroks_table.grid(row=1, column=0, sticky='nsew')
    
    def refresh(self):
        """Refresh all data."""
        self._load_residents()
        self._load_households()
        self._load_puroks()
    
    def _load_residents(self):
        """Load residents into table."""
        try:
            residents = self.resident_ctrl.get_all_residents()
            
            # Format data
            data = []
            for r in residents:
                data.append({
                    'resident_id': r.get('res_id'),
                    'full_name': f"{r.get('first_name', '')} {r.get('middle_name', '')} {r.get('last_name', '')}".strip(),
                    'birthdate': r.get('birthdate', ''),
                    'gender': r.get('sex', ''),
                    'civil_status': r.get('civil_status', ''),
                    'purok_name': r.get('purok_name', 'N/A'),
                    'voter_status': 'Yes' if r.get('is_voter') else 'No',
                })
            
            self.residents_table.load_data(data)
            self.status_callback(f"Loaded {len(data)} residents", 'success')
        except Exception as e:
            self.status_callback(f"Error loading residents: {str(e)}", 'error')
    
    def _load_households(self):
        """Load households into table."""
        try:
            households = self.resident_ctrl.get_all_households()
            
            data = []
            for h in households:
                # Combine house_number and street_name into address
                house_num = h.get('house_number', '')
                street = h.get('street_name', '')
                address = f"{house_num} {street}".strip() if house_num or street else ''
                
                data.append({
                    'household_id': h.get('hh_id'),
                    'household_head': h.get('household_head', 'N/A'),
                    'address': address,
                    'purok_name': h.get('purok_name', 'N/A'),
                    'member_count': h.get('member_count', 0),
                })
            
            self.households_table.load_data(data)
        except Exception as e:
            self.status_callback(f"Error loading households: {str(e)}", 'error')
    
    def _load_puroks(self):
        """Load puroks into table."""
        try:
            puroks = self.resident_ctrl.get_all_puroks()
            self.puroks_table.load_data(puroks)
        except Exception as e:
            self.status_callback(f"Error loading puroks: {str(e)}", 'error')
    
    def _search_residents(self, query: str):
        """Search residents."""
        if not query:
            self._load_residents()
            return
        
        try:
            results = self.resident_ctrl.search_residents(query)
            
            data = []
            for r in results:
                data.append({
                    'resident_id': r.get('res_id'),
                    'full_name': f"{r.get('first_name', '')} {r.get('middle_name', '')} {r.get('last_name', '')}".strip(),
                    'birthdate': r.get('birthdate', ''),
                    'gender': r.get('sex', ''),
                    'civil_status': r.get('civil_status', ''),
                    'purok_name': r.get('purok_name', 'N/A'),
                    'voter_status': 'Yes' if r.get('is_voter') else 'No',
                })
            
            self.residents_table.load_data(data)
            self.status_callback(f"Found {len(data)} residents", 'info')
        except Exception as e:
            self.status_callback(f"Search error: {str(e)}", 'error')
    
    def _on_resident_select(self, item: Dict):
        """Handle resident selection."""
        state = 'normal' if item else 'disabled'
        self.view_btn.configure(state=state)
        self.edit_btn.configure(state=state)
        self.delete_btn.configure(state=state)
    
    def _add_resident(self):
        """Add new resident."""
        dialog = ResidentFormDialog(self, "Add Resident", self.resident_ctrl)
        if dialog.show():
            self._load_residents()
            self.status_callback("Resident added successfully", 'success')
    
    def _view_resident(self):
        """View selected resident."""
        selected = self.residents_table.get_selected()
        if selected:
            resident = self.resident_ctrl.get_resident(selected['resident_id'])
            if resident:
                ResidentDetailDialog(self, resident)
    
    def _edit_resident(self, event=None):
        """Edit selected resident."""
        selected = self.residents_table.get_selected()
        if selected:
            resident = self.resident_ctrl.get_resident(selected['resident_id'])
            if resident:
                dialog = ResidentFormDialog(self, "Edit Resident", self.resident_ctrl, resident)
                if dialog.show():
                    self._load_residents()
                    self.status_callback("Resident updated successfully", 'success')
    
    def _delete_resident(self):
        """Delete selected resident."""
        selected = self.residents_table.get_selected()
        if selected:
            dialog = ConfirmDialog(
                self,
                "Delete Resident",
                f"Are you sure you want to delete this resident?\nThis action cannot be undone.",
                confirm_text="Delete",
                confirm_style="Danger"
            )
            
            if dialog.show():
                success, msg = self.resident_ctrl.delete_resident(selected['resident_id'])
                if success:
                    self._load_residents()
                    self.status_callback("Resident deleted", 'success')
                else:
                    self.status_callback(f"Delete failed: {msg}", 'error')
    
    def _add_household(self):
        """Add new household."""
        dialog = HouseholdFormDialog(self, "Add Household", self.resident_ctrl)
        if dialog.show():
            self._load_households()
            self.status_callback("Household added successfully", 'success')
    
    def _add_purok(self):
        """Add new purok."""
        dialog = PurokFormDialog(self, "Add Purok", self.resident_ctrl)
        if dialog.show():
            self._load_puroks()
            self.status_callback("Purok added successfully", 'success')


class ResidentFormDialog(tk.Toplevel):
    """Dialog for adding/editing residents."""
    
    def __init__(self, parent, title: str, controller: ResidentController, resident: Dict = None):
        super().__init__(parent)
        
        self.controller = controller
        self.resident = resident
        self.result = False
        
        self.title(title)
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        self._build_form()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _build_form(self):
        """Build the form."""
        # Scrollable frame
        canvas = tk.Canvas(self, bg=KalasagTheme.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        form_frame = tk.Frame(canvas, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        
        form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Form fields
        self.entries = {}
        
        fields = [
            ('first_name', 'First Name *', 'entry'),
            ('middle_name', 'Middle Name', 'entry'),
            ('last_name', 'Last Name *', 'entry'),
            ('suffix', 'Suffix', 'entry'),
            ('birthdate', 'Birthdate (YYYY-MM-DD) *', 'entry'),
            ('gender', 'Gender *', 'combo', ['Male', 'Female']),
            ('civil_status', 'Civil Status *', 'combo', ['Single', 'Married', 'Widowed', 'Separated', 'Divorced']),
            ('contact_number', 'Contact Number', 'entry'),
            ('email', 'Email', 'entry'),
            ('occupation', 'Occupation', 'entry'),
            ('voter_status', 'Registered Voter', 'check'),
        ]
        
        for field_info in fields:
            field_name = field_info[0]
            label_text = field_info[1]
            field_type = field_info[2]
            
            lbl = tk.Label(
                form_frame,
                text=label_text,
                font=KalasagTheme.FONT_BODY,
                bg=KalasagTheme.BG_CARD,
                fg=KalasagTheme.TEXT_SECONDARY,
                anchor='w'
            )
            lbl.pack(fill=tk.X, pady=(KalasagTheme.PAD_SMALL, 0))
            
            if field_type == 'entry':
                entry = ttk.Entry(form_frame, font=KalasagTheme.FONT_BODY)
                entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_SMALL))
                self.entries[field_name] = entry
                
            elif field_type == 'combo':
                combo = ttk.Combobox(form_frame, values=field_info[3], state='readonly', font=KalasagTheme.FONT_BODY)
                combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_SMALL))
                self.entries[field_name] = combo
                
            elif field_type == 'check':
                var = tk.BooleanVar()
                check = ttk.Checkbutton(form_frame, variable=var)
                check.pack(anchor='w', pady=(2, KalasagTheme.PAD_SMALL))
                self.entries[field_name] = var
        
        # Household selection
        lbl = tk.Label(
            form_frame,
            text="Household",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_SECONDARY,
            anchor='w'
        )
        lbl.pack(fill=tk.X, pady=(KalasagTheme.PAD_SMALL, 0))
        
        households = self.controller.get_all_households()
        hh_values = ['None'] + [f"{h['hh_id']} - {h.get('house_number', '')} {h.get('street_name', '')}".strip() for h in households]
        
        self.household_combo = ttk.Combobox(form_frame, values=hh_values, state='readonly', font=KalasagTheme.FONT_BODY)
        self.household_combo.current(0)
        self.household_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_SMALL))
        
        # Populate if editing
        if self.resident:
            self._populate_form()
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY,
            bd=1,
            padx=KalasagTheme.PAD_LARGE,
            pady=KalasagTheme.PAD_SMALL,
            command=self.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        
        save_btn = tk.Button(
            btn_frame,
            text="Save",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_LARGE,
            pady=KalasagTheme.PAD_SMALL,
            command=self._save
        )
        save_btn.pack(side=tk.RIGHT)
    
    def _populate_form(self):
        """Populate form with existing data."""
        for field_name, widget in self.entries.items():
            # Map form field names to database column names
            db_field = field_name
            if field_name == 'gender':
                db_field = 'sex'
            
            value = self.resident.get(db_field, '')
            
            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            elif isinstance(widget, ttk.Combobox):
                if value:
                    widget.set(value)
            else:
                widget.insert(0, str(value) if value else '')
        
        # Set household
        hh_id = self.resident.get('hh_id')
        if hh_id:
            for i, val in enumerate(self.household_combo['values']):
                if val.startswith(str(hh_id)):
                    self.household_combo.current(i)
                    break
    
    def _save(self):
        """Save the resident."""
        data = {}
        
        for field_name, widget in self.entries.items():
            if isinstance(widget, tk.BooleanVar):
                data[field_name] = widget.get()
            elif isinstance(widget, ttk.Combobox):
                data[field_name] = widget.get()
            else:
                data[field_name] = widget.get().strip()
        
        # Map 'gender' to 'sex' for database compatibility
        if 'gender' in data:
            data['sex'] = data.pop('gender')
        
        # Map 'household_id' to 'hh_id' for database compatibility
        if 'household_id' in data:
            data['hh_id'] = data.pop('household_id')
        
        # Get household ID from combo
        hh_selection = self.household_combo.get()
        if hh_selection and hh_selection != 'None':
            data['hh_id'] = int(hh_selection.split(' - ')[0])
        else:
            data['hh_id'] = None
        
        # Validate required fields
        required = ['first_name', 'last_name', 'birthdate', 'sex', 'civil_status']
        for field in required:
            if not data.get(field):
                field_label = 'Gender' if field == 'sex' else field.replace('_', ' ').title()
                messagebox.showerror("Validation Error", f"{field_label} is required")
                return
        
        # Save
        if self.resident:
            success, msg = self.controller.update_resident(self.resident['res_id'], data)
        else:
            success, msg = self.controller.create_resident(data)
        
        if success:
            self.result = True
            self.destroy()
        else:
            error_msg = msg if isinstance(msg, str) else ', '.join(msg)
            messagebox.showerror("Error", error_msg)
    
    def show(self) -> bool:
        """Show dialog and return result."""
        self.wait_window()
        return self.result


class ResidentDetailDialog(tk.Toplevel):
    """Dialog to view resident details."""
    
    def __init__(self, parent, resident: Dict):
        super().__init__(parent)
        
        self.title("Resident Details")
        self.geometry("450x500")
        self.resizable(False, False)
        self.transient(parent)
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        # Content
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        full_name = f"{resident.get('first_name', '')} {resident.get('middle_name', '')} {resident.get('last_name', '')}".strip()
        
        name_label = tk.Label(
            frame,
            text=full_name,
            font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        name_label.pack(anchor='w')
        
        # Details
        details = [
            ('ID', resident.get('resident_id')),
            ('Birthdate', resident.get('birthdate')),
            ('Gender', resident.get('gender')),
            ('Civil Status', resident.get('civil_status')),
            ('Contact', resident.get('contact_number', 'N/A')),
            ('Email', resident.get('email', 'N/A')),
            ('Occupation', resident.get('occupation', 'N/A')),
            ('Voter', 'Yes' if resident.get('voter_status') else 'No'),
            ('Purok', resident.get('purok_name', 'N/A')),
            ('Household', resident.get('household_id', 'N/A')),
        ]
        
        for label, value in details:
            row = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
            row.pack(fill=tk.X, pady=KalasagTheme.PAD_SMALL)
            
            tk.Label(
                row,
                text=f"{label}:",
                font=KalasagTheme.FONT_BODY,
                bg=KalasagTheme.BG_CARD,
                fg=KalasagTheme.TEXT_SECONDARY,
                width=15,
                anchor='w'
            ).pack(side=tk.LEFT)
            
            tk.Label(
                row,
                text=str(value),
                font=KalasagTheme.FONT_BODY,
                bg=KalasagTheme.BG_CARD,
                fg=KalasagTheme.TEXT_PRIMARY,
                anchor='w'
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button
        close_btn = tk.Button(
            frame,
            text="Close",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_LARGE,
            pady=KalasagTheme.PAD_SMALL,
            command=self.destroy
        )
        close_btn.pack(pady=KalasagTheme.PAD_LARGE)
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class HouseholdFormDialog(tk.Toplevel):
    """Dialog for adding/editing households."""
    
    def __init__(self, parent, title: str, controller: ResidentController, household: Dict = None):
        super().__init__(parent)
        
        self.controller = controller
        self.household = household
        self.result = False
        
        self.title(title)
        self.geometry("400x300")
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
        
        # House Number
        tk.Label(frame, text="House Number *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.house_number_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.house_number_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Street Name
        tk.Label(frame, text="Street Name *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.street_name_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.street_name_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Purok
        tk.Label(frame, text="Purok *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        
        puroks = self.controller.get_all_puroks()
        purok_values = [f"{p['purok_id']} - {p.get('purok_name', p.get('name', ''))}" for p in puroks]
        
        self.purok_combo = ttk.Combobox(frame, values=purok_values, state='readonly', font=KalasagTheme.FONT_BODY)
        self.purok_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        if self.household:
            self.house_number_entry.insert(0, self.household.get('house_number', ''))
            self.street_name_entry.insert(0, self.household.get('street_name', ''))
            purok_id = self.household.get('purok_id')
            for i, val in enumerate(purok_values):
                if val.startswith(str(purok_id)):
                    self.purok_combo.current(i)
                    break
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Save", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._save).pack(side=tk.RIGHT)
    
    def _save(self):
        """Save household."""
        house_number = self.house_number_entry.get().strip()
        street_name = self.street_name_entry.get().strip()
        purok_selection = self.purok_combo.get()
        
        if not house_number:
            messagebox.showerror("Error", "House number is required")
            return
        
        if not street_name:
            messagebox.showerror("Error", "Street name is required")
            return
        
        if not purok_selection:
            messagebox.showerror("Error", "Purok is required")
            return
        
        purok_id = int(purok_selection.split(' - ')[0])
        
        if self.household:
            success, msg = self.controller.update_household(
                self.household.get('hh_id', self.household.get('household_id')), 
                house_number, street_name, purok_id
            )
        else:
            success, msg = self.controller.create_household(house_number, street_name, purok_id)
        
        if success:
            self.result = True
            self.destroy()
        else:
            error_msg = msg if isinstance(msg, str) else ', '.join(msg) if isinstance(msg, list) else str(msg)
            messagebox.showerror("Error", error_msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result


class PurokFormDialog(tk.Toplevel):
    """Dialog for adding/editing puroks."""
    
    def __init__(self, parent, title: str, controller: ResidentController, purok: Dict = None):
        super().__init__(parent)
        
        self.controller = controller
        self.purok = purok
        self.result = False
        
        self.title(title)
        self.geometry("400x250")
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
        
        # Name
        tk.Label(frame, text="Purok Name *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.name_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.name_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Tanod Leader
        tk.Label(frame, text="Assigned Tanod Leader", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.desc_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.desc_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        if self.purok:
            self.name_entry.insert(0, self.purok.get('purok_name', self.purok.get('name', '')))
            self.desc_entry.insert(0, self.purok.get('assigned_tanod_leader', ''))
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Save", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._save).pack(side=tk.RIGHT)
    
    def _save(self):
        """Save purok."""
        name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Purok name is required")
            return
        
        data = {'purok_name': name, 'assigned_tanod_leader': description}
        
        if self.purok:
            success, msg = self.controller.update_purok(self.purok['purok_id'], name, description)
        else:
            success, msg = self.controller.add_purok(data)
        
        if success:
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result
