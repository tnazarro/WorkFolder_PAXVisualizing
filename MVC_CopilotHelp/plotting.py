import seaborn as sns
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from data_processing import *
from constants import *

def create_figure(figsize=(6, 6)):
    """
    Create a matplotlib figure.
    """
    return Figure(figsize=figsize)

def create_axes(figure, position=(1, 1, 1)):
    """
    Create axes for the given figure.
    """
    return figure.add_subplot(*position)

#make figure as its own element
class FigureCreate:
    def __init__(self, figsize=(6, 6)):
        self.fig = plt.figure(figsize=figsize)
    
    def get_figure(self):
        return self.fig

class AxesCreate:
    def __init__(self, figure, position=(1, 1, 1)):
        self.ax = figure.add_subplot(*position)
    
    def get_axes(self):
        return self.ax

def plot_data(df, selection, ax, xloc1, xloc2, xlocA, xlocB):
    """
    Plot the selected data on the provided axes.
    """
    ax.clear()
    for trace in selection:
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        
        sns.lineplot(data=df, x='time', y=df.columns[trace], ax=ax)
        ax.tick_params(axis='x', rotation=20)

    ax.axvline(df['time'][xloc1], color='green', linestyle='--')
    ax.axvline(df['time'][xloc2], color='red', linestyle='--')
    ax.axvspan(df['time'][xloc1], df['time'][xloc2], facecolor='gray', alpha=.25)
    ax.axvline(df['time'][xlocA], color='#90EE90', linestyle=':')
    ax.axvline(df['time'][xlocB], color='#FF7276', linestyle=':')
    ax.axvspan(df['time'][xlocA], df['time'][xlocB], facecolor='gray', alpha=.25)
    

def slider_changed(event, df, label_widget, plot_callback):
    """
    Generic slider change handler that updates labels and triggers plot updates.
    """
    if df.empty:
        return
    
    # Convert slider value to valid DataFrame index
    max_index = len(df) - 1
    slider_value = float(event)
    index = int(min(max(0, slider_value), max_index))
    
    # Update the label with current time value
    try:
        time_value = df['time'].iloc[index]
        label_widget.config(text=f"Time: {time_value.strftime('%H:%M:%S')}")
    except (IndexError, KeyError):
        label_widget.config(text=f"Index: {index}")
    
    # Trigger plot update
    plot_callback()

def update_slider_ranges(df, *sliders):
    """
    Update slider ranges based on DataFrame length.
    
    Parameters:
    - df: The DataFrame containing the data
    - *sliders: Variable number of slider widgets to update
    """
    if df.empty:
        max_val = 1000  # Default fallback
    else:
        max_val = len(df) - 1
    
    for slider in sliders:
        slider.config(to=max_val)


def updateVLine(line, frame):
    line.set_xdata(frame)
    return line

def plot_data_subplots(df, selection, fig, subplot_mode=False, xloc1=0, xloc2=100, xlocA=200, xlocB=300):
    """
    Plot the selected data either on one axis or multiple subplots.
    
    Parameters:
    - df: DataFrame containing the data
    - selection: List of selected column indices from listbox
    - fig: The matplotlib figure object
    - subplot_mode: Boolean - True for subplots, False for single axis
    - xloc1, xloc2, xlocA, xlocB: Slider position indices
    """
    # Clear the entire figure
    fig.clear()
    
    if not selection:
        return
    
    if subplot_mode and len(selection) > 1:
        # Multiple subplots mode
        num_plots = min(len(selection), 4)  # Maximum 4 subplots
        
        # Determine subplot layout
        if num_plots == 1:
            rows, cols = 1, 1
        elif num_plots == 2:
            rows, cols = 2, 1
        elif num_plots == 3:
            rows, cols = 3, 1
        else:  # 4 plots
            rows, cols = 2, 2
        
        # Create subplots
        for i, trace in enumerate(selection[:4]):  # Limit to 4 subplots
            ax = fig.add_subplot(rows, cols, i + 1)
            
            # Plot the data
            sns.lineplot(data=df, x='time', y=df.columns[trace], ax=ax)
            
            # Add vertical lines and spans
            try:
                ax.axvline(df['time'].iloc[xloc1], color='green', linestyle='--', alpha=0.7)
                ax.axvline(df['time'].iloc[xloc2], color='red', linestyle='--', alpha=0.7)
                ax.axvspan(df['time'].iloc[xloc1], df['time'].iloc[xloc2], facecolor='gray', alpha=0.15)
                ax.axvline(df['time'].iloc[xlocA], color='#90EE90', linestyle=':', alpha=0.7)
                ax.axvline(df['time'].iloc[xlocB], color='#FF7276', linestyle=':', alpha=0.7)
                ax.axvspan(df['time'].iloc[xlocA], df['time'].iloc[xlocB], facecolor='blue', alpha=0.1)
            except IndexError:
                pass  # Skip if indices are out of range
            
            # Format the subplot
            locator = mdates.AutoDateLocator()
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
            ax.tick_params(axis='x', rotation=20, labelsize='small')
            ax.tick_params(axis='y', labelsize='small')
            ax.set_title(df.columns[trace], fontsize=10)
            ax.grid(True, alpha=0.3)
        
        # Adjust layout to prevent overlap
        fig.tight_layout(pad=1.5)
        
    else:
        # Single axis mode (original behavior)
        ax = fig.add_subplot(1, 1, 1)
        
        # Plot all selected traces on the same axis
        for trace in selection:
            sns.lineplot(data=df, x='time', y=df.columns[trace], ax=ax, label=df.columns[trace])
        
        # Add vertical lines and spans
        try:
            ax.axvline(df['time'].iloc[xloc1], color='green', linestyle='--')
            ax.axvline(df['time'].iloc[xloc2], color='red', linestyle='--')
            ax.axvspan(df['time'].iloc[xloc1], df['time'].iloc[xloc2], facecolor='gray', alpha=.25)
            ax.axvline(df['time'].iloc[xlocA], color='#90EE90', linestyle=':')
            ax.axvline(df['time'].iloc[xlocB], color='#FF7276', linestyle=':')
            ax.axvspan(df['time'].iloc[xlocA], df['time'].iloc[xlocB], facecolor='gray', alpha=.25)
        except IndexError:
            pass
        
        # Format the main plot
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params(axis='x', rotation=20)
        
        # Add legend if multiple traces
        if len(selection) > 1:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

