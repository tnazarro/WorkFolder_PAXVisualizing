====================
Pax Analyzer 2.0
====================

(Current To-Do list/explanation): Refining module separation, improving plotting options/interface
(In more detail): Once MVC modules are set up, moving on to feature additions including: version tracking, report generation, file concatenation, and gui improvements


Description
===========

This program acts as a visualizer and simplified calibration tool for the PAX (PhotoAcoustic eXtinctiometer) at DMT (Droplet Measurement Technologies). It is primarily an internal use tool to expedite data analysis and visualization.


Features
--------

* Quickly run scattering/absorbing calibration procedures, when given standard form housekeeping files in the .xlsx or .csv format, for the PAX software version 3.1.2
* Translates alarm codes to a more ledgible output
* Quickly graph the 5 most relevant data channels 
* Creates a pandas dataframe, df, for flexible data analysis


Upcoming Features
--------

* Arbitrary number of simultaneous plots
* I0 selection for calibration
* Alpha filtering optional view (deprecated)
* Software versioning using PAX.txt input
* Filter out flush/zero information automatically/toggleable (done automatically now, toggleable later)
* Concatenate multiple files 
* Generate clean calibration report summaries
* Sig figs in r^2 summary


Authors
=========

Tate Nazarro (lead)
Jesse Steiner (supervisor)
Tanner Coggins (resource)


Requirements
=========

* Python 3
* Tkinter
* pyinstaller (used to create sharable exe file)


Usage
========

To start the application, simply open the executable located in the "Most recent" file directory


General Notes
========
The program works best when given the standard file format housekeeping file for PAX data. A number of PAX data files are available in the FTP output of the PAX, but we will be focusing on those of the format "PAX-XXX_20250131.csv" and "PAX.txt"