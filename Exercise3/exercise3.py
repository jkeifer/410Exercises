# **********************************************************************
#
# NAME: Your Name
# DATE: date
# CLASS: GEOG410
# ASSIGNMENT: Lab #
#
# DESCRIPTION: describe the script, what it does, how it does it,
#       and any other important information
#
# INSTRUCTIONS: usage instructions, i.e., inputs, outputs, and how to
#       run the script
#
# SOURCE(S): list any sources used to complete this script
#
# **********************************************************************

# ********** IMPORT STATEMENTS **********
import sys
import os
import datetime
import argparse
from osgeo import ogr, osr

ogr.UseExceptions()


# ********** GLOBAL CONSTANTS **********

POINTS = "points"
REQUIRED = [POINTS]

OUTPUT = "buffer"
OUT_CRS = 2913


# ********** FUNCTIONS **********

def parse_args(argv):
    """
    """
    a = argparse.ArgumentParser()
    a.add_argument("workspace", type=str)
    a.add_argument("buffer_dist", type=int)
    b = a.parse_args(argv)
    return b.workspace, b.buffer_dist


def open_shapefile(path, writable=False):
    """
    """
    #
    driver = ogr.GetDriverByName('ESRI Shapefile')
    #
    data = driver.Open(path, writable)

    #
    if not data:
        raise Exception ("Failed to open shapefile or workspace.")

    return data


def create_spatial_ref_from_EPSG(epsg_code):
    """
    """
    #
    spatial_ref = osr.SpatialReference()
    #
    spatial_ref.ImportFromEPSG(epsg_code)
    return spatial_ref


def check_for_and_delete_existing_layer(open_workspace, existing_layer_name):
    """
    """
    #
    for index in xrange(open_workspace.GetLayerCount()):
        #
        layer = open_workspace.GetLayer(index)
        #
        layer_name = layer.GetName()
        #
        if layer_name == existing_layer_name:
            #
            open_workspace.DeleteLayer(index)
            return True
    return False


# Note: you do not need to include the following function in your exercise;
# it became redundant by the optional srs argument to CreatLayer in the
# create_new_layer function. I merely include it here for reference/example.
def add_spatial_reference_to_layer(workspace_path, layer_name, spatial_ref_EPSG):
    """
    """
    spatial_ref = create_spatial_ref_from_EPSG(spatial_ref_EPSG)
    #
    spatial_ref.MorphToESRI()
    #
    with open(os.path.join(workspace_path, layer_name) + ".prj", 'w') as outprj:
        #
        outprj.write(spatial_ref.ExportToWkt())


def create_new_layer(open_workspace, out_layer_name, geometry_type,
                     spatial_ref=None):
    """
    """
    #
    check_for_and_delete_existing_layer(open_workspace, out_layer_name)
    #
    out_layer = open_workspace.CreateLayer(out_layer_name,
                                           geom_type=geometry_type,
                                           srs=spatial_ref)

    #
    if not out_layer:
        raise Exception("Failed to create new layer in workspace.")

    return out_layer


def copy_fields(in_layer, out_layer):
    """
    """
    #
    in_layer_defn = in_layer.GetLayerDefn()
    #
    for index in xrange(0, in_layer_defn.GetFieldCount()):
        #
        field_defn = in_layer_defn.GetFieldDefn(index)
        #
        out_layer.CreateField(field_defn)


def buffer_features(in_layer, out_poly_layer, buffer_distance,
                    spatial_ref=None):
    #
    out_layer_defn = out_poly_layer.GetLayerDefn()

    #
    in_feature = in_layer.GetNextFeature()
    while in_feature:
        #
        geometry = in_feature.GetGeometryRef()

        #
        if spatial_ref:
            geometry.TransformTo(spatial_ref)

        #
        geometry = geometry.Buffer(buffer_distance)
        #
        out_feature = ogr.Feature(out_layer_defn)
        #
        out_feature.SetGeometry(geometry)
        #
        for index in xrange(0, out_layer_defn.GetFieldCount()):
            #
            out_feature.SetField(out_layer_defn.GetFieldDefn(index).GetNameRef(),
                                 in_feature.GetField(index))

        #
        out_poly_layer.CreateFeature(out_feature)

        #
        out_feature = None
        #
        in_feature = in_layer.GetNextFeature()


# ********** MAIN **********

def main(argv):
    #
    workspace, buffer_dist = parse_args(argv)

    #
    opened_workspace = open_shapefile(workspace, True)

    #
    out_spatial_ref = create_spatial_ref_from_EPSG(OUT_CRS)

    #
    in_layer = opened_workspace.GetLayerByName(POINTS)

    #
    out_layer = create_new_layer(opened_workspace, OUTPUT, ogr.wkbPolygon, out_spatial_ref)

    #
    copy_fields(in_layer, out_layer)

    #
    buffer_features(in_layer, out_layer, buffer_dist,
                    spatial_ref=out_spatial_ref)

    #
    in_layer = None
    out_layer = None
    opened_workspace = None

    return 0


# ********** MAIN CHECK **********

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
