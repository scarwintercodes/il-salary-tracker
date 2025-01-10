import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
import os
from data_utils import DataValidator, get_data_summary
import logging

class JobFilterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Posting Filter")
        self.root.geometry("1200x700")
        
        # Initialize data validator
        self.validator = DataValidator()
        
        # Data storage
        self.df = None
        self.filtered_df = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create main containers
        self.create_filter_frame()
        self.create_results_frame()
        self.create_status_bar()
        
        # Initialize the UI
        self.setup_styles()
        self.load_data()

    def load_data(self):
        """Load and validate the most recent CSV file"""
        try:
            # Find the most recent CSV file
            files = [f for f in os.listdir() if f.startswith('non_compliant_jobs_') and f.endswith('.csv')]
            if not files:
                messagebox.showwarning("No Data", "No job posting data files found.")
                return
            
            latest_file = max(files)
            self.logger.info(f"Loading data from {latest_file}")
            
            # Read the CSV file
            df = pd.read_csv(latest_file)
            
            # Validate and repair data
            df, is_valid = self.validator.validate_and_repair_data(df)
            
            if not is_valid:
                messagebox.showwarning("Data Issues", "Some data issues were found and repaired. Check the log file for details.")
            
            # Get data summary
            summary = get_data_summary(df)
            self.logger.info(f"Data summary: {summary}")
            
            self.df = df
            self.filtered_df = df.copy()
            
            self.update_results_display()
            self.status_var.set(f"Loaded {summary['total_records']} records from {latest_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            messagebox.showerror("Error", f"Error loading data: {str(e)}")
            self.status_var.set("Error loading data")

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.configure('Filter.TFrame', padding=10)
        style.configure('Results.TFrame', padding=10)
        style.configure('Status.TFrame', padding=5)
        
    def create_filter_frame(self):
        """Create the filter controls section"""
        filter_frame = ttk.Frame(self.root, style='Filter.TFrame')
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        # Date range filter
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill='x', pady=5)
        
        ttk.Label(date_frame, text="Date Range:").pack(side='left', padx=5)
        self.start_date_var = tk.StringVar(value="2025-01-01")
        self.start_date_entry = ttk.Entry(date_frame, textvariable=self.start_date_var, width=10)
        self.start_date_entry.pack(side='left', padx=5)
        
        ttk.Label(date_frame, text="to").pack(side='left', padx=5)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.end_date_entry = ttk.Entry(date_frame, textvariable=self.end_date_var, width=10)
        self.end_date_entry.pack(side='left', padx=5)
        """Create the filter controls section"""
        filter_frame = ttk.Frame(self.root, style='Filter.TFrame')
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        # Platform filter
        ttk.Label(filter_frame, text="Platform:").pack(side='left', padx=5)
        self.platform_var = tk.StringVar(value="All")
        self.platform_combo = ttk.Combobox(filter_frame, textvariable=self.platform_var, 
                                         values=["All", "LinkedInScraper", "IndeedScraper", "BuiltInChicagoScraper"],
                                         width=20)
        self.platform_combo.pack(side='left', padx=5)
        
        # Company filter
        ttk.Label(filter_frame, text="Company:").pack(side='left', padx=5)
        self.company_var = tk.StringVar()
        self.company_entry = ttk.Entry(filter_frame, textvariable=self.company_var, width=20)
        self.company_entry.pack(side='left', padx=5)
        
        # City filter
        ttk.Label(filter_frame, text="City:").pack(side='left', padx=5)
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(filter_frame, textvariable=self.city_var,
                                     values=["All", "Chicago", "Springfield", "Naperville", "Evanston", 
                                            "Skokie", "Schaumburg", "Peoria", "Rockford"],
                                     width=15)
        self.city_combo.pack(side='left', padx=5)
        
        # Filter button
        self.filter_btn = ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters)
        self.filter_btn.pack(side='left', padx=10)
        
        # Export button
        self.export_btn = ttk.Button(filter_frame, text="Export Results", command=self.export_results)
        self.export_btn.pack(side='left', padx=5)
        
        # Refresh button
        self.refresh_btn = ttk.Button(filter_frame, text="Refresh Data", command=self.load_data)
        self.refresh_btn.pack(side='left', padx=5)

    def create_results_frame(self):
        """Create the results display section"""
        results_frame = ttk.Frame(self.root, style='Results.TFrame')
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create Treeview
        columns = ('Found Date', 'Post Date', 'Platform', 'Company', 'Title', 'URL')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, width=100)
        
        self.tree.column('URL', width=200)
        self.tree.column('Title', width=300)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        # Configure grid weights
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

    def create_status_bar(self):
        """Create the status bar"""
        status_frame = ttk.Frame(self.root, style='Status.TFrame')
        status_frame.pack(fill='x', side='bottom')
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side='left', padx=5)
        
        self.count_var = tk.StringVar()
        self.count_label = ttk.Label(status_frame, textvariable=self.count_var)
        self.count_label.pack(side='right', padx=5)

    def load_data(self):
        """Load the most recent CSV file"""
        try:
            # Find the most recent CSV file
            files = [f for f in os.listdir() if f.startswith('non_compliant_jobs_') and f.endswith('.csv')]
            if not files:
                messagebox.showwarning("No Data", "No job posting data files found.")
                return
            
            latest_file = max(files)
            self.df = pd.read_csv(latest_file)
            
            # Ensure post_date column exists
            if 'post_date' not in self.df.columns:
                self.df['post_date'] = None
            
            # Convert post_date to datetime, handling errors
            try:
                self.df['post_date'] = pd.to_datetime(self.df['post_date'], errors='coerce')
            except Exception:
                self.df['post_date'] = pd.NaT
            
            # Fill NaN/NaT values with None for display purposes
            self.df['post_date'] = self.df['post_date'].astype(object).where(self.df['post_date'].notna(), None)
            
            self.filtered_df = self.df.copy()
            
            self.update_results_display()
            self.status_var.set(f"Loaded data from {latest_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading data: {str(e)}")
            self.status_var.set("Error loading data")

    def apply_filters(self):
        """Apply selected filters to the data"""
        if self.df is None:
            return
        
        try:
            start_date = pd.to_datetime(self.start_date_var.get())
            end_date = pd.to_datetime(self.end_date_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
            return
        
        self.filtered_df = self.df.copy()
        
        # Date filter
        self.filtered_df['post_date'] = pd.to_datetime(self.filtered_df['post_date'])
        date_mask = (self.filtered_df['post_date'] >= start_date) & (self.filtered_df['post_date'] <= end_date)
        self.filtered_df = self.filtered_df[date_mask]
        """Apply selected filters to the data"""
        if self.df is None:
            return
        
        self.filtered_df = self.df.copy()
        
        # Platform filter
        if self.platform_var.get() != "All":
            self.filtered_df = self.filtered_df[self.filtered_df['platform'] == self.platform_var.get()]
        
        # Company filter
        if self.company_var.get():
            company_filter = self.company_var.get().lower()
            self.filtered_df = self.filtered_df[self.filtered_df['company'].str.lower().str.contains(company_filter, na=False)]
        
        # City filter
        if self.city_var.get() != "All":
            city_filter = self.city_var.get().lower()
            self.filtered_df = self.filtered_df[self.filtered_df['url'].str.lower().str.contains(city_filter, na=False)]
        
        self.update_results_display()
        self.status_var.set("Filters applied")

    def update_results_display(self):
        """Update the Treeview with filtered results"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if self.filtered_df is None or len(self.filtered_df) == 0:
                self.count_var.set("No results to display")
                return
            
            # Add filtered data
            for _, row in self.filtered_df.iterrows():
                try:
                    # Format post_date safely
                    post_date = self.format_date_for_display(row.get('post_date'))
                    found_date = self.format_date_for_display(row.get('date_found'))
                    
                    self.tree.insert('', 'end', values=(
                        found_date,
                        post_date,
                        row.get('platform', 'Unknown'),
                        row.get('company', 'Unknown'),
                        row.get('title', 'Unknown'),
                        row.get('url', 'Unknown')
                    ))
                except Exception as e:
                    self.logger.error(f"Error adding row to display: {str(e)}")
                    continue
            
            self.count_var.set(f"Showing {len(self.filtered_df)} results")
            
        except Exception as e:
            self.logger.error(f"Error updating display: {str(e)}")
            messagebox.showerror("Error", "Error updating display. Check the log file for details.")

    def format_date_for_display(self, date_value):
        """Safely format a date value for display"""
        try:
            if pd.isna(date_value):
                return 'Unknown'
            
            if isinstance(date_value, str):
                date_value = pd.to_datetime(date_value)
                
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime('%Y-%m-%d')
                
            return str(date_value)
        except Exception as e:
            self.logger.warning(f"Error formatting date {date_value}: {str(e)}")
            return 'Unknown'

    def sort_treeview(self, col):
        """Sort treeview by column"""
        if self.filtered_df is None:
            return
            
        self.filtered_df = self.filtered_df.sort_values(by=col.lower())
        self.update_results_display()

    def export_results(self):
        """Export filtered results to CSV"""
        if self.filtered_df is None or len(self.filtered_df) == 0:
            messagebox.showwarning("No Data", "No results to export.")
            return
            
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"filtered_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            if filename:
                self.filtered_df.to_csv(filename, index=False)
                self.status_var.set(f"Results exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")

def launch_ui():
    """Launch the Job Filter UI"""
    root = tk.Tk()
    app = JobFilterUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_ui()