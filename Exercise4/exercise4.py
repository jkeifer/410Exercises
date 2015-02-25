""" (wrapped in triple quotes to make answering questions easier)
# **********************************************************************
#
# NAME: Your Name
# DATE: date
# CLASS: GEOG410
# ASSIGNMENT: Exercise 4
#
# DESCRIPTION: describe the script, what it does, how it does it,
#       and any other important information
#
# INSTRUCTIONS: usage instructions, i.e., inputs, outputs, and how to
#       run the script
#
# QUESTIONS:
#   1) What tools in ArcGIS could perform a similar analysis (possible
#      responses may include tools that would generate a similar statistic
#      even if in a different format)? Try out one of these similar tools
#      in ArcMap and see how much time it takes versus this script.
#
#   >>>
#
#
#   2) Can you think of any ways to improve the analysis portion of this
#      script to ensure it will accomodate other data? (Hint: for one, try
#      commenting out the SetAttributeFilter line in main and see what
#      happens...) How might you implement any of the improvements you
#      identified?
#
#   >>>
#
#
# **********************************************************************
"""

# ********** IMPORT STATEMENTS **********
import sys
import os
import numpy
import argparse
from osgeo import ogr
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GA_Update


# ********** GLOBAL CONSTANTS **********

RASTER = "elevation.img"
SHAPES = "polygons.shp"

ELEVATION_FIELD = "MEAN_ELEV"
ID_FIELD_NAME = "FID"

IMG_DRIVER_NAME = "HFA"


# ********** FUNCTIONS **********

