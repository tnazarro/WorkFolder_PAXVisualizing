import warnings
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os
from datetime import datetime, timedelta

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
    
# ==================== EXTINCTION COEFFICIENT IMPLEMENTATION ====================

import pandas as pd
import numpy as np
from tkinter import messagebox
import constants

def calculate_extinction_coefficient(df, i0_low_idx, i0_high_idx, 
                                   laser_power_column='Detected Laser power (W)',
                                   calculated_column_name='Extinction_Coefficient'):
    """
    Calculate extinction coefficient using Beer-Lambert law: -ln(I/I0)
    
    Parameters:
    - df: DataFrame containing the data
    - i0_low_idx: Lower index of I0 region (from slider)
    - i0_high_idx: Higher index of I0 region (from slider)
    - laser_power_column: Column containing laser power measurements
    - calculated_column_name: Name for the new calculated column
    
    Returns:
    - df: DataFrame with new calculated column added
    - i0_mean: Baseline value used for calculation
    """
    
    # Validate inputs
    if laser_power_column not in df.columns:
        # Try alternative column names
        alt_names = [
            'Detected Laser Power (W)', 
            'Laser Power (W)',
            'Laser power (W)'
        ]
        found_col = None
        for alt_name in alt_names:
            if alt_name in df.columns:
                laser_power_column = alt_name
                found_col = alt_name
                break
        
        if not found_col:
            available_cols = [col for col in df.columns if 'laser' in col.lower() or 'power' in col.lower()]
            raise ValueError(f"Laser power column not found. Available power-related columns: {available_cols}")
    
    if i0_low_idx >= len(df) or i0_high_idx >= len(df) or i0_low_idx >= i0_high_idx:
        raise ValueError(f"Invalid I0 region indices: {i0_low_idx} to {i0_high_idx} (dataframe length: {len(df)})")
    
    # Calculate I0 baseline (mean of clean air region)
    i0_region_data = df[laser_power_column].iloc[i0_low_idx:i0_high_idx]
    i0_mean = i0_region_data.mean()
    
    if pd.isna(i0_mean) or i0_mean <= 0:
        raise ValueError(f"Invalid I0 baseline calculated: {i0_mean}. Check I0 region data quality.")
    
    # Calculate extinction coefficient using Beer-Lambert law: -ln(I/I0)
    # Add small epsilon to prevent log(0) errors
    epsilon = 1e-10
    current_power = df[laser_power_column] + epsilon
    baseline_power = i0_mean + epsilon
    
    # Ensure we don't take log of negative or zero values
    intensity_ratio = np.maximum(current_power / baseline_power, epsilon)
    
    # Calculate extinction coefficient
    df[calculated_column_name] = -(1/.354) * np.log(intensity_ratio) * 1000000  # Convert to 1/Mm
    
    print(f"✅ Created extinction coefficient column: '{calculated_column_name}'")
    print(f"📊 I0 baseline: {i0_mean:.6f} W")
    print(f"📈 I0 region: indices {i0_low_idx} to {i0_high_idx} ({i0_high_idx - i0_low_idx} points)")
    print(f"📉 Extinction range: {df[calculated_column_name].min():.6f} to {df[calculated_column_name].max():.6f}")
    
    return df, i0_mean

def create_extinction_column_if_needed(gui_instance):
    """
    Check if 'Debug Ext Calculation' exists, if not, create extinction coefficient column.
    
    Parameters:
    - gui_instance: Reference to the PAXView GUI instance
    
    Returns:
    - column_name: Name of the column to use for calibration analysis
    - is_calculated: Boolean indicating if we created a calculated column
    - i0_baseline: Baseline value used (None if using existing column)
    """
    
    if constants.df_main.empty:
        raise ValueError("No data loaded")
    
    # Check if the original debug column exists
    debug_col = 'Debug Ext Calculation'
    if debug_col in constants.df_main.columns:
        print(f"✅ Using existing '{debug_col}' column")
        return debug_col, False, None
    
    # Column doesn't exist, create extinction coefficient column
    print(f"⚠️ '{debug_col}' not found - creating extinction coefficient column")
    
    try:
        # Get current I0 slider values
        i0_low = int(gui_instance.current_valueI0Low.get())
        i0_high = int(gui_instance.current_valueI0High.get())
        
        # Create the extinction coefficient column
        constants.df_main, i0_baseline = calculate_extinction_coefficient(
            constants.df_main, 
            i0_low, 
            i0_high, 
            calculated_column_name='Extinction_Coefficient'
        )
        
        return 'Extinction_Coefficient', True, i0_baseline
        
    except Exception as e:
        raise ValueError(f"Error creating extinction coefficient column: {str(e)}")

