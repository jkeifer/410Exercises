# **********************************************************************
#
# NAME: Jarrett Keifer
# DATE: 2015-01-31
# CLASS: GEOG410
# ASSIGNMENT: Lab 4
#
# DESCRIPTION: Finds a suitable site for a mountain man shack.
#
# INSTRUCTIONS: Script uses command line arguments to set analysis
#       parameters. Requires an input geodatabase with an elevation
#       raster, a soils raster, and a water feature class.
#
#       Run the script at the command line with the option "-h"
#       to view the command help and see all the parameters and
#       the option values.
#
# SOURCE(S): ESRI Docs
#       more on decorators: https://pythonconquerstheuniverse.wordpress.com/2009/08/06/introduction-to-python-decorators-part-1/
#
# **********************************************************************

# ********** IMPORT STATEMENTS **********
from __future__ import print_function
import sys
import os
import argparse
import datetime
import arcpy
from arcpy import env
from arcpy import sa


# ********** GLOBAL CONSTANTS **********

# analysis layer names and a list for iterating
ELEVATION = "elevation"
WATER = "water"
SOILS = "soil"
REQUIRED_LAYERS = [ELEVATION, WATER, SOILS]

# slope calculation setttings
SLOPE_MEASURE = "DEGREE"
SLOPE_ZFACTOR = 1

# if true, write all rasters to gdb for debugging
DEBUG_SAVE_RASTERS = False

# intermediate workspace for vector operations
INTERMEDIATE_WORKSPACE = "in_memory"

# in memory fc of all vectorized polygons from raster
# name and options
RASTER_TO_VECTOR_NAME = "polygons"
SIMPLIFY = "NO_SIMPLIFY"

# name for final output of suitable polygons
OUT_NAME = "SuitableArea"

# ********** CLASSES **********

class LicenseError(Exception):
    """Custom exception for unavailable ArcGIS
    extension licenses.
    """
    pass


# ********** FUNCTIONS **********

def spatial_analyst(original_function):
    """A decorator used to wrap functions requiring a
    spatial analyst license in the check-out/check-in
    logic.
    """
    def check_out_spatial_analyst(*args, **kwargs):
        extension = "Spatial"
        # if extension is available, check out license, else error
        if arcpy.CheckExtension(extension) == "Available":
            arcpy.CheckOutExtension(extension)
        else:
            raise LicenseError("Spatial Analyst Extension not available.")
        # call the function passed in with its args
        try:
            out = original_function(*args, **kwargs)
        finally:
            # check extension back in
            arcpy.CheckInExtension(extension)
        # return output of original function
        return out
    # return the new function, which is the original wrapped with
    # the check-out/check-in
    return check_out_spatial_analyst


def parse_arguments(argv):
    """Gets the user-supplied arguemnts, parses them,
    and returns them as elements of a tuple.
    """
    # create argparse parser
    parser = argparse.ArgumentParser(description='Finds a site suitable for a mountain man shack.')

    # add all arguments
    parser.add_argument('geodatabase', type=valid_geodatabase,
                        help='the path to the input gdb')
    parser.add_argument('-o', '--overwrite', required=False, action="store_true",
                        help='option to allow overwrite of existing files')
    parser.add_argument('-d', '--max_water_distance', type=positive_int,
                        help='max distance to a water feature')
    parser.add_argument('-a', '--min_area', required=True, type=positive_int,
                        help='minimum area to consider for shack site')
    parser.add_argument('-s', '--max_slope', type=valid_slope, default=4.5,
                        help='maximum slope of the shack site; default 4.5')
    parser.add_argument('-m', '--min_elevation', type=int, default=None,
                        help='minimum elevation for shack site')
    parser.add_argument('-M', '--max_elevation', type=int, default=None,
                        help='minimum elevation for shack site')
    parser.add_argument('-t', '--soil_type', type=int, required=True, action='append',
                        help='integer value for acceptable soil type')

    # parse the argvs pass in into args
    args = parser.parse_args(argv)

    ## validate validatable argument values ##
    error = False
    # check that geodatabase is valid and has layers
    if not has_required_layers(args.geodatabase, REQUIRED_LAYERS):
        print("ERROR: Geodatabase does not have the required layers for this analysis.")
        error = True

    # check geodatabase for output fc if overwrite is not true
    if not args.overwrite and arcpy.Exists(os.path.join(args.geodatabase,
                                                        OUT_NAME)):
        print("ERROR: Output FC already exists in geodatabase (use -o to overwrite).")
        error = True

    if error:
        parser.error("One or more script arguments was invalid; aborting.")

    return vars(args)


