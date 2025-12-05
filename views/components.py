"""
KALASAG - Reusable UI Components
Custom Tkinter widgets for consistent UI across the application.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Dict, Any, Optional
from views.theme import KalasagTheme


class SearchableListbox(ttk.Frame):
    """A listbox with integrated search functionality."""
    
    def __init__(
        self,
        parent,
        items: List[str] = None,
        on_select: Callable = None,
        height: int = 10,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.items = items or []
        self.filtered_items = self.items.copy()
        self.on_select = on_select
        
        self._create_widgets(height)
        self._bind_events()
        
    def _create_widgets(self, height: int):
        """Create the search entry and listbox."""
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self,
            textvariable=self.search_var,
            width=30
        )
        self.search_entry.pack(fill=tk.X, pady=(0, KalasagTheme.PAD_SMALL))
        
        # Placeholder text
        self.search_entry.insert(0, "🔍 Search...")
        self.search_entry.bind("<FocusIn>", self._on_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_frame,
            height=height,
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY,
            selectbackground=KalasagTheme.PRIMARY_LIGHT,
            selectforeground=KalasagTheme.TEXT_LIGHT,
            yscrollcommand=self.scrollbar.set,
            exportselection=False
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)
        
        self._populate_listbox()
    
    def _bind_events(self):
        """Bind event handlers."""
        self.search_var.trace_add("write", self._on_search)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        self.listbox.bind("<Double-1>", self._on_double_click)
    
    def _on_focus_in(self, event):
        """Clear placeholder on focus."""
        if self.search_entry.get() == "🔍 Search...":
            self.search_entry.delete(0, tk.END)
    
    def _on_focus_out(self, event):
        """Restore placeholder if empty."""
        if not self.search_entry.get():
            self.search_entry.insert(0, "🔍 Search...")
    
    def _on_search(self, *args):
        """Filter items based on search text."""
        search_text = self.search_var.get().lower()
        if search_text == "🔍 search...":
            search_text = ""
        
        if search_text:
            self.filtered_items = [
                item for item in self.items
                if search_text in item.lower()
            ]
        else:
            self.filtered_items = self.items.copy()
        
        self._populate_listbox()
    
    def _populate_listbox(self):
        """Update listbox with filtered items."""
        self.listbox.delete(0, tk.END)
        for item in self.filtered_items:
            self.listbox.insert(tk.END, item)
    
    def _on_listbox_select(self, event):
        """Handle item selection."""
        if self.on_select:
            selection = self.listbox.curselection()
            if selection:
                index = selection[0]
                item = self.filtered_items[index]
                self.on_select(item, index)
    
    def _on_double_click(self, event):
        """Handle double-click."""
        self._on_listbox_select(event)
    
    def set_items(self, items: List[str]):
        """Set new items list."""
        self.items = items
        self.filtered_items = items.copy()
        self._populate_listbox()
    
    def get_selected(self) -> Optional[str]:
        """Get currently selected item."""
        selection = self.listbox.curselection()
        if selection:
            return self.filtered_items[selection[0]]
        return None
    
    def clear_selection(self):
        """Clear the selection."""
        self.listbox.selection_clear(0, tk.END)


class DataTable(ttk.Frame):
    """A customizable data table using Treeview."""
    
    def __init__(
        self,
        parent,
        columns: List[Dict[str, Any]],
        on_select: Callable = None,
        on_double_click: Callable = None,
        show_scrollbar: bool = True,
        height: int = 15,
        **kwargs
    ):
        """
        Initialize DataTable.
        
        Args:
            columns: List of dicts with 'key', 'header', 'width', 'anchor'
            on_select: Callback when row selected
            on_double_click: Callback when row double-clicked
        """
        super().__init__(parent, **kwargs)
        
        # Convert tuple columns to dict format if needed
        self.columns = self._normalize_columns(columns)
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.data = []
        
        self._create_widgets(show_scrollbar, height)
        self._bind_events()
    
    def _normalize_columns(self, columns):
        """Convert columns to dict format if they are tuples."""
        normalized = []
        for col in columns:
            if isinstance(col, dict):
                normalized.append(col)
            elif isinstance(col, (list, tuple)):
                # Assume format: (key, header, width) or (key, header)
                col_dict = {'key': col[0]}
                if len(col) > 1:
                    col_dict['header'] = col[1]
                if len(col) > 2:
                    col_dict['width'] = col[2]
                if len(col) > 3:
                    col_dict['anchor'] = col[3]
                normalized.append(col_dict)
            else:
                # Assume it's just a key string
                normalized.append({'key': col, 'header': col})
        return normalized
    
    def _create_widgets(self, show_scrollbar: bool, height: int):
        """Create treeview and scrollbars."""
        # Create container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Column keys
        col_keys = [col['key'] for col in self.columns]
        
        # Create Treeview
        self.tree = ttk.Treeview(
            container,
            columns=col_keys,
            show='headings',
            height=height,
            selectmode='browse'
        )
        
        # Configure columns
        for col in self.columns:
            self.tree.heading(
                col['key'],
                text=col.get('header', col['key']),
                anchor=col.get('anchor', 'w')
            )
            self.tree.column(
                col['key'],
                width=col.get('width', 100),
                minwidth=col.get('minwidth', 50),
                anchor=col.get('anchor', 'w')
            )
        
        # Scrollbars
        if show_scrollbar:
            y_scroll = ttk.Scrollbar(
                container,
                orient=tk.VERTICAL,
                command=self.tree.yview
            )
            x_scroll = ttk.Scrollbar(
                container,
                orient=tk.HORIZONTAL,
                command=self.tree.xview
            )
            
            self.tree.configure(
                yscrollcommand=y_scroll.set,
                xscrollcommand=x_scroll.set
            )
            
            # Grid layout
            self.tree.grid(row=0, column=0, sticky='nsew')
            y_scroll.grid(row=0, column=1, sticky='ns')
            x_scroll.grid(row=1, column=0, sticky='ew')
            
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)
        else:
            self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Alternating row colors
        self.tree.tag_configure('oddrow', background='#f8f9fa')
        self.tree.tag_configure('evenrow', background=KalasagTheme.BG_CARD)
        
        # Status row tags
        self.tree.tag_configure('pending', foreground=KalasagTheme.WARNING_YELLOW)
        self.tree.tag_configure('resolved', foreground=KalasagTheme.SUCCESS_GREEN)
        self.tree.tag_configure('danger', foreground=KalasagTheme.DANGER_RED)
    
    def _bind_events(self):
        """Bind event handlers."""
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<Double-1>', self._on_tree_double_click)
    
    def _on_tree_select(self, event):
        """Handle row selection."""
        if self.on_select:
            selected = self.get_selected()
            if selected:
                self.on_select(selected)
    
    def _on_tree_double_click(self, event):
        """Handle double-click."""
        if self.on_double_click:
            selected = self.get_selected()
            if selected:
                self.on_double_click(selected)
    
    def set_data(self, data: List[Dict[str, Any]], id_key: str = 'id'):
        """
        Populate table with data.
        
        Args:
            data: List of dicts containing row data
            id_key: Key to use as row identifier
        """
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.data = data
        
        # Insert rows
        for i, row in enumerate(data):
            values = [row.get(col['key'], '') for col in self.columns]
            row_id = str(row.get(id_key, i))
            
            # Determine tag
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            # Add status tag if present
            status = str(row.get('status', '')).lower()
            if 'pending' in status:
                tag = 'pending'
            elif status in ('resolved', 'closed', 'settled'):
                tag = 'resolved'
            
            self.tree.insert('', tk.END, iid=row_id, values=values, tags=(tag,))
    
    def get_selected(self) -> Optional[Dict[str, Any]]:
        """Get the selected row data."""
        selected = self.tree.selection()
        if selected:
            item_id = selected[0]
            # Find matching data by checking various id keys
            for row in self.data:
                for key in ['id', 'resident_id', 'case_id', 'log_id', 'user_id', 'household_id', 'purok_id', 'type_id']:
                    if str(row.get(key, '')) == item_id:
                        return row
            # Fallback: return values as dict
            values = self.tree.item(item_id)['values']
            return dict(zip([col['key'] for col in self.columns], values))
        return None
    
    def clear_selection(self):
        """Clear selection."""
        for item in self.tree.selection():
            self.tree.selection_remove(item)
    
    def refresh(self):
        """Refresh the table display."""
        if self.data:
            self.set_data(self.data)
    
    def load_data(self, data: List[Dict[str, Any]]):
        """Alias for set_data - load data into table."""
        # Detect id key
        if data and len(data) > 0:
            first = data[0]
            id_key = 'id'
            for key in ['id', 'resident_id', 'case_id', 'log_id', 'user_id', 'household_id', 'purok_id']:
                if key in first:
                    id_key = key
                    break
            self.set_data(data, id_key)
        else:
            self.set_data([], 'id')


class SearchFrame(ttk.Frame):
    """A search bar component with search button and clear functionality."""
    
    def __init__(
        self,
        parent,
        placeholder: str = "Search...",
        on_search: Callable = None,
        width: int = 30,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.placeholder = placeholder
        self.on_search = on_search
        
        self._create_widgets(width)
    
    def _create_widgets(self, width: int):
        """Create search widgets."""
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self,
            textvariable=self.search_var,
            width=width,
            font=KalasagTheme.FONT_BODY
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add placeholder
        self.search_entry.insert(0, self.placeholder)
        self.search_entry.configure(foreground='gray')
        
        # Bind events
        self.search_entry.bind('<FocusIn>', self._on_focus_in)
        self.search_entry.bind('<FocusOut>', self._on_focus_out)
        self.search_entry.bind('<Return>', self._on_search)
        
        # Search button
        self.search_btn = tk.Button(
            self,
            text="🔍",
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE,
            fg=KalasagTheme.TEXT_LIGHT,
            bd=0,
            padx=KalasagTheme.PAD_SMALL,
            cursor='hand2',
            command=self._on_search
        )
        self.search_btn.pack(side=tk.LEFT, padx=(KalasagTheme.PAD_SMALL, 0))
        
        # Clear button
        self.clear_btn = tk.Button(
            self,
            text="✕",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_SECONDARY,
            bd=0,
            cursor='hand2',
            command=self._on_clear
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(2, 0))
    
    def _on_focus_in(self, event):
        """Clear placeholder on focus."""
        if self.search_entry.get() == self.placeholder:
            self.search_entry.delete(0, tk.END)
            self.search_entry.configure(foreground=KalasagTheme.TEXT_PRIMARY)
    
    def _on_focus_out(self, event):
        """Restore placeholder if empty."""
        if not self.search_entry.get():
            self.search_entry.insert(0, self.placeholder)
            self.search_entry.configure(foreground='gray')
    
    def _on_search(self, event=None):
        """Trigger search callback."""
        query = self.search_var.get()
        if query == self.placeholder:
            query = ""
        if self.on_search:
            self.on_search(query)
    
    def _on_clear(self):
        """Clear the search."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, self.placeholder)
        self.search_entry.configure(foreground='gray')
        if self.on_search:
            self.on_search("")
    
    def get_query(self) -> str:
        """Get current search query."""
        query = self.search_var.get()
        return "" if query == self.placeholder else query


