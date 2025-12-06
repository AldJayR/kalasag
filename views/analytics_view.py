"""
KALASAG - Analytics View
Intelligence & Analytics dashboard interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, Optional, List
from datetime import datetime, timedelta

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from views.theme import KalasagTheme
from views.components import CardWidget, DashboardCard
from controllers.analytics_controller import AnalyticsController


class AnalyticsView(ttk.Frame):
    """Analytics and reporting view."""
    
    def __init__(self, parent, current_user: Dict, status_callback: Callable):
        super().__init__(parent, style="Main.TFrame")
        
        self.current_user = current_user
        self.status_callback = status_callback
        self.analytics_ctrl = AnalyticsController()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the analytics UI."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Notebook for different analytics
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky='nsew')
        
        # Create tabs
        self._create_overview_tab()
        self._create_crime_tab()
        self._create_demographics_tab()
        self._create_reports_tab()
    
    def _create_header(self):
        """Create header."""
        header = tk.Frame(self, bg=KalasagTheme.BG_MAIN)
        header.grid(row=0, column=0, sticky='ew', pady=(0, KalasagTheme.PAD_MEDIUM))
        
        title = tk.Label(
            header,
            text="Intelligence & Analytics",
            font=KalasagTheme.FONT_H1,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)
        
        # Refresh button
        tk.Button(
            header, text="🔄 Refresh", font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
            bd=0, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_SMALL,
            cursor='hand2', command=self.refresh
        ).pack(side=tk.RIGHT)
    
    def _create_overview_tab(self):
        """Create overview statistics tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  📊 Overview  ")
        
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Stats cards row
        cards_frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN)
        cards_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=KalasagTheme.PAD_MEDIUM)
        
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1, uniform='stats')
        
        self.total_residents_card = DashboardCard(cards_frame, "👥", "Total Residents", "0", KalasagTheme.PRIMARY_BLUE)
        self.total_residents_card.grid(row=0, column=0, sticky='ew', padx=(0, KalasagTheme.PAD_SMALL))
        
        self.total_cases_card = DashboardCard(cards_frame, "📋", "Total Cases", "0", KalasagTheme.WARNING_ORANGE)
        self.total_cases_card.grid(row=0, column=1, sticky='ew', padx=KalasagTheme.PAD_SMALL)
        
        self.resolved_cases_card = DashboardCard(cards_frame, "✅", "Resolved Cases", "0", KalasagTheme.SUCCESS_GREEN)
        self.resolved_cases_card.grid(row=0, column=2, sticky='ew', padx=KalasagTheme.PAD_SMALL)
        
        self.documents_card = DashboardCard(cards_frame, "📄", "Documents Issued", "0", KalasagTheme.INFO_BLUE)
        self.documents_card.grid(row=0, column=3, sticky='ew', padx=(KalasagTheme.PAD_SMALL, 0))
        
        # Left: Population summary
        pop_card = CardWidget(tab, "Population Summary")
        pop_card.grid(row=1, column=0, sticky='nsew', padx=(0, KalasagTheme.PAD_SMALL), pady=KalasagTheme.PAD_SMALL)
        
        self.pop_list = tk.Listbox(
            pop_card.content_frame,
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            bd=0,
            highlightthickness=0
        )
        self.pop_list.pack(fill=tk.BOTH, expand=True)
        
        # Right: Recent activity
        activity_card = CardWidget(tab, "Recent Cases")
        activity_card.grid(row=1, column=1, sticky='nsew', padx=(KalasagTheme.PAD_SMALL, 0), pady=KalasagTheme.PAD_SMALL)
        
        self.recent_cases_list = tk.Listbox(
            activity_card.content_frame,
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            bd=0,
            highlightthickness=0
        )
        self.recent_cases_list.pack(fill=tk.BOTH, expand=True)
    
    def _create_crime_tab(self):
        """Create crime analytics tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  🚨 Crime Analytics  ")
        
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # Incident Types (Top Left)
        types_card = CardWidget(tab, "Incidents by Type")
        types_card.grid(row=0, column=0, sticky='nsew', padx=(0, KalasagTheme.PAD_SMALL), pady=KalasagTheme.PAD_SMALL)
        
        self.incident_types_list = tk.Listbox(
            types_card.content_frame,
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            bd=0,
            highlightthickness=0
        )
        self.incident_types_list.pack(fill=tk.BOTH, expand=True)
        
        # Crime Heatmap (Top Right)
        self.heatmap_card = CardWidget(tab, "Crime Heatmap (by Purok)")
        self.heatmap_card.grid(row=0, column=1, sticky='nsew', padx=(KalasagTheme.PAD_SMALL, 0), pady=KalasagTheme.PAD_SMALL)
        
        # Container for heatmap chart
        self.heatmap_frame = tk.Frame(self.heatmap_card.content_frame, bg=KalasagTheme.BG_CARD)
        self.heatmap_frame.pack(fill=tk.BOTH, expand=True)
        
        # Monthly Trend (Bottom Left)
        trend_card = CardWidget(tab, "Monthly Trend")
        trend_card.grid(row=1, column=0, sticky='nsew', padx=(0, KalasagTheme.PAD_SMALL), pady=KalasagTheme.PAD_SMALL)
        
        self.trend_list = tk.Listbox(
            trend_card.content_frame,
            font=KalasagTheme.FONT_BODY,
            bg=KalasagTheme.BG_CARD,
            bd=0,
            highlightthickness=0
        )
        self.trend_list.pack(fill=tk.BOTH, expand=True)

        # Time Analysis (Bottom Right)
        self.time_card = CardWidget(tab, "Time Analysis")
        self.time_card.grid(row=1, column=1, sticky='nsew', padx=(KalasagTheme.PAD_SMALL, 0), pady=KalasagTheme.PAD_SMALL)
        
        # Container for time chart
        self.time_frame = tk.Frame(self.time_card.content_frame, bg=KalasagTheme.BG_CARD)
        self.time_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_demographics_tab(self):
        """Create demographics tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  📈 Demographics  ")
        
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
        # By Gender (Top Left)
        gender_card = CardWidget(tab, "Population by Gender")
        gender_card.grid(row=0, column=0, sticky='nsew', padx=(0, KalasagTheme.PAD_SMALL), pady=KalasagTheme.PAD_SMALL)
        
        self.gender_frame = tk.Frame(gender_card.content_frame, bg=KalasagTheme.BG_CARD)
        self.gender_frame.pack(fill=tk.BOTH, expand=True)
        
        # By Civil Status (Top Right)
        civil_card = CardWidget(tab, "Population by Civil Status")
        civil_card.grid(row=0, column=1, sticky='nsew', padx=(KalasagTheme.PAD_SMALL, 0), pady=KalasagTheme.PAD_SMALL)
        
        self.civil_frame = tk.Frame(civil_card.content_frame, bg=KalasagTheme.BG_CARD)
        self.civil_frame.pack(fill=tk.BOTH, expand=True)
        
        # By Purok (Bottom Full Width)
        purok_card = CardWidget(tab, "Population by Purok")
        purok_card.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=KalasagTheme.PAD_SMALL)
        
        self.purok_frame = tk.Frame(purok_card.content_frame, bg=KalasagTheme.BG_CARD)
        self.purok_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_reports_tab(self):
        """Create reports generation tab."""
        tab = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab, text="  📝 Reports  ")
        
        # Report options
        frame = tk.Frame(tab, bg=KalasagTheme.BG_MAIN, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_LARGE)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            frame,
            text="Generate Reports",
            font=KalasagTheme.FONT_H2,
            bg=KalasagTheme.BG_MAIN,
            fg=KalasagTheme.TEXT_PRIMARY
        ).pack(anchor='w', pady=(0, KalasagTheme.PAD_LARGE))
        
        reports = [
            ("📊 Residents Report", "Export all resident data to CSV", self._export_residents),
            ("📋 Blotter Cases Report", "Export all blotter cases to CSV", self._export_cases),
            ("📄 Documents Report", "Export document issuance records", self._export_documents),
            ("📈 Demographics Summary", "Export demographic statistics", self._export_demographics),
            ("🚨 Crime Statistics Report", "Export crime/incident statistics", self._export_crime_stats),
        ]
        
        for title, desc, command in reports:
            card = tk.Frame(frame, bg=KalasagTheme.BG_CARD, padx=KalasagTheme.PAD_MEDIUM, pady=KalasagTheme.PAD_MEDIUM)
            card.pack(fill=tk.X, pady=KalasagTheme.PAD_SMALL)
            
            left = tk.Frame(card, bg=KalasagTheme.BG_CARD)
            left.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(left, text=title, font=KalasagTheme.FONT_H3, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_PRIMARY, anchor='w').pack(fill=tk.X)
            tk.Label(left, text=desc, font=KalasagTheme.FONT_SMALL, bg=KalasagTheme.BG_CARD, fg=KalasagTheme.TEXT_SECONDARY, anchor='w').pack(fill=tk.X)
            
            tk.Button(
                card, text="Export", font=KalasagTheme.FONT_BODY,
                bg=KalasagTheme.PRIMARY_BLUE, fg=KalasagTheme.TEXT_LIGHT,
                bd=0, padx=KalasagTheme.PAD_LARGE, pady=KalasagTheme.PAD_SMALL,
                command=command
            ).pack(side=tk.RIGHT)
    
    def refresh(self):
        """Refresh all analytics data."""
        try:
            self._load_overview()
            self._load_crime_analytics()
            self._load_demographics()
            self.status_callback("Analytics refreshed", 'success')
        except Exception as e:
            self.status_callback(f"Error refreshing analytics: {str(e)}", 'error')
    
    def _load_overview(self):
        """Load overview statistics."""
        try:
            # Get stats
            from controllers.resident_controller import ResidentController
            from controllers.blotter_controller import BlotterController
            from controllers.document_controller import DocumentController
            
            resident_ctrl = ResidentController()
            blotter_ctrl = BlotterController()
            doc_ctrl = DocumentController()
            
            residents = resident_ctrl.get_all_residents()
            cases = blotter_ctrl.get_all_cases()
            resolved = [c for c in cases if c.get('status') == 'Resolved']
            documents = doc_ctrl.get_all_documents()
            
            self.total_residents_card.update_value(str(len(residents)))
            self.total_cases_card.update_value(str(len(cases)))
            self.resolved_cases_card.update_value(str(len(resolved)))
            self.documents_card.update_value(str(len(documents)))
            
            # Population summary
            self.pop_list.delete(0, tk.END)
            households = resident_ctrl.get_all_households()
            puroks = resident_ctrl.get_all_puroks()
            
            self.pop_list.insert(tk.END, f"Total Residents: {len(residents)}")
            self.pop_list.insert(tk.END, f"Total Households: {len(households)}")
            self.pop_list.insert(tk.END, f"Total Puroks: {len(puroks)}")
            
            # Gender breakdown
            males = len([r for r in residents if r.get('gender') == 'Male'])
            females = len([r for r in residents if r.get('gender') == 'Female'])
            self.pop_list.insert(tk.END, f"Male: {males}")
            self.pop_list.insert(tk.END, f"Female: {females}")
            
            # Voters
            voters = len([r for r in residents if r.get('voter_status')])
            self.pop_list.insert(tk.END, f"Registered Voters: {voters}")
            
            # Recent cases
            self.recent_cases_list.delete(0, tk.END)
            for case in cases[:10]:
                date = case.get('date_time', '')[:10]
                incident_type = case.get('incident_type', case.get('name', 'Unknown'))
                status = case.get('status', 'Filed')
                self.recent_cases_list.insert(tk.END, f"{date} | {incident_type} ({status})")
            
        except Exception as e:
            print(f"Error loading overview: {e}")
    
    def _load_crime_analytics(self):
        """Load crime analytics."""
        try:
            stats = self.analytics_ctrl.get_crime_statistics()
            
            # By type
            self.incident_types_list.delete(0, tk.END)
            for item in stats.get('by_type', []):
                name = item.get('name', 'Unknown')
                count = item.get('count', 0)
                self.incident_types_list.insert(tk.END, f"{name}: {count}")
            
            # Monthly trend
            self.trend_list.delete(0, tk.END)
            for item in stats.get('monthly_trend', []):
                month = item.get('month', 'Unknown')
                count = item.get('count', 0)
                self.trend_list.insert(tk.END, f"{month}: {count} incidents")
            
            # Charts
            if MATPLOTLIB_AVAILABLE:
                # Clear previous charts
                for widget in self.heatmap_frame.winfo_children():
                    widget.destroy()
                for widget in self.time_frame.winfo_children():
                    widget.destroy()
                
                # Heatmap
                fig_heatmap = self.analytics_ctrl.get_heatmap_figure()
                if fig_heatmap:
                    canvas = FigureCanvasTkAgg(fig_heatmap, master=self.heatmap_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                else:
                    tk.Label(self.heatmap_frame, text="No data available", bg=KalasagTheme.BG_CARD).pack()
                
                # Time Analysis
                fig_time = self.analytics_ctrl.get_time_analysis_figure()
                if fig_time:
                    canvas = FigureCanvasTkAgg(fig_time, master=self.time_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                else:
                    tk.Label(self.time_frame, text="No data available", bg=KalasagTheme.BG_CARD).pack()
            else:
                tk.Label(self.heatmap_frame, text="Matplotlib not installed", bg=KalasagTheme.BG_CARD).pack()
                tk.Label(self.time_frame, text="Matplotlib not installed", bg=KalasagTheme.BG_CARD).pack()
            
        except Exception as e:
            print(f"Error loading crime analytics: {e}")
    
    def _load_demographics(self):
        """Load demographics data."""
        try:
            if MATPLOTLIB_AVAILABLE:
                # Clear previous charts
                for widget in self.gender_frame.winfo_children():
                    widget.destroy()
                for widget in self.civil_frame.winfo_children():
                    widget.destroy()
                for widget in self.purok_frame.winfo_children():
                    widget.destroy()
                
                # Gender Chart
                fig_gender = self.analytics_ctrl.get_demographic_figure('gender')
                if fig_gender:
                    canvas = FigureCanvasTkAgg(fig_gender, master=self.gender_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                else:
                    tk.Label(self.gender_frame, text="No data available", bg=KalasagTheme.BG_CARD).pack()
                
                # Civil Status Chart
                fig_civil = self.analytics_ctrl.get_demographic_figure('civil_status')
                if fig_civil:
                    canvas = FigureCanvasTkAgg(fig_civil, master=self.civil_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                else:
                    tk.Label(self.civil_frame, text="No data available", bg=KalasagTheme.BG_CARD).pack()
                
                # Purok Chart
                fig_purok = self.analytics_ctrl.get_demographic_figure('purok')
                if fig_purok:
                    canvas = FigureCanvasTkAgg(fig_purok, master=self.purok_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                else:
                    tk.Label(self.purok_frame, text="No data available", bg=KalasagTheme.BG_CARD).pack()
            else:
                # Fallback to text lists if matplotlib not available
                tk.Label(self.gender_frame, text="Matplotlib not installed", bg=KalasagTheme.BG_CARD).pack()
                tk.Label(self.civil_frame, text="Matplotlib not installed", bg=KalasagTheme.BG_CARD).pack()
                tk.Label(self.purok_frame, text="Matplotlib not installed", bg=KalasagTheme.BG_CARD).pack()
            
        except Exception as e:
            print(f"Error loading demographics: {e}")
    
    def _export_residents(self):
        """Export residents to CSV."""
        self._export_table('resident', 'residents_report')
    
    def _export_cases(self):
        """Export cases to CSV."""
        self._export_table('blotter_case', 'blotter_cases_report')
    
    def _export_documents(self):
        """Export documents to CSV."""
        self._export_table('doc_log', 'documents_report')
    
    def _export_demographics(self):
        """Export demographics summary."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"demographics_summary_{datetime.now().strftime('%Y%m%d')}.txt"
            )
            
            if filename:
                stats = self.analytics_ctrl.get_demographic_statistics()
                
                with open(filename, 'w') as f:
                    f.write("KALASAG - Demographics Summary\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                    
                    f.write("BY GENDER:\n")
                    for item in stats.get('by_gender', []):
                        f.write(f"  {item.get('gender', 'Unknown')}: {item.get('count', 0)}\n")
                    
                    f.write("\nBY CIVIL STATUS:\n")
                    for item in stats.get('by_civil_status', []):
                        f.write(f"  {item.get('civil_status', 'Unknown')}: {item.get('count', 0)}\n")
                    
                    f.write("\nBY PUROK:\n")
                    for item in stats.get('by_purok', []):
                        f.write(f"  {item.get('purok_name', item.get('name', 'Unknown'))}: {item.get('count', 0)}\n")
                
                self.status_callback(f"Report exported to {filename}", 'success')
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
        except Exception as e:
            self.status_callback(f"Export error: {str(e)}", 'error')
    
    def _export_crime_stats(self):
        """Export crime statistics."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"crime_statistics_{datetime.now().strftime('%Y%m%d')}.txt"
            )
            
            if filename:
                stats = self.analytics_ctrl.get_crime_statistics()
                
                with open(filename, 'w') as f:
                    f.write("KALASAG - Crime Statistics Report\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                    
                    f.write("BY INCIDENT TYPE:\n")
                    for item in stats.get('by_type', []):
                        f.write(f"  {item.get('name', 'Unknown')}: {item.get('count', 0)}\n")
                    
                    f.write("\nBY LOCATION:\n")
                    for item in stats.get('by_location', []):
                        f.write(f"  {item.get('location', 'Unknown')}: {item.get('count', 0)}\n")
                    
                    f.write("\nMONTHLY TREND:\n")
                    for item in stats.get('monthly_trend', []):
                        f.write(f"  {item.get('month', 'Unknown')}: {item.get('count', 0)} incidents\n")
                
                self.status_callback(f"Report exported to {filename}", 'success')
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
        except Exception as e:
            self.status_callback(f"Export error: {str(e)}", 'error')
    
    def _export_table(self, table_name: str, filename_prefix: str):
        """Export a table to CSV."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                from database import export_to_csv
                export_to_csv(table_name, filename)
                self.status_callback(f"Report exported to {filename}", 'success')
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
        except Exception as e:
            self.status_callback(f"Export error: {str(e)}", 'error')
