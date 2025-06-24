====================
Pax Analyzer 3.0
====================

(Current To-Do list/explanation): Add PADS style data slicer/Add ability to select regions of data to view


Description
===========

This program acts as a visualizer and simplified calibration tool for the PAX (PhotoAcoustic eXtinctiometer) at DMT (Droplet Measurement Technologies). It is primarily an internal use tool to expedite data analysis and visualization.
The PAX Data Visualizer is a comprehensive analysis tool designed to streamline PAX data processing and visualization. This application automatically handles parts of the PAX data analysis, including loading multiple files simultaneously, converting various time formats, and creating calculated extinction coefficients when missing from older instrument software. The visualizer provides an intuitive interface that transforms time-consuming manual tasks into efficient, one-click operations.
At its core, the application offers two primary functions: interactive data visualization with real-time plotting controls, and automated calibration analysis with some statistical validation. The visualization system allows you to explore your data using either single-axis overlays or individual subplots, with interactive sliders for selecting I0 baseline and calibration regions. The calibration dashboard provides analysis capabilities for both scattering and absorbing modes, detailed error diagnostics with actionable recommendations, and integrated note-taking for research documentation.
The application works well with PAX data from multiple software generations, automatically adapting to different file formats and column structures.


Features
--------

Modern Interface Design

Intuitive layout: Organized into logical sections with collapsible panels
Progress tracking: Visual feedback during multi-file processing operations
Color-coded buttons: Clear visual hierarchy for different function types
Professional styling: Modern color scheme with consistent iconography

Comprehensive Data Summary

Multi-source overview: Detailed breakdown of loaded files and row counts
Time range analysis: Automatic detection and display of temporal coverage
Column inventory: Complete listing of available measurement parameters
Processing history: Track of applied transformations and data sources

Authors
=========

Tate Nazarro (lead)
Jesse Steiner (supervisor)
Jaren Fleischman (resource)


Requirements
=========

* Python 3
* Tkinter
* pyinstaller (used to create sharable exe file)
--Suggested pyinstaller command: pyinstaller --onefile --windowed --add-data "assets;assets" --name "PAX_Data_Visualizer" main.py


Usage
========

To start the application, simply open the executable located in the "Most recent" file directory


General Notes
========
The program works best when given the standard file format housekeeping file for PAX data. A number of PAX data files are available in the FTP output of the PAX, but we will be focusing on those of the format "PAX-XXX_20250131.csv" and "PAX.txt"