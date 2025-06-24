import csv
import os
import pandas as pd

# Constants for the GUI layout and configuration
geometry_width_pct = 1.0
geometry_height_pct = 1.0

#Location of the logo image
logo_name = "assets\\DropletLogoTemp.png"
#Double check the path to the logo image

#starting column index (if implemented)
col_index = 0

#Adding an easily accessible location for the dataframe to be saved to
df_main = pd.DataFrame()
#Adding a second dataframe for concatenation of dataframes
df_to_add = pd.DataFrame()

#Column names for the PAX alarm data
alarm_names = [
    "Bscat (1/Mm)",
    "scat_raw",
    "Babs (1/Mm)",
    "Babs phase (deg)",
    "Babs noise (1/Mm)",
    "Detected Laser power (W)",
    "Laser power phase (deg)",
    "Q factor",
    "Reserved",
    "Resonance Frequency (Hz)",
    "Background Bscat (1/Mm)",
    "mic_raw",
    "Background Babs (1/Mm)",
    "Background Babs phase (deg)",
    "Bext (1/Mm)",
    "Single Scat Albedo",
    "BC Mass (ug/m3)",
    "Relative Humidity (%)",
    "Cell Temperature (C)",
    "Dewpoint (C)",
    "Analong Input 1",
    "Analong Input 2",
    "Calibration Bscat",
    "Calibration Babs",
    "Alpha",
    "Processing",
    "HK Case Temperature (C)",
    "HK Case Pressure (mbar)",
    "Reserved",
    "HK plus5V",
    "HK 3.3V",
    "Calibration Bext",
    "HK 5Vdig",
    "Calibration I0",
    "Reserved",
    "Reserved",
    "HK Laser PD Current (Amp)",
    "HK Laser Current (Amp)",
    "HK Laser Temp (C)",
    "HK minus5V",
    "HK Cell Pressure (mbar)",
    "HK Inlet Pressure (mbar)",
    "HK Sample Pump Vac (mbar)",
    "HK 12V",
    "Reserved",
    "Mode",
    "Countdown Timer (secs)",
    "Disk Free Space (Gbytes)",
    "Laser on Time (hours)",
    "Reserved",
    "USB Status",
] 

#Not too much to set up as initial values, but this constants file is a good place to put them