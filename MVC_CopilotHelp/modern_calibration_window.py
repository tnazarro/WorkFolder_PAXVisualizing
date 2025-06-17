# =============================================================================
# MODERN CALIBRATION ANALYSIS WINDOW FOR PAX DATA VISUALIZER
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from scipy.stats import linregress

from data_processing import create_extinction_column_if_needed, update_listbox_with_new_column
from constants import *

class ModernCalibrationWindow:
    def __init__(self, parent_window, gui_instance, constants_module):
        """
        Create a modern calibration analysis window.
        
        Parameters:
        - parent_window: The main application window
        - gui_instance: Reference to the main PAXView instance for accessing GUI elements
        """
        self.parent = parent_window
        self.gui = gui_instance
        self.constants = constants_module
        
        # Create the calibration window
        self.create_calibration_window()
        
        # Initialize results storage
        self.analysis_results = {}
        
    def create_calibration_window(self):
        """Create the main calibration window with modern styling and scrolling"""
        
        # Create toplevel window
        self.calib_window = tk.Toplevel(self.parent)
        self.calib_window.title("🔬 PAX Calibration Analysis")
        self.calib_window.geometry("1400x900")
        self.calib_window.configure(bg="#f8f9fa")
        
        # Make window resizable but set minimum size
        self.calib_window.minsize(1200, 700)
        
        # CREATE SCROLLABLE CONTAINER
        main_container = tk.Frame(self.calib_window)
        main_container.pack(fill="both", expand=True)

        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        # Add vertical scrollbar
        v_scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        v_scrollbar.pack(side="right", fill="y")

        # Configure canvas scrolling
        canvas.configure(yscrollcommand=v_scrollbar.set)

        # Create the scrollable frame that will contain all content
        scrollable_frame = tk.Frame(canvas)
        
        # Add the scrollable frame to the canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Bind events for proper scrolling behavior
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Create all sections in the scrollable frame
        self.create_header_section(scrollable_frame)
        self.create_parameters_section(scrollable_frame)
        self.create_plots_section(scrollable_frame)
        self.create_results_section(scrollable_frame)
        self.create_action_buttons(scrollable_frame)
        
        # Run analysis immediately if data is available
        self.run_calibration_analysis()
        
    def create_header_section(self, parent=None):
        """Create the header section with title and status"""
        if parent is None:
            parent = self.calib_window
    
        header_frame = tk.Frame(parent, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="🔬 Calibration Analysis Dashboard",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # Status indicator
        self.status_frame = tk.Frame(header_frame, bg="#2c3e50")
        self.status_frame.pack(side="right", padx=20, pady=20)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="● Ready for Analysis",
            font=("Arial", 12, "bold"),
            fg="#27ae60",
            bg="#2c3e50"
        )
        self.status_label.pack()
        
    def create_parameters_section(self, parent=None):
        """Create the parameters display section"""
        if parent is None:
            parent = self.calib_window
        params_frame = ttk.LabelFrame(
            parent, 
            text="📊 Analysis Parameters", 
            padding="15"
        )
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # Create parameter display in a grid
        params_grid = tk.Frame(params_frame)
        params_grid.pack(fill="x")
        
        # Parameters from GUI
        self.create_parameter_display(params_grid, "Calibration Mode:", 
                                    lambda: self.gui.calibvar.get(), 0, 0)
        self.create_parameter_display(params_grid, "Min Value:", 
                                    lambda: self.gui.entry_min.get(), 0, 1)
        self.create_parameter_display(params_grid, "Max Value:", 
                                    lambda: self.gui.entry_max.get(), 0, 2)
        self.create_parameter_display(params_grid, "% Change Limit:", 
                                    lambda: f"{self.gui.entry_percent.get()}%", 0, 3)
        
        # Slider positions
        self.create_parameter_display(params_grid, "Calib Start Index:", 
                                    lambda: f"{int(self.gui.current_valueCalibLow.get())}", 1, 0)
        self.create_parameter_display(params_grid, "Calib End Index:", 
                                    lambda: f"{int(self.gui.current_valueCalibHigh.get())}", 1, 1)
        
        # Data info
        self.create_parameter_display(params_grid, "Total Data Points:", 
                                    lambda: f"{len(self.constants.df_main)}" if not self.constants.df_main.empty else "0", 1, 2)
        self.create_parameter_display(params_grid, "Selected Range:", 
                                    self.get_time_range_text, 1, 3)
        
    def create_parameter_display(self, parent, label_text, value_func, row, col):
        """Create a parameter display widget"""
        
        param_frame = tk.Frame(parent, relief="ridge", bd=1, padx=10, pady=8)
        param_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        label = tk.Label(param_frame, text=label_text, font=("Arial", 9, "bold"), fg="#2c3e50")
        label.pack()
        
        value_label = tk.Label(param_frame, text="--", font=("Arial", 10), fg="#3498db")
        value_label.pack()
        
        # Store reference for updating
        setattr(self, f"param_{label_text.replace(':', '').replace(' ', '_').lower()}", 
               {'func': value_func, 'label': value_label})
        
    def get_time_range_text(self):
        """Get formatted time range text"""
        try:
            if self.constants.df_main.empty:
                return "No data"
            
            start_idx = int(self.gui.current_valueCalibLow.get())
            end_idx = int(self.gui.current_valueCalibHigh.get())
            
            start_time = self.constants.df_main['time'].iloc[start_idx].strftime('%H:%M:%S')
            end_time = self.constants.df_main['time'].iloc[end_idx].strftime('%H:%M:%S')
            
            return f"{start_time} - {end_time}"
        except:
            return "Invalid range"
        
    def create_plots_section(self, parent=None):
        """Create the plots section with two subplots"""
        if parent is None:
            parent = self.calib_window
        plots_frame = ttk.LabelFrame(
            parent, 
            text="📈 Analysis Plots", 
            padding="10"
        )
        plots_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create matplotlib figure with modern styling
        self.fig = Figure(figsize=(14, 6), dpi=100, facecolor='white')
        self.fig.suptitle("Calibration Analysis Results", fontsize=14, fontweight='bold')
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        
        # Configure subplot appearance
        for ax in [self.ax1, self.ax2]:
            ax.grid(True, alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=plots_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        
        # Create toolbar
        toolbar_frame = tk.Frame(plots_frame)
        toolbar_frame.pack(side="bottom", fill="x")
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
    def create_results_section(self, parent=None):
        """Create the results display section"""
        if parent is None:
            parent = self.calib_window
        results_frame = ttk.LabelFrame(
            parent, 
            text="📋 Analysis Results", 
            padding="15"
        )
        results_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Results grid
        results_grid = tk.Frame(results_frame)
        results_grid.pack(fill="x")
        
        # Configure grid weights for even distribution
        for i in range(6):
            results_grid.columnconfigure(i, weight=1)
            
        # Create result displays
        self.create_result_display(results_grid, "R² Value", "r2_value", 0, 0, "#e74c3c")
        self.create_result_display(results_grid, "Slope", "slope_value", 0, 1, "#9b59b6")
        self.create_result_display(results_grid, "Intercept", "intercept_value", 0, 2, "#3498db")
        self.create_result_display(results_grid, "P-Value", "p_value", 0, 3, "#f39c12")
        self.create_result_display(results_grid, "Std Error", "std_error", 0, 4, "#27ae60")
        self.create_result_display(results_grid, "Data Points", "data_points", 0, 5, "#34495e")
        
        # Equation display
        equation_frame = tk.Frame(results_frame, relief="sunken", bd=2, bg="#ecf0f1")
        equation_frame.pack(fill="x", pady=(15, 0))
        
        tk.Label(equation_frame, text="Best Fit Equation:", 
                font=("Arial", 11, "bold"), bg="#ecf0f1").pack(pady=(10, 5))
        
        self.equation_label = tk.Label(
            equation_frame,
            text="y = mx + b",
            font=("Courier New", 14, "bold"),
            fg="#2c3e50",
            bg="#ecf0f1"
        )
        self.equation_label.pack(pady=(0, 10))
        
    def create_result_display(self, parent, label_text, attr_name, row, col, color):
        """Create a result display widget"""
        
        result_frame = tk.Frame(parent, relief="raised", bd=1, padx=15, pady=10)
        result_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        label = tk.Label(result_frame, text=label_text, font=("Arial", 9, "bold"), fg="#2c3e50")
        label.pack()
        
        value_label = tk.Label(result_frame, text="--", font=("Arial", 12, "bold"), fg=color)
        value_label.pack()
        
        setattr(self, attr_name, value_label)
        
    def create_action_buttons(self, parent=None):
        """Create action buttons at the bottom"""
        if parent is None:
            parent = self.calib_window
        button_frame = tk.Frame(parent, bg="#f8f9fa")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Refresh analysis button
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 Refresh Analysis",
            command=self.run_calibration_analysis,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=30,
            pady=10
        )
        refresh_btn.pack(side="left", padx=(0, 10))
        
        # Export results button
        export_btn = tk.Button(
            button_frame,
            text="📤 Export Results",
            command=self.export_results,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=30,
            pady=10
        )
        export_btn.pack(side="left", padx=(0, 10))
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="❌ Close Window",
            command=self.calib_window.destroy,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=30,
            pady=10
        )
        close_btn.pack(side="right")
        
    def run_calibration_analysis(self):
        """Run the calibration analysis using original logic"""
        
        try:
            # Update status
            self.status_label.config(text="● Running Analysis...", fg="#f39c12")
            self.calib_window.update()
            
            # Update parameter displays
            self.update_parameter_displays()
            
            # Get parameters from GUI
            if not self.validate_inputs():
                return
                
            min_val = float(self.gui.entry_min.get())
            max_val = float(self.gui.entry_max.get())
            percent = float(self.gui.entry_percent.get())
            calib_mode = self.gui.calibvar.get()
            
            # Get slider positions (calibration region)
            xlocA = int(self.gui.current_valueCalibLow.get())
            xlocB = int(self.gui.current_valueCalibHigh.get())
            
            # Get data
            df = self.constants.df_main
            
            if df.empty:
                messagebox.showerror("Error", "No data loaded!")
                return
                
            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()
            
            # Run analysis based on calibration mode
            if calib_mode == 'Scattering':
                self.modified_analyze_scattering_mode(df, xlocA, xlocB, min_val, max_val, percent)
            elif calib_mode == 'Absorbing':
                self.modified_analyze_absorbing_mode(df, xlocA, xlocB, min_val, max_val, percent)
            else:
                messagebox.showerror("Error", "Please select a calibration mode (Scattering or Absorbing)")
                return
                
            # Update plots
            self.finalize_plots()
            
            # Update status
            self.status_label.config(text="● Analysis Complete", fg="#27ae60")
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error during analysis: {str(e)}")
            self.status_label.config(text="● Analysis Failed", fg="#e74c3c")
            
    def validate_inputs(self):
        """Validate that all inputs are properly filled"""
        try:
            float(self.gui.entry_min.get())
            float(self.gui.entry_max.get())
            float(self.gui.entry_percent.get())
            return True
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all calibration parameters are valid numbers")
            return False
            
    def modified_analyze_scattering_mode(self, df, xlocA, xlocB, min_val, max_val, percent):
        """
        Modified scattering analysis that uses extinction coefficient if needed.
        Replace the analyze_scattering_mode method in ModernCalibrationWindow.
        """
        
        try:
            # Determine which column to use for analysis
            if 'Debug Ext Calculation' in df.columns:
                ext_column = 'Debug Ext Calculation'
                print("📊 Using existing 'Debug Ext Calculation' column")
            elif 'Extinction_Coefficient' in df.columns:
                ext_column = 'Extinction_Coefficient'
                print("🔬 Using calculated 'Extinction_Coefficient' column")
            else:
                # Try to create extinction coefficient column automatically
                ext_column, is_calculated, i0_baseline = create_extinction_column_if_needed(self.gui)
                if is_calculated:
                    # Update the GUI listbox
                    update_listbox_with_new_column(self.gui, highlight_column=ext_column)
                    messagebox.showinfo("Column Created", 
                                    f"Created '{ext_column}' column for analysis\nI0 Baseline: {i0_baseline:.6f}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not determine extinction column: {str(e)}")
            return
        
        # Extract data for the specified range
        filtered_time = df['time'].iloc[xlocA:xlocB]
        filtered_dfx = df['Bscat (1/Mm)'].iloc[xlocA:xlocB]
        filtered_dfy = df[ext_column].iloc[xlocA:xlocB]
        
        # Apply percentage change filter
        y_pct_change = filtered_dfy.pct_change() * 100
        mask_pct = (y_pct_change.abs() <= percent) | (y_pct_change.isna())
        
        filtered_dfy = filtered_dfy[mask_pct]
        filtered_dfx = filtered_dfx[mask_pct]
        filtered_time = filtered_time[mask_pct]
        
        # Apply min/max filter
        mask_range = (filtered_dfy >= min_val) & (filtered_dfy <= max_val)
        filtered_dfx = filtered_dfx[mask_range]
        filtered_dfy = filtered_dfy[mask_range]
        filtered_time = filtered_time[mask_range]
        
        # Store filtered data
        self.filtered_x = filtered_dfx
        self.filtered_y = filtered_dfy
        self.filtered_time = filtered_time
        
        # Perform linear regression
        if len(filtered_dfx) > 1:
            from scipy.stats import linregress
            slope, intercept, r_value, p_value, std_err = linregress(filtered_dfx, filtered_dfy)
            self.store_results(slope, intercept, r_value, p_value, std_err, len(filtered_dfx))
            
            # Create regression plot
            import seaborn as sns
            sns.regplot(x=filtered_dfx, y=filtered_dfy, ax=self.ax1, 
                    marker='x', line_kws=dict(color='red'), scatter_kws={'alpha': 0.6})
            self.ax1.set_xlabel('Bscat (1/Mm)')
            self.ax1.set_ylabel(f'{ext_column}')
            self.ax1.set_title(f'Scattering Mode: {ext_column} vs Bscat')
            
            # Create time series plot
            self.ax2.scatter(filtered_time, filtered_dfy, alpha=0.6, color='blue', label='Filtered Data')
            self.ax2.set_xlabel('Time')
            self.ax2.set_ylabel(f'{ext_column}')
            self.ax2.set_title('Filtered Data Over Time')
            
        else:
            print(len(filtered_dfx))
            messagebox.showwarning("Warning", "Not enough data points after filtering!")

    def modified_analyze_absorbing_mode(self, df, xlocA, xlocB, min_val, max_val, percent):
        """
        Modified absorbing analysis that uses extinction coefficient if needed.
        Replace the analyze_absorbing_mode method in ModernCalibrationWindow.
        """
        
        try:
            # Determine which column to use for analysis
            if 'Debug Ext Calculation' in df.columns:
                ext_column = 'Debug Ext Calculation'
                print("📊 Using existing 'Debug Ext Calculation' column")
            elif 'Extinction_Coefficient' in df.columns:
                ext_column = 'Extinction_Coefficient'
                print("🔬 Using calculated 'Extinction_Coefficient' column")
            else:
                # Try to create extinction coefficient column automatically
                ext_column, is_calculated, i0_baseline = create_extinction_column_if_needed(self.gui)
                if is_calculated:
                    # Update the GUI listbox
                    update_listbox_with_new_column(self.gui, highlight_column=ext_column)
                    messagebox.showinfo("Column Created", 
                                    f"Created '{ext_column}' column for analysis\nI0 Baseline: {i0_baseline:.6f}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not determine extinction column: {str(e)}")
            return
        
        # Extract data for the specified range
        filtered_time = df['time'].iloc[xlocA:xlocB]
        filtered_dfx = df['Babs (1/Mm)'].iloc[xlocA:xlocB]
        
        # Calculate difference (extinction coefficient - Bscat)
        difference_dfy = (df[ext_column].iloc[xlocA:xlocB] - 
                        df['Bscat (1/Mm)'].iloc[xlocA:xlocB])
        
        # Apply percentage change filter
        y_pct_change = difference_dfy.pct_change() * 100
        mask_pct = (y_pct_change.abs() <= percent) | (y_pct_change.isna())
        
        filtered_dfy = difference_dfy[mask_pct]
        filtered_dfx = filtered_dfx[mask_pct]
        filtered_time = filtered_time[mask_pct]
        
        # Apply min/max filter
        mask_range = (filtered_dfy >= min_val) & (filtered_dfy <= max_val)
        filtered_dfx = filtered_dfx[mask_range]
        filtered_dfy = filtered_dfy[mask_range]
        filtered_time = filtered_time[mask_range]
        
        # Store filtered data
        self.filtered_x = filtered_dfx
        self.filtered_y = filtered_dfy
        self.filtered_time = filtered_time
        
        # Perform linear regression
        if len(filtered_dfx) > 1:
            from scipy.stats import linregress
            slope, intercept, r_value, p_value, std_err = linregress(filtered_dfx, filtered_dfy)
            self.store_results(slope, intercept, r_value, p_value, std_err, len(filtered_dfx))
            
            # Create regression plot
            import seaborn as sns
            sns.regplot(x=filtered_dfx, y=filtered_dfy, ax=self.ax1, 
                    marker='x', line_kws=dict(color='red'), scatter_kws={'alpha': 0.6})
            self.ax1.set_xlabel('Babs (1/Mm)')
            self.ax1.set_ylabel(f'{ext_column} - Scat Difference')
            self.ax1.set_title(f'Absorbing Mode: {ext_column} - Scat vs Babs')
            
            # Create time series plot
            self.ax2.scatter(filtered_time, filtered_dfy, alpha=0.6, color='green', label='Filtered Data')
            self.ax2.set_xlabel('Time')
            self.ax2.set_ylabel(f'{ext_column} - Scat Difference')
            self.ax2.set_title('Filtered Data Over Time')
            
        else:
            print(len(filtered_dfx))
            messagebox.showwarning("Warning", "Not enough data points after filtering!")    
    def store_results(self, slope, intercept, r_value, p_value, std_err, data_points):
        """Store analysis results"""
        self.analysis_results = {
            'slope': slope,
            'intercept': intercept,
            'r_value': r_value,
            'r2': r_value ** 2,
            'p_value': p_value,
            'std_err': std_err,
            'data_points': data_points
        }
        
        # Update result displays
        self.r2_value.config(text=f"{self.analysis_results['r2']:.4f}")
        self.slope_value.config(text=f"{slope:.4f}")
        self.intercept_value.config(text=f"{intercept:.4f}")
        self.p_value.config(text=f"{p_value:.4f}")
        self.std_error.config(text=f"{std_err:.4f}")
        self.data_points.config(text=f"{data_points}")
        
        # Update equation
        sign = "+" if intercept >= 0 else "-"
        equation = f"y = {slope:.4f}x {sign} {abs(intercept):.4f}"
        self.equation_label.config(text=equation)
        
    def finalize_plots(self):
        """Finalize plot formatting and refresh canvas"""
        
        # Format both axes
        for ax in [self.ax1, self.ax2]:
            ax.tick_params(axis='both', labelsize='small', labelrotation=20)
            ax.grid(True, alpha=0.3)
            
        # Format time axis for ax2
        if hasattr(self, 'filtered_time') and len(self.filtered_time) > 0:
            locator = mdates.AutoDateLocator()
            formatter = mdates.ConciseDateFormatter(locator)
            self.ax2.xaxis.set_major_locator(locator)
            self.ax2.xaxis.set_major_formatter(formatter)
            
        # Adjust layout and refresh
        self.fig.tight_layout()
        self.canvas.draw()
        
    def update_parameter_displays(self):
        """Update all parameter display values"""
        for attr_name in dir(self):
            if attr_name.startswith('param_'):
                param_info = getattr(self, attr_name)
                try:
                    value = param_info['func']()
                    param_info['label'].config(text=str(value))
                except:
                    param_info['label'].config(text="Error")
                    
    def export_results(self):
        """Export analysis results (placeholder for future implementation)"""
        if hasattr(self, 'analysis_results') and self.analysis_results:
            # Here you could implement CSV export, report generation, etc.
            messagebox.showinfo("Export", f"Results ready for export:\n\n"
                              f"R² = {self.analysis_results['r2']:.4f}\n"
                              f"Slope = {self.analysis_results['slope']:.4f}\n"
                              f"Data Points = {self.analysis_results['data_points']}")
        else:
            messagebox.showwarning("Warning", "No results to export. Run analysis first.")