def update_listbox_with_new_column(gui_instance, highlight_column=None):
    """
    Update the listbox to show all columns, optionally highlighting a specific column.
    
    Parameters:
    - gui_instance: Reference to the PAXView GUI instance
    - highlight_column: Column name to highlight (optional)
    """
    gui_instance.listbox.delete(0, 'end')
    i = 0
    excluded_columns = ['Alarm', 'time', 'source_file']
    
    for column in constants.df_main.columns:
        if column not in excluded_columns:
            gui_instance.listbox.insert(i, column)
            
            # Regular alternating background
            if (i % 2) == 0:
                gui_instance.listbox.itemconfigure(i, background='#f0f0f0')
            
            # Highlight the specified column
            if column == highlight_column:
                gui_instance.listbox.itemconfigure(i, background='#90EE90', foreground='#006400')  # Light green with dark green text
            
            i += 1
            
def create_time_column(df):
    """
    Create a 'time' column using flexible logic:
    1. Try to combine 'Local Date' and 'Local Time' columns
    2. Try alternative time column combinations
    3. Fall back to row index if time columns unavailable/malformed
    
    Parameters:
    - df: DataFrame containing PAX data
    
    Returns:
    - time_series: pandas Series with time data (either datetime or index)
    - time_source: string describing what was used for time
    """
    
    time_series = None
    time_source = "unknown"
    
    # Strategy 1: Try standard Local Date + Local Time combination
    try:
        if 'Local Date' in df.columns and 'Local Time' in df.columns:
            print("📅 Attempting to create time from 'Local Date' + 'Local Time'")
            time_series = pd.to_datetime(
                df['Local Date'].astype(str) + ',' + df['Local Time'].astype(str), 
                format='%Y-%m-%d,%H:%M:%S'
            )
            time_source = "Local Date + Local Time"
            print(f"✅ Successfully created time column from {time_source}")
            return time_series, time_source
    except Exception as e:
        print(f"⚠️ Failed to create time from Local Date + Local Time: {str(e)}")
    
    # Strategy 2: Try alternative datetime column combinations
    datetime_combinations = [
        # (date_col, time_col, format)
        ('Date', 'Time', '%Y-%m-%d,%H:%M:%S'),
        ('Local Date', 'Local Time', '%m/%d/%Y,%H:%M:%S'),  # Alternative format
        ('Local Date', 'Local Time', '%Y-%m-%d %H:%M:%S'),  # Space instead of comma
        ('Date', 'Time', '%m/%d/%Y,%H:%M:%S'),
    ]
    
    for date_col, time_col, fmt in datetime_combinations:
        try:
            if date_col in df.columns and time_col in df.columns:
                print(f"📅 Attempting to create time from '{date_col}' + '{time_col}' with format {fmt}")
                
                if fmt.endswith(',%H:%M:%S'):
                    # Use comma separator
                    combined_str = df[date_col].astype(str) + ',' + df[time_col].astype(str)
                else:
                    # Use space separator
                    combined_str = df[date_col].astype(str) + ' ' + df[time_col].astype(str)
                
                time_series = pd.to_datetime(combined_str, format=fmt)
                time_source = f"{date_col} + {time_col}"
                print(f"✅ Successfully created time column from {time_source}")
                return time_series, time_source
        except Exception as e:
            print(f"⚠️ Failed with {date_col} + {time_col}: {str(e)}")
            continue
    
    # Strategy 3: Try existing combined datetime columns
    potential_time_columns = [
        'DateTime', 'Timestamp', 'Time', 'Date_Time', 'LocalTime', 
        'UTC_Time', 'Measurement_Time', 'Sample_Time'
    ]
    
    for col in potential_time_columns:
        try:
            if col in df.columns:
                print(f"📅 Attempting to use existing '{col}' column as time")
                time_series = pd.to_datetime(df[col])
                time_source = f"Existing {col} column"
                print(f"✅ Successfully created time column from {time_source}")
                return time_series, time_source
        except Exception as e:
            print(f"⚠️ Failed to use {col} as time: {str(e)}")
            continue
    
    # Strategy 4: Fall back to row index
    print("⚠️ No valid time columns found - falling back to row index")
    try:
        # Create a simple sequential time series based on row index
        # Assuming 1-second intervals (common for PAX data)
        time_series = pd.to_datetime('2000-01-01') + pd.to_timedelta(df.index, unit='s')
        time_source = "Row index (1-second intervals)"
        print(f"✅ Created time column from {time_source}")
        return time_series, time_source
    except Exception as e:
        print(f"❌ Even row index fallback failed: {str(e)}")
        # Last resort: just use integer index
        time_series = df.index
        time_source = "Integer row index"
        print(f"🔧 Using {time_source} as fallback")
        return time_series, time_source

