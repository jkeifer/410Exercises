Exercise 1: Cursors and Geometry Objects
========================================
for GEOG 410/510 winter term 2015


**Instructions**

THe first purpose of this exercise is to provide an example of
a simple script that uses arcpy cursors and geometry objects.
To that end, a PDF of such a python script is provided.
However, while the logic and program flow is correct and complete,
the example is lacking in documentation and all the function,
constant, and variable names are inappropriate.

Thus, to meet the second goal of this exercise, which is to test your
python and arcpy comprehension, your task is to add all
the missing comments, documenting what happens in every step of the
program. Everywhere you find a `#` comment sign you must add a comment
explaining what happens in the following statement and why. Additionally,
you must also change all the names in the script to be appropriate
given the purpose and value(s) of each function, constant, and variable.
For example, the constant `A` could be renamed to something like
`INPUT_SHAPEFILE`.

The code provided is specifically in PDF format as an image to prevent
copying and pasting the code from the example to your submission.
Typing out code examples and snippets by hand is much better for
memorization and learning than simply copying and pasting bits
and pieces from here and there.

Also included is a data directory containing a point dataset in
shapefile format. You can run the script to see what the input
and output look like to ascertain the code's specific operations.
The script was tested with the provided data and said data is
known to be compatible with the script as it is setup.
However, the script should be able to process any point feature
class, so feel free to try it with different data, if you desire.
You may need, depending the data used, to change the spatial
reference assigned to the constant `C`. In either case,
set the constant `A` to the path of the input point dataset.

You may also desire to change the value of parameter `D`, whether
you process different data or the sample data (hint: `D` is a linear
measurement in the units of the output spatial reference). If you
run the script, have both the input and output data in a map document,
and do not see the effect, you many want to try zooming in or
increasing the value of `D`.


**Submissions and Points**

All that need be submitted for this exercise is a .py file with the
commented and better-named code. Please email it to the instructor,
attaching the file named as `LastnameFirstname_Exercise1.py`, with
your last name and first name.

This exercise is worth a total of 10 points. Points will be given
based on the quality/thoroughness of comments, the quality and
appropriateness of variable/function/constant names, and how well
the submitted code matches the example code in all other areas.
Keep in mind that part of this assignment is to test your code
comprehension; do not write comments as you might for an actual
script, but to show your understanding of every step of the example
program's execution. You will not be penalized for too many
comments, or for comments that are too long. The names you choose,
however, should be as you would use in an actual script; clear,
concise names that accurately describe operation or purpose are
required.