class CardWidget(tk.Frame):
    """A titled card container widget."""
    
    def __init__(self, parent, title: str = None, **kwargs):
        super().__init__(parent, bg=KalasagTheme.BG_CARD, **kwargs)
        
        self.configure(
            highlightbackground=KalasagTheme.BORDER_LIGHT,
            highlightthickness=1
        )
        
        # Title bar
        if title:
            title_frame = tk.Frame(self, bg=KalasagTheme.BG_CARD)
            title_frame.pack(fill=tk.X, padx=KalasagTheme.PAD_MEDIUM, pady=(KalasagTheme.PAD_MEDIUM, 0))
            
            tk.Label(
                title_frame,
                text=title,
                font=KalasagTheme.FONT_H3,
                bg=KalasagTheme.BG_CARD,
                fg=KalasagTheme.TEXT_PRIMARY
            ).pack(side=tk.LEFT)
        
        # Content frame
        self.content_frame = tk.Frame(self, bg=KalasagTheme.BG_CARD)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_MEDIUM)


class DashboardCard(tk.Frame):
    """A dashboard statistics card with icon, title, and value."""
    
    def __init__(
        self,
        parent,
        icon: str,
        title: str,
        value: str,
        color: str = None,
        **kwargs
    ):
        super().__init__(parent, bg=KalasagTheme.BG_CARD, **kwargs)
        
        self.configure(
            highlightbackground=KalasagTheme.BORDER_LIGHT,
            highlightthickness=1
        )
        
        # Padding frame
        inner = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_MEDIUM)
        inner.pack(fill=tk.BOTH, expand=True)
        
        # Icon
        icon_color = color or KalasagTheme.PRIMARY_BLUE
        tk.Label(
            inner,
            text=icon,
            font=("Segoe UI", 24),
            bg=KalasagTheme.BG_CARD,
            fg=icon_color
        ).pack(anchor='w')
        
        # Value
        self.value_label = tk.Label(
            inner,
            text=value,
            font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        self.value_label.pack(anchor='w')
        
        # Title
        tk.Label(
            inner,
            text=title,
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_SECONDARY
        ).pack(anchor='w')
    
    def update_value(self, value: str):
        """Update the displayed value."""
        self.value_label.configure(text=value)


class StatusBadge(tk.Label):
    """A colored status badge label."""
    
    STATUS_COLORS = {
        'active': KalasagTheme.SUCCESS_GREEN,
        'inactive': KalasagTheme.TEXT_MUTED,
        'pending': KalasagTheme.WARNING_YELLOW,
        'resolved': KalasagTheme.SUCCESS_GREEN,
        'filed': KalasagTheme.INFO_BLUE,
        'under investigation': KalasagTheme.WARNING_ORANGE,
        'scheduled': KalasagTheme.PRIMARY_BLUE,
        'dismissed': KalasagTheme.TEXT_MUTED,
        'high': KalasagTheme.DANGER_RED,
        'critical': KalasagTheme.DANGER_RED,
        'normal': KalasagTheme.INFO_BLUE,
        'low': KalasagTheme.SUCCESS_GREEN,
    }
    
    def __init__(self, parent, status: str, **kwargs):
        color = self.STATUS_COLORS.get(status.lower(), KalasagTheme.TEXT_MUTED)
        
        super().__init__(
            parent,
            text=status,
            font=KalasagTheme.FONT_SMALL,
            bg=color,
            fg=KalasagTheme.TEXT_LIGHT,
            padx=8,
            pady=2,
            **kwargs
        )
    
    def set_status(self, status: str):
        """Update the status."""
        color = self.STATUS_COLORS.get(status.lower(), KalasagTheme.TEXT_MUTED)
        self.configure(text=status, bg=color)


class FormField(ttk.Frame):
    """A labeled form field with validation support."""
    
    def __init__(
        self,
        parent,
        label: str,
        field_type: str = 'entry',
        required: bool = False,
        options: List[str] = None,
        width: int = 30,
        **kwargs
    ):
        """
        Initialize FormField.
        
        Args:
            label: Field label text
            field_type: 'entry', 'combobox', 'text', 'date'
            required: Whether field is required
            options: Options for combobox
            width: Field width
        """
        super().__init__(parent, **kwargs)
        
        self.label_text = label
        self.required = required
        self.field_type = field_type
        
        self._create_widgets(field_type, options, width)
    
    def _create_widgets(self, field_type: str, options: List[str], width: int):
        """Create label and input widgets."""
        # Label
        label_text = self.label_text
        if self.required:
            label_text += " *"
        
        self.label = ttk.Label(
            self,
            text=label_text,
            font=KalasagTheme.FONT_BODY
        )
        self.label.pack(anchor='w')
        
        # Input field
        self.var = tk.StringVar()
        
        if field_type == 'combobox':
            self.input = ttk.Combobox(
                self,
                textvariable=self.var,
                values=options or [],
                width=width,
                state='readonly'
            )
        elif field_type == 'text':
            self.input = tk.Text(
                self,
                width=width,
                height=4,
                font=KalasagTheme.FONT_BODY,
                wrap=tk.WORD
            )
        else:  # entry
            self.input = ttk.Entry(
                self,
                textvariable=self.var,
                width=width
            )
        
        self.input.pack(fill=tk.X, pady=(2, 0))
        
        # Error label (hidden by default)
        self.error_label = ttk.Label(
            self,
            text="",
            foreground=KalasagTheme.DANGER_RED,
            font=KalasagTheme.FONT_SMALL
        )
    
    def get(self) -> str:
        """Get field value."""
        if self.field_type == 'text':
            return self.input.get("1.0", tk.END).strip()
        return self.var.get()
    
    def set(self, value: str):
        """Set field value."""
        if self.field_type == 'text':
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", value)
        else:
            self.var.set(value)
    
    def clear(self):
        """Clear field."""
        if self.field_type == 'text':
            self.input.delete("1.0", tk.END)
        else:
            self.var.set("")
    
    def show_error(self, message: str):
        """Show error message."""
        self.error_label.config(text=message)
        self.error_label.pack(anchor='w')
        if hasattr(self.input, 'configure'):
            # Highlight input border (Entry/Combobox)
            pass
    
    def clear_error(self):
        """Clear error message."""
        self.error_label.config(text="")
        self.error_label.pack_forget()
    
    def validate(self) -> bool:
        """Validate field. Returns True if valid."""
        self.clear_error()
        value = self.get()
        
        if self.required and not value:
            self.show_error(f"{self.label_text} is required")
            return False
        
        return True
    
    def set_options(self, options: List[str]):
        """Update combobox options."""
        if self.field_type == 'combobox':
            self.input['values'] = options
    
    def set_state(self, state: str):
        """Set field state ('normal', 'disabled', 'readonly')."""
        if hasattr(self.input, 'configure'):
            if self.field_type == 'text':
                self.input.configure(state=state)
            else:
                self.input.configure(state=state)


class ActionButton(ttk.Button):
    """A styled action button with icon support."""
    
    def __init__(
        self,
        parent,
        text: str,
        command: Callable = None,
        style: str = 'Primary',
        icon: str = None,
        width: int = None,
        **kwargs
    ):
        """
        Initialize ActionButton.
        
        Args:
            text: Button text
            command: Click handler
            style: 'Primary', 'Success', 'Danger', 'Default'
            icon: Unicode icon character
        """
        if icon:
            text = f"{icon} {text}"
        
        style_name = f"{style}.TButton" if style != 'Default' else "TButton"
        
        super().__init__(
            parent,
            text=text,
            command=command,
            style=style_name,
            width=width,
            **kwargs
        )


class StatusBar(ttk.Frame):
    """Application status bar with messages and progress."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(style="Card.TFrame")
        
        # Message label
        self.message_var = tk.StringVar(value="Ready")
        self.message_label = ttk.Label(
            self,
            textvariable=self.message_var,
            style="Card.TLabel"
        )
        self.message_label.pack(side=tk.LEFT, padx=KalasagTheme.PAD_MEDIUM)
        
        # Progress bar (hidden by default)
        self.progress = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=150
        )
        
        # User info (right side)
        self.user_var = tk.StringVar(value="")
        self.user_label = ttk.Label(
            self,
            textvariable=self.user_var,
            style="Card.TLabel"
        )
        self.user_label.pack(side=tk.RIGHT, padx=KalasagTheme.PAD_MEDIUM)
        
        # Timestamp
        self.time_var = tk.StringVar()
        self.time_label = ttk.Label(
            self,
            textvariable=self.time_var,
            style="Card.TLabel"
        )
        self.time_label.pack(side=tk.RIGHT, padx=KalasagTheme.PAD_MEDIUM)
        
        self._update_time()
    
    def _update_time(self):
        """Update the time display."""
        from datetime import datetime
        self.time_var.set(datetime.now().strftime("%I:%M %p"))
        self.after(60000, self._update_time)  # Update every minute
    
    def set_message(self, message: str, message_type: str = 'info'):
        """Set status message."""
        self.message_var.set(message)
        
        # Update color based on type
        if message_type == 'success':
            self.message_label.configure(foreground=KalasagTheme.SUCCESS_GREEN)
        elif message_type == 'error':
            self.message_label.configure(foreground=KalasagTheme.DANGER_RED)
        elif message_type == 'warning':
            self.message_label.configure(foreground=KalasagTheme.WARNING_YELLOW)
        else:
            self.message_label.configure(foreground=KalasagTheme.TEXT_PRIMARY)
    
    def set_user(self, username: str, role: str = None):
        """Set logged-in user info."""
        if role:
            self.user_var.set(f"👤 {username} ({role})")
        else:
            self.user_var.set(f"👤 {username}")
    
    def show_progress(self):
        """Show loading indicator."""
        self.progress.pack(side=tk.LEFT, padx=KalasagTheme.PAD_MEDIUM)
        self.progress.start()
    
    def hide_progress(self):
        """Hide loading indicator."""
        self.progress.stop()
        self.progress.pack_forget()


class LoadingIndicator(tk.Toplevel):
    """Modal loading indicator overlay."""
    
    def __init__(self, parent, message: str = "Loading..."):
        super().__init__(parent)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 100
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 40
        self.geometry(f"200x80+{x}+{y}")
        
        # Style
        self.configure(bg=KalasagTheme.BG_CARD)
        
        # Content
        frame = ttk.Frame(self, style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.message_label = ttk.Label(
            frame,
            text=message,
            style="Card.TLabel"
        )
        self.message_label.pack(pady=(KalasagTheme.PAD_MEDIUM, KalasagTheme.PAD_SMALL))
        
        self.progress = ttk.Progressbar(
            frame,
            mode='indeterminate',
            length=150
        )
        self.progress.pack(pady=KalasagTheme.PAD_SMALL)
        self.progress.start()
    
    def set_message(self, message: str):
        """Update the loading message."""
        self.message_label.configure(text=message)
    
    def close(self):
        """Close the loading indicator."""
        self.progress.stop()
        self.grab_release()
        self.destroy()


class ConfirmDialog(tk.Toplevel):
    """Confirmation dialog."""
    
    def __init__(
        self,
        parent,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_style: str = "Primary"
    ):
        super().__init__(parent)
        
        self.result = False
        
        self.title(title)
        self.transient(parent)
        self.grab_set()
        
        # Size and center
        self.geometry("350x150")
        self.resizable(False, False)
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 175
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 75
        self.geometry(f"+{x}+{y}")
        
        # Content
        frame = ttk.Frame(self, style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        
        # Message
        ttk.Label(
            frame,
            text=message,
            style="Card.TLabel",
            wraplength=300
        ).pack(pady=KalasagTheme.PAD_MEDIUM)
        
        # Buttons
        btn_frame = ttk.Frame(frame, style="Card.TFrame")
        btn_frame.pack(pady=KalasagTheme.PAD_MEDIUM)
        
        ActionButton(
            btn_frame,
            text=cancel_text,
            command=self._on_cancel,
            style="Default",
            width=12
        ).pack(side=tk.LEFT, padx=KalasagTheme.PAD_SMALL)
        
        ActionButton(
            btn_frame,
            text=confirm_text,
            command=self._on_confirm,
            style=confirm_style,
            width=12
        ).pack(side=tk.LEFT, padx=KalasagTheme.PAD_SMALL)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Focus
        self.focus_set()
    
    def _on_confirm(self):
        """Handle confirm action."""
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel action."""
        self.result = False
        self.destroy()
    
    def show(self) -> bool:
        """Show dialog and return result."""
        self.wait_window()
        return self.result


class StatusBar(tk.Frame):
    """Application status bar."""
    
    def __init__(self, parent):
        super().__init__(parent, bg=KalasagTheme.BG_SIDEBAR, height=30)
        
        self.pack_propagate(False)
        
        # Left: Status message
        self.status_label = tk.Label(
            self,
            text="Ready",
            font=KalasagTheme.FONT_SMALL,
            fg=KalasagTheme.TEXT_LIGHT,
            bg=KalasagTheme.BG_SIDEBAR,
            anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=KalasagTheme.PAD_MEDIUM)
        
        # Right: User info
        self.user_label = tk.Label(
            self,
            text="",
            font=KalasagTheme.FONT_SMALL,
            fg=KalasagTheme.TEXT_MUTED,
            bg=KalasagTheme.BG_SIDEBAR,
            anchor='e'
        )
        self.user_label.pack(side=tk.RIGHT, padx=KalasagTheme.PAD_MEDIUM)
    
    def set_message(self, message: str, msg_type: str = 'info'):
        """Set status message with optional type (info, success, error, warning)."""
        colors = {
            'info': KalasagTheme.TEXT_LIGHT,
            'success': KalasagTheme.SUCCESS_GREEN,
            'error': KalasagTheme.DANGER_RED,
            'warning': KalasagTheme.WARNING_ORANGE,
        }
        
        self.status_label.configure(text=message, fg=colors.get(msg_type, KalasagTheme.TEXT_LIGHT))
        
        # Reset to default after 5 seconds
        self.after(5000, lambda: self.status_label.configure(text="Ready", fg=KalasagTheme.TEXT_LIGHT))
    
    def set_user(self, username: str, role: str):
        """Set logged-in user information."""
        self.user_label.configure(text=f"👤 {username} ({role})")


class FormDialog(tk.Toplevel):
    """Base class for form dialogs."""
    
    def __init__(self, parent, title: str, width: int = 400, height: int = 300):
        super().__init__(parent)
        
        self.result = None
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")
    
    def show(self):
        """Show dialog and return result."""
        self.wait_window()
        return self.result