def valid_geodatabase(geodatabase):
    """A custom type for argparse. Logic ensures that a path
    entered by a user for a geodatabase is actually a geodatabase.
    """
    try:
        desc = arcpy.Describe(geodatabase)
        # assert raises an error if a condition is not true
        assert desc.DataType == 'Workspace'
        assert desc.workspacetype == 'LocalDatabase'
    # arcpy.Describe throws an IOError if path does not exist
    except IOError:
        raise argparse.ArgumentTypeError("Supplied geodatabase does not exist.")
    # the error from the asserts, if not true
    except AssertionError:
        raise argparse.ArgumentTypeError("Supplied geodatabase is not valid.")
    else:
        return geodatabase


def valid_slope(slope_str):
    """Custom type for argparse. Checks a slope value entered
    by the user to ensure it is a valid float and that it is
    not less than 0 or greater than 90.
    """
    try:
        slope = float(slope_str)
    except:
        raise argparse.ArgumentTypeError("Slope was not a number.")
    if slope < 0 or slope > 90:
        raise argparse.ArgumentTypeError("Slope was not a valid value (must be between 0 and 90).")
    return slope


def positive_int(int_str):
    """A custom type for argparse. Checks user input to ensure
    it is a valid int and that the value is greater than 0.
    """
    try:
        p_int = int(int_str)
    except:
        raise argparse.ArgumentTypeError("Not an integer.")
    if p_int <= 0:
        raise argparse.ArgumentTypeError("Not a positive integer.")
    return p_int


def has_required_layers(workspace, required_layers):
    """Check a workspace for required layers.
    Returns True if all layers are present, or False
    if one or more layers are missing.
    """
    for layer in required_layers:
        if not arcpy.Exists(os.path.join(workspace, layer)):
            return False
    return True


# using spatial analyst DECORATOR (defined above)
# to wrap function in license check-out/check-in
# decreases code duplication, and increases reusability
@spatial_analyst
def eucledian_distance(inputfc, max_distance=None, cell_size=None,
                       analysis_extent=None, direction_raster=None):
    """Creates a distance raster based on the input fc.

    Optional arguments:
        max_distance -- any cells beyond this distance will get NoData
        cell_size -- a raster to use as a template or a number
        analysis_extent -- an extent object to use for the analysis
                (default is the environment extent or inputfc extent)
        direction_raster -- an output path for a direction raster, if desired

    Returns the distance raster as an arcpy raster object
    """
    # I wanted this function to be reusable and capable of
    # supporting an analysis extent different from the
    # environment settings
    original_extent = env.extent

    if analysis_extent:
        env.extent = analysis_extent

    try:
        distance = sa.EucDistance(inputfc,
                                  maximum_distance=max_distance,
                                  cell_size=cell_size,
                                  out_direction_raster=direction_raster)
    finally:
        env.extent = original_extent

    return distance


@spatial_analyst
def slope(inraster, slope_measure, slope_zfactor, max_slope=None):
    """Creates a slope raster from a continuous data raster inraster.

    slope_measure is the units to use for the slope values
        ("DEGREE" or "PERCENT_RISE").
    slope_zfactor is the number of ground units (x, y) in one
        surface unit (z). If units are same for both, use 1.
    max_slope is a value threshold beyond which all cells
        will have NoData. Default is no max slope.

    Returns the slope raster as an arcpy raster object.
    """
    slope = sa.Slope(inraster, slope_measure, slope_zfactor)

    if max_slope:
        slope = sa.LessThanEqual(slope, max_slope)

    return slope


@spatial_analyst
def get_good_values(inraster, good_values):
    """Creates a boolean raster based on the inraster
    with 1 where inraster has a value in good_values
    and 0 where inraster is not equal to a value in
    good_values.

    Returns the boolean raster as an arcpy raster object.
    """
    query = []
    # build a list of queries for sa.Test
    for value in good_values:
        query.append("VALUE = {}".format(value))
    # return result of sa.Test
    # join queries in query with " OR " to
    # create a single query string
    return sa.Test(inraster, " OR ".join(query))


@spatial_analyst
def multiple_OR(rasterlist):
    """Given a list of rasters, OR them all
    together into a single output boolean raster.

    Returns the boolean result as an arcpy raster object.
    """
    # pop returns last item in list and removes from list
    raster = rasterlist.pop()
    # iterate through rasters, OR-ing them
    for remaining in rasterlist:
        raster |= remaining
    return raster


@spatial_analyst
def multiple_AND(rasterlist):
    """Given a list of rasters, AND them all
    together into a single output boolean raster.

    Returns the boolean result as an arcpy raster object.
    """
    raster = rasterlist.pop()
    # iterate through rasters, AND-ing them
    for remaining in rasterlist:
        raster &= remaining
    return raster


@spatial_analyst
def get_good_range(inraster, min_value=None, max_value=None):
    """Create a boolean raster from inraster with 1 where
    inraster is greater than or equal to a minimum value
    and less than or equal to a maximum value. If the min
    value is not supplied, no minimum value will be used.
    If the max value is not supplied, no max will be used.
    If neither is supplied, the input will simply be
    returned unchanged.

    Returns an arcpy raster object.
    """
    query = []
    # if min value, add min test to query
    if min_value:
        query.append("VALUE >= {}".format(min_value))
    # if max value, add max test to query
    if max_value:
        query.append("VALUE <= {}".format(max_value))
    # ensure a query
    if query:
        # if query return the result of test
        # use join with " AND " to put query elements together
        return sa.Test(inraster, " AND ".join(query))
    # if not query return inraster unchanged
    return inraster


