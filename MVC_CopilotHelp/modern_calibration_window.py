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

from data_processing import create_extinction_column_if_needed, update_listbox_with_new_column, enhanced_calibration_analysis
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
        self.create_parameters_section_with_notes(scrollable_frame)
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
        
    def create_parameters_section_with_notes(self, parent=None):
        """
        Enhanced parameters section with notes area.
        """
        if parent is None:
            parent = self.calib_window
        
        params_frame = ttk.LabelFrame(
            parent, 
            text="📊 Analysis Parameters & Notes", 
            padding="15"
        )
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # Create main container with two columns
        main_container = tk.Frame(params_frame)
        main_container.pack(fill="x", expand=True)
        
        # Configure column weights for proper resizing
        main_container.columnconfigure(0, weight=2)  # Parameters get more space
        main_container.columnconfigure(1, weight=1)  # Notes get less space
        
        # LEFT SIDE: Parameters (existing functionality)
        params_left_frame = tk.Frame(main_container)
        params_left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Create parameter display in a grid
        params_grid = tk.Frame(params_left_frame)
        params_grid.pack(fill="x")
        
        # Parameters from GUI (same as before)
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
        
        # RIGHT SIDE: Notes section (NEW)
        self.create_notes_section(main_container)
        
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
                self.analyze_scattering_mode(df, xlocA, xlocB, min_val, max_val, percent)
            elif calib_mode == 'Absorbing':
                self.analyze_absorbing_mode(df, xlocA, xlocB, min_val, max_val, percent)
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
            
    def analyze_scattering_mode(self, df, xlocA, xlocB, min_val, max_val, percent):
        """
        Ultimate enhanced scattering mode analysis with both automatic column creation 
        and comprehensive debugging.
        """
        
        try:
            # STEP 1: Handle missing extinction column (from extinction coefficient implementation)
            if 'Debug Ext Calculation' in df.columns:
                ext_column = 'Debug Ext Calculation'
                print("📊 Using existing 'Debug Ext Calculation' column")
            elif 'Extinction_Coefficient' in df.columns:
                ext_column = 'Extinction_Coefficient'
                print("🔬 Using calculated 'Extinction_Coefficient' column")
            else:
                # Try to create extinction coefficient column automatically
                try:
                    from data_processing import create_extinction_column_if_needed, update_listbox_with_new_column
                    ext_column, is_calculated, i0_baseline = create_extinction_column_if_needed(self.gui)
                    if is_calculated:
                        # Update the GUI listbox
                        update_listbox_with_new_column(self.gui, highlight_column=ext_column)
                        messagebox.showinfo("Column Created", 
                                        f"Created '{ext_column}' column for analysis\nI0 Baseline: {i0_baseline:.6f}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not determine extinction column: {str(e)}")
                    return
            
            # STEP 2: Run enhanced analysis with debugging (from long-term solution)
            filtered_data, debug_info = enhanced_calibration_analysis(
                df, xlocA, xlocB, min_val, max_val, percent, mode='Scattering'
            )
            
            # STEP 3: Store results for access by other methods
            self.filtered_x = filtered_data['x']
            self.filtered_y = filtered_data['y'] 
            self.filtered_time = filtered_data['time']
            
            # STEP 4: Perform linear regression
            from scipy.stats import linregress
            slope, intercept, r_value, p_value, std_err = linregress(
                filtered_data['x'], filtered_data['y']
            )
            self.store_results(slope, intercept, r_value, p_value, std_err, filtered_data['count'])
            
            # STEP 5: Create plots
            import seaborn as sns
            sns.regplot(x=filtered_data['x'], y=filtered_data['y'], ax=self.ax1, 
                    marker='x', line_kws=dict(color='red'), scatter_kws={'alpha': 0.6})
            self.ax1.set_xlabel(filtered_data['x_column'])
            self.ax1.set_ylabel(filtered_data['y_column'])
            self.ax1.set_title(f'Scattering Mode: {filtered_data["count"]} points')
            
            # Time series plot
            self.ax2.scatter(filtered_data['time'], filtered_data['y'], alpha=0.6, color='blue')
            self.ax2.set_xlabel('Time')
            self.ax2.set_ylabel(filtered_data['y_column'])
            self.ax2.set_title('Filtered Data Over Time')
            
            # STEP 6: Show success message with debug info
            if debug_info['issues']:
                warning_msg = f"Analysis completed with {len(debug_info['issues'])} warning(s):\n"
                for issue in debug_info['issues'][:3]:  # Show first 3 issues
                    warning_msg += f"• {issue}\n"
                messagebox.showwarning("Analysis Warnings", warning_msg)
            
        except ValueError as e:
            # Show detailed error with recommendations
            error_msg = f"❌ Scattering Analysis Failed:\n\n{str(e)}\n\n"
            
            if 'debug_info' in locals() and debug_info['recommendations']:
                error_msg += "💡 Recommendations:\n"
                for rec in debug_info['recommendations'][:3]:
                    error_msg += f"• {rec}\n"
            
            messagebox.showerror("Scattering Analysis Error", error_msg)
            
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"Unexpected error in scattering analysis:\n{str(e)}")

    def analyze_absorbing_mode(self, df, xlocA, xlocB, min_val, max_val, percent):
        """
        Ultimate enhanced absorbing mode analysis with both automatic column creation 
        and comprehensive debugging.
        """
        
        try:
            # STEP 1: Handle missing extinction column
            if 'Debug Ext Calculation' in df.columns:
                ext_column = 'Debug Ext Calculation'
                print("📊 Using existing 'Debug Ext Calculation' column")
            elif 'Extinction_Coefficient' in df.columns:
                ext_column = 'Extinction_Coefficient'
                print("🔬 Using calculated 'Extinction_Coefficient' column")
            else:
                # Try to create extinction coefficient column automatically
                try:
                    from data_processing import create_extinction_column_if_needed, update_listbox_with_new_column
                    ext_column, is_calculated, i0_baseline = create_extinction_column_if_needed(self.gui)
                    if is_calculated:
                        # Update the GUI listbox
                        update_listbox_with_new_column(self.gui, highlight_column=ext_column)
                        messagebox.showinfo("Column Created", 
                                        f"Created '{ext_column}' column for analysis\nI0 Baseline: {i0_baseline:.6f}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not determine extinction column: {str(e)}")
                    return
            
            # STEP 2: Run enhanced analysis with debugging
            filtered_data, debug_info = enhanced_calibration_analysis(
                df, xlocA, xlocB, min_val, max_val, percent, mode='Absorbing'
            )
            
            # STEP 3: Store results
            self.filtered_x = filtered_data['x']
            self.filtered_y = filtered_data['y']
            self.filtered_time = filtered_data['time']
            
            # STEP 4: Perform linear regression
            from scipy.stats import linregress
            slope, intercept, r_value, p_value, std_err = linregress(
                filtered_data['x'], filtered_data['y']
            )
            self.store_results(slope, intercept, r_value, p_value, std_err, filtered_data['count'])
            
            # STEP 5: Create plots  
            import seaborn as sns
            sns.regplot(x=filtered_data['x'], y=filtered_data['y'], ax=self.ax1,
                    marker='x', line_kws=dict(color='red'), scatter_kws={'alpha': 0.6})
            self.ax1.set_xlabel(filtered_data['x_column'])
            self.ax1.set_ylabel(filtered_data['y_column'])
            self.ax1.set_title(f'Absorbing Mode: {filtered_data["count"]} points')
            
            # Time series plot
            self.ax2.scatter(filtered_data['time'], filtered_data['y'], alpha=0.6, color='green')
            self.ax2.set_xlabel('Time')
            self.ax2.set_ylabel(filtered_data['y_column'])
            self.ax2.set_title('Filtered Data Over Time')
            
            # STEP 6: Show success message with debug info
            if debug_info['issues']:
                warning_msg = f"Analysis completed with {len(debug_info['issues'])} warning(s):\n"
                for issue in debug_info['issues'][:3]:
                    warning_msg += f"• {issue}\n"
                messagebox.showwarning("Analysis Warnings", warning_msg)
            
        except ValueError as e:
            # Show detailed error with recommendations
            error_msg = f"❌ Absorbing Analysis Failed:\n\n{str(e)}\n\n"
            
            if 'debug_info' in locals() and debug_info['recommendations']:
                error_msg += "💡 Recommendations:\n"
                for rec in debug_info['recommendations'][:3]:
                    error_msg += f"• {rec}\n"
            
            messagebox.showerror("Absorbing Analysis Error", error_msg)
            
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"Unexpected error in absorbing analysis:\n{str(e)}")

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
    def create_notes_section(self, parent):
        """
        Create the notes section with text area and controls.
        """
        notes_frame = ttk.LabelFrame(parent, text="📝 Analysis Notes", padding="10")
        notes_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Configure the notes frame to expand
        notes_frame.rowconfigure(1, weight=1)
        notes_frame.columnconfigure(0, weight=1)
        
        # Notes header with timestamp
        header_frame = tk.Frame(notes_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        notes_label = tk.Label(
            header_frame, 
            text="Custom Notes:", 
            font=("Arial", 9, "bold"), 
            fg="#2c3e50"
        )
        notes_label.pack(side="left")
        
        # Timestamp label
        self.notes_timestamp = tk.Label(
            header_frame, 
            text="", 
            font=("Arial", 8), 
            fg="#7f8c8d"
        )
        self.notes_timestamp.pack(side="right")
        
        # Text area with scrollbar
        text_frame = tk.Frame(notes_frame)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 5))
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        
        # Text widget
        self.notes_text = tk.Text(
            text_frame,
            width=30,
            height=8,
            wrap='word',
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#2c3e50",
            relief="sunken",
            bd=1
        )
        self.notes_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for text area
        notes_scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=self.notes_text.yview)
        notes_scrollbar.grid(row=0, column=1, sticky="ns")
        self.notes_text.config(yscrollcommand=notes_scrollbar.set)
        
        # Button frame
        button_frame = tk.Frame(notes_frame)
        button_frame.grid(row=2, column=0, sticky="ew")
        
        # Save button
        save_btn = tk.Button(
            button_frame,
            text="💾 Save Notes",
            command=self.save_notes,
            bg="#27ae60",
            fg="white",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=15,
            pady=5
        )
        save_btn.pack(side="left", padx=(0, 5))
        
        # Load button
        load_btn = tk.Button(
            button_frame,
            text="📂 Load Notes",
            command=self.load_notes,
            bg="#3498db",
            fg="white",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=15,
            pady=5
        )
        load_btn.pack(side="left", padx=(0, 5))
        
        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="🗑️ Clear",
            command=self.clear_notes,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=15,
            pady=5
        )
        clear_btn.pack(side="right")
        
        # Auto-save binding
        self.notes_text.bind('<KeyRelease>', self.on_notes_changed)
        

    def save_notes(self):
        """
        Save notes to a file with timestamp and analysis parameters.
        """
        try:
            from datetime import datetime
            import os
            
            # Get notes content
            notes_content = self.notes_text.get("1.0", "end-1c")
            
            if not notes_content.strip():
                messagebox.showinfo("Save Notes", "No notes to save.")
                return
            
            # Create notes directory if it doesn't exist
            notes_dir = "calibration_notes"
            if not os.path.exists(notes_dir):
                os.makedirs(notes_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"calibration_notes_{timestamp}.txt"
            filepath = os.path.join(notes_dir, filename)
            
            # Prepare content with metadata
            metadata = self.get_analysis_metadata()
            
            full_content = f"""PAX Calibration Analysis Notes
    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    {'='*50}

    ANALYSIS PARAMETERS:
    {metadata}

    CUSTOM NOTES:
    {notes_content}
    """
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            # Update timestamp display
            self.notes_timestamp.config(text=f"Saved: {datetime.now().strftime('%H:%M:%S')}")
            
            messagebox.showinfo("Notes Saved", f"Notes saved to:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving notes: {str(e)}")

    def load_notes(self):
        """
        Load notes from a file.
        """
        try:
            from tkinter import filedialog
            import os
            
            # Set initial directory to notes folder if it exists
            initial_dir = "calibration_notes" if os.path.exists("calibration_notes") else "."
            
            filepath = filedialog.askopenfilename(
                title="Load Calibration Notes",
                initialdir=initial_dir,
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if filepath:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract just the notes section if it's a full metadata file
                if "CUSTOM NOTES:" in content:
                    notes_start = content.find("CUSTOM NOTES:") + len("CUSTOM NOTES:")
                    notes_content = content[notes_start:].strip()
                else:
                    notes_content = content
                
                # Load into text widget
                self.notes_text.delete("1.0", "end")
                self.notes_text.insert("1.0", notes_content)
                
                # Update timestamp
                from datetime import datetime
                self.notes_timestamp.config(text=f"Loaded: {datetime.now().strftime('%H:%M:%S')}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading notes: {str(e)}")

    def clear_notes(self):
        """
        Clear the notes text area.
        """
        if self.notes_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno("Clear Notes", "Are you sure you want to clear all notes?"):
                self.notes_text.delete("1.0", "end")
                self.notes_timestamp.config(text="")

    def on_notes_changed(self, event=None):
        """
        Handle notes text changes (for auto-save indication).
        """
        from datetime import datetime
        self.notes_timestamp.config(text=f"Modified: {datetime.now().strftime('%H:%M:%S')}")

    def get_analysis_metadata(self):
        """
        Get current analysis parameters as formatted text.
        """
        try:
            metadata = f"""Mode: {self.gui.calibvar.get()}
    Min Value: {self.gui.entry_min.get()}
    Max Value: {self.gui.entry_max.get()}
    % Change Limit: {self.gui.entry_percent.get()}%
    Calibration Start: {int(self.gui.current_valueCalibLow.get())}
    Calibration End: {int(self.gui.current_valueCalibHigh.get())}
    Total Data Points: {len(self.constants.df_main) if not self.constants.df_main.empty else 0}
    Time Range: {self.get_time_range_text()}"""

            # Add results if available
            if hasattr(self, 'analysis_results') and self.analysis_results:
                metadata += f"""

    ANALYSIS RESULTS:
    R² Value: {self.analysis_results['r2']:.4f}
    Slope: {self.analysis_results['slope']:.4f}
    Intercept: {self.analysis_results['intercept']:.4f}
    P-Value: {self.analysis_results['p_value']:.4f}
    Data Points: {self.analysis_results['data_points']}"""
            
            return metadata
            
        except Exception as e:
            return f"Error generating metadata: {str(e)}"