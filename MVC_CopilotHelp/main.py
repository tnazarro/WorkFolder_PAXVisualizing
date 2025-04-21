#This is the main file that runs the application. It runs the main loop.


import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import seaborn as sns
import matplotlib.dates as mdates


from controller import *
from gui import *
from constants import *
from plotting import *
from data_processing import *

def main():
    """
    Entry point for the application.
    Initializes the Tkinter root window and starts the main loop.
    """
    root = tk.Tk()  # Create the root window
    app = PAXView(root)  # Instantiate the PAXView class
    app.mainloop()  # Start the Tkinter main loop

if __name__ == "__main__":
    main()