@spatial_analyst
def remove_value(inraster, value=0):
    """Set a given value in an inraster as NoData.

    Returns an arcpy raster object.
    """
    return sa.SetNull(inraster, inraster, "Value = {}".format(value))


def save_features_to_feature_class(features, workspace, out_name):
    """Creates a feature class in the workspace with the specified
    out_name. Inserts the geometry objects in the features list
    into the created feature class.

    Returns an arcpy result object from the create feature class
    operation.
    """
    outfc = arcpy.CreateFeatureclass_management(workspace, out_name,
                                                geometry_type=features[0].type,
                                                spatial_reference=features[0].spatialReference)

    with arcpy.da.InsertCursor(outfc, ["SHAPE@"]) as cursor:
        for feature in features:
            cursor.insertRow([feature])

    return outfc



# ********** MAIN **********

def main(geodatabase, max_slope, soil_type, min_area, max_water_distance=None,
         min_elevation=None, max_elevation=None, overwrite_output=False,
         print=print):
    # all args validated by parse args function, and can be assumed correct
    start = datetime.datetime.now()

    # print analysis settings
    print("Running shack site selection selector with the following options:")
    print("  Geodatabase: {}".format(geodatabase))
    print("  Maximum water distance: {}".format(max_water_distance))
    print("  Max slope: {}".format(max_slope))
    print("  Good soil types: {}".format(", ".join([str(i) for i in soil_type])))
    print("  Minimum elevation: {}".format(min_elevation))
    print("  Maximum elevation: {}".format(max_elevation))
    print("  Minimum site area: {}".format(min_area))
    print("  Overwriting existing results: {}".format(overwrite_output, "\n"))

    # set arcpy overwrite
    env.overwriteOutput = overwrite_output

    # create Raster objects for input rasters
    elevation = arcpy.Raster(os.path.join(geodatabase, ELEVATION))
    soils = arcpy.Raster(os.path.join(geodatabase, SOILS))

    # get full paths to non-raster layers
    water = os.path.join(geodatabase, WATER)

    # extent of analysis is based on elevation raster
    env.extent = elevation.extent

    # find distance to waterbodies
    print("Finding areas within distance threshold of water...")
    water_dist = eucledian_distance(water, cell_size=elevation,
                                    max_distance=max_water_distance)

    # calc slope
    print("Finding suitable slope areas...")
    good_slope = slope(elevation, SLOPE_MEASURE, SLOPE_ZFACTOR,
                       max_slope=max_slope)

    # get acceptable soil types
    print("Finding suitable soil areas...")
    good_soils = get_good_values(soils, soil_type)

    # find good elevation
    print("Finding suitable elevation areas...")
    good_elevation = get_good_range(elevation,
                                    min_value=min_elevation,
                                    max_value=max_elevation)


    # create sutiable raster by finding common areas in good rasters
    print("Totalling results to find suitable shack sites...")
    suitable_raster = multiple_AND([water_dist,
                                    good_slope,
                                    good_soils,
                                    good_elevation])

    # remove zero values to prevent features that do not meet requirements
    suitable_raster = remove_value(suitable_raster, value=0)

    # convert raster to vector in memory
    print("Converting suitable raster to vector...")
    features = arcpy.RasterToPolygon_conversion(suitable_raster,
                                                os.path.join(INTERMEDIATE_WORKSPACE,
                                                             RASTER_TO_VECTOR_NAME),
                                                simplify=SIMPLIFY)

    # select on those features meeting the area requirement
    print("Selecting all features with a greater size than the minimum area...")
    suitable = [row[0] for row in \
                arcpy.da.SearchCursor(features,
                                      ["SHAPE@", "SHAPE@AREA"]) \
                if row[1] >= min_area]

    # save selected features
    print("Saving features greater than area threshold...")
    save_features_to_feature_class(suitable, geodatabase, OUT_NAME)

    # if debugging, save features to gdb
    if DEBUG_SAVE_RASTERS:
        rasters = [(water_dist, "water_dist"),
                   (good_slope, "good_slope"),
                   (good_soils, "good_soils"),
                   (good_elevation, "good_elevation"),
                   (suitable_raster, "suitable_rst"),
                   ]
        for raster, name in rasters:
            raster.save(os.path.join(geodatabase, name))

    # process completed message
    end = datetime.datetime.now()
    print("\n\nProcessing completed. Time elapsed: {}".format(end-start))

    return 0


# ********** MAIN CHECK **********

if __name__ == '__main__':
    # call parse args and unpack tuple into call to main
    sys.exit(main(**parse_arguments(sys.argv[1:])))
