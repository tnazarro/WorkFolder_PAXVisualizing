"""Starting point for the MVC_CopilotHelp project. Contains all helper/utility functions and classes."""
import os
import sys
import tkinter as tk
from tkinter import messagebox



from constants import *

# This function is used to get the absolute path of a resource file.
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    # Join the base path with the relative path
    absolute_path = os.path.join(base_path, relative_path)

    # Ensure the path exists
    if not os.path.exists(absolute_path):
        raise FileNotFoundError(f"Resource not found: {absolute_path}")

    return absolute_path

def alarm_translate(user_alarm_string, alarm_names, log):
	"""
	Translates alarm codes and logs the corresponding messages.

	Parameters:
	- user_alarm_string: A string containing alarm codes ('r', 'y', 'g').
	- alarm_names: A list of alarm names corresponding to the codes.
	- write_to_log: A function to log messages.
	"""
	for index in range(len(user_alarm_string)):
		match user_alarm_string[index]:
			case 'r':
				writeToLog(f'{alarm_names[index]:25} RED', log)
			case 'y':
				writeToLog(f'{alarm_names[index]:25} YELLOW', log)
			case 'g':
				pass

#Handles the writing to the log window, set up in the top-center of the GUI
def writeToLog(msg, log):
    numlines = int(log.index('end - 1 line').split('.')[0])
    log['state'] = 'normal'
    if numlines == 24:
        log.delete(1.0, 2.0)
    if log.index('end-1c') != '1.0':
        log.insert('end', '\n')
    log.insert('end', msg)
    log['state'] = 'disabled'

def are_you_sure(window):
	"""
	Opens a message box to confirm window destruction.

	Parameters:
	- window: The Tkinter window to be destroyed.
	"""
	if messagebox.askyesno("Quit Dialog", "Are you sure you want to quit the app?"):
		window.destroy()