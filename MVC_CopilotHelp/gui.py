import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import seaborn as sns
import matplotlib.dates as mdates
from PIL import ImageTk, Image
import os
import sys

#This should import the constants from the constants.py file in the same directory, and anything else needed
from constants import *
# Import specific functions instead of * for better control
from data_processing import (
    load_multiple_files, 
    process_multiple_files_automatically, 
    get_file_info_summary,
    load_file,  # Legacy
    pax_analyzer,  # Legacy
    concatenate_df,  # Legacy
    simple_listbox_load,
    process_paxtxt,
    clear_df,
    clearNaN,
    update_df_main,
    update_df_to_add,
    pax_analyzer_flexible
)
from controller import resource_path, alarm_translate, writeToLog
from plotting import *
from modern_calibration_window import ModernCalibrationWindow

#One class handles the main viewing window, and calls it root for reference; can be passed main application window
class PAXView:
    def __init__(self, root):
        self.root = root
        #TODO: Make the title a constant?
        self.root.title("PAX Data Visualizer - Plotting in TKinter")
        #Get the screen size and set the window size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        #This should set the window size to ~80% of the screen size by default, but pull the pct from the constants file
        self.root.geometry(str(int(screen_width*geometry_width_pct))+"x"+str(int(screen_height*geometry_height_pct)))

        #Topleft (TL) frame for file loading and radio buttons

        # Create enhanced top-left frame with multi-file capabilities
        self.create_enhanced_topleft_frame(root)

        # self.df = pd.DataFrame()  # Initialize df to empty DataFrame; commented out to avoid confusion with the global df in constants.py
        
        
        #===Legacy code for the top left frame===
        # self.analyze_button = tk.Button(self.frame_TL, text="Analyze PAX data", 
        #                                 command=lambda: pax_analyzer(self.file_path.get(), self.selected, self.listbox, self), 
        #                                 bg='light green')
        # self.analyze_button.grid(row=2, column=0, columnspan=3)
        
        # self.radio_version = tk.Radiobutton(self.frame_TL, text="(optional) Load Pax.txt", value="V3", variable=self.selected)
        # self.radio_version.grid(row=4, column=0)
        # #Currently, the version handling is not very advanced, and the processing/concatenating functions are finicky. See readme for more details
        # self.add_version_button = tk.Button(self.frame_TL, text="Process Pax.txt", command=lambda: process_paxtxt(self.file_path.get(),self.version_var), bg='light blue')
        # self.add_version_button.grid(row=4, column=1, columnspan=1)
        # self.concatenate_button = tk.Button(self.frame_TL, text="Concatenate Loaded Data", command=lambda: concatenate_df(self.file_path.get(), self.selected, self.listbox), bg='light blue')
        # self.concatenate_button.grid(row=3, column=0, columnspan=3)
        # self.load_concatenated_button = tk.Button(self.frame_TL, text="Load Concatenated Data", command=lambda: simple_listbox_load(self.listbox), bg='light blue')
        # self.load_concatenated_button.grid(row=5, column=0, columnspan=3)
        # self.clear_df_button = tk.Button(self.frame_TL, text="Clear DataFrame", command=lambda: clear_df(), bg='light blue')
        # self.clear_df_button.grid(row=6, column=0, columnspan=3)

        #TC
        self.frame_TC = tk.Frame(root)
        #Creates a text box for the log window
        self.log = tk.Text(self.frame_TC, state='disabled', width=70, height=5, wrap='char')
        self.log.grid(row=0, column=0)
        self.frame_TC.grid(row=0, column=3)

        #TR
        self.frame_TR = tk.Frame(root)
        #An optional logo image; an easy add or remove, but be careful to set the path correctly, especially if using pyinstaller
        self.myImgLogo = Image.open(resource_path(logo_name))
        self.myImgLogo = ImageTk.PhotoImage(self.myImgLogo)
        self.image_label = tk.Label(self.frame_TR, image=self.myImgLogo)
        self.image_label.pack()
        self.frame_TR.grid(row=0, column=5)


        #The middle center (MC) frame for the plot
        self.frame_MC = tk.Frame(root)
        self.frame_MC.grid(row=2, column=3)
        # Embed the figure in a Tkinter frame
        self.main_plot = FigureCreate()
        self.main_axes = AxesCreate(self.main_plot.get_figure())
        self.canvas = FigureCanvasTkAgg(self.main_plot.get_figure(), master=self.frame_MC)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self.ax = self.main_axes.get_axes()

        #The Middle Right (MR) frame for the calibration options (this will be a collapsible frame)
        self.container_MR = CollapsibleFrame(root, title="Calibration Options")
        self.container_MR.grid(row=2, column=5)
        self.frame_MR = ttk.Labelframe(self.container_MR.sub_frame, text='Important Numbers and Calibration Settings:')
        self.frame_MR.grid(row=0, column=0, sticky="nsew")  # Ensure it is gridded into the sub_frame

        self.sMR = ttk.Separator(self.frame_MR, orient='vertical').grid(column=1,rowspan=9,sticky="ns")

        #Large section below to set up the calibration range selection, and the sliders for the I0 selection
        self.calibvar = tk.StringVar()
        self.calibration_select = ttk.Combobox(self.frame_MR, textvariable=self.calibvar)
        self.calibration_select['values'] = ('Scattering','Absorbing','Neither')
        self.calibration_select.set('Scattering') # Set default value
        self.calibration_select.grid(row = 0, column = 0)

        #Min, max, and percent change entry boxes for the calibration region
        self.label_min = ttk.Label(self.frame_MR, text = "Min:")
        self.label_min.grid(row = 1, column = 0)
        self.label_max = ttk.Label(self.frame_MR, text = "Max:")
        self.label_max.grid(row = 2, column = 0)
        self.label_percent = ttk.Label(self.frame_MR, text = "Pct change:")
        self.label_percent.grid(row = 3, column = 0)      

        #Labels for the min, max, and percent change entry boxes
        self.entry_min = tk.Entry(self.frame_MR, width = 20)
        self.entry_min.grid(row = 1, column = 2)
        self.entry_max = tk.Entry(self.frame_MR, width = 20)
        self.entry_max.grid(row = 2, column = 2)
        self.entry_percent = tk.Entry(self.frame_MR, width = 20)
        self.entry_percent.grid(row = 3, column = 2)

        #Main button to generate the calibration frame; this will call the function to generate the calibration frame
        self.calibStarter = tk.Button(self.frame_MR, 
            text = "Generate calibration frame", 
            command = lambda: create_modern_calibration_window(self.root, self, constants), bg = 'light blue')
        self.calibStarter.grid(row = 4, column = 2)

        # Beginning of I0 slider logic
        self.label_spanI0 = tk.Label(self.frame_MR, text="I0 selection:")
        self.label_spanI0.grid(row=5, column=0)

        # I0 Low Slider
        self.current_valueI0Low = tk.DoubleVar()
        self.current_valueI0Low.set(0)  # Set initial value
        
        self.slider_I0Low = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,  # Will be updated when data is loaded
            orient='horizontal',
            variable=self.current_valueI0Low,
            command=lambda event: slider_changed(
                event, 
                constants.df_main,
                self.label_sliderI0Low,
                self.update_plot_from_sliders
            )
        )
        self.slider_I0Low.grid(row=6, column=0)

        # I0 High Slider
        self.current_valueI0High = tk.DoubleVar()
        self.current_valueI0High.set(100)  # Set initial value
        
        self.slider_I0High = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,  # Will be updated when data is loaded
            orient='horizontal',
            variable=self.current_valueI0High,
            command=lambda event: slider_changed(
                event, 
                constants.df_main,
                self.label_sliderI0High,
                self.update_plot_from_sliders
            )
        )
        self.slider_I0High.grid(row=7, column=0)

        # I0 Slider Labels
        self.label_sliderI0Low = tk.Label(self.frame_MR, text="I0 Low: Not set", fg='green')
        self.label_sliderI0Low.grid(row=6, column=2)
        self.label_sliderI0High = tk.Label(self.frame_MR, text="I0 High: Not set", fg='green')
        self.label_sliderI0High.grid(row=7, column=2)

        # Calibration region selection
        self.label_spanCalib = tk.Label(self.frame_MR, text="Calib. Region:")
        self.label_spanCalib.grid(row=8, column=0)

        # Calibration Low Slider
        self.current_valueCalibLow = tk.DoubleVar()
        self.current_valueCalibLow.set(200)  # Set initial value
        
        self.slider_CalibLow = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,  # Will be updated when data is loaded
            orient='horizontal',
            variable=self.current_valueCalibLow,
            command=lambda event: slider_changed(
                event, 
                constants.df_main,
                self.label_sliderCalibLow,
                self.update_plot_from_sliders
            )
        )
        self.slider_CalibLow.grid(row=9, column=0)

        # Calibration High Slider
        self.current_valueCalibHigh = tk.DoubleVar()
        self.current_valueCalibHigh.set(300)  # Set initial value
        
        self.slider_CalibHigh = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,  # Will be updated when data is loaded
            orient='horizontal',
            variable=self.current_valueCalibHigh,
            command=lambda event: slider_changed(
                event, 
                constants.df_main,
                self.label_sliderCalibHigh,
                self.update_plot_from_sliders
            )
        )
        self.slider_CalibHigh.grid(row=10, column=0)

        # Calibration Slider Labels
        self.label_sliderCalibLow = tk.Label(self.frame_MR, text="Calib Low: Not set", fg='green')
        self.label_sliderCalibLow.grid(row=9, column=2)
        self.label_sliderCalibHigh = tk.Label(self.frame_MR, text="Calib High: Not set", fg='green')
        self.label_sliderCalibHigh.grid(row=10, column=2)


        #The text box for the alarm translation; this will be used to translate the alarm codes into the corresponding messages
        self.alarmTextbox = ttk.Entry(self.frame_MR)
        self.alarmTextbox.grid(row = 12, column = 0)

        self.translateButton = tk.Button(self.frame_MR, 
             text = "Translate Alarm", 
             command = lambda: alarm_translate(self.alarmTextbox.get(), alarm_names, self.log), bg = 'light blue')
        self.translateButton.grid(row = 12, column = 2)



        #The bottom left (BL) frame for the quit and clear buttons, and any other functional buttons
        self.frame_BL = tk.Frame(root)
        self.button_quit = tk.Button(self.frame_BL, text="Quit", command=self.quit_app, bg='#FF2222')
        self.button_clear = tk.Button(self.frame_BL, text="Clear Selection", command = lambda: self.listbox.selection_clear(0,'end'), bg='light green')
        self.testTextButton = tk.Button(self.frame_BL, text="Display filename", command = lambda: writeToLog(self.file_path.get(),self.log), width=15, bg='light yellow')
        self.frame_BL.grid(row=4, column=0)
        self.button_quit.grid(row=2, column=0)
        self.button_clear.grid(row=0, column=0)
        self.testTextButton.grid(row=1, column=0)
        # Subplot toggle controls
        self.subplot_mode = tk.BooleanVar()
        self.subplot_mode.set(True)  # Default to multi axis mode
        
        #Moved to bottom-middle for better layout
        self.frame_BM = tk.Frame(root)
        self.frame_BM.grid(row=4, column=3)
        self.subplot_checkbox = tk.Checkbutton(
            self.frame_BM, 
            text="Use Subplots", 
            variable=self.subplot_mode,
            command=self.on_subplot_toggle
        )
        self.subplot_checkbox.grid(row=3, column=0, sticky='w')
        
        # Optional: Add a label to show current mode
        self.plot_mode_label = tk.Label(self.frame_BM, text="Mode: Subplots (max 4)", fg='blue', font=('Arial', 8))
        self.plot_mode_label.grid(row=2, column=0, sticky='w')


        #The bottom middle (BM) frame for the big 5 and 4x plots
        #Commented out for now, as these are redundant with the new plotting system
        # self.frame_BM = tk.Frame(root)
        # self.button_big5 = tk.Button(self.frame_BM, text="Plot Big 5", command=lambda: plot_big5(constants.df_main, self.root), bg='light blue')
        # self.button_big5.grid(row=0, column=0)
        # self.frame_BM.grid(row=4, column=3)
        # self.button_4x = tk.Button(self.frame_BM, text="Plot 4x", command=lambda: plot_4x(constants.df_main, self.root), bg='light blue')
        # self.button_4x.grid(row=1, column=0)

        #The bottom right (BR) frame for the progress bar and version info
        self.frame_BR = tk.Frame(root)
        self.frame_BR.grid(row=4, column=5)

        # Commented out the version label for now, as it is not implemented yet
        # #TODO: Set up the version text to be a label that updates with the version of the program
        # self.version_var = tk.StringVar()
        # self.version_var.set("Version Unknown")
        # self.label_version = tk.Label(self.frame_BR, textvariable=self.version_var, fg='blue')
        # self.label_version.grid(row=1, column=0)

        self.pb = ttk.Progressbar(self.frame_BR, orient="horizontal", length=200, mode="determinate")
        self.pb.grid(row=0, column=0)

        #The frame for the listbox of columns; this will be the left side of the window
        self.list_frame = tk.Frame(root)
        self.listbox = tk.Listbox(self.list_frame, selectmode='multiple',height=30, width=30)
        self.listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        self.scrollbar = tk.Scrollbar(self.list_frame, orient="vertical")
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.list_frame.grid(row=2, column=0, padx= 5, pady=5, sticky='nsew')
        self.listbox.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")

    def create_enhanced_topleft_frame(self, root):
        """
        Enhanced version of the top-left frame with multi-file loading capabilities.
        """
        # Topleft (TL) frame for file loading and radio buttons
        self.frame_TL = tk.Frame(root)
        self.selected = tk.StringVar() # Variable to hold the selected file type
        self.selected.set("V2") # Default to .xlsx
        self.file_path = tk.StringVar()
        self.file_path.set("")
        
        # Radio buttons for file type selection
        self.radio_csv = tk.Radiobutton(self.frame_TL, text="CSV files", value="V1", variable=self.selected)
        self.radio_xlsx = tk.Radiobutton(self.frame_TL, text="Excel files", value="V2", variable=self.selected)
        # self.radio_paxtxt = tk.Radiobutton(self.frame_TL, text="PAX.txt files", value="V3", variable=self.selected)
        
        # Enhanced file loading buttons
        self.load_single_button = tk.Button(
            self.frame_TL, 
            text="📁 Load Single File", 
            command=self.load_single_file_legacy,
            width=25, 
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        
        self.load_multiple_button = tk.Button(
            self.frame_TL, 
            text="📂 Load Multiple Files", 
            command=self.load_and_process_multiple_files,
            width=25, 
            bg='#27ae60',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        
        # Analysis button
        self.analyze_button = tk.Button(
            self.frame_TL, 
            text="🔍 Analyze Data", 
            command=self.analyze_current_data,
            width=25,
            bg='#f39c12',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        
        # Data info button
        self.data_info_button = tk.Button(
            self.frame_TL,
            text="ℹ️ Data Summary",
            command=self.show_data_summary,
            width=25,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        
        # Legacy buttons (for compatibility)
        self.concatenate_button = tk.Button(
            self.frame_TL, 
            text="Concatenate Single File", 
            command=lambda: concatenate_df(self.file_path.get(), self.selected, self.listbox), 
            bg='#95a5a6',
            font=('Arial', 8)
        )
        
        self.load_concatenated_button = tk.Button(
            self.frame_TL, 
            text="Reload Listbox", 
            command=lambda: simple_listbox_load(self.listbox), 
            bg='#95a5a6',
            font=('Arial', 8)
        )
        
        self.clear_df_button = tk.Button(
            self.frame_TL, 
            text="Clear All Data", 
            command=self.clear_all_data, 
            bg='#e74c3c',
            fg='white',
            font=('Arial', 8, 'bold')
        )
        
        # Layout the components
        # self.load_single_button.grid(row=0, column=0, columnspan=3, pady=2, padx=2, sticky='ew') #Commented out to avoid confusion with the new multi-file button
        self.load_multiple_button.grid(row=0, column=0, columnspan=3, pady=2, padx=2, sticky='ew')
        
        self.radio_csv.grid(row=1, column=0, sticky='w')
        self.radio_xlsx.grid(row=1, column=1, sticky='w')
        # self.radio_paxtxt.grid(row=1, column=2, sticky='w')
        
        #Commented out the single file analyze button to avoid confusion with the new multi-file button
        # self.analyze_button.grid(row=2, column=0, columnspan=3, pady=2, padx=2, sticky='ew')
        self.data_info_button.grid(row=2, column=0, columnspan=3, pady=2, padx=2, sticky='ew')
        
        # # NEW: Extinction coefficient button
        #Commented out for now as the column creation happens automatically in the new system
        # self.create_extinction_button = tk.Button(
        #     self.frame_TL,
        #     text="🔬 Create Extinction Column",
        #     command=self.create_extinction_column_manually,
        #     width=25,
        #     bg='#e67e22',
        #     fg='white',
        #     font=('Arial', 9, 'bold')
        # )
        # self.create_extinction_button.grid(row=3, column=0, columnspan=3, pady=2, padx=2, sticky='ew')


        #Unused legacy buttons commented out for now, but can be uncommented if needed
        # # Separator
        # separator = ttk.Separator(self.frame_TL, orient='horizontal')
        # separator.grid(row=5, column=0, columnspan=3, sticky='ew', pady=5)
        
        # # Legacy functions (smaller buttons)
        # legacy_label = tk.Label(self.frame_TL, text="Legacy Functions:", font=('Arial', 8, 'italic'))
        # legacy_label.grid(row=6, column=0, columnspan=3)
        
        # self.concatenate_button.grid(row=7, column=0, columnspan=3, pady=1, padx=2, sticky='ew')
        # self.load_concatenated_button.grid(row=8, column=0, columnspan=3, pady=1, padx=2, sticky='ew')
        # self.clear_df_button.grid(row=9, column=0, columnspan=3, pady=2, padx=2, sticky='ew')
        
        # Process PAX.txt button (if needed)
        # Commented out for cleanliness as it is not currently used
        # self.add_version_button = tk.Button(
        #     self.frame_TL, 
        #     text="Process Pax.txt", 
        #     command=lambda: process_paxtxt(self.file_path.get(), self.version_var), 
        #     bg='#95a5a6',
        #     font=('Arial', 8)
        # )
        # self.add_version_button.grid(row=10, column=0, columnspan=3, pady=1, padx=2, sticky='ew')
        
        self.frame_TL.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

    def load_single_file_legacy(self):
        """Load a single file using the legacy method."""
        load_file(self.selected, self.file_path, self.pb)

    def load_and_process_multiple_files(self):
        """Load multiple files and automatically process and concatenate them."""
        try:
            # Load multiple files
            file_paths = load_multiple_files(self.selected, self.file_path, self.pb)
            
            if file_paths:
                # Automatically process and concatenate the files
                process_multiple_files_automatically_flexible(
                    file_paths, 
                    self.selected, 
                    self.listbox, 
                    gui_instance=self,
                    pb=self.pb
                )
                
                # Log the operation
                writeToLog(f"Loaded and processed {len(file_paths)} files successfully", self.log)
                
            else:
                writeToLog("No files selected for multi-file loading", self.log)
                
        except Exception as e:
            messagebox.showerror("Multi-File Loading Error", f"Error during multi-file loading: {str(e)}")
            writeToLog(f"Error in multi-file loading: {str(e)}", self.log)

    def analyze_current_data(self):
        """Analyze the currently loaded data (works for both single and multi-file data)."""
        if constants.df_main.empty:
            messagebox.showwarning("No Data", "Please load data files first!")
            return
        
        try:
            # Refresh the listbox
            simple_listbox_load(self.listbox)
            
            # Update slider ranges
            self.update_slider_ranges_after_load()
            
            # Show success message
            row_count = len(constants.df_main)
            if 'source_file' in constants.df_main.columns:
                file_count = constants.df_main['source_file'].nunique()
                message = f"Analysis complete!\n\nData loaded: {row_count:,} rows from {file_count} file(s)"
            else:
                message = f"Analysis complete!\n\nData loaded: {row_count:,} rows"
            
            messagebox.showinfo("Analysis Complete", message)
            writeToLog(f"Data analysis complete: {row_count:,} rows", self.log)
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error during data analysis: {str(e)}")
            writeToLog(f"Analysis error: {str(e)}", self.log)

    def show_data_summary(self):
        """Show a detailed summary of the currently loaded data."""
        if constants.df_main.empty:
            messagebox.showinfo("Data Summary", "No data currently loaded.")
            return
        
        try:
            file_info = get_file_info_summary()
            
            # Build summary message
            summary = "📊 Data Summary\n" + "="*40 + "\n\n"
            
            if isinstance(file_info.get("total_files"), int):
                summary += f"📁 Source files: {file_info['total_files']}\n"
                summary += f"📈 Total rows: {file_info['total_rows']:,}\n\n"
                
                if file_info['files_detail']:
                    summary += "📋 Rows per file:\n"
                    for filename, count in file_info['files_detail'].items():
                        summary += f"  • {filename}: {count:,} rows\n"
                    summary += "\n"
                
                if file_info['time_range']['start'] and file_info['time_range']['end']:
                    summary += f"⏰ Time range:\n"
                    summary += f"  Start: {file_info['time_range']['start']}\n"
                    summary += f"  End: {file_info['time_range']['end']}\n"
            else:
                summary += f"📈 Total rows: {file_info['total_rows']:,}\n"
                summary += f"📁 Source: {file_info['total_files']}\n"
            
            # Show columns info
            excluded_cols = ['Alarm', 'time', 'source_file']
            data_columns = [col for col in constants.df_main.columns if col not in excluded_cols]
            summary += f"\n📊 Data columns: {len(data_columns)}\n"
            
            messagebox.showinfo("Data Summary", summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating data summary: {str(e)}")

    def clear_all_data(self):
        """Clear all loaded data with confirmation."""
        if constants.df_main.empty:
            messagebox.showinfo("Clear Data", "No data to clear.")
            return
        
        if messagebox.askyesno("Clear Data", "Are you sure you want to clear all loaded data?\n\nThis action cannot be undone."):
            clear_df()
            self.listbox.delete(0, 'end')
            self.file_path.set("")
            writeToLog("All data cleared", self.log)
            messagebox.showinfo("Data Cleared", "All data has been cleared successfully.")


    def quit_app(self):
        if messagebox.askyesno("Quit Dialog", "Are you sure you want to quit the app?"):
                  self.root.destroy()

    def plot(self, df, x_column, y_column):
        fig = Figure(figsize=(5,5))
        ax = fig.add_subplot(111)
        sns.lineplot(data=df, x=x_column, y=y_column, ax=ax)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
        canvas = FigureCanvasTkAgg(fig, master=self.frame_MC)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0)
        toolbar = NavigationToolbar2Tk(canvas, self.frame_MC, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=1, column=0)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
        #TODO: Figure out if this is needed, or if it is just a remnant of the old code
    
    def mainloop(self):
        self.root.mainloop()

    def update_slider_ranges_after_load(self):
        """
        Call this after loading data to update slider ranges.
        """
        if not constants.df_main.empty:
            max_index = len(constants.df_main) - 1
            
            # Update all slider ranges
            self.slider_I0Low.config(to=max_index)
            self.slider_I0High.config(to=max_index)
            self.slider_CalibLow.config(to=max_index)
            self.slider_CalibHigh.config(to=max_index)
            
            # Set reasonable default values
            quarter = max_index // 4
            self.current_valueI0Low.set(quarter)
            self.current_valueI0High.set(quarter * 2)
            self.current_valueCalibLow.set(quarter * 2.5)
            self.current_valueCalibHigh.set(quarter * 3)
            
            # Update labels immediately
            self.update_plot_from_sliders()

    def on_subplot_toggle(self):
        """
        Handle subplot mode toggle.
        """
        if self.subplot_mode.get():
            self.plot_mode_label.config(text="Mode: Subplots (max 4)")
        else:
            self.plot_mode_label.config(text="Mode: Single Axis")
        
        # Refresh the plot with new mode
        self.update_plot_from_sliders()

    def update_plot_from_sliders(self):
        """
        REPLACE existing update_plot_from_sliders method with this enhanced version.
        """
        if constants.df_main.empty or not self.listbox.curselection():
            return
        
        # Get current slider values as indices
        i0_low = int(self.current_valueI0Low.get())
        i0_high = int(self.current_valueI0High.get())
        calib_low = int(self.current_valueCalibLow.get())
        calib_high = int(self.current_valueCalibHigh.get())
        
        # Use the new subplot-aware plotting function
        plot_data_subplots(
            constants.df_main,
            self.listbox.curselection(),
            self.main_plot.get_figure(),
            self.subplot_mode.get(),  # Pass the subplot mode
            i0_low,
            i0_high,
            calib_low,
            calib_high
        )
        
        # Redraw the canvas
        self.canvas.draw()

    def on_listbox_select(self, event):
        """
        REPLACE existing on_listbox_select method with this enhanced version.
        """
        if constants.df_main.empty or not self.listbox.curselection():
            messagebox.showerror("Error", "No data to plot or no selection made")
            return
        
        # Update the plot mode label based on selection count
        selection_count = len(self.listbox.curselection())
        if self.subplot_mode.get() and selection_count > 1:
            shown_plots = min(selection_count, 4)
            self.plot_mode_label.config(text=f"Mode: Subplots ({shown_plots} of {selection_count} shown)")
        elif self.subplot_mode.get():
            self.plot_mode_label.config(text="Mode: Single Plot")
        else:
            self.plot_mode_label.config(text=f"Mode: Single Axis ({selection_count} traces)")
        
        self.update_plot_from_sliders()

    def create_extinction_column_manually(self):
        """
        Manually create an extinction coefficient column for calibration analysis.
        """
        if constants.df_main.empty:
            messagebox.showwarning("No Data", "Please load data files first!")
            return
        
        try:
            # Check if extinction column already exists
            if 'Extinction_Coefficient' in constants.df_main.columns:
                overwrite = messagebox.askyesno(
                    "Column Exists", 
                    "Extinction_Coefficient column already exists.\n\nDo you want to recalculate it?"
                )
                if not overwrite:
                    return
            
            # Get current I0 slider values
            i0_low = int(self.current_valueI0Low.get())
            i0_high = int(self.current_valueI0High.get())
            
            # Validate I0 region
            if i0_low >= i0_high:
                messagebox.showerror("Invalid I0 Region", 
                                f"I0 Low ({i0_low}) must be less than I0 High ({i0_high})")
                return
            
            if i0_high - i0_low < 10:
                messagebox.showwarning("Small I0 Region", 
                                    f"I0 region only has {i0_high - i0_low} points. Consider using a larger region for better baseline calculation.")
            
            # Create the extinction coefficient column
            constants.df_main, i0_baseline = calculate_extinction_coefficient(
                constants.df_main, 
                i0_low, 
                i0_high,
                calculated_column_name='Extinction_Coefficient'
            )
            
            # Update the listbox and highlight the new column
            update_listbox_with_new_column(self, highlight_column='Extinction_Coefficient')
            
            # Show success message
            success_msg = (
                f"✅ Extinction Coefficient Created!\n\n"
                f"📊 I0 Baseline: {i0_baseline:.6f} W\n"
                f"📈 I0 Region: {i0_low} to {i0_high} ({i0_high - i0_low} points)\n"
                f"🔬 Column: 'Extinction_Coefficient'\n\n"
                f"This column can now be used for calibration analysis."
            )
            
            messagebox.showinfo("Success", success_msg)
            writeToLog(f"Created Extinction_Coefficient column (baseline: {i0_baseline:.6f})", self.log)
            
        except Exception as e:
            error_msg = f"Error creating extinction coefficient column: {str(e)}"
            messagebox.showerror("Error", error_msg)
            writeToLog(f"Extinction coefficient error: {str(e)}", self.log)



def create_modern_calibration_window(parent_window, gui_instance, constants_module):
    """
    Function to create the calibration window.
    Call this from the "Generate calibration frame" button.
    """
    return ModernCalibrationWindow(parent_window, gui_instance, constants_module)

#Creates a collapsible tkinter frame, for selectively hiding elements. Each instance of the collapsible frame can toggle itself
class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, title="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.title_frame = ttk.Frame(self)
        self.title_frame.pack(fill="x", expand=1)

        self.title_label = ttk.Label(self.title_frame, text=title)
        self.title_label.pack(side="left", fill="x", expand=1)

        self.toggle_button = ttk.Button(self.title_frame, text="▼", width=2, command=self.toggle)
        self.toggle_button.pack(side="right")

        self.sub_frame = ttk.Frame(self, relief="sunken", borderwidth=1)
        self.sub_frame.pack(fill="x", expand=1)

        self.is_collapsed = False

    def toggle(self):
        if self.is_collapsed:
            self.sub_frame.pack(fill="x", expand=1)
            self.toggle_button.config(text="▼")
        else:
            self.sub_frame.forget()
            self.toggle_button.config(text="▲")
        self.is_collapsed = not self.is_collapsed

def update_label(label, value):
    label.config(text=f"Slider Value: {value}")

