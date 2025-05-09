#views.py

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
from data_processing import *
from controller import resource_path, alarm_translate, writeToLog
from plotting import *

#One class handles the main viewing window, and calls it root for reference; can be passed main application window
class PAXView:
    def __init__(self, root):
        self.root = root
        #TODO: Make the title a constant?
        self.root.title("PAX Data Visualizer - Plotting in TKinter")
        #Get the screen size and set the window size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        #This should set the window size to 80% of the screen size by default, but pull the pct from the constants file
        self.root.geometry(str(int(screen_width*geometry_width_pct))+"x"+str(int(screen_height*geometry_height_pct)))

        #Topleft (TL) frame for file loading and radio buttons
        self.frame_TL = tk.Frame(root)
        self.selected = tk.StringVar() #Variable to hold the selected file type
        self.selected.set("V2") #Default to .xlsx
        self.file_path = tk.StringVar()
        self.file_path.set("")
        self.radio_csv = tk.Radiobutton(self.frame_TL, text="Load default .csv", value="V1", variable=self.selected)
        self.radio_xlsx = tk.Radiobutton(self.frame_TL, text="Load default .xlsx", value="V2", variable=self.selected)
        self.load_file_button = tk.Button(self.frame_TL, text="Load PAX data file", command=lambda: load_file(self.selected, self.file_path,self.pb), width=30, bg='orange')
        self.load_file_button.grid(row=0, column=0, columnspan=3)
        self.radio_csv.grid(row=1, column=0)
        self.radio_xlsx.grid(row=1, column=1)
        self.frame_TL.grid(row=0, column=0)
        # self.df = pd.DataFrame()  # Initialize df to empty DataFrame; commented out to avoid confusion with the global df in constants.py
        self.analyze_button = tk.Button(self.frame_TL, text="Analyze PAX data", command=lambda: pax_analyzer(self.file_path.get(), self.selected, self.listbox), bg='light green')
        self.analyze_button.grid(row=2, column=0, columnspan=3)
        
        self.radio_version = tk.Radiobutton(self.frame_TL, text="(optional) Load Pax.txt", value="V3", variable=self.selected)
        self.radio_version.grid(row=4, column=0)
        #Currently, the version handling is not very advanced, and the processing/concatenating functions are finicky. See readme for more details
        self.add_version_button = tk.Button(self.frame_TL, text="Process Pax.txt", command=lambda: process_paxtxt(self.file_path.get(),self.version_var), bg='light blue')
        self.add_version_button.grid(row=4, column=1, columnspan=1)
        self.concatenate_button = tk.Button(self.frame_TL, text="Concatenate Loaded Data", command=lambda: concatenate_df(self.file_path.get(), self.selected, self.listbox), bg='light blue')
        self.concatenate_button.grid(row=3, column=0, columnspan=3)
        self.load_concatenated_button = tk.Button(self.frame_TL, text="Load Concatenated Data", command=lambda: simple_listbox_load(self.listbox), bg='light blue')
        self.load_concatenated_button.grid(row=5, column=0, columnspan=3)
        self.clear_df_button = tk.Button(self.frame_TL, text="Clear DataFrame", command=lambda: clear_df, bg='light blue')
        self.clear_df_button.grid(row=6, column=0, columnspan=3)

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
        #TODO: Edit to make a more advanced plot with multiple axes, and a more advanced toolbar

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
             command = lambda: print("calibStarter"), bg = 'light blue')
        self.calibStarter.grid(row = 4, column = 2)

        #TODO: Work on the section below 
        #Beginning of I0 slider logic
        self.label_spanI0 = tk.Label(self.frame_MR, text = "I0 selection:")
        self.label_spanI0.grid(row = 5, column = 0)

        #Setting up the I0 sliders; these will be used to select the range of I0 values for the calibration region
        self.current_valueI0Low = tk.DoubleVar()
        self.slider_I0Low = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,
            orient='horizontal',
            variable=self.current_valueI0Low,
            command=lambda event: slider_changed(
            event, 
            constants.df_main,  # Replace self.df with constants.df_main
            self.current_valueI0Low,  # Replace self.current_value1 with self.current_valueI0Low
            self.label_sliderI0Low,  # Replace self.label_slider1 with self.label_sliderI0Low
            lambda: plot_data(  # Replace self.plot_callback with an inline lambda for plotting
                constants.df_main, 
                self.listbox.curselection(), 
                self.main_axes.get_axes(), 
                self.current_valueI0Low.get(), 
                self.current_valueI0High.get(), 
                self.current_valueCalibLow.get(), 
                self.current_valueCalibHigh.get()
            )
            )
        )
        #TODO: Add a command to the slider to update the label with the current value

        self.slider_I0Low.grid(row=6, column=0)

        self.current_valueI0High = tk.DoubleVar()
        self.slider_I0High = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,
            orient='horizontal',
            variable=self.current_valueI0High,
            command=lambda event: slider_changed2(event, self.df, self.current_value2, self.label_slider2, self.plot_callback)
        )
        self.slider_I0High.grid(row=7, column=0)

        self.label_sliderI0Low = tk.Label(self.frame_MR, text = "Slider is at " + str(self.current_valueI0Low.get()), fg = 'green')
        self.label_sliderI0Low.grid(row = 6, column = 2)
        self.label_sliderI0High = tk.Label(self.frame_MR, text = "Slider is at " + str(self.current_valueI0High.get()), fg = 'green')
        self.label_sliderI0High.grid(row = 7, column = 2)


        #Repeating the above logic for the calibration region selection
        self.label_spanCalib = tk.Label(self.frame_MR, text = "Calib. Region:")
        self.label_spanCalib.grid(row = 8, column = 0)

        self.current_valueCalibLow = tk.DoubleVar()
        self.slider_CalibLow = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,
            orient='horizontal',
            variable=self.current_valueCalibLow,
            command=lambda event: slider_changedA(event, self.df, self.current_valueA, self.label_sliderA, self.plot_callback)
        )
        self.slider_CalibLow.grid(row=9, column=0)

        self.current_valueCalibHigh = tk.DoubleVar()
        self.slider_CalibHigh = ttk.Scale(
            self.frame_MR,
            from_=0,
            to=1000,
            orient='horizontal',
            variable=self.current_valueCalibHigh,
            command=lambda event: slider_changedB(event, self.df, self.current_valueB, self.label_sliderB, self.plot_callback)
        )
        self.slider_CalibHigh.grid(row=10, column=0)

        self.label_sliderCalibLow = tk.Label(self.frame_MR, text = "Slider is at " + str(self.current_valueCalibLow.get()), fg = 'green')
        self.label_sliderCalibLow.grid(row = 9, column = 2)
        self.label_sliderCalibHigh = tk.Label(self.frame_MR, text = "Slider is at " + str(self.current_valueCalibHigh.get()), fg = 'green')
        self.label_sliderCalibHigh.grid(row = 10, column = 2)

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

        #TODO: Add a BM section that calls the big 5 and 4x plots
        #The bottom middle (BM) frame for the big 5 and 4x plots
        self.frame_BM = tk.Frame(root)
        self.button_big5 = tk.Button(self.frame_BM, text="Plot Big 5", command=lambda: plot_big5(constants.df_main, self.root), bg='light blue')
        self.button_big5.grid(row=0, column=0)
        self.frame_BM.grid(row=4, column=3)
        self.button_4x = tk.Button(self.frame_BM, text="Plot 4x", command=lambda: plot_4x(constants.df_main, self.root), bg='light blue')
        self.button_4x.grid(row=1, column=0)

        #The bottom right (BR) frame for the progress bar and version info
        self.frame_BR = tk.Frame(root)
        self.frame_BR.grid(row=4, column=5)
        #TODO: Set up the version text to be a label that updates with the version of the program
        self.version_var = tk.StringVar()
        self.version_var.set("Version Unknown")
        self.label_version = tk.Label(self.frame_BR, textvariable=self.version_var, fg='blue')
        self.label_version.grid(row=1, column=0)
        self.pb = ttk.Progressbar(self.frame_BR, orient="horizontal", length=200, mode="determinate")
        self.pb.grid(row=0, column=0)

        #The frame for the listbox of columns; this will be the left side of the window
        self.list_frame = tk.Frame(root)
        self.listbox = tk.Listbox(self.list_frame, selectmode='multiple',height=30, width=30)
        self.listbox.bind('<<ListboxSelect>>', lambda _: (plot_data(
            constants.df_main, 
            self.listbox.curselection(), 
            self.main_axes.get_axes(), 
            self.current_valueI0Low.get(), 
            self.current_valueI0High.get(), 
            self.current_valueCalibLow.get(), 
            self.current_valueCalibHigh.get()
        ), self.canvas.draw()) if not constants.df_main.empty and self.listbox.curselection() else messagebox.showerror("Error", "No data to plot or no selection made"))
        self.scrollbar = tk.Scrollbar(self.list_frame, orient="vertical")
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.list_frame.grid(row=2, column=0)
        self.listbox.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")

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
