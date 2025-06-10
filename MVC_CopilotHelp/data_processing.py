import warnings
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import pandas as pd
import numpy as np

import constants

#This is to ignore a deprecated functionality warning
warnings.filterwarnings("ignore", "use_inf_as_na")

#load file - the default for PAX happens to be CSV
def load_file(selected, file_to_set, pb):
    """
    Loading default style PAX files. M0 files can technically be loaded, but functionality will be reduced.
    """
    pb.start()
	# Get the file path based on the selected format
    if selected.get() == "V1":
        file_path = filedialog.askopenfilename(title="Choose PAX Data File", filetypes=(("Comma Separated", "*.csv"),))
    elif selected.get() == "V2":
        file_path = filedialog.askopenfilename(title="Choose PAX Data File", filetypes=(("PAX Data", "*.xlsx"),))
    elif selected.get() == "V3":
        file_path = filedialog.askopenfilename(title="Choose supplementary PAX.txt", filetypes=(("Text File", "*.txt"),))
    else:
        tk.messagebox.showinfo("File Selection Error", "This program does not currently support non xlsx or csv imports")
        #pb.stop()
        return None
    pb.stop()
    file_to_set.set(file_path)  # Set the file path in the GUI

def process_paxtxt(file_path, version_var_to_set):
	"""
	Processing the PAX.txt file. This is a placeholder for future functionality."""
	print("Processing PAX.txt file...")
	# Placeholder for processing logic
	# You can implement the specific logic for processing the PAX.txt file here
	with open(file_path, 'r') as file:
		lines = file.readlines()

	# Example: Extract lines containing a specific keyword
	keyword = "PAX Version"
	selected_line = [line.strip() for line in lines if keyword in line]

	# Convert the selected lines into a DataFrame for further processing
	version_var = selected_line[0].split('=')[1].strip()
	print(version_var)
	if isinstance(version_var_to_set, tk.StringVar):
		version_var_to_set.set(version_var)  # Set the version variable in the GUI
	else:
		raise TypeError("version_var_to_set must be a tkinter.StringVar")
	



def clearNaN(df):
	"""
	Small function to loop through the columns and clean up the df.
	"""
	df.replace([np.inf, -np.inf], np.nan, inplace=True)
	df.bfill(inplace=True)

def pax_analyzer(file_path, selected, listbox, gui_instance=None):
	"""
	Creating the pd df frames from files, cleaning/prepping the df.
	Of note, recently changed the global "data" to "df" to prevent namespace overlap.
	"""
	print("File path is " + file_path + ".")
	
	# Load the file based on the selected format
	if selected.get() == "V1":
		df = pd.read_csv(file_path)
	elif selected.get() == "V2":
		df = pd.read_excel(file_path)
	else:
		raise ValueError("Unsupported file format selected.")

	# NaN cleared prior to any datetime operations
	clearNaN(df)
	
	# Combine date and time columns into a single datetime column
	time = pd.to_datetime(df['Local Date'].astype(str) + ',' + df['Local Time'].astype(str), format='%Y-%m-%d,%H:%M:%S')

	# Drop unnecessary columns
	df.drop(columns=[
		'Sec UTC', 'DOY UTC', 'Year UTC', 'Sec Local', 'DOY Local', 'Year Local',
		'Local Date', 'Local Time', 'Reserved.1', 'Reserved.2', 'Reserved.3',
		'Reserved.4', 'Reserved.5'
	], inplace=True)
	df['time'] = time

	# Populate the listbox with column names
	i = 0
	listbox.delete('0', 'end')
	for column in df.columns:
		if column not in ['Alarm', 'time']:
			listbox.insert(i, column)
			if (i % 2) == 0:
				listbox.itemconfigure(i, background='#f0f0f0')
			i += 1
	update_df_main(df)
	print(constants.df_main)
	
	# ADD THIS LINE to update slider ranges after loading data:
	if gui_instance is not None:
		gui_instance.update_slider_ranges_after_load()

