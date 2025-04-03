import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
import os
import logging
import traceback

class JobFilterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Illinois Job Posting Filter")
        self.root.geometry("1400x800")  # Increased size to accommodate statistics
        
        # Create main containers
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)
        
        # Create left panel for filters and results
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Create right panel for statistics
        self.stats_panel = ttk.Frame(self.main_frame, style='Stats.TFrame')
        self.stats_panel.pack(side='right', fill='y', padx=5, pady=5)
        
        # Data storage
        self.df = None
        self.filtered_df = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize UI components
        self.setup_styles()
        self.create_filter_frame()
        self.create_results_frame()
        self.create_stats_panel()
        self.create_status_bar()
        self.load_data()

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.configure('Filter.TFrame', padding=10)
        style.configure('Results.TFrame', padding=10)
        style.configure('Status.TFrame', padding=5)
        style.configure('Stats.TFrame', padding=10)
        style.configure('StatsHeader.TLabel', font=('Helvetica', 12, 'bold'))

    def create_filter_frame(self):
        """Create the filter controls section"""
        filter_frame = ttk.Frame(self.left_panel, style='Filter.TFrame')
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
        
        # Company filter
        ttk.Label(filter_frame, text="Company:").pack(side='left', padx=5)
        self.company_var = tk.StringVar()
        self.company_entry = ttk.Entry(filter_frame, textvariable=self.company_var)
        self.company_entry.pack(side='left', padx=5)
        
        # City filter
        ttk.Label(filter_frame, text="City:").pack(side='left', padx=5)
        self.city_var = tk.StringVar(value="All")
        self.city_combo = ttk.Combobox(filter_frame, textvariable=self.city_var,
                                     values=["All", "Chicago", "Springfield", "Naperville", 
                                            "Evanston", "Rockford", "Peoria"])
        self.city_combo.pack(side='left', padx=5)
        
        # Buttons
        ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Refresh Data", command=self.load_data).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Export Results", command=self.export_results).pack(side='left', padx=5)

    def create_results_frame(self):
        """Create the results display section"""
        results_frame = ttk.Frame(self.left_panel, style='Results.TFrame')
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create Treeview
        columns = ('Post Date', 'Company', 'Title', 'Location', 'URL')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, width=100)
        
        self.tree.column('Title', width=300)
        self.tree.column('URL', width=200)
        
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

    def create_stats_panel(self):
        """Create the statistics panel"""
        ttk.Label(self.stats_panel, text="Statistics", style='StatsHeader.TLabel').pack(pady=10)
        
        # Create frame for stats content
        stats_content = ttk.Frame(self.stats_panel)
        stats_content.pack(fill='x', padx=10)
        
        # Create labels for each statistic
        self.total_jobs_var = tk.StringVar(value="Total Jobs: 0")
        self.unique_companies_var = tk.StringVar(value="Unique Companies: 0")
        self.top_locations_var = tk.StringVar(value="Top Locations:\n")
        self.company_size_stats_var = tk.StringVar(value="Company Sizes:\n")
        
        ttk.Label(stats_content, textvariable=self.total_jobs_var).pack(anchor='w', pady=5)
        ttk.Label(stats_content, textvariable=self.unique_companies_var).pack(anchor='w', pady=5)
        ttk.Label(stats_content, textvariable=self.top_locations_var).pack(anchor='w', pady=5)
        ttk.Label(stats_content, textvariable=self.company_size_stats_var).pack(anchor='w', pady=5)
        
        # Add company size distribution chart
        self.create_size_chart_frame()

    def create_size_chart_frame(self):
        """Create frame for company size distribution chart"""
        self.size_chart_frame = ttk.Frame(self.stats_panel)
        self.size_chart_frame.pack(fill='x', padx=10, pady=10)
        
        # Add size distribution bars
        self.size_canvas = tk.Canvas(self.size_chart_frame, height=100)
        self.size_canvas.pack(fill='x', expand=True)

    def update_size_chart(self):
        """Update the company size distribution chart"""
        if self.filtered_df is None or self.filtered_df.empty:
            return
            
        self.size_canvas.delete('all')
        
        # Get company size distribution
        size_counts = self.filtered_df['company_size'].value_counts()
        
        # Draw bars
        width = self.size_canvas.winfo_width()
        height = self.size_canvas.winfo_height()
        bar_width = width / (len(size_counts) + 1)
        
        max_count = size_counts.max()
        for i, (size, count) in enumerate(size_counts.items()):
            bar_height = (count / max_count) * height
            x1 = i * bar_width + 5
            y1 = height - bar_height
            x2 = (i + 1) * bar_width - 5
            y2 = height
            
            # Draw bar
            self.size_canvas.create_rectangle(x1, y1, x2, y2, fill='blue')
            
            # Add label
            self.size_canvas.create_text(
                (x1 + x2) / 2, height - 5,
                text=f"{size}\n({count})",
                anchor='s'
            )

    def update_statistics(self):
        """Update statistics panel with current data"""
        if self.filtered_df is not None:
            # Update existing stats
            total_jobs = len(self.filtered_df)
            self.total_jobs_var.set(f"Total Jobs: {total_jobs}")
            
            unique_companies = self.filtered_df['company'].nunique()
            self.unique_companies_var.set(f"Unique Companies: {unique_companies}")
            
            # Update location stats
            top_locations = self.filtered_df['location'].value_counts().head(5)
            locations_text = "Top Locations:\n"
            for loc, count in top_locations.items():
                locations_text += f"{loc}: {count}\n"
            self.top_locations_var.set(locations_text)
            
            # Update company size stats
            size_stats = self.filtered_df['company_size'].value_counts()
            size_text = "Company Sizes:\n"
            for size, count in size_stats.items():
                size_text += f"{size}: {count}\n"
            self.company_size_stats_var.set(size_text)
            
            # Update size distribution chart
            self.update_size_chart()
        else:
            self.total_jobs_var.set("Total Jobs: 0")
            self.unique_companies_var.set("Unique Companies: 0")
            self.top_locations_var.set("Top Locations:\nNo data available")
            self.company_size_stats_var.set("Company Sizes:\nNo data available")
        ttk.Label(self.stats_panel, text="Statistics", style='StatsHeader.TLabel').pack(pady=10)
        
        # Create frame for stats content
        stats_content = ttk.Frame(self.stats_panel)
        stats_content.pack(fill='x', padx=10)
        
        # Create labels for each statistic
        self.total_jobs_var = tk.StringVar(value="Total Jobs: 0")
        self.unique_companies_var = tk.StringVar(value="Unique Companies: 0")
        self.top_locations_var = tk.StringVar(value="Top Locations:\n")
        
        ttk.Label(stats_content, textvariable=self.total_jobs_var).pack(anchor='w', pady=5)
        ttk.Label(stats_content, textvariable=self.unique_companies_var).pack(anchor='w', pady=5)
        ttk.Label(stats_content, textvariable=self.top_locations_var).pack(anchor='w', pady=5)
        
        # Add location distribution chart (placeholder)
        self.location_chart_frame = ttk.Frame(self.stats_panel)
        self.location_chart_frame.pack(fill='x', padx=10, pady=10)

    def create_status_bar(self): # any way for this to appear while the script is running?
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
            # Find all CSV files
            files = [f for f in os.listdir() if f.endswith('.csv')]
            print(f"Found CSV files: {files}")  # debug print
            
            if not files:
                messagebox.showwarning("No Data", "No CSV files found.")
                return
            
            latest_file = max(files)
            print(f"\nAttempting to load: {latest_file}")  # debug print
            
            # read the CSV file
            df = pd.read_csv(latest_file)
            print(f"\nDataFrame columns: {df.columns.tolist()}")  # debug print
            print(f"\nTotal records: {len(df)}")  # debug print
            
            # convert post_date to datetime with error handling
            df['post_date'] = pd.to_datetime(df['post_date'], errors='coerce')
            
            self.df = df
            self.filtered_df = df.copy()
            
            self.update_results_display()
            self.update_statistics()  # update statistics panel
            self.status_var.set(f"Loaded {len(df)} records from {latest_file}")
            
        except Exception as e:
            print(f"\nERROR loading data: {str(e)}")  # debug print
            self.logger.error(f"Error loading data: {str(e)}")
            traceback.print_exc()  # print full traceback
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
        
        # date filter
        date_mask = (self.filtered_df['post_date'] >= start_date) & (self.filtered_df['post_date'] <= end_date)
        self.filtered_df = self.filtered_df[date_mask]
        
        # company filter
        if self.company_var.get():
            company_filter = self.company_var.get().lower()
            self.filtered_df = self.filtered_df[self.filtered_df['company'].str.lower().str.contains(company_filter, na=False)]
        
        # city filter
        if self.city_var.get() != "All":
            city_filter = self.city_var.get().lower()
            self.filtered_df = self.filtered_df[self.filtered_df['location'].str.lower().str.contains(city_filter, na=False)]
        
        self.update_results_display()
        self.update_statistics()  # update statistics after filtering
        self.status_var.set("Filters applied")

    def update_results_display(self):
        """Update the Treeview with filtered results"""
        try:
            print("\nUpdating results display...")  # debug print
            
            # clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if self.filtered_df is None:
                print("filtered_df is None")  # debug print
                self.count_var.set("No results to display")
                return
                
            print(f"\nFiltered DataFrame has {len(self.filtered_df)} rows")  # Debug print
            print("\nFiltered DataFrame columns:", self.filtered_df.columns.tolist())  # Debug print
            
            # add filtered data
            for idx, row in self.filtered_df.iterrows():
                try:
                    print(f"\nProcessing row {idx}:")  # debug print
                    print(row)  # debug print
                    
                    # format the date
                    if pd.notnull(row['post_date']):
                        formatted_date = row['post_date'].strftime('%Y-%m-%d')
                    else:
                        formatted_date = 'Unknown'
                        
                    values = (
                        formatted_date,
                        row.get('company', 'Unknown'),
                        row.get('title', 'Unknown'),
                        row.get('location', 'Unknown'),
                        row.get('url', 'Unknown')
                    )
                    
                    print(f"Inserting values: {values}")  # Debug print
                    self.tree.insert('', 'end', values=values)
                    
                except Exception as row_error:
                    print(f"Error processing row {idx}: {str(row_error)}")  # Debug print
                    continue
            
            self.count_var.set(f"Showing {len(self.filtered_df)} results")
            print("\nDisplay update completed")  # Debug print
            
        except Exception as e:
            print(f"\nERROR updating display: {str(e)}")  # Debug print
            self.logger.error(f"Error updating display: {str(e)}")
            raise

    def update_statistics(self):
        """Update statistics panel with current data"""
        if self.filtered_df is not None:
            # Update total jobs
            total_jobs = len(self.filtered_df)
            self.total_jobs_var.set(f"Total Jobs: {total_jobs}")
            
            # Update unique companies
            unique_companies = self.filtered_df['company'].nunique()
            self.unique_companies_var.set(f"Unique Companies: {unique_companies}")
            
            # Update top locations
            top_locations = self.filtered_df['location'].value_counts().head(5)
            locations_text = "Top Locations:\n"
            for loc, count in top_locations.items():
                locations_text += f"{loc}: {count}\n"
            self.top_locations_var.set(locations_text)
        else:
            self.total_jobs_var.set("Total Jobs: 0")
            self.unique_companies_var.set("Unique Companies: 0")
            self.top_locations_var.set("Top Locations:\nNo data available")

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
                self.status
        except:
            print("An exception occurred")
            