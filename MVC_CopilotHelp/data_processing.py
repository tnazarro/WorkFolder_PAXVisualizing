import warnings
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os

import pandas as pd
import numpy as np

import constants

#This is to ignore a deprecated functionality warning
warnings.filterwarnings("ignore", "use_inf_as_na")

def load_multiple_files(selected, file_to_set, pb):
    """
    Enhanced file loading function that allows selection of multiple files.
    Automatically processes and concatenates them into a single dataframe.
    """
    pb.start()
    
    # Get multiple file paths based on the selected format
    if selected.get() == "V1":
        file_paths = filedialog.askopenfilenames(
            title="Choose Multiple PAX Data Files", 
            filetypes=(("Comma Separated", "*.csv"),)
        )
    elif selected.get() == "V2":
        file_paths = filedialog.askopenfilenames(
            title="Choose Multiple PAX Data Files", 
            filetypes=(("PAX Data", "*.xlsx"),)
        )
    elif selected.get() == "V3":
        file_paths = filedialog.askopenfilenames(
            title="Choose Multiple PAX.txt Files", 
            filetypes=(("Text File", "*.txt"),)
        )
    else:
        tk.messagebox.showinfo("File Selection Error", "This program does not currently support non xlsx or csv imports")
        pb.stop()
        return None
    
    pb.stop()
    
    # If no files selected, return
    if not file_paths:
        return None
    
    # Store the list of selected files (for display purposes)
    file_to_set.set(f"{len(file_paths)} files selected: {', '.join([os.path.basename(f) for f in file_paths])}")
    
    return file_paths

def process_multiple_files_automatically(file_paths, selected, listbox, gui_instance=None, pb=None):
    """
    Automatically process multiple files and concatenate them into a single dataframe.
    This combines the functionality of pax_analyzer and concatenate_df for batch processing.
    """
    if not file_paths:
        messagebox.showerror("Error", "No files to process!")
        return
    
    if pb:
        pb.start()
    
    dataframes = []
    failed_files = []
    
    try:
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                print(f"Processing file {i+1}/{total_files}: {os.path.basename(file_path)}")
                
                # Update progress if progress bar available
                if pb:
                    progress = (i / total_files) * 100
                    pb['value'] = progress
                    pb.update()
                
                # Load the file based on the selected format
                if selected.get() == "V1":
                    df = pd.read_csv(file_path)
                elif selected.get() == "V2":
                    df = pd.read_excel(file_path)
                else:
                    print(f"Skipping unsupported file format: {file_path}")
                    failed_files.append(file_path)
                    continue

                # Clean NaN values before datetime operations
                clearNaN(df)
                
                # Combine date and time columns into a single datetime column
                time = pd.to_datetime(
                    df['Local Date'].astype(str) + ',' + df['Local Time'].astype(str), 
                    format='%Y-%m-%d,%H:%M:%S'
                )

                # Drop unnecessary columns (same logic as original pax_analyzer)
                columns_to_drop = [
                    'Sec UTC', 'DOY UTC', 'Year UTC', 'Sec Local', 'DOY Local', 'Year Local',
                    'Local Date', 'Local Time', 'Reserved.1', 'Reserved.2', 'Reserved.3',
                    'Reserved.4', 'Reserved.5'
                ]
                
                # Only drop columns that exist in the dataframe
                existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
                df.drop(columns=existing_columns_to_drop, inplace=True)
                
                df['time'] = time
                
                # Add a source file column to track which file each row came from
                df['source_file'] = os.path.basename(file_path)
                
                dataframes.append(df)
                print(f"Successfully processed: {os.path.basename(file_path)} ({len(df)} rows)")
                
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                failed_files.append(file_path)
                continue
        
        # Concatenate all successfully processed dataframes
        if dataframes:
            # Sort dataframes by their first timestamp to maintain chronological order
            dataframes.sort(key=lambda df: df['time'].min())
            
            # Concatenate all dataframes
            concatenated_df = pd.concat(dataframes, ignore_index=True)
            
            # Sort the final dataframe by time to ensure proper chronological order
            concatenated_df.sort_values('time', inplace=True)
            concatenated_df.reset_index(drop=True, inplace=True)
            
            # Update the global dataframe
            update_df_main(concatenated_df)
            
            # Populate the listbox with column names (excluding metadata columns)
            populate_listbox(listbox, concatenated_df)
            
            # Update slider ranges if GUI instance is available
            if gui_instance is not None:
                gui_instance.update_slider_ranges_after_load()
            
            # Show summary
            total_rows = len(concatenated_df)
            successful_files = len(dataframes)
            time_range = f"{concatenated_df['time'].min()} to {concatenated_df['time'].max()}"
            
            summary_message = (
                f"Batch Processing Complete!\n\n"
                f"✅ Successfully processed: {successful_files} files\n"
                f"📊 Total data points: {total_rows:,}\n"
                f"⏰ Time range: {time_range}\n"
                f"📁 Source files tracked in 'source_file' column"
            )
            
            if failed_files:
                summary_message += f"\n\n❌ Failed files ({len(failed_files)}):\n"
                summary_message += "\n".join([os.path.basename(f) for f in failed_files])
            
            messagebox.showinfo("Batch Processing Results", summary_message)
            
            print(f"Final concatenated dataframe shape: {concatenated_df.shape}")
            print(f"Columns: {list(concatenated_df.columns)}")
            
        else:
            messagebox.showerror("Error", "No files were successfully processed!")
            
    except Exception as e:
        messagebox.showerror("Batch Processing Error", f"Error during batch processing: {str(e)}")
        
    finally:
        if pb:
            pb.stop()

