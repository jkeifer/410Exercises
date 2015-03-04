from __future__ import print_function
import arcpy
import lab4_part2

# get all parameters via arcpy
geodatabase = arcpy.GetParameterAsText(0)
min_elevation = arcpy.GetParameter(1)
max_elevation = arcpy.GetParameter(2)
max_water_distance = arcpy.GetParameter(3)
min_area = arcpy.GetParameter(4)
max_slope = arcpy.GetParameter(5)
soil_type = arcpy.GetParameter(6)
overwrite_output = arcpy.env.overwriteOutput

# call analysis function (note that print function is reassigned)
lab4_part2.main(geodatabase=geodatabase,
                min_elevation=min_elevation,
                max_elevation=max_elevation,
                overwrite_output=overwrite_output,
                max_water_distance=max_water_distance,
                min_area=min_area,
                soil_type=soil_type,
                max_slope=max_slope,
                print=arcpy.AddMessage,
               )
