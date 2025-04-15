import csv
import os

geometry_width_pct = 0.8
geometry_height_pct = 0.8

logo_name = DropletLogoTemp.png

col_index = 0

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
    "Reserved",
    "Reserved",
    "HK Case Temperature (C)",
    "HK Case Pressure (mbar)",
    "Reserved",
    "HK plus5V",
    "HK 3.3V",
    "Debug Ext Calculation",
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