def concatenate_df(file_path, selected, listbox):
	"""
	Concatenating the dataframes together. This is a placeholder for future functionality.
	"""
	# Load the file based on the selected format
	if selected.get() == "V1":
		df_to_add = pd.read_csv(file_path)
	elif selected.get() == "V2":
		df_to_add = pd.read_excel(file_path)
	else:
		raise ValueError("Unsupported file format selected.")

	# NaN cleared prior to any datetime operations
	clearNaN(df_to_add)
	
	# Combine date and time columns into a single datetime column
	time = pd.to_datetime(df_to_add['Local Date'].astype(str) + ',' + df_to_add['Local Time'].astype(str), format='%Y-%m-%d,%H:%M:%S')

	# Drop unnecessary columns; this is based on the assumption that columns are the same as v3.1.3 or more current code
	df_to_add.drop(columns=[
		'Sec UTC', 'DOY UTC', 'Year UTC', 'Sec Local', 'DOY Local', 'Year Local',
		'Local Date', 'Local Time', 'Reserved.1', 'Reserved.2', 'Reserved.3',
		'Reserved.4', 'Reserved.5'
	], inplace=True)
	df_to_add['time'] = time

	if constants.df_main is not None:
		constants.df_main = pd.concat([constants.df_main, df_to_add], ignore_index=True)
	else:
		constants.df_main = df_to_add

	# Populate the listbox with column names
	i = 0
	listbox.delete('0', 'end')
	for column in constants.df_main.columns:
		if column not in ['Alarm', 'time']:
			listbox.insert(i, column)
			if (i % 2) == 0:
				listbox.itemconfigure(i, background='#f0f0f0')
			i += 1
	print(constants.df_main)

def simple_listbox_load(listbox):
		# Populate the listbox with column names
	print("Loading listbox...")
	i = 0
	listbox.delete('0', 'end')
	for column in constants.df_main.columns:
		if column not in ['Alarm', 'time']:
			listbox.insert(i, column)
			if (i % 2) == 0:
				listbox.itemconfigure(i, background='#f0f0f0')
			i += 1 
	print(constants.df_main)
	

def update_df_main(new_value):
	constants.df_main = new_value

def update_df_to_add(new_value):
	constants.df_to_add = new_value

def clear_df():
	"""
	Clears the df_main and df_to_add dataframes.
	"""
	constants.df_main = pd.DataFrame()
	constants.df_to_add = pd.DataFrame()

def chooseBestFit(window):
	newFitWindow = tk.Toplevel(window)
	newFitWindow.title("Testing line of best fit")
	newFitWindow.geometry("1000x800")
	tk.Label(newFitWindow, text = "Line of Best Fit Calculation (WIP)")

    
	btn = tk.Button(newFitWindow, 
				 text = "Click to close this window", 
				 command = newFitWindow.destroy)
	btn.grid(row = 0, column = 0)

	frame_top = tk.Frame(newFitWindow)
	frame_top.grid(row = 1, column = 0)
	s1 = tk.ttk.Separator(newFitWindow, orient = 'horizontal').grid(row = 2,columnspan = 9,sticky = "ew")
	frame_bottom = tk.ttk.Labelframe(newFitWindow, text = 'Fit numbers:')
	frame_bottom.grid(row = 3, column = 0)

    
	fig = Figure(figsize = (10, 5), 
                 dpi = 100) 
    # adding the subplots 
	plot1 = fig.add_subplot(121)
	plot2 = fig.add_subplot(122)


	ax1 = plot1
	ax2 = plot2


	locator = mdates.AutoDateLocator()
	formatter = mdates.ConciseDateFormatter(locator)
	ax1.xaxis.set_major_locator(locator)
	ax1.xaxis.set_major_formatter(formatter)


    
	min = float(entry_min.get())
	max = float(entry_max.get())
	percent = float(entry_percent.get())


    
	r2 = 0
	slope = 0



    
	if calibvar.get() == 'Scattering':
		
		filtered_time = df['time'].iloc[xlocA:xlocB]
		filtered_dfx = df['Bscat (1/Mm)'].iloc[xlocA:xlocB]
		filtered_dfy = df['Debug Ext Calculation'].iloc[xlocA:xlocB]


		y_pct_change = filtered_dfy.pct_change() * 100
		filtered_dfy = filtered_dfy[(y_pct_change.abs() <= percent) | (y_pct_change.isna())]
		filtered_dfx = filtered_dfx[(y_pct_change.abs() <= percent) | (y_pct_change.isna())]
		filtered_time = filtered_time[(y_pct_change.abs() <= percent) | (y_pct_change.isna())]
        
		mask = (filtered_dfy >= min) & (filtered_dfy <= max)
		filtered_dfx = filtered_dfx[mask]
		filtered_dfy = filtered_dfy[mask]
		filtered_time = filtered_time[mask]
    
    
		slope, intercept, r_value, p_value, std_err = linregress(filtered_dfx, filtered_dfy)
		r2 = r_value **2
		sns.regplot(data = df, x = filtered_dfx,y = filtered_dfy, ax = ax1, marker = 'x', line_kws = dict(color = 'r'), fit_reg = True)

		plt.xticks(rotation = 20)

		ax2.scatter(filtered_time,filtered_dfy,label = 'Filtered')

    
