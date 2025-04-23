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
from controller import resource_path

#One class handles the main viewing window, and calls it root for reference; can be passed main application window
class PAXView:
    def __init__(self, root):
        self.root = root
        self.root.title("PAX Data Visualizer - Plotting in TKinter")
        #Get the screen size and set the window size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        #This should set the window size to 80% of the screen size by default, but pull the pct from the constants file
        self.root.geometry(str(int(screen_width*geometry_width_pct))+"x"+str(int(screen_height*geometry_height_pct)))

        #Topleft (TL) frame for file loading and radio buttons
        self.frame_TL = tk.Frame(root)
        self.selected = tk.StringVar()
        self.selected.set("V2")
        self.radio_csv = tk.Radiobutton(self.frame_TL, text="Load default .csv", value="V1", variable=self.selected)
        self.radio_xlsx = tk.Radiobutton(self.frame_TL, text="Load default .xlsx", value="V2", variable=self.selected)
        self.load_file_button = tk.Button(self.frame_TL, text="Load PAX data file", command=lambda: load_file(self.selected), width=30, bg='orange')
        self.load_file_button.grid(row=0, column=0, columnspan=3)
        self.radio_csv.grid(row=1, column=0)
        self.radio_xlsx.grid(row=1, column=1)
        self.frame_TL.grid(row=0, column=0)
        #TODO: Add a button to load a pax.txt file, and a radio button eventually to select what to merge



        #TC
        self.frame_TC = tk.Frame(root)
        self.log = tk.Text(self.frame_TC, state='disabled', width=70, height=5, wrap='char')
        self.log.grid(row=0, column=0)
        self.frame_TC.grid(row=0, column=3)

        #TR
        self.frame_TR = tk.Frame(root)
        self.myImgLogo = Image.open(resource_path(logo_name))
        self.myImgLogo = ImageTk.PhotoImage(self.myImgLogo)
        self.image_label = tk.Label(self.frame_TR, image=self.myImgLogo)
        self.image_label.pack()
        self.frame_TR.grid(row=0, column=5)

        #The middle center (MC) frame for the plot
        self.frame_MC = tk.Frame(root)
        self.frame_MC.grid(row=2, column=2)
        #TODO: Edit to make a more advanced plot with multiple axes, and a more advanced toolbar

        #The Middle Right (MR) frame for the calibration options (this will be a collapsible frame)
        self.frame_MR = tk.Frame(root)
        self.frame_MR.grid(row=2, column=4)
        #TODO: Add the collapsible frame for the calibration options
        self.collapsible_frame = CollapsibleFrame(self.frame_MR, title="Calibration Options")

        

        #The bottom left (BL) frame for the quit and clear buttons, and any other functional buttons
        self.frame_BL = tk.Frame(root)
        self.button_quit = tk.Button(self.frame_BL, text="Quit", command=self.quit_app, bg='#FF2222')
        self.button_clear = tk.Button(self.frame_BL, text="Clear Selection", bg='light green')
        self.testTextButton = tk.Button(self.frame_BL, text="Display filename", width=15, bg='light yellow')
        self.frame_BL.grid(row=4, column=0)
        self.button_quit.grid(row=2, column=0)
        self.button_clear.grid(row=0, column=0)
        self.testTextButton.grid(row=1, column=0)

        #TODO: Add a BM section that calls the big 5 and 4x plots

        #The frame for the listbox of columns; this will be the left side of the window
        self.list_frame = tk.Frame(root)
        self.listbox = tk.Listbox(self.list_frame, selectmode='multiple',height=30, width=30)
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
