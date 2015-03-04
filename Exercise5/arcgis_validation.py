import os
import arcpy


ELEVATION = "elevation"
WATER = "water"
SOILS = "soil"
REQUIRED_LAYERS = [ELEVATION, WATER, SOILS]
OUT_NAME = "SuitableArea"


def has_required_layers(workspace, required_layers):
    """Check a workspace for required layers.
    Returns True if all layers are present, or False
    if one or more layers are missing.
    """
    for layer in required_layers:
        if not arcpy.Exists(os.path.join(workspace, layer)):
            return False
    return True


class ToolValidator(object):
  """Class for validating a tool's parameter values and controlling
  the behavior of the tool's dialog."""

  def __init__(self):
    """Setup arcpy and the list of tool parameters."""
    self.params = arcpy.GetParameterInfo()

  def initializeParameters(self):
    """Refine the properties of a tool's parameters.  This method is
    called when the tool is opened."""
    return

  def updateParameters(self):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parameter
    has been changed."""
    return

  def updateMessages(self):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""

    # check geodatabase for output layer and required layers
    if not (self.params[0].hasError() or self.params[0].hasWarning()) and self.params[0].value:
        if not has_required_layers(str(self.params[0].value), REQUIRED_LAYERS):
            self.params[0].setErrorMessage("Geodatabase does not contain required analysis layers")

        existing_output = arcpy.Exists(os.path.join(str(self.params[0].value), OUT_NAME))

        if existing_output:
            if arcpy.env.overwriteOutput:
                self.params[0].setWarningMessage("Output layer will be overwritten in Analysis Geodatabase")
            else:
                self.params[0].setErrorMessage("Output layer already exists in Analysis Geodatabase")

    # validate min/max elevation values:
    # min must be lower than max if both are set
    if self.params[1].value and self.params[2].value:
        if self.params[1].value >= self.params[2].value:
            self.params[1].setErrorMessage("Min Elevation greater than or eqaul to Max Elevation")
            self.params[2].setErrorMessage("Min Elevation greater than or eqaul to Max Elevation")

    # make sure max_water_dist and min_area are >= 0
    if self.params[3].value < 0:
	self.params[3].setErrorMessage("Cannot be less than zero")

    if self.params[4].value < 0:
	self.params[4].setErrorMessage("Cannot be less than zero")

    return
