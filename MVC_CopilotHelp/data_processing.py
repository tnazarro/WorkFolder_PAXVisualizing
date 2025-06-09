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

def pax_analyzer(file_path, selected, listbox):
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


	
	