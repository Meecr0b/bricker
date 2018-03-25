"""
    Copyright (C) 2017 Bricks Brought to Life
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
from bpy.types import Operator

# Bricker imports
from ..undo_stack import *
from ..functions import *
from ...brickify import *
from ...brickify import *
from ....lib.bricksDict.functions import getDictKey
from ....lib.Brick.legal_brick_sizes import *
from ....functions import *


class changeMaterial(Operator):
    """Change material for selected bricks"""
    bl_idname = "bricker.change_brick_material"
    bl_label = "Change Material"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 object is selected and is brick
        for obj in objs:
            if not obj.isBrick:
                continue
            return True
        return False

    def execute(self, context):
        try:
            if self.mat_name == "NONE":
                return {"FINISHED"}
            scn = bpy.context.scene
            objsToSelect = []
            # iterate through cm_ids of selected objects
            for cm_id in self.objNamesD.keys():
                cm = getItemByID(scn.cmlist, cm_id)
                self.undo_stack.iterateStates(cm)
                # initialize vars
                bricksDict = deepcopy(self.bricksDicts[cm_id])
                keysToUpdate = []

                # iterate through cm_ids of selected objects
                for obj_name in self.objNamesD[cm_id]:
                    dictKey, _ = getDictKey(obj_name)
                    # change material
                    keysInBrick = getKeysInBrick(bricksDict[dictKey]["size"], dictKey)
                    for k in keysInBrick:
                        bricksDict[k]["mat_name"] = self.mat_name
                    # delete the object that was split
                    delete(bpy.data.objects.get(obj_name))
                    keysToUpdate.append(dictKey)

                # draw modified bricks
                drawUpdatedBricks(cm, bricksDict, uniquify1(keysToUpdate))

                # model is now customized
                cm.customized = True

                # add selected objects to objects to select at the end
                objsToSelect += bpy.context.selected_objects.copy()
            # select the new objects created
            select(objsToSelect)
        except:
            handle_exception()
        return{"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        # initialize vars
        selected_objects = bpy.context.selected_objects
        self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictsDs(selected_objects)
        # push to undo stack
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('change material', list(self.objNamesD.keys()))

    ###################################################
    # class variables

    # get items for mat_name prop
    def get_items(self, context):
        items = [("NONE", "None", "")] + [(k, k, "") for k in bpy.data.materials.keys()]
        return items

    # variables
    bricksDicts = {}
    objNamesD = {}

    # properties
    mat_name = bpy.props.EnumProperty(
        name="Material Names",
        description="Choose material to apply to selected bricks",
        items=get_items)

    #############################################