def process_single_file_with_flexible_time(file_path, file_format):
    """
    Process a single PAX file with flexible time handling.
    
    Parameters:
    - file_path: Path to the file
    - file_format: 'V1' for CSV, 'V2' for Excel
    
    Returns:
    - df: Processed DataFrame with time column and cleaned data
    - time_source: Description of what was used for time
    """
    
    # Load the file
    if file_format == "V1":
        df = pd.read_csv(file_path)
    elif file_format == "V2":
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format selected.")
    
    print(f"📂 Processing file: {os.path.basename(file_path)}")
    print(f"📊 Original columns: {list(df.columns)}")
    print(f"📈 Original shape: {df.shape}")
    
    # Clean NaN values before any operations
    clearNaN(df)
    
    # Create time column with flexible logic
    time_series, time_source = create_time_column(df)
    
    # Drop unnecessary columns (only if they exist)
    columns_to_drop = [
        'Sec UTC', 'DOY UTC', 'Year UTC', 'Sec Local', 'DOY Local', 'Year Local',
        'Local Date', 'Local Time', 'Reserved.1', 'Reserved.2', 'Reserved.3',
        'Reserved.4', 'Reserved.5'
    ]
    
    existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
    if existing_columns_to_drop:
        df.drop(columns=existing_columns_to_drop, inplace=True)
        print(f"🗑️ Dropped columns: {existing_columns_to_drop}")
    
    # Add the time column
    df['time'] = time_series
    
    print(f"⏰ Time source: {time_source}")
    print(f"🕐 Time range: {df['time'].min()} to {df['time'].max()}")
    print(f"✅ Final shape: {df.shape}")
    
    return df, time_source

# Updated version of the existing functions to use flexible time handling

def pax_analyzer_flexible(file_path, selected, listbox, gui_instance=None):
    """
    Enhanced version of pax_analyzer with flexible time handling.
    """
    print("File path is " + file_path + ".")
    
    try:
        # Process the file with flexible time handling
        df, time_source = process_single_file_with_flexible_time(file_path, selected.get())
        
        df = fix_pax_data_time_issue(df)

        # Add source file tracking
        df['source_file'] = os.path.basename(file_path)
        
        # Populate the listbox with column names
        populate_listbox(listbox, df)
        update_df_main(df)
        
        # Show summary of what was loaded
        summary_msg = (
            f"✅ File loaded successfully!\n\n"
            f"📁 File: {os.path.basename(file_path)}\n"
            f"📊 Rows: {len(df):,}\n"
            f"⏰ Time source: {time_source}\n"
            f"🕐 Time range: {df['time'].min()} to {df['time'].max()}"
        )
        
        messagebox.showinfo("File Loaded", summary_msg)
        print(constants.df_main)
        
        # Update slider ranges after loading data
        if gui_instance is not None:
            gui_instance.update_slider_ranges_after_load()
            
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(error_msg)
        messagebox.showerror("File Processing Error", error_msg)