def parse_arguments(argv):
    """
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("data_directory", type=valid_workspace,
                        help="Path to the directory containing the analysis data.")
    args = parser.parse_args(argv)
    raster, shapes = args.data_directory
    args = {"raster": raster, "shapes": shapes}
    return args


def valid_workspace(workspace_path):
    """
    """
    if not os.path.isdir(workspace_path):
        raise argparse.ArgumentError("Not a directory.")

    raster = os.path.join(workspace_path, RASTER)
    shapes = os.path.join(workspace_path, SHAPES)

    if not (os.path.exists(raster) or os.path.exists(shapes)):
        raise argparse.ArgumentTypeError("Cannot find analysis data.")

    return (raster, shapes)


def open_raster(infilepath, readonly=True):
    """
    """
    #
    gdal.AllRegister()

    #
    if readonly is True:
        #
        raster = gdal.Open(infilepath, GA_ReadOnly)
    #
    elif readonly is False:
        raster = gdal.Open(infilepath, GA_Update)
    #
    else:
        raise Exception("Error: the read status could not be be determined.")

    #
    if raster is None:
        raise Exception("Error encountered opening file.")

    return raster


def open_vector(path, writable=False):
    """
    """
    #
    vector = ogr.Open(path, writable)

    #
    if not vector:
        raise Exception("Failed to open shapefile or workspace.")

    return vector


# included for reference only -- not used and do not need to copy
def copy_raster(raster_datasource, output_path="", driver="MEM",
                overwrite=False):
    """
    """
    #
    driver = gdal.GetDriverByName(driver)

    #
    if not driver:
        raise Exception("Driver specified is not a valid GDAL Raster Driver.")

    #
    driver.Register()

    #
    if overwrite:
        if os.path.exists(output_path):
            driver.Delete(output_path)

    #
    newraster = driver.CreateCopy(output_path, raster_datasource)

    #
    if not newraster:
        raise Exception("Failed to create copy of input raster.")

    return newraster


def create_new_raster(outpath, cols, rows, bands, datatype, drivername,
                      geotransform=None, projection=None, overwrite=False):
    """
    """
    #
    driver = gdal.GetDriverByName(drivername)

    #
    if not driver:
        raise Exception("Driver specified is not a valid GDAL Raster Driver.")

    #
    driver.Register()

    #
    if overwrite:
        if os.path.exists(outpath):
            driver.Delete(outpath)

    #
    raster = driver.Create(outpath, cols, rows, bands, datatype)

    #
    if raster is None:
        raise Exception("Error encountered creating output raster.")

    #
    if geotransform:
        raster.SetGeoTransform(geotransform)

    #
    if projection:
        raster.SetProjection(projection)

    return raster


def blank_raster_from_existing_raster(inraster,
                                      outpath,
                                      numberofbands=None,
                                      drivername=None,
                                      datatype=None,
                                      cols=None,
                                      rows=None,
                                      geotransform=None,
                                      projection=None,
                                      overwrite=False):
    """
    """
    #
    if drivername is None:
        drivername = "MEM"

    #
    if datatype is None:
        band = inraster.GetRasterBand(1)
        datatype = band.DataType
        band = None

    #
    if cols is None:
        cols = inraster.RasterXSize

    #
    if rows is None:
        rows = inraster.RasterYSize

    #
    if geotransform is None:
        geotransform = inraster.GetGeoTransform()

    #
    if projection is None:
        projection = inraster.GetProjection()

    #
    if not numberofbands:
        numberofbands = inraster.RasterCount

    #
    newimage = create_new_raster(outpath, cols, rows, numberofbands,
                                 datatype, drivername,
                                 geotransform=geotransform,
                                 projection=projection,
                                 overwrite=overwrite)

    return newimage


def burn_geometry_into_raster(geometry, raster, value):
    """
    """
    # this code is based on the GDAL rasterize.py utility

    #
    sr = geometry.GetSpatialReference()

    #
    rast_ogr_ds = ogr.GetDriverByName('Memory').CreateDataSource('wrk')
    #
    rast_mem_lyr = rast_ogr_ds.CreateLayer('layer', srs=sr)

    #
    feature = ogr.Feature(rast_mem_lyr.GetLayerDefn())
    #
    feature.SetGeometry(geometry)
    #
    rast_mem_lyr.CreateFeature(feature)

    #
    result = gdal.RasterizeLayer(raster, [1], rast_mem_lyr, burn_values=[value])

    #
    if result:
        print result
        raise Exception("Rasterization failed.")


def get_pixel_coords_from_geographic_coords(raster,
                                            list_point_xys,
                                            round_px_coords=True):
    """
    """
    # An explaination: if you want to find the pixel coordinate of a point,
    # then you do not want to round, as even if the point is close to the edge,
    # say px coords (343.998, 112.875), it is still within the current pixel.
    # You would not want the coords returned to be (344, 113), so you'd always
    # want the number rounded down (floor). However, other times you want to
    # round based on how much of the cell is covered: if you are finding the
    # pixels covered by a polygon's extent, for example, you likely want to
    # include all cells where the cell center is covered by the extent. Thus,
    # if a coordinate has a decimal of 0.5 or greater you want to include it,
    # by rounding up. In other applications you may need to adopt an approach
    # beyond these two basic cases.
    if round_px_coords:
        round_function = round
    else:
        from math import floor
        round_function = floor

    #
    raster_geotransform = raster.GetGeoTransform()
    raster_cols = raster.RasterXSize
    raster_rows = raster.RasterYSize

    # get raster edge coords
    left = raster_geotransform[0]
    #
    top = raster_geotransform[3]
    #
    right = (raster_cols * raster_geotransform[1]) + raster_geotransform[0]
    #
    bottom = (raster_rows * raster_geotransform[5]) + raster_geotransform[3]

    #
    pxcoords = []
    for coords in list_point_xys:
        #
        col = int(round_function(raster_cols * float(coords[0]-left) / (right-left)))
        #
        row = int(round_function(raster_rows * float(coords[1]-top) / (bottom-top)))
        #
        pxcoords.append((row, col))

    return pxcoords


def calc_corner_coords(x_min, x_max, y_min, y_max):
    """
    """
    return [(x_min, y_min),
            (x_max, y_min),
            (x_max, y_max),
            (x_min, y_max)]


def change_geotransform(originaltransform, x_px_offset, y_px_offset):
    """
    """
    #
    newtransform = list(originaltransform)

    #
    newtransform[0] += newtransform[1] * y_px_offset
    #
    newtransform[3] += newtransform[5] * x_px_offset

    #
    return tuple(newtransform)


def blank_raster_copy_to_extent(inraster, outraster, corner_px_coords,
                                drivername=None, overwrite=False):
    """
    """
    #
    newgeotransform = change_geotransform(inraster.GetGeoTransform(),
                                          corner_px_coords[3][0],
                                          corner_px_coords[3][1])

    #
    outds = blank_raster_from_existing_raster(inraster,
                        outraster,
                        drivername=drivername,
                        cols=corner_px_coords[1][1] - corner_px_coords[3][1],
                        rows=corner_px_coords[1][0] - corner_px_coords[3][0],
                        geotransform=newgeotransform,
                        overwrite=overwrite)

    return outds


# ********** MAIN **********

def main(raster, shapes):
    #
    inraster = open_raster(raster)
    invector = open_vector(shapes, writable=True)

    #
    elev_band = inraster.GetRasterBand(1)

    #
    layer = invector.GetLayer()

    #
    if layer.FindFieldIndex(ELEVATION_FIELD, True) == -1:
        layer.CreateField(ogr.FieldDefn(ELEVATION_FIELD, ogr.OFTReal))

    #
    layer.SetAttributeFilter("Authority = 'USFS'")

    #
    in_mem_raster = blank_raster_from_existing_raster(inraster, "")

    #
    for feature in layer:
        #
        feature_geom = feature.GetGeometryRef()
        #
        feature_id = feature.GetFID()
        #
        burn_geometry_into_raster(feature_geom,
                                  in_mem_raster,
                                  feature_id + 1)

        #
        geom_extent = feature_geom.GetEnvelope()
        #
        corner_coords = calc_corner_coords(*geom_extent)
        #
        corner_px_coords = \
                get_pixel_coords_from_geographic_coords(in_mem_raster,
                                                        corner_coords)

        #
        feat_band = in_mem_raster.GetRasterBand(1)

        #
        feat_array = \
            feat_band.ReadAsArray(corner_px_coords[3][1],
                                  corner_px_coords[3][0],
                                  corner_px_coords[1][1] - corner_px_coords[3][1],
                                  corner_px_coords[1][0] - corner_px_coords[3][0])

        #
        elev_array = \
            elev_band.ReadAsArray(corner_px_coords[3][1],
                                  corner_px_coords[3][0],
                                  corner_px_coords[1][1] - corner_px_coords[3][1],
                                  corner_px_coords[1][0] - corner_px_coords[3][0])

        #
        feat_array = feat_array == feature_id + 1

        #
        elev_array[feat_array == 0] = None

        #
        raster_to_save = blank_raster_copy_to_extent(inraster,
                                                     os.path.join(os.path.dirname(raster),
                                                                  "outraster_{}.img".format(feature_id)),
                                                     corner_px_coords,
                                                     drivername=IMG_DRIVER_NAME,
                                                     overwrite=True)

        #
        outband = raster_to_save.GetRasterBand(1)
        outband.WriteArray(elev_array)

        #
        feature.SetField(ELEVATION_FIELD, float(numpy.nanmean(elev_array)))
        #
        layer.SetFeature(feature)

        #
        outband = None
        raster_to_save = None
        feature_geom = None
        feat_band = None
        feature = None

    #
    layer = None
    elev_band = None
    in_mem_raster = None
    inraster = None
    invector = None

    return 0


# ********** MAIN CHECK **********

if __name__ == '__main__':
    sys.exit(main(**parse_arguments(sys.argv[1:])))