#Old
def plot_big5(df, parent_window):
	"""
	Plot the 'Big 5' measurements in a new Tkinter window.

	Parameters:
	- df: pandas DataFrame containing the data to plot.
	- parent_window: Tkinter parent window.
	"""
	newBig5 = tk.Toplevel(parent_window)
	newBig5.title("Temp Big 5 Window")
	newBig5.geometry("1200x1000")
	tk.Label(newBig5, text="The 'Big 5' represents the 3 major measurables, as well as the corresponding SSA and BCMass").pack()

	btn = tk.Button(newBig5, 
					text="Click to close this window", 
					command=newBig5.destroy)
	btn.pack()

	# Create the figure
	fig = Figure(figsize=(12, 8), dpi=100)

	# Add subplots
	plot1 = fig.add_subplot(321)
	plot2 = fig.add_subplot(323)
	plot3 = fig.add_subplot(325)
	plot4 = fig.add_subplot(322)
	plot5 = fig.add_subplot(324)

	axes = [plot1, plot2, plot3, plot4, plot5]
	labels = ['Bscat (1/Mm)', 'Babs (1/Mm)', 'Bext (1/Mm)', 'Single Scat Albedo', 'BC Mass (ug/m3)']
	y_labels = ['Bscat', 'Babs', 'Bext', 'SSA', 'BC Mass']

	# Configure each subplot
	for ax, label, y_label in zip(axes, labels, y_labels):
		locator = mdates.AutoDateLocator()
		formatter = mdates.ConciseDateFormatter(locator)
		ax.xaxis.set_major_locator(locator)
		ax.xaxis.set_major_formatter(formatter)
		ax.plot(df['time'], df[label], label=label)
		ax.tick_params(axis='both', labelsize='small', labelrotation=20)
		ax.set_ylabel(y_label)

	# Add the figure to the Tkinter window
	canvas = FigureCanvasTkAgg(fig, master=newBig5)
	canvas.draw()
	canvas.get_tk_widget().pack()

	# Add the Matplotlib toolbar
	toolbar = NavigationToolbar2Tk(canvas, newBig5, pack_toolbar=False)
	toolbar.update()
	toolbar.pack()

#Old
def plot_4x(df, parent_window):
	"""
	Create a 4x4 sanity check plot in a new Tkinter window.

	Parameters:
	- df: pandas DataFrame containing the data to plot.
	- parent_window: Tkinter parent window.
	"""
	new4x = tk.Toplevel(parent_window)
	new4x.title("Temp 4x Sanity Check Window")
	new4x.geometry("1200x1000")
	tk.Label(new4x, text="Test (WIP)").pack()


	btn = tk.Button(new4x, 
					text="Click to close this window", 
					command=new4x.destroy)
	btn.pack()

	# Create the figure
	fig = Figure(figsize=(12, 8), dpi=100)
     

	# Add subplots
	plot1 = fig.add_subplot(221)
	plot2 = fig.add_subplot(222)
	plot3 = fig.add_subplot(223)
	plot4 = fig.add_subplot(224)

	axes = [plot1, plot2, plot3, plot4]
	labels = ['Bscat RAW', 'Bext (1/Mm)', 'Detected Laser power (W)', 'Placeholder']
	y_labels = ['Bscat RAW', 'Bext', 'Laser Power', 'Placeholder. "Generate calibration frame" for r^2']
	columns = ['scat_raw', 'Bext (1/Mm)', 'Detected Laser power (W)', 'time']  # Placeholder for the last column

	# Configure each subplot
	for ax, label, y_label, column in zip(axes, labels, y_labels, columns):
		locator = mdates.AutoDateLocator()
		formatter = mdates.ConciseDateFormatter(locator)
		ax.xaxis.set_major_locator(locator)
		ax.xaxis.set_major_formatter(formatter)
		ax.plot(df['time'], df[column], label=label)
		ax.tick_params(axis='both', labelsize='small', labelrotation=20)
		ax.set_ylabel(y_label)

	# Add the figure to the Tkinter window
	canvas = FigureCanvasTkAgg(fig, master=new4x)
	canvas.draw()
	canvas.get_tk_widget().pack()

	# Add the Matplotlib toolbar
	toolbar = NavigationToolbar2Tk(canvas, new4x, pack_toolbar=False)
	toolbar.update()
	toolbar.pack()
