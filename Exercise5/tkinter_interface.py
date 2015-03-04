print "Starting GUI...\n"

import os
import re
from Tkinter import *
from ttk import *
import tkFileDialog
from arcpy import Describe, Exists
from lab4_part2 import REQUIRED_LAYERS, OUT_NAME


entries = {}


class LabeledEntry(Entry):
    def __init__(self, master, labeltext, required=False,
                 *args, **kwargs):
        self.required = required
        column = kwargs.pop('column', None)
        row = kwargs.pop('row', None)

        label_args = kwargs.pop('label_args', ())
        label_kwargs = kwargs.pop('label_kwargs', {})

        self.label = Label(master, *label_args,
                           text=labeltext, **label_kwargs)
        self.label.grid(column=column, row=row, sticky=E)

        initial_value = kwargs.pop("default", "")
        #assert self.validate(initial_value), "Invalid initial_value given"
        self.text = StringVar(value=initial_value)

        Entry.__init__(self, master, *args, textvariable=self.text, **kwargs)
        self.grid(column=column+1, row=row, sticky=E)

        self.is_valid = self.validate(self.text.get())

        self.vcmd = self.register(self.validate)
        self.ivcmd = self.register(self._invalid_value)
        self["validate"] = kwargs.pop("validate", "focusout")
        self["validatecommand"] = self.vcmd, "%P",
        self["invalidcommand"] = self.ivcmd,

    def validate(self, value):
        if value is "":
            if self.required:
                self._invalid_value()
                return False
        self._valid_value()
        return True

    def _invalid_value(self):
        self.is_valid = False
        self.label.configure(foreground="red")

    def _valid_value(self):
        self.is_valid = True
        self.label.configure(foreground="black")


class FloatEntry(LabeledEntry):
    def __init__(self, master, labeltext, required=False,
                 *args, **kwargs):
        self.min = kwargs.pop('minimum', None)
        self.min_inclusive = kwargs.pop('min_inclusive', True)
        self.max = kwargs.pop('maximum', None)
        self.max_inclusive = kwargs.pop('max_inclusive', True)

        initial_value = 0.0
        if not required:
            initial_value = ""

        initial_value = kwargs.pop("default", initial_value)

        LabeledEntry.__init__(self, master, labeltext, *args,
                              default=initial_value,
                              required=required,
                              **kwargs)

        self.vcmd = self.register(self.validate)
        self["validatecommand"] = self.vcmd, "%P",

    def get_float(self):
        return float(self.get())

    def validate(self, value):
        if value is "":
            if self.required:
                self._invalid_value()
                return False
            else:
                self._valid_value()
                return True

        try:
            value = float(value)
        except ValueError:
            self._invalid_value()
            return False

        if not self.min is None:
            try:
                assert value >= self.min if self.min_inclusive else value > self.min
            except AssertionError:
                self._invalid_value()
                return False

        if not self.max is None:
            try:
                assert value <= self.max if self.max_inclusive else value < self.max
            except AssertionError:
                self._invalid_value()
                return False

        self._valid_value()
        return True


class GeodatabaseEntry(LabeledEntry):
    def __init__(self, master, labeltext, required=True, required_layers=None,
                 *args, **kwargs):
        self.required_layers = required_layers

        LabeledEntry.__init__(self, master, labeltext, *args,
                              required=required,
                              **kwargs)

        self.last_validated_value = self.get()

        self.vcmd = self.register(self.validate)
        self['validatecommand'] = self.vcmd, '%P',

    def validate(self, value, previous_value=None):
        if value is "":
            if self.required:
                self._gdb_invalid_value(value)
                return False
            else:
                self_gdb._valid_value(value)
                return True

        if self.last_validated_value == value:
            if self.is_valid:
                return True
            else:
                return False

        # get rid of quotes at beginning or end to prevent crashing arcpy
        if value.startswith('"'):
            self.delete(0)
            value = value[1:]

        if value.endswith('"'):
            self.delete(len(self.get()) - 1)
            value = value[:-1]

        if not valid_geodatabase(value):
            self._gdb_invalid_value(value)
            return False

        if self.required_layers:
            if not has_required_layers(value, self.required_layers):
                self._gdb_invalid_value(value)
                return False

        self._gdb_valid_value(value)
        return True

    def _gdb_invalid_value(self, value):
        self._invalid_value()
        self.last_validated_value = value

    def _gdb_valid_value(self, value):
        self._valid_value()
        self.last_validated_value = value


class ListEntry(LabeledEntry):
    def __init__(self, master, labeltext, required=False, element_type=None,
                 *args, **kwargs):
        self.type = element_type

        LabeledEntry.__init__(self, master, labeltext, *args,
                              required=required, **kwargs)

        self.vcmd = self.register(self.validate)
        self['validatecommand'] = self.vcmd, '%P',

    def validate(self, value):
        if value is "":
            if self.required:
                self._invalid_value()
                return False
            else:
                self._valid_value()
                return True

        try:
            self.get_list(value)
        except Exception:
            self._invalid_value()
            return False

        self._valid_value()
        return True

    def get_list(self, text=None):
        # text can be passed in for validation routine
        if not text:
            text = self.get()

        # find all individual elements of the list
        values = re.findall(r"[\w']+", text)

        # if list is typed, make sure all elements are converted
        # to type
        goodvalues = []
        if self.type:
            for value in values:
                goodvalues.append(self.type(value))
        else:
            # if not typed then just take the values
            goodvalues = values

        return goodvalues


def valid_geodatabase(geodatabase):
    if not geodatabase:
        return False

    if not Exists(geodatabase):
        return False

    try:
        desc = Describe(geodatabase)
        assert desc.DataType == 'Workspace'
        assert desc.workspacetype == 'LocalDatabase'
    except IOError:
        return False
    except AssertionError:
        return False
    else:
        return True


