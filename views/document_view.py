"""
KALASAG - Document View
Document Issuance management interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, Optional, List
from datetime import datetime

from views.theme import KalasagTheme
from views.components import SearchFrame, DataTable, CardWidget, ConfirmDialog
from controllers.document_controller import DocumentController
from controllers.resident_controller import ResidentController


class DocumentView(ttk.Frame):
    """Document issuance view."""
    
    def __init__(self, parent, current_user: Dict, status_callback: Callable):
        super().__init__(parent, style="Main.TFrame")
        
        self.current_user = current_user
        self.status_callback = status_callback
        self.doc_ctrl = DocumentController()
        self.resident_ctrl = ResidentController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the document management UI."""
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
            text="Document Issuance",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)
        
        # Issue buttons
        btn_frame = tk.Frame(header, bg=KalasagTheme.BG_MAIN)
        btn_frame.pack(side=tk.RIGHT)
        
        doc_types = [
            ("📜 Clearance", "Barangay Clearance"),
            ("📋 Indigency", "Certificate of Indigency"),
            ("🏠 Residency", "Certificate of Residency"),
            ("📝 Business", "Business Permit"),
        ]
        
        for text, doc_type in doc_types:
            btn = tk.Button(
                btn_frame,
                text=text,
                font=KalasagTheme.FONT_SMALL,
                bg=KalasagTheme.PRIMARY_BLUE,
                fg=KalasagTheme.TEXT_LIGHT,
                activebackground=KalasagTheme.PRIMARY_LIGHT,
                bd=0,
                padx=KalasagTheme.PAD_MEDIUM,
                pady=KalasagTheme.PAD_SMALL,
                cursor='hand2',
                command=lambda dt=doc_type: self._issue_document(dt)
            )
            btn.pack(side=tk.LEFT, padx=(KalasagTheme.PAD_SMALL, 0))
    
    def _create_content(self):
        """Create main content area."""
        content = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        content.grid(row=1, column=0, sticky='nsew')
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        
        # Filter bar
        filter_frame = tk.Frame(content, bg=KalasagTheme.BG_MAIN)
        filter_frame.grid(row=0, column=0, sticky='ew', pady=(0, KalasagTheme.PAD_SMALL))
        
        # Document type filter
        tk.Label(filter_frame, text="Type:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_MAIN).pack(side=tk.LEFT)
        
        self.type_filter = ttk.Combobox(
            filter_frame,
            values=['All', 'Barangay Clearance', 'Certificate of Indigency', 'Certificate of Residency', 'Business Permit'],
            state='readonly',
            width=20
        )
        self.type_filter.current(0)
        self.type_filter.pack(side=tk.LEFT, padx=KalasagTheme.PAD_SMALL)
        self.type_filter.bind('<<ComboboxSelected>>', lambda e: self._filter_documents())
        
        # Date range
        tk.Label(filter_frame, text="From:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_MAIN).pack(side=tk.LEFT, padx=(KalasagTheme.PAD_MEDIUM, 0))
        self.date_from = ttk.Entry(filter_frame, width=12)
        self.date_from.pack(side=tk.LEFT, padx=2)
        self.date_from.insert(0, datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        
        tk.Label(filter_frame, text="To:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_MAIN).pack(side=tk.LEFT, padx=(KalasagTheme.PAD_SMALL, 0))
        self.date_to = ttk.Entry(filter_frame, width=12)
        self.date_to.pack(side=tk.LEFT, padx=2)
        self.date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(
            filter_frame, text="🔍 Filter", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.INFO_BLUE, fg=KalasagTheme.TEXT_LIGHT, bd=0,
            command=self._filter_documents
        ).pack(side=tk.LEFT, padx=KalasagTheme.PAD_SMALL)
        
        # Search
        search_frame = SearchFrame(filter_frame, placeholder="Search by resident...", on_search=self._search_documents)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=KalasagTheme.PAD_MEDIUM)
        
        # Documents table
        columns = [
            ('log_id', 'ID', 50),
            ('document_type', 'Document Type', 180),
            ('resident_name', 'Resident', 200),
            ('issue_date', 'Issue Date', 120),
            ('purpose', 'Purpose', 200),
            ('or_number', 'OR #', 100),
        ]
        
        self.docs_table = DataTable(
            content, columns,
            on_select=self._on_doc_select,
            on_double_click=self._view_document
        )
        self.docs_table.grid(row=1, column=0, sticky='nsew')
        
        # Action buttons
        btn_frame = tk.Frame(content, bg=KalasagTheme.BG_MAIN)
        btn_frame.grid(row=2, column=0, sticky='ew', pady=KalasagTheme.PAD_SMALL)
        
        self.view_btn = tk.Button(
            btn_frame, text="👁️ View", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.INFO_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._view_document, state='disabled'
        )
        self.view_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        self.print_btn = tk.Button(
            btn_frame, text="🖨️ Print", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._print_document, state='disabled'
        )
        self.print_btn.pack(side=tk.LEFT, padx=(0, KalasagTheme.PAD_SMALL))
        
        # Export button
        tk.Button(
            btn_frame, text="📊 Export Report", font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            command=self._export_report
        ).pack(side=tk.RIGHT)
    
    def refresh(self):
        """Refresh document data."""
        self._load_documents()
    
    def _load_documents(self):
        """Load documents into table."""
        try:
            date_from = self.date_from.get().strip()
            date_to = self.date_to.get().strip()
            
            documents = self.doc_ctrl.get_documents_by_date_range(date_from, date_to)
            
            data = []
            for d in documents:
                # Get resident name
                resident_name = 'N/A'
                if d.get('res_id'):
                    resident = self.resident_ctrl.get_resident(d['res_id'])
                    if resident:
                        resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip()
                
                data.append({
                    'log_id': d.get('log_id'),
                    'document_type': d.get('document_type', ''),
                    'resident_name': resident_name,
                    'issue_date': d.get('issue_date', ''),
                    'purpose': d.get('purpose', ''),
                    'or_number': d.get('or_number', ''),
                })
            
            self.docs_table.load_data(data)
            self.status_callback(f"Loaded {len(data)} documents", 'success')
        except Exception as e:
            self.status_callback(f"Error loading documents: {str(e)}", 'error')
    
    def _filter_documents(self):
        """Filter documents."""
        doc_type = self.type_filter.get()
        date_from = self.date_from.get().strip()
        date_to = self.date_to.get().strip()
        
        try:
            if doc_type == 'All':
                documents = self.doc_ctrl.get_documents_by_date_range(date_from, date_to)
            else:
                documents = self.doc_ctrl.get_documents_by_type(doc_type)
                # Further filter by date
                documents = [d for d in documents if date_from <= d.get('issue_date', '') <= date_to]
            
            data = []
            for d in documents:
                resident_name = 'N/A'
                if d.get('res_id'):
                    resident = self.resident_ctrl.get_resident(d['res_id'])
                    if resident:
                        resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip()
                
                data.append({
                    'log_id': d.get('log_id'),
                    'document_type': d.get('document_type', ''),
                    'resident_name': resident_name,
                    'issue_date': d.get('issue_date', ''),
                    'purpose': d.get('purpose', ''),
                    'or_number': d.get('or_number', ''),
                })
            
            self.docs_table.load_data(data)
            self.status_callback(f"Found {len(data)} documents", 'info')
        except Exception as e:
            self.status_callback(f"Filter error: {str(e)}", 'error')
    
    def _search_documents(self, query: str):
        """Search documents by resident name."""
        if not query:
            self._load_documents()
            return
        
        try:
            # Search residents first
            residents = self.resident_ctrl.search_residents(query)
            resident_ids = [r['res_id'] for r in residents]
            
            # Get all documents and filter
            all_docs = self.doc_ctrl.get_all_documents()
            documents = [d for d in all_docs if d.get('res_id') in resident_ids]
            
            data = []
            for d in documents:
                resident_name = 'N/A'
                if d.get('res_id'):
                    resident = self.resident_ctrl.get_resident(d['res_id'])
                    if resident:
                        resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip()
                
                data.append({
                    'log_id': d.get('log_id'),
                    'document_type': d.get('document_type', ''),
                    'resident_name': resident_name,
                    'issue_date': d.get('issue_date', ''),
                    'purpose': d.get('purpose', ''),
                    'or_number': d.get('or_number', ''),
                })
            
            self.docs_table.load_data(data)
            self.status_callback(f"Found {len(data)} documents", 'info')
        except Exception as e:
            self.status_callback(f"Search error: {str(e)}", 'error')
    
    def _on_doc_select(self, item: Dict):
        """Handle document selection."""
        state = 'normal' if item else 'disabled'
        self.view_btn.configure(state=state)
        self.print_btn.configure(state=state)
    
    def _issue_document(self, doc_type: str):
        """Issue a new document."""
        dialog = IssueDocumentDialog(self, doc_type, self.doc_ctrl, self.resident_ctrl, self.current_user)
        if dialog.show():
            self._load_documents()
            self.status_callback(f"{doc_type} issued successfully", 'success')
    
    def _view_document(self, event=None):
        """View selected document."""
        selected = self.docs_table.get_selected()
        if selected:
            document = self.doc_ctrl.get_document(selected['log_id'])
            if document:
                DocumentDetailDialog(self, document, self.resident_ctrl)
    
    def _print_document(self):
        """Print/generate PDF for selected document."""
        selected = self.docs_table.get_selected()
        if selected:
            document = self.doc_ctrl.get_document(selected['log_id'])
            if document:
                try:
                    from utils.pdf_generator import PDFGenerator
                    
                    # Get resident info
                    resident = None
                    if document.get('res_id'):
                        resident = self.resident_ctrl.get_resident(document['res_id'])
                    
                    # Ask for save location
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".pdf",
                        filetypes=[("PDF files", "*.pdf")],
                        initialfilename=f"{document['document_type'].replace(' ', '_')}_{selected['log_id']}.pdf"
                    )
                    
                    if filename:
                        pdf_gen = PDFGenerator()
                        success = pdf_gen.generate_document(document['document_type'], resident, document, filename)
                        
                        if success:
                            self.status_callback(f"PDF saved to {filename}", 'success')
                            messagebox.showinfo("Success", f"Document saved to:\n{filename}")
                        else:
                            self.status_callback("Failed to generate PDF", 'error')
                except Exception as e:
                    self.status_callback(f"Print error: {str(e)}", 'error')
    
    def _export_report(self):
        """Export documents report."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfilename=f"documents_report_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                from database import export_to_csv
                export_to_csv('doc_log', filename)
                self.status_callback(f"Report exported to {filename}", 'success')
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
        except Exception as e:
            self.status_callback(f"Export error: {str(e)}", 'error')


class IssueDocumentDialog(tk.Toplevel):
    """Dialog for issuing documents."""
    
    def __init__(self, parent, doc_type: str, doc_ctrl: DocumentController, 
                 resident_ctrl: ResidentController, current_user: Dict):
        super().__init__(parent)
        
        self.doc_type = doc_type
        self.doc_ctrl = doc_ctrl
        self.resident_ctrl = resident_ctrl
        self.current_user = current_user
        self.result = False
        
        self.title(f"Issue {doc_type}")
        self.geometry("450x400")
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
        
        # Header
        tk.Label(
            frame,
            text=f"Issue {self.doc_type}",
            font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        # Resident selection
        tk.Label(frame, text="Resident *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        
        residents = self.resident_ctrl.get_all_residents()
        res_values = [f"{r['res_id']} - {r.get('first_name', '')} {r.get('last_name', '')}".strip() for r in residents]
        
        self.resident_combo = ttk.Combobox(frame, values=res_values, font=KalasagTheme.FONT_BODY)
        self.resident_combo.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Purpose
        tk.Label(frame, text="Purpose *", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.purpose_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.purpose_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # OR Number
        tk.Label(frame, text="OR Number", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.or_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.or_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Amount
        tk.Label(frame, text="Amount (₱)", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.amount_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.amount_entry.insert(0, "0.00")
        self.amount_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Remarks
        tk.Label(frame, text="Remarks", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY).pack(anchor='w')
        self.remarks_entry = ttk.Entry(frame, font=KalasagTheme.FONT_BODY)
        self.remarks_entry.pack(fill=tk.X, pady=(2, KalasagTheme.PAD_MEDIUM))
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
        btn_frame.pack(fill=tk.X, pady=KalasagTheme.PAD_LARGE)
        
        tk.Button(btn_frame, text="Cancel", font=KalasagTheme.FONT_BODY, command=self.destroy).pack(side=tk.RIGHT, padx=(KalasagTheme.PAD_SMALL, 0))
        tk.Button(btn_frame, text="Issue Document", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.SUCCESS_GREEN, fg=KalasagTheme.TEXT_LIGHT, bd=0, command=self._issue).pack(side=tk.RIGHT)
    
    def _issue(self):
        """Issue the document."""
        resident_sel = self.resident_combo.get()
        purpose = self.purpose_entry.get().strip()
        or_number = self.or_entry.get().strip()
        amount = self.amount_entry.get().strip()
        remarks = self.remarks_entry.get().strip()
        
        if not resident_sel:
            messagebox.showerror("Error", "Please select a resident")
            return
        
        if not purpose:
            messagebox.showerror("Error", "Purpose is required")
            return
        
        resident_id = int(resident_sel.split(' - ')[0])
        
        try:
            amount_val = float(amount) if amount else 0.0
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
            return
        
        data = {
            'res_id': resident_id,
            'document_type': self.doc_type,
            'purpose': purpose,
            'or_number': or_number or None,
            'amount': amount_val,
            'remarks': remarks or None,
            'issued_by': self.current_user.get('user_id'),
            'issue_date': datetime.now().strftime("%Y-%m-%d"),
        }
        
        success, msg = self.doc_ctrl.issue_document(data)
        
        if success:
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
    
    def show(self) -> bool:
        self.wait_window()
        return self.result


class DocumentDetailDialog(tk.Toplevel):
    """Dialog to view document details."""
    
    def __init__(self, parent, document: Dict, resident_ctrl: ResidentController):
        super().__init__(parent)
        
        self.title("Document Details")
        self.geometry("450x400")
        self.resizable(False, False)
        self.transient(parent)
        
        self.configure(bg=KalasagTheme.BG_CARD)
        
        # Get resident info
        resident = None
        resident_name = 'N/A'
        if document.get('res_id'):
            resident = resident_ctrl.get_resident(document['res_id'])
            if resident:
                resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip()
        
        # Content
        frame = tk.Frame(self, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(
            frame,
            text=document.get('document_type', 'Document'),
            font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w')
        
        tk.Label(
            frame,
            text=f"ID: {document.get('log_id')}",
            font=KalasagTheme.FONT_SMALL,
            bg=KalasagTheme.BG_CARD,
            fg=KalasagTheme.TEXT_MUTED
        ).pack(anchor='w', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        # Details
        details = [
            ('Resident', resident_name),
            ('Issue Date', document.get('issue_date', 'N/A')),
            ('Purpose', document.get('purpose', 'N/A')),
            ('OR Number', document.get('or_number', 'N/A')),
            ('Amount', f"₱{document.get('amount', 0):.2f}"),
            ('Remarks', document.get('remarks', 'N/A')),
        ]
        
        for label, value in details:
            row = tk.Frame(frame, bg=KalasagTheme.BG_CARD)
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{label}:", font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY, width=12, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=KalasagTheme.FONT_BODY, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY, anchor='w', wraplength=250).pack(side=tk.LEFT, fill=tk.X)
        
        # Close
        tk.Button(
            frame, text="Close", font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_SMALL,
            command=self.destroy
        ).pack(pady=KalasagTheme.PAD_LARGE)
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
