"""
Copyright (C) 2018 Bricks Brought to Life
http://bblanimation.com/
chris@bblanimation.com

Created by Christopher Gearhart

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# System imports
# NONE!

# Blender imports
import bpy
from bpy.props import *

# Addon imports
from ..functions import *
from .cmlist_utils import *
from .matlist_utils import *


# Create custom property group
class Bricker_CreatedModels(bpy.types.PropertyGroup):
    # CMLIST ITEM SETTINGS
    name = StringProperty(update=uniquifyName)
    id = IntProperty()
    idx = IntProperty()

    # NAME OF SOURCE
    source_name = StringProperty(
        name="Source Object Name",
        description="Name of the source object to Brickify",
        default="",
        update=setNameIfEmpty)

    # TRANSFORMATION SETTINGS
    modelLoc = StringProperty(default="-1,-1,-1")
    modelRot = StringProperty(default="-1,-1,-1")
    modelScale = StringProperty(default="-1,-1,-1")
    transformScale = FloatProperty(
        name="Scale",
        description="Scale of the brick model",
        update=updateModelScale,
        step=1,
        default=1.0)
    applyToSourceObject = BoolProperty(
        name="Apply to source",
        description="Apply transformations to source object when Brick Model is deleted",
        default=True)
    parent_name = StringProperty(default="")
    exposeParent = BoolProperty(
        name="Show Manipulator",
        description="Expose the parent object for this brick model for viewport manipulation",
        update=updateParentExposure,
        default=False)

    # ANIMATION SETTINGS
    startFrame = IntProperty(
        name="Start Frame",
        description="Start frame of Brick animation",
        update=dirtyAnim,
        min=0, max=500000,
        default=1)
    stopFrame = IntProperty(
        name="Stop Frame",
        description="Stop frame of Brick animation",
        update=dirtyAnim,
        min=0, max=500000,
        default=10)
    useAnimation = BoolProperty(
        name="Use Animation",
        description="Create Brick Model for each frame, from start to stop frame (WARNING: Calculation takes time, and may result in large blend file )",
        default=False)

    # BASIC MODEL SETTINGS
    brickHeight = FloatProperty(
        name="Brick Height",
        description="Height of the bricks in the final Brick Model",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0.001, max=10,
        default=0.1)
    gap = FloatProperty(
        name="Gap Between Bricks",
        description="Distance between bricks",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.005)
    mergeSeed = IntProperty(
        name="Random Seed",
        description="Random seed for brick merging calculations",
        update=dirtyBuild,
        min=-1, max=5000,
        default=1000)
    connectThresh = IntProperty(
        name="Connectivity",
        description="Quality of the model's brick connectivity (higher numbers are slower but bricks will be more interconnected)",
        update=dirtyBuild,
        min=1, max=100,
        default=1)
    smokeDensity = FloatProperty(
        name="Smoke Density",
        description="Density of brickified smoke (threshold for smoke: 1 - d)",
        update=dirtyMatrix,
        min=0, max=1,
        default=0.9)
    smokeQuality = FloatProperty(
        name="Smoke Quality",
        description="Amount of data to analyze for density and color of brickified smoke",
        update=dirtyMatrix,
        min=1, max=100,
        default=1)
    smokeBrightness = FloatProperty(
        name="Smoke Brightness",
        description="Add brightness to smoke colors read from smoke data",
        update=dirtyMatrix,
        min=-4, max=100,
        default=1)
    smokeSaturation = FloatProperty(
        name="Smoke Saturation",
        description="Change saturation level of smoke colors read from smoke data",
        update=dirtyMatrix,
        min=0, max=100,
        default=1)
    flameColor = FloatVectorProperty(
        name="Hex Value",
        subtype='COLOR',
        update=dirtyMatrix,
        default=[1.0, 0.63, 0.2])
    flameIntensity = FloatProperty(
        name="Flame Intensity",
        description="Intensity of the flames",
        update=dirtyMatrix,
        min=1, max=50,
        default=4)
    splitModel = BoolProperty(
        name="Split Model",
        description="Split model into separate objects (slower)",
        update=dirtyModel,
        default=False)
    randomLoc = FloatProperty(
        name="Random Location",
        description="Max random location applied to each brick",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.01)
    randomRot = FloatProperty(
        name="Random Rotation",
        description="Max random rotation applied to each brick",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.025)
    brickShell = EnumProperty(
        name="Brick Shell",
        description="Choose whether the shell of the model will be inside or outside source mesh",
        items=[("INSIDE", "Inside Mesh (recommended)", "Draw brick shell inside source mesh (Recommended)"),
               ("OUTSIDE", "Outside Mesh", "Draw brick shell outside source mesh"),
               ("INSIDE AND OUTSIDE", "Inside and Outside", "Draw brick shell inside and outside source mesh (two layers)")],
        update=dirtyMatrix,
        default="INSIDE")
    calculationAxes = EnumProperty(
        name="Expanded Axes",
        description="The brick shell will be drawn on the outside in these directions",
        items=[("XYZ", "XYZ", "PLACEHOLDER"),
               ("XY", "XY", "PLACEHOLDER"),
               ("YZ", "YZ", "PLACEHOLDER"),
               ("XZ", "XZ", "PLACEHOLDER"),
               ("X", "X", "PLACEHOLDER"),
               ("Y", "Y", "PLACEHOLDER"),
               ("Z", "Z", "PLACEHOLDER")],
        update=dirtyMatrix,
        default="XY")
    shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the Brick shell",
        update=dirtyBuild,
        min=1, max=50,
        default=1)

    # BRICK TYPE SETTINGS
    description = "Use this brick type to build the model"
    brickType = EnumProperty(
        name="Brick Type",
        description="Type of brick used to build the model",
        items=[("STUD_HOLLOWS", "Hollow Studs", description),
               ("STUDS", "Studs", description),
               # ("SLOPES", "Slopes (fast)", description),
               ("PLATES", "Plates", description),
               ("CYLINDERS", "Cylinders", description),
               ("CUSTOM", "Custom", "Use custom object to build the model"),
               ("CONES", "Cones", description),
               ("BRICKS AND PLATES", "Bricks and Plates", description),
               ("BRICKS", "Bricks (fast)", description)],
        update=dirtyMatrix,
        default="BRICKS")
    alignBricks = BoolProperty(
        name="Align Bricks Horizontally",
        description="Keep bricks aligned horizontally, and fill the gaps with plates",
        update=dirtyBuild,
        default=True)
    offsetBrickLayers = IntProperty(
        name="Offset Brick Layers",
        description="Offset the layers that will be merged into bricks if possible",
        update=dirtyBuild,
        step=1,
        min=0, max=2,
        default=0)
    maxWidth = IntProperty(
        name="Max Width",
        description="Maximum brick width",
        update=dirtyBuild,
        step=1,
        min=1, max=1000,
        default=2)
    maxDepth = IntProperty(
        name="Max Depth",
        description="Maximum brick depth",
        update=dirtyBuild,
        step=1,
        min=1, max=1000,
        default=10)
    mergeType = EnumProperty(
        name="Merge Type",
        description="Type of algorithm to use for merging bricks together",
        items=[("GREEDY", "Greedy", "Creates fewest amount of bricks possible"),
               ("RANDOM", "Random", "Merges randomly for realistic build")],
        update=dirtyBuild,
        default="RANDOM")
    legalBricksOnly = BoolProperty(
        name="Legal Bricks Only",
        description="Construct model using only legal brick sizes",
        update=dirtyBuild,
        default=True)
    customObjectName1 = StringProperty(
        name="Custom Object Name 1",
        description="Name of custom object 1 to use as bricks",
        default="")
    customObjectName2 = StringProperty(
        name="Custom Object Name 2",
        description="Name of custom object 2 to use as bricks",
        default="")
    customObjectName3 = StringProperty(
        name="Custom Object Name 3",
        description="Name of custom object 3 to use as bricks",
        default="")
    distOffset = FloatVectorProperty(
        name="Offset Distance",
        description="Offset of custom bricks (1.0 = side-by-side)",
        update=dirtyMatrix,
        step=1,
        precision=3,
        subtype="TRANSLATION",
        min=0.001, max=2,
        default=(1, 1, 1))

    # CUSTOMIZE SETTINGS
    autoUpdateOnDelete = BoolProperty(
        name="Auto Update on Delete",
        description="Draw newly exposed bricks when existing bricks are deleted",
        default=True)

    # MATERIAL & COLOR SETTINGS
    materialType = EnumProperty(
        name="Material Type",
        description="Choose what materials will be applied to model",
        items=[("NONE", "None", "No material applied to bricks"),
               ("RANDOM", "Random", "Apply a random material from Brick materials to each generated brick"),
               ("CUSTOM", "Custom", "Choose a custom material to apply to all generated bricks"),
               ("SOURCE", "Use Source Materials", "Apply material based on closest intersecting face")],
        update=dirtyMaterial,
        default="NONE")
    materialName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to all bricks",
        default="")
    internalMatName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to bricks inside material shell",
        update=dirtyMaterial,
        default="")
    matShellDepth = IntProperty(
        name="Shell Material Depth",
        description="Depth to which the outer materials should be applied (1 = Only exposed bricks",
        step=1,
        min=1, max=50,
        default=1,
        update=dirtyModel)
    mergeInconsistentMats = BoolProperty(
        name="Merge Inconsistent Materials",
        description="Merge bricks whether or not they share a material",
        default=False,
        update=dirtyBuild)
    randomMatSeed = IntProperty(
        name="Random Seed",
        description="Random seed for material assignment",
        min=-1, max=5000,
        default=1000)
    useUVMap = BoolProperty(
        name="Use UV Map",
        description="Transfer colors from source UV map (source must be unwrapped)",
        default=True,
        update=dirtyMaterial)
    uvImageName = StringProperty(
        name="UV Image",
        description="UV Image to use for UV Map color transfer (defaults to active UV if left blank)",
        default="",
        update=dirtyBuild)
    colorSnap = EnumProperty(
        name="Color Snaping",
        description="Snap nearest source materials",
        items=[("NONE", "None", "Use source materials as is"),
               ("ABS", "ABS Plastic", "Use ABS Plastic Materials"),
               ("RGB", "RGB Average", "Use average RGB value of snapped colors")],
        update=dirtyMaterial,
        default="RGB")
    colorSnapAmount = FloatProperty(
        name="Color Snap Amount",
        description="Threshold for combining colors together",
        precision=3,
        min=0.00001, max=1.0,
        default=0.001,
        update=dirtyBuild)
    colorSnapSpecular = FloatProperty(
        name="Specular",
        description="Specular value for the created materials",
        precision=3,
        min=0.0, max=1.0,
        default=0.5,
        update=dirtyMaterial)
    colorSnapRoughness = FloatProperty(
        name="Roughness",
        description="Roughness value for the created materials",
        precision=3,
        min=0.0, max=1.0,
        default=0.5,
        update=dirtyMaterial)
    colorSnapSubsurface = FloatProperty(
        name="Subsurface Sattering",
        description="Subsurface scattering value for the created materials",
        precision=3,
        min=0.0, max=1.0,
        default=0.0,
        update=dirtyMaterial)
    colorSnapSubsurfaceSaturation = FloatProperty(
        name="SSS Saturation",
        description="Saturation of the subsurface scattering for the created materials (relative to base color value)",
        precision=3,
        min=0.0, max=10.0,
        default=0.0,
        update=dirtyMaterial)
    colorSnapIOR = FloatProperty(
        name="IOR",
        description="IOR value for the created materials",
        precision=3,
        min=0.0, max=1000.0,
        default=1.45,
        update=dirtyMaterial)
    colorSnapTransmission = FloatProperty(
        name="Transmission",
        description="Transmission value for the created materials",
        precision=3,
        min=0.0, max=1.0,
        default=0.0,
        update=dirtyMaterial)
    includeTransparency = BoolProperty(
        name="Include Transparency",
        description="Mix diffuse and transparency nodes to represent alpha value of color picked",
        default=False,
        update=dirtyMatrix)
    transparentWeight = FloatProperty(
        name="Transparency Weight",
        description="How much affect color transparency has on chosen ABS color",
        precision=3,
        min=0, max=2,
        default=1,
        update=dirtyMaterial)
    targetMaterial = StringProperty(
        name="Target Material",
        description="Add material to materials list",
        update=addMaterialToList,
        default="")

    # BRICK DETAIL SETTINGS
    studDetail = EnumProperty(
        name="Stud Detailing",
        description="Choose where to draw brick studs",
        items=[("ALL", "On All Bricks", "Include Brick Logo only on bricks with studs exposed"),
               ("EXPOSED", "On Exposed Bricks", "Include Brick Logo only on bricks with studs exposed"),
               ("NONE", "None", "Don't include Brick Logo on bricks")],
        update=dirtyBricks,
        default="EXPOSED")
    logoType = EnumProperty(
        name="Logo Type",
        description="Choose logo type to draw on brick studs",
        items=[("CUSTOM", "Custom Logo", "Choose a mesh object to use as the brick stud logo"),
               ("LEGO", "LEGO Logo", "Include a LEGO logo on each stud"),
               ("NONE", "None", "Don't include Brick Logo on bricks")],
        update=dirtyBricks,
        default="NONE")
    logoResolution = IntProperty(
        name="Resolution",
        description="Resolution of the brick logo",
        update=dirtyBricks,
        min=1, max=10,
        default=1)
    logoResolution = IntProperty(
        name="Resolution",
        description="Resolution of the brick logo",
        update=dirtyBricks,
        min=1, max=10,
        default=3)
    logoDecimate = FloatProperty(
        name="Decimate",
        description="Decimate the brick logo (lower number for higher resolution)",
        update=dirtyBricks,
        precision=0,
        min=0, max=10,
        default=7.25)
    logoObjectName = StringProperty(
        name="Logo Object Name",
        description="Name of the custom logo object",
        update=dirtyBricks,
        default="")
    logoScale = FloatProperty(
        name="Logo Scale",
        description="Logo scale relative to stud scale",
        step=1,
        update=dirtyBricks,
        precision=2,
        min=0.000001, max=2,
        default=0.78)
    logoInset = FloatProperty(
        name="Logo Inset",
        description="Percentage inset of logo in stud",
        step=1,
        update=dirtyBricks,
        precision=2,
        min=0.0, max=1.0,
        default=0.5)
    hiddenUndersideDetail = EnumProperty(
        name="Underside Detailing of Obstructed Bricks",
        description="Level of detail on underside of obstructed bricks",
        items=[("FLAT", "Flat", "draw single face on brick underside"),
               ("LOW", "Low", "Hollow out brick underside and draw tube supports"),
               ("MEDIUM", "Medium", "Draw inset tubes below studs and support beams"),
               ("HIGH", "High", "Draw support ticks on 2 by x bricks")],
        update=dirtyBricks,
        default="FLAT")
    exposedUndersideDetail = EnumProperty(
        name="Underside Detailing of Exposed Bricks",
        description="Level of detail on underside of exposed bricks",
        items=[("FLAT", "Flat", "draw single face on brick underside"),
               ("LOW", "Low", "Hollow out brick underside and draw tube supports"),
               ("MEDIUM", "Medium", "Draw inset tubes below studs and support beams"),
               ("HIGH", "High", "Draw support ticks on 2 by x bricks")],
        update=dirtyBricks,
        default="FLAT")
    circleVerts = IntProperty(
        name="Num Verts",
        description="Number of vertices in each circle in brick mesh",
        update=updateCircleVerts,
        min=4, max=64,
        default=16)
    loopCut = BoolProperty(
        name="Loop Cut Cylinders",
        description="Make loop cut on cylinders so that bevel operation can bevel base of studs",
        update=dirtyBricks,
        default=False)
    # BEVEL SETTINGS
    bevelWidth = FloatProperty(
        name="Bevel Width",
        description="Bevel amount (relative to Brick Height)",
        step=1,
        min=0.000001, max=10,
        default=0.01,
        update=updateBevel)
    bevelSegments = IntProperty(
        name="Bevel Resolution",
        description="Number of segments for round edges/verts",
        step=1,
        min=1, max=10,
        default=1,
        update=updateBevel)
    bevelProfile = FloatProperty(
        name="Bevel Profile",
        description="The profile shape (0.5 = round)",
        step=1,
        min=0, max=1,
        default=0.7,
        update=updateBevel)

    # INTERNAL SUPPORTS SETTINGS
    internalSupports = EnumProperty(
        name="Internal Supports",
        description="Choose what type of brick support structure to use inside your model",
        items=[("NONE", "None", "No internal supports"),
               ("LATTICE", "Lattice", "Use latice inside model"),
               ("COLUMNS", "Columns", "Use columns inside model")],
        update=dirtyInternal,
        default="NONE")
    latticeStep = IntProperty(
        name="Step",
        description="Distance between cross-beams",
        update=dirtyInternal,
        step=1,
        min=2, max=25,
        default=4)
    latticeHeight = IntProperty(
        name="Height",
        description="Height of the cross-beams",
        update=dirtyInternal,
        step=1,
        min=1, max=3,
        default=1)
    alternateXY = BoolProperty(
        name="Alternate X and Y",
        description="Alternate back-and-forth and side-to-side beams",
        update=dirtyInternal,
        default=True)
    colThickness = IntProperty(
        name="Thickness",
        description="Thickness of the columns",
        update=dirtyInternal,
        min=1, max=25,
        default=2)
    colStep = IntProperty(
        name="Step",
        description="Distance between columns",
        update=dirtyInternal,
        step=1,
        min=1, max=25,
        default=2)

    # ADVANCED SETTINGS
    insidenessRayCastDir = EnumProperty(
        name="Insideness Ray Cast Direction",
        description="Ray cast method for calculation of insideness",
        items=[("HIGH EFFICIENCY", "High Efficiency", "Reuses single intersection ray cast for insideness calculation"),
               ("X", "X", "Cast rays along X axis for insideness calculations"),
               ("Y", "Y", "Cast rays along Y axis for insideness calculations"),
               ("Z", "Z", "Cast rays along Z axis for insideness calculations"),
               ("XYZ", "XYZ (Best Result)", "Cast rays in all axis directions for insideness calculation (slowest; uses result consistent for at least 2 of the 3 rays)")],
        update=dirtyMatrix,
        default="HIGH EFFICIENCY")
    castDoubleCheckRays = BoolProperty(
        name="Cast Both Directions",
        description="Cast additional ray(s) the opposite direction for insideness calculation (Slightly slower but much more accurate if mesh is not single closed mesh)",
        default=True,
        update=dirtyMatrix)
    useNormals = BoolProperty(
        name="Use Normals",
        description="Use normals to calculate insideness of bricks (WARNING: May produce inaccurate model if source is not single closed mesh)",
        default=False,
        update=dirtyMatrix)
    verifyExposure = BoolProperty(
        name="Verify Exposure",
        description="Run insideness calculations on every brick location (slower, but may fix issue where row(s)/column(s) of extra bricks are drawn)",
        default=False,
        update=dirtyMatrix)
    useLocalOrient = BoolProperty(
        name="Use Local Orient",
        description="Generate bricks based on local orientation of source object",
        default=False)

    # EXPORT SETTINGS
    exportPath = StringProperty(
        name="Export Path",
        description="Destination path for exported files",
        subtype="FILE_PATH",
        default="//")

    # Source Object Properties
    modelScalePreview = FloatVectorProperty(default=(-1, -1, -1))
    objVerts = IntProperty(default=0)
    objPolys = IntProperty(default=0)
    objEdges = IntProperty(default=0)
    isWaterTight = BoolProperty(default=False)


    # Deep Cache of bricksDict
    BFMCache = StringProperty(default="")

    # Blender State for Undo Stack
    blender_undo_state = IntProperty(default=0)

    # Back-End UI Properties
    activeKey = IntVectorProperty(default=(-1,-1,-1))
    firstKey = StringProperty(default="")

    # Internal Model Properties
    modelCreated = BoolProperty(default=False)
    animated = BoolProperty(default=False)
    materialApplied = BoolProperty(default=False)
    armature = BoolProperty(default=False)
    # rigid_body = BoolProperty(default=False)
    bevelAdded = BoolProperty(default=False)
    customized = BoolProperty(default=True)
    brickSizesUsed = StringProperty(default="")  # list of brickSizes used separated by | (e.g. '5,4,3|7,4,5|8,6,5')
    brickTypesUsed = StringProperty(default="")  # list of brickTypes used separated by | (e.g. 'PLATE|BRICK|STUD')
    modelCreatedOnFrame = IntProperty(default=-1)
    isSmoke = BoolProperty(default=False)
    hasCustomObj1 = BoolProperty(default=False)
    hasCustomObj2 = BoolProperty(default=False)
    hasCustomObj3 = BoolProperty(default=False)

    # Properties for checking of model needs updating
    animIsDirty = BoolProperty(default=True)
    materialIsDirty = BoolProperty(default=True)
    modelIsDirty = BoolProperty(default=True)
    buildIsDirty = BoolProperty(default=False)
    bricksAreDirty = BoolProperty(default=True)
    matrixIsDirty = BoolProperty(default=True)
    matrixLost = BoolProperty(default=False)
    internalIsDirty = BoolProperty(default=True)
    lastLogoType = StringProperty(default="NONE")
    lastSplitModel = BoolProperty(default=False)
    lastStartFrame = IntProperty(default=-1)
    lastStopFrame = IntProperty(default=-1)
    lastSourceMid = StringProperty(default="-1,-1,-1")
    lastMaterialType = StringProperty(default="SOURCE")
    lastShellThickness = IntProperty(default=1)
    lastBrickType = StringProperty(default="BRICKS")
    lastMatrixSettings = StringProperty(default="")
    lastLegalBricksOnly = BoolProperty(default=False)
    lastMatShellDepth = IntProperty(default=1)
    lastBevelWidth = FloatProperty()
    lastBevelSegments = IntProperty()
    lastBevelProfile = IntProperty()
    lastIsSmoke = BoolProperty()

    # Bricker Version of Model
    version = StringProperty(default="1.0.4")
    # Left over attrs from earlier versions
    maxBrickScale1 = IntProperty(default=-1)
    maxBrickScale2 = IntProperty(default=-1)
    distOffsetX = FloatProperty(default=-1)
    distOffsetY = FloatProperty(default=-1)
    distOffsetZ = FloatProperty(default=-1)
    logoDetail = StringProperty(default="NONE")
