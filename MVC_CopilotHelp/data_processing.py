import warnings
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import pandas as pd
import numpy as np

#This is to ignore a deprecated functionality warning
warnings.filterwarnings("ignore", "use_inf_as_na")

#load file - the default for PAX happens to be CSV
def load_file(selected):
    """
    Loading default style PAX files. M0 files can technically be loaded, but functionality will be reduced.
    """
    #pb.start()  # Start the progress bar (if implemented)
	#pb.start()
    if selected.get() == "V1":
        file_path = filedialog.askopenfilename(title="Choose PAX Data File", filetypes=(("Comma Separated", "*.csv"),))
    elif selected.get() == "V2":
        file_path = filedialog.askopenfilename(title="Choose PAX Data File", filetypes=(("PAX Data", "*.xlsx"),))
    else:
        tk.messagebox.showinfo("File Selection Error", "This program does not currently support non xlsx or csv imports")
        #pb.stop()
        return None
	#pb.stop() is a placeholder for a progress bar stop function, if implemented
    #pb.stop()
    return file_path


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

	return df