def populate_listbox(listbox, df):
    """
    Populate the listbox with column names from the dataframe.
    Excludes metadata columns like 'Alarm', 'time', and 'source_file'.
    """
    listbox.delete('0', 'end')
    i = 0
    
    excluded_columns = ['Alarm', 'time', 'source_file']
    
    for column in df.columns:
        if column not in excluded_columns:
            listbox.insert(i, column)
            if (i % 2) == 0:
                listbox.itemconfigure(i, background='#f0f0f0')
            i += 1

def get_file_info_summary():
    """
    Get a summary of the loaded data including file sources.
    Returns a dictionary with file information.
    """
    if constants.df_main.empty:
        return {"status": "No data loaded"}
    
    df = constants.df_main
    
    if 'source_file' in df.columns:
        file_counts = df['source_file'].value_counts()
        file_info = {
            "total_files": len(file_counts),
            "total_rows": len(df),
            "files_detail": file_counts.to_dict(),
            "time_range": {
                "start": df['time'].min(),
                "end": df['time'].max()
            }
        }
    else:
        file_info = {
            "total_files": "Unknown (legacy load)",
            "total_rows": len(df),
            "files_detail": {},
            "time_range": {
                "start": df['time'].min() if 'time' in df.columns else "Unknown",
                "end": df['time'].max() if 'time' in df.columns else "Unknown"
            }
        }
    
    return file_info

# ==================== LEGACY FUNCTIONS (MAINTAINED FOR COMPATIBILITY) ====================

def load_file(selected, file_to_set, pb):
    """
    LEGACY: Loading default style PAX files. Maintained for backward compatibility.
    Consider using load_multiple_files() for enhanced functionality.
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
        return None
    
    pb.stop()
    file_to_set.set(file_path)  # Set the file path in the GUI

def clearNaN(df):
    """
    Small function to loop through the columns and clean up the df.
    """
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.bfill(inplace=True)

def pax_analyzer(file_path, selected, listbox, gui_instance=None):
    """
    LEGACY: Creating the pd df frames from files, cleaning/prepping the df.
    Maintained for backward compatibility. Consider using process_multiple_files_automatically().
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
    populate_listbox(listbox, df)
    update_df_main(df)
    print(constants.df_main)
    
    # Update slider ranges after loading data
    if gui_instance is not None:
        gui_instance.update_slider_ranges_after_load()

def concatenate_df(file_path, selected, listbox):
    """
    LEGACY: Concatenating the dataframes together. 
    Maintained for backward compatibility. Consider using process_multiple_files_automatically().
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

    # Drop unnecessary columns
    df_to_add.drop(columns=[
        'Sec UTC', 'DOY UTC', 'Year UTC', 'Sec Local', 'DOY Local', 'Year Local',
        'Local Date', 'Local Time', 'Reserved.1', 'Reserved.2', 'Reserved.3',
        'Reserved.4', 'Reserved.5'
    ], inplace=True)
    df_to_add['time'] = time

    if constants.df_main is not None and not constants.df_main.empty:
        constants.df_main = pd.concat([constants.df_main, df_to_add], ignore_index=True)
    else:
        constants.df_main = df_to_add

    # Populate the listbox with column names
    populate_listbox(listbox, constants.df_main)
    print(constants.df_main)

def simple_listbox_load(listbox):
    """
    Load the listbox with column names from the current dataframe.
    """
    print("Loading listbox...")
    populate_listbox(listbox, constants.df_main)
    print(constants.df_main)

def process_paxtxt(file_path, version_var_to_set):
    """
    Processing the PAX.txt file. This is a placeholder for future functionality.
    """
    print("Processing PAX.txt file...")
    
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