def has_required_layers(workspace, required_layers):
    """Check a workspace for required layers.
    Returns True if all layers are present, or False
    if one or more layers are missing.
    """
    for layer in required_layers:
        if not Exists(os.path.join(workspace, layer)):
            return False
    return True


def browse_gdb(geodatabase_entry):
    # see if current value is a directory and if not try to make it a directory
    currentdir = geodatabase_entry.get()
    while not os.path.exists(currentdir) and currentdir:
        currentdir = os.path.dirname(currentdir)

    # if current directory is empty, use the path to this file as
    # the default path
    if not currentdir:
        currentdir = os.path.abspath(__file__)

    # open a select directory window using currentdir as the inital location
    newpath = tkFileDialog.askdirectory(parent=geodatabase_entry,
                                        mustexist=True,
                                        title='Select your analysis geodatabase...',
                                        initialdir=currentdir)

    # if directory dialog returned a value, delete contents of
    # the geodatabase entry, insert the new path, then validate
    if newpath:
        geodatabase_entry.delete(0, len(geodatabase_entry.get()) + 1)
        geodatabase_entry.insert(0, newpath)
        geodatabase_entry.validate(geodatabase_entry.get())


def run_analysis(entries):
    # check to make sure all entry values are valid
    valid_values = True
    for entry in entries.itervalues():
        valid_values = valid_values and entry.is_valid

    # check to make sure output doesn't already exist if not overwriting
    if not entries["overwrite"].var.get():
        if Exists(os.path.join(entries["geodatabase"].get(), OUT_NAME)):
            print "Output FC already exists in geodatabase " + \
                      "(use overwrite option to force processing)."
            return

    # if all values are valid then run the analysis
    if valid_values:
        from lab4_part2 import main
        main(geodatabase=entries["geodatabase"].get(),
             min_elevation=entries["min_elevation"].get_float(),
             max_elevation=entries["max_elevation"].get_float(),
             overwrite_output=entries["overwrite"].var.get(),
             max_water_distance=entries["max_water_dist"].get_float(),
             min_area=entries["min_area"].get_float(),
             soil_type=entries["soil_types"].get_list(),
             max_slope=entries["max_slope"].get_float(),
             )
        print ""
    else:
        print "Invalid arguments. Correct any red fields and try again."


def _gui():
    # make root
    root = Tk()
    root.title("Shack Analysis")

    # setup the main tk frame
    mainframe = Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    # setup entry style
    invalid_entry = Style()
    invalid_entry.configure("Invalid.TEntry")
    #invalid_entry.map('Invalid.TEntry', foreground=[('invalid', 'red')])

    # create dictionary to hold all entry objects

    # row 1: geodatabase path and browse button
    entries["geodatabase"] = GeodatabaseEntry(mainframe, "Geodatabase Path:",
                                              width=100, column=1, row=1,
                                              style="Invalid.TEntry",
                                              required_layers=REQUIRED_LAYERS)
    # notice the lambda: this is an anonymous function simply to allow
    # passing argument to browse gdb (reason: lambda is not implicitly called)
    Button(mainframe, text="Browse...",
           command=lambda: browse_gdb(entries["geodatabase"])
          ).grid(column=3, row=1, sticky=W)

    # rows 2 and 3: min and max elevation
    entries["min_elevation"] = FloatEntry(mainframe, "Minimum Elevation:",
                                          width=100, column=1, row=2,
                                          style="Invalid.TEntry")


    entries["max_elevation"] = FloatEntry(mainframe, "Maximum Elevation:",
                                          width=100, column=1, row=3,
                                          style="Invalid.TEntry")

    # row 4: max water distance
    entries["max_water_dist"] = FloatEntry(mainframe,
                                           "Maximum Distance to Water (>=0):",
                                           width=100, column=1, row=4,
                                           style="Invalid.TEntry",
                                           minimum=0)

    # row 5: min area size
    entries["min_area"] = FloatEntry(mainframe,
                                     "Minimum Acceptable Area (>=0):",
                                     width=100, column=1, row=5,
                                     required=True, style="Invalid.TEntry",
                                     minimum=0)

    # row 6: max slope
    entries["max_slope"] = FloatEntry(mainframe,
                                  "Maximum Slope (degrees) (between 0 and 90):",
                                  width=100, column=1, row=6,
                                  required=True, style="Invalid.TEntry",
                                  minimum=0, maximum=90,
                                  default=4.5)

    # row 7: acceptable soil types
    entries["soil_types"] = ListEntry(mainframe,
                                  "Acceptable Soil Types (comma-separated):",
                                  width=100, column=1, row=7, required=True,
                                  style="Invalid.TEntry", element_type=int)


    # row 8: overwrite
    overwrite = BooleanVar()
    entries["overwrite"] = Checkbutton(mainframe,
                                       text="Overwrite Existing Layers",
                                       variable=overwrite)
    # add variable overwrite as property of the checkbutton instance
    # to allow access later via .var property
    entries["overwrite"].var = overwrite
    # make checkbutton same as entries with an is_valid attribute
    # (impossible for it to be invalid, so setting to True is fine)
    entries["overwrite"].is_valid = True
    entries["overwrite"].grid(column=2, row=8, sticky=(W, E))

    # row 9: run analysis button
    Button(mainframe, text="Run Analysis",
           command=lambda: run_analysis(entries)
          ).grid(column=2, row=9, sticky=W)

    # add padding around all main frame elements
    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)

    # set start focus and bind return key
    entries["geodatabase"].focus()
    root.bind('<Return>', run_analysis)

    # run root
    root.mainloop()


if __name__ == '__main__':
    _gui()