#Repeat the graph setup above, just changing the y axis
    
	elif calibvar.get() == 'Absorbing':  #ToDo: Currently, Absorbing is inappropriately setting dates as relevant; fix the date parsing somehow?

		filtered_time = df['time'].iloc[xlocA:xlocB]
		filtered_dfx = df['Babs (1/Mm)'].iloc[xlocA:xlocB]

		difference_dfy = (df['Debug Ext Calculation'].iloc[xlocA:xlocB]-df['Bscat (1/Mm)'].iloc[xlocA:xlocB])
		# filtered_dfy = difference_dfy.iloc[xlocA:xlocB]

		y_pct_change = difference_dfy.pct_change() * 100
		filtered_dfy = difference_dfy[(y_pct_change.abs() <= percent) | (y_pct_change.isna())]
		filtered_dfx = filtered_dfx[(y_pct_change.abs() <= percent) | (y_pct_change.isna())]
		filtered_time = filtered_time[(y_pct_change.abs() <= percent) | (y_pct_change.isna())]        

        
		mask = (filtered_dfy >= min) & (filtered_dfy <= max)
		filtered_dfx = filtered_dfx[mask]
		filtered_dfy = filtered_dfy[mask]
		filtered_time = filtered_time[mask]        
    
		combined_df = pd.concat([filtered_dfx, filtered_dfy],axis=1)
        
		slope, intercept, r_value, p_value, std_err = linregress(filtered_dfx, filtered_dfy)
		r2 = r_value **2
		sns.regplot(data = combined_df, x = filtered_dfx,y = filtered_dfy, ax = ax1, marker = 'x', line_kws = dict(color = 'r'), fit_reg = True)

		ax2.scatter(filtered_time,filtered_dfy,label = 'Filtered')

	else:
		print('did not work as expected')

	
	ax1.tick_params(axis = 'both', labelsize = 'small',labelrotation = 20)
	ax2.tick_params(axis = 'both', labelsize = 'small',labelrotation = 20)    


    
	ax1.set_ylabel("Lin Reg Best Fit, given constraints")
	ax2.set_ylabel("Filtered data")

	label_r2 = tk.ttk.Label(frame_bottom, text = f"r^2: {r2}")
	label_r2.grid(row = 0, column = 0)
	label_slope = tk.ttk.Label(frame_bottom, text = f"Slope: {slope}")
	label_slope.grid(row = 1, column = 0)

    
    # containing the Matplotlib figure 
	canvas = FigureCanvasTkAgg(fig, 
                               master = frame_top)   
	canvas.draw() 
  
    # placing the canvas on the Tkinter window 
	canvas.get_tk_widget().pack()
  
    # creating the Matplotlib toolbar 
	toolbar = NavigationToolbar2Tk(canvas, 
                                   frame_top, pack_toolbar=False) 
	toolbar.update() 
	toolbar.pack()