def process_multiple_files_automatically_flexible(file_paths, selected, listbox, gui_instance=None, pb=None):
    """
    Enhanced version of process_multiple_files_automatically with flexible time handling.
    """
    if not file_paths:
        messagebox.showerror("Error", "No files to process!")
        return
    
    if pb:
        pb.start()
    
    dataframes = []
    failed_files = []
    time_sources = {}
    
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
                
                # Process file with flexible time handling
                df, time_source = process_single_file_with_flexible_time(file_path, selected.get())
                
                df = fix_pax_data_time_issue(df)

                # Add a source file column to track which file each row came from
                df['source_file'] = os.path.basename(file_path)
                
                dataframes.append(df)
                time_sources[os.path.basename(file_path)] = time_source
                print(f"✅ Successfully processed: {os.path.basename(file_path)} ({len(df)} rows, time: {time_source})")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {str(e)}")
                failed_files.append(file_path)
                continue
        
        # Concatenate all successfully processed dataframes
        if dataframes:
            # Sort dataframes by their first timestamp to maintain chronological order
            # Handle both datetime and integer index cases
            def get_sort_key(df):
                try:
                    return df['time'].min()
                except:
                    return 0  # Fallback for integer indices
            
            dataframes.sort(key=get_sort_key)
            
            # Concatenate all dataframes
            concatenated_df = pd.concat(dataframes, ignore_index=True)
            
            # Sort the final dataframe by time to ensure proper chronological order
            try:
                concatenated_df.sort_values('time', inplace=True)
                concatenated_df.reset_index(drop=True, inplace=True)
            except:
                print("⚠️ Could not sort by time (may be using index-based time)")
            
            # Update the global dataframe
            update_df_main(concatenated_df)
            
            # Populate the listbox with column names
            populate_listbox(listbox, concatenated_df)
            
            # Update slider ranges if GUI instance is available
            if gui_instance is not None:
                gui_instance.update_slider_ranges_after_load()
            
            # Show comprehensive summary
            total_rows = len(concatenated_df)
            successful_files = len(dataframes)
            
            # Create time sources summary
            time_summary = "\n".join([f"  • {file}: {source}" for file, source in time_sources.items()])
            
            try:
                time_range = f"{concatenated_df['time'].min()} to {concatenated_df['time'].max()}"
            except:
                time_range = "Index-based time"
            
            summary_message = (
                f"🎉 Batch Processing Complete!\n\n"
                f"✅ Successfully processed: {successful_files} files\n"
                f"📊 Total data points: {total_rows:,}\n"
                f"⏰ Time range: {time_range}\n\n"
                f"🕐 Time sources used:\n{time_summary}\n\n"
                f"📁 Source files tracked in 'source_file' column"
            )
            
            if failed_files:
                summary_message += f"\n\n❌ Failed files ({len(failed_files)}):\n"
                summary_message += "\n".join([f"  • {os.path.basename(f)}" for f in failed_files])
            
            messagebox.showinfo("Batch Processing Results", summary_message)
            
            print(f"🎯 Final concatenated dataframe shape: {concatenated_df.shape}")
            print(f"📋 Columns: {list(concatenated_df.columns)}")
            
        else:
            messagebox.showerror("Error", "No files were successfully processed!")
            
    except Exception as e:
        messagebox.showerror("Batch Processing Error", f"Error during batch processing: {str(e)}")
        
    finally:
        if pb:
            pb.stop()

def concatenate_df_flexible(file_path, selected, listbox):
    """
    Enhanced version of concatenate_df with flexible time handling.
    """
    try:
        # Process file with flexible time handling
        df_to_add, time_source = process_single_file_with_flexible_time(file_path, selected.get())
        
        # Add source file tracking
        df_to_add['source_file'] = os.path.basename(file_path)
        
        if constants.df_main is not None and not constants.df_main.empty:
            constants.df_main = pd.concat([constants.df_main, df_to_add], ignore_index=True)
        else:
            constants.df_main = df_to_add
        
        # Populate the listbox with column names
        populate_listbox(listbox, constants.df_main)
        
        # Show success message
        messagebox.showinfo("File Added", 
                          f"✅ File concatenated successfully!\n\n"
                          f"📁 File: {os.path.basename(file_path)}\n"
                          f"⏰ Time source: {time_source}\n"
                          f"📊 Total rows now: {len(constants.df_main):,}")
        
        print(constants.df_main)
        
    except Exception as e:
        error_msg = f"Error concatenating file: {str(e)}"
        messagebox.showerror("Concatenation Error", error_msg)

# ==================== END OF EXTINCTION COEFFICIENT IMPLEMENTATION ====================

# ==================== START OF TIME PARSING FIX ====================

