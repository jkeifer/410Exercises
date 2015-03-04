Exercise 5: Importing a Python Script into an ArcGIS Toolbox
============================================================
for GEOG 410/510 winter term 2015


**Instructions**

Provided in this directory are a number of python files,
as well as a data directory containing a file geodatabase.
The lab4_part2.py file is my example code for Lab 4 with
some minor modifications (the modifications will be reviewed
in class). Also provided is a file named tkinter_interface.py.
This file is an example of a GUI interface built using the
native python tkinter framework. You can run it by double-clicking
the python file; it will start and you can play around with it.
Again, the specifics of this file will be reviewed in class. Also,
this file is not relevant to the assignment; it is included merely
as reference.

The two files that are directly appliciable to the assignment are
arcgis_interface.py and arcgis_validation.py. You will need to read
through both of these files and make sure you understand how they
work. The arcgis_interface.py file you will import into a new
ArcGIS toolbox within the ArcGIS Desktop interface. You will need
to setup all the parameters listed in the interface file as
appropriate.

Once the script has been imported, you will need to setup the
validation of the script parameters. To do this, right-click on
the script tool in the toolbox you created and select "Properties".
In the properties window, click on the validation tab, click the edit
button, then copy the contents into of the arcgis_validation.py file
into the edit window, replacing everything that was there. Save the
modified file, close the edit window, then click apply in the
tool's properties window.

Now the tool should be setup correctly. Give it a test run. Try
modifying the parameters to be incorrect and see how the tool
responds. Take a screenshot of the tool interface. This will be
your only submission for this exercise.

**Submissions and Points**

All that need be submitted for this exercise is the screenshot
of the completed tool GUI in ArcGIS. Please email it to the instructor,
attaching the file named as `LastnameFirstname_Exercise5.ext`, with
your last name, first name, and correct file extension for your
image file type.

This exercise is worth a total of 10 points.