def convert_excel_serial_date(date_serial, time_serial):
    """
    Convert Excel serial date and time to proper datetime.
    """
    try:
        # Excel epoch (accounting for the 1900 leap year bug)
        excel_epoch = datetime(1899, 12, 30)
        
        # Convert date
        date_part = excel_epoch + timedelta(days=int(date_serial))
        
        # Convert time (decimal fraction of day to hours/minutes/seconds)
        time_seconds = time_serial * 24 * 60 * 60
        time_part = timedelta(seconds=time_seconds)
        
        return date_part + time_part
        
    except Exception as e:
        print(f"Warning: Excel date conversion failed: {e}")
        return None

def create_time_column_enhanced(df):
    """
    Enhanced time column creation that handles Excel serial dates.
    """
    
    time_series = None
    time_source = "unknown"
    
    # Strategy 1: Try Excel serial date conversion
    try:
        if 'Local Date' in df.columns and 'Local Time' in df.columns:
            # Check if these are numeric (Excel serial dates)
            first_date = df['Local Date'].iloc[0]
            first_time = df['Local Time'].iloc[0]
            
            if isinstance(first_date, (int, float)) and isinstance(first_time, (int, float)):
                print("📅 Detected Excel serial date format - converting...")
                
                # Convert Excel serial dates to proper datetime
                datetime_list = []
                for idx, row in df.iterrows():
                    dt = convert_excel_serial_date(row['Local Date'], row['Local Time'])
                    if dt:
                        datetime_list.append(dt)
                    else:
                        # Fallback for failed conversions
                        datetime_list.append(datetime(2000, 1, 1) + timedelta(seconds=idx))
                
                time_series = pd.Series(datetime_list)
                time_source = "Excel serial date conversion"
                print(f"✅ Successfully converted Excel serial dates")
                print(f"Time range: {time_series.min()} to {time_series.max()}")
                return time_series, time_source
                
    except Exception as e:
        print(f"⚠️ Excel serial date conversion failed: {str(e)}")
    
    # Strategy 2: Try standard string datetime conversion
    try:
        if 'Local Date' in df.columns and 'Local Time' in df.columns:
            print("📅 Attempting standard string datetime conversion")
            time_series = pd.to_datetime(
                df['Local Date'].astype(str) + ',' + df['Local Time'].astype(str), 
                format='%Y-%m-%d,%H:%M:%S'
            )
            time_source = "String datetime conversion"
            print(f"✅ Successfully created time from strings")
            return time_series, time_source
    except Exception as e:
        print(f"⚠️ String datetime conversion failed: {str(e)}")
    
    # Strategy 3: Fall back to row index
    print("⚠️ Using row index fallback for time")
    try:
        time_series = pd.to_datetime('2000-01-01') + pd.to_timedelta(df.index, unit='s')
        time_source = "Row index (1-second intervals)"
        print(f"✅ Created synthetic time from row index")
        return time_series, time_source
    except Exception as e:
        print(f"❌ Even row index fallback failed: {str(e)}")
        time_series = df.index
        time_source = "Integer row index"
        return time_series, time_source

def fix_pax_data_time_issue(df):
    """
    Quick fix specifically for PAX data files with Excel serial dates.
    Call this right after loading your CSV file.
    """
    
    print("🔧 Applying PAX data fixes...")
    
    # Fix 1: Convert Excel serial dates to proper datetime
    time_series, time_source = create_time_column_enhanced(df)
    df['time'] = time_series
    print(f"✅ Time column fixed: {time_source}")
    
    # Fix 2: Handle column name differences
    if 'Laser power (W)' in df.columns and 'Detected Laser power (W)' not in df.columns:
        df['Detected Laser power (W)'] = df['Laser power (W)']
        print("✅ Added 'Detected Laser power (W)' alias")
    
    # Fix 3: Create extinction coefficient if missing Debug Ext Calculation
    if 'Debug Ext Calculation' not in df.columns:
        print("⚠️ Missing 'Debug Ext Calculation' - you'll need to create extinction coefficient")
        print("💡 Use the 'Create Extinction Column' button after loading")
    
    return df

def enhanced_calibration_analysis(df, xlocA, xlocB, min_val, max_val, percent, mode='Scattering'):
    """
    Enhanced calibration analysis with comprehensive debugging and error handling.
    """
    
    print("🔍 Enhanced Calibration Analysis Starting...")
    print("=" * 50)
    
    debug_info = {
        'step_counts': {},
        'issues': [],
        'recommendations': [],
        'data_stats': {}
    }
    
    # Step 1: Validate inputs and data
    print(f"📊 Step 1: Input Validation")
    print(f"Mode: {mode}")
    print(f"Calibration region: {xlocA} to {xlocB}")
    print(f"Range filter: {min_val} to {max_val}")
    print(f"Percentage limit: {percent}%")
    
    if xlocA >= xlocB:
        error_msg = f"Invalid calibration region: start ({xlocA}) >= end ({xlocB})"
        debug_info['issues'].append(error_msg)
        raise ValueError(error_msg)
    
    if xlocB >= len(df):
        error_msg = f"Calibration end ({xlocB}) exceeds data length ({len(df)})"
        debug_info['issues'].append(error_msg)
        debug_info['recommendations'].append(f"Set calibration end to < {len(df)}")
        raise ValueError(error_msg)
    
    region_size = xlocB - xlocA
    debug_info['step_counts']['region_size'] = region_size
    
    if region_size < 10:
        warning = f"Small calibration region ({region_size} points)"
        debug_info['issues'].append(warning)
        debug_info['recommendations'].append("Consider expanding calibration region")
    
    # Step 2: Determine extinction column
    print(f"\n🔬 Step 2: Extinction Column Detection")
    
    ext_column = None
    if 'Debug Ext Calculation' in df.columns:
        ext_column = 'Debug Ext Calculation'
        print(f"✅ Using existing '{ext_column}'")
    elif 'Extinction_Coefficient' in df.columns:
        ext_column = 'Extinction_Coefficient'
        print(f"✅ Using calculated '{ext_column}'")
    else:
        error_msg = "No extinction column found - need to create extinction coefficient first"
        debug_info['issues'].append(error_msg)
        debug_info['recommendations'].append("Create extinction coefficient using I0 baseline")
        
        # Try to find laser power column for guidance
        laser_columns = ['Detected Laser power (W)', 'Laser power (W)', 'Detected Laser Power (W)']
        found_laser = None
        for col in laser_columns:
            if col in df.columns:
                found_laser = col
                break
        
        if found_laser:
            debug_info['recommendations'].append(f"Use '{found_laser}' to calculate extinction coefficient")
        
        raise ValueError(error_msg)
    
    # Step 3: Extract calibration region data
    print(f"\n🎯 Step 3: Data Extraction")
    
    try:
        filtered_time = df['time'].iloc[xlocA:xlocB] if 'time' in df.columns else df.index[xlocA:xlocB]
        filtered_dfx = df['Bscat (1/Mm)'].iloc[xlocA:xlocB]
        
        if mode == 'Scattering':
            filtered_dfy = df[ext_column].iloc[xlocA:xlocB]
            y_column_name = ext_column
        else:  # Absorbing mode
            filtered_dfy = (df[ext_column].iloc[xlocA:xlocB] - 
                           df['Bscat (1/Mm)'].iloc[xlocA:xlocB])
            y_column_name = f"{ext_column} - Bscat"
        
        initial_count = len(filtered_dfy)
        debug_info['step_counts']['initial'] = initial_count
        
        print(f"✅ Extracted {initial_count} points")
        print(f"X-data (Bscat) range: {filtered_dfx.min():.3f} to {filtered_dfx.max():.3f}")
        print(f"Y-data ({y_column_name}) range: {filtered_dfy.min():.6f} to {filtered_dfy.max():.6f}")
        
        # Store data statistics
        debug_info['data_stats'] = {
            'x_min': float(filtered_dfx.min()),
            'x_max': float(filtered_dfx.max()),
            'y_min': float(filtered_dfy.min()),
            'y_max': float(filtered_dfy.max()),
            'y_mean': float(filtered_dfy.mean()),
            'y_std': float(filtered_dfy.std())
        }
        
    except Exception as e:
        error_msg = f"Data extraction failed: {str(e)}"
        debug_info['issues'].append(error_msg)
        raise ValueError(error_msg)
    
    # Step 4: Apply percentage change filter
    print(f"\n📈 Step 4: Percentage Change Filter")
    
    y_pct_change = filtered_dfy.pct_change() * 100
    
    # Handle the first NaN value from pct_change
    mask_pct = (y_pct_change.abs() <= percent) | (y_pct_change.isna())
    
    filtered_dfy_pct = filtered_dfy[mask_pct]
    filtered_dfx_pct = filtered_dfx[mask_pct]
    filtered_time_pct = filtered_time[mask_pct]
    
    after_pct_count = len(filtered_dfy_pct)
    debug_info['step_counts']['after_percent'] = after_pct_count
    
    print(f"Points before: {initial_count}")
    print(f"Points after: {after_pct_count}")
    print(f"Points removed: {initial_count - after_pct_count}")
    
    if after_pct_count == 0:
        # Analyze percentage changes to give better recommendations
        pct_changes_valid = y_pct_change.dropna()
        if len(pct_changes_valid) > 0:
            max_pct = pct_changes_valid.abs().max()
            p95_pct = pct_changes_valid.abs().quantile(0.95)
            
            error_msg = f"All points removed by percentage change filter ({percent}%)"
            debug_info['issues'].append(error_msg)
            debug_info['recommendations'].append(f"Increase percentage limit to at least {max_pct:.1f}%")
            debug_info['recommendations'].append(f"Recommended: {p95_pct:.1f}% (95th percentile)")
            
            print(f"❌ {error_msg}")
            print(f"Max percentage change: {max_pct:.2f}%")
            print(f"95th percentile: {p95_pct:.2f}%")
        
        raise ValueError("No data points survived percentage change filter")
    
    # Step 5: Apply range filter
    print(f"\n📊 Step 5: Range Filter")
    
    mask_range = (filtered_dfy_pct >= min_val) & (filtered_dfy_pct <= max_val)
    
    filtered_dfx_final = filtered_dfx_pct[mask_range]
    filtered_dfy_final = filtered_dfy_pct[mask_range]
    filtered_time_final = filtered_time_pct[mask_range]
    
    final_count = len(filtered_dfy_final)
    debug_info['step_counts']['final'] = final_count
    
    print(f"Points before: {after_pct_count}")
    print(f"Points after: {final_count}")
    print(f"Points removed: {after_pct_count - final_count}")
    
    if final_count == 0:
        data_min = filtered_dfy_pct.min()
        data_max = filtered_dfy_pct.max()
        
        error_msg = f"All points removed by range filter ({min_val} to {max_val})"
        debug_info['issues'].append(error_msg)
        
        # Provide specific recommendations based on data range
        if data_max < min_val:
            debug_info['recommendations'].append(f"Lower min value to below {data_max:.3f}")
        elif data_min > max_val:
            debug_info['recommendations'].append(f"Raise max value to above {data_min:.3f}")
        else:
            debug_info['recommendations'].append(f"Expand range to {data_min:.3f} to {data_max:.3f}")
        
        print(f"❌ {error_msg}")
        print(f"Data actually ranges from {data_min:.6f} to {data_max:.6f}")
        
        raise ValueError("No data points survived range filter")
    
    # Step 6: Final validation
    print(f"\n✅ Step 6: Final Results")
    print(f"Final data points: {final_count}")
    print(f"Data retention: {(final_count/initial_count*100):.1f}%")
    
    if final_count < 5:
        warning = f"Very few points remaining ({final_count}) - regression may be unreliable"
        debug_info['issues'].append(warning)
        debug_info['recommendations'].append("Consider relaxing filter parameters")
    
    # Calculate correlation for quality assessment
    if final_count > 1:
        correlation = np.corrcoef(filtered_dfx_final, filtered_dfy_final)[0, 1]
        debug_info['data_stats']['correlation'] = float(correlation)
        print(f"Correlation: {correlation:.3f}")
        
        if abs(correlation) < 0.1:
            debug_info['issues'].append("Very low correlation between X and Y data")
    
    # Return the filtered data
    filtered_data = {
        'x': filtered_dfx_final,
        'y': filtered_dfy_final,
        'time': filtered_time_final,
        'count': final_count,
        'x_column': 'Bscat (1/Mm)',
        'y_column': y_column_name
    }
    
    print("=" * 50)
    print("🎉 Analysis completed successfully!")
    
    return filtered_data, debug_info