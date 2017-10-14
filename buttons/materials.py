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
import time
import bmesh
import os
import math
import numpy as np

# Blender imports
import bpy
from mathutils import Matrix, Vector, Euler
props = bpy.props

# Rebrickr imports
from ..functions import *
from ..functions.wrappers import *
from .delete import RebrickrDelete


class RebrickrApplyMaterial(bpy.types.Operator):
    """Apply specified material to all bricks """                        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.apply_material"                                 # unique identifier for buttons and menu items to reference.
    bl_label = "Apply Material"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    def __init__(self):
        self.setAction()

    def setAction(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if cm.materialType == "Use Source Materials":
            self.action = "INTERNAL"
        elif cm.materialType == "Custom":
            self.action = "CUSTOM"
        elif cm.materialType == "Random":
            self.action = "RANDOM"

    @classmethod
    def getBricks(cls, cm):
        n = cm.source_name
        Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()
        if cm.modelCreated:
            bricks = list(bpy.data.groups[Rebrickr_bricks_gn].objects)
        elif cm.animated:
            bricks = []
            for cf in range(cm.lastStartFrame, cm.lastStopFrame+1):
                gn = "Rebrickr_%(n)s_bricks_frame_%(cf)s" % locals()
                bGroup = bpy.data.groups.get(gn)
                for obj in bGroup.objects:
                    bricks.append(obj)

        return bricks

    @classmethod
    def applyRandomMaterial(cls, context, bricks):
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        # initialize list of brick materials
        brick_mats = []
        mats = bpy.data.materials.keys()
        for color in bpy.props.abs_plastic_materials:
            if color in mats and color in bpy.props.abs_plastic_materials_for_random:
                brick_mats.append(color)
        randS0 = np.random.RandomState(0)
        # if model is split, apply a random material to each brick
        for i,brick in enumerate(bricks):
            lastMatSlots = list(brick.material_slots.keys())

            if (cm.lastSplitModel or len(lastMatSlots) == 0) and len(brick_mats) > 0:
                # clear existing materials
                brick.data.materials.clear(1)
                # iterate seed and set random index
                randS0.seed(cm.randomMatSeed + i)
                if len(brick_mats) == 1:
                    randIdx = 0
                else:
                    randIdx = randS0.randint(0, len(brick_mats))
                # Assign random material to object
                mat = bpy.data.materials.get(brick_mats[randIdx])
                brick.data.materials.append(mat)
                continue

            if len(lastMatSlots) == len(brick_mats):
                brick_mats_dup = brick_mats.copy()
                for i in range(len(lastMatSlots)):
                    # iterate seed and set random index
                    randS0.seed(cm.randomMatSeed + i)
                    if len(brick_mats_dup) == 1:
                        randIdx = 0
                    else:
                        randIdx = randS0.randint(0, len(brick_mats_dup))
                    # Assign random material to object
                    matName = brick_mats_dup.pop(randIdx)
                    mat = bpy.data.materials.get(matName)
                    brick.data.materials[i] = mat

    @timed_call('Total Time Elapsed')
    def runApplyMaterial(self, context):

        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        bricks = RebrickrApplyMaterial.getBricks(cm)
        cm.lastMaterialType = cm.materialType
        if self.action == "CUSTOM":
            matName = cm.materialName
        elif self.action == "INTERNAL":
            matName = cm.internalMatName
        elif self.action == "RANDOM":
            RebrickrApplyMaterial.applyRandomMaterial(context, bricks)

        if self.action != "RANDOM":
            mat = bpy.data.materials.get(matName)
            if mat is None:
                self.report({"WARNING"}, "Specified material doesn't exist")

            for brick in bricks:
                if self.action == "CUSTOM":
                    if brick.data.materials:
                        # clear existing materials
                        brick.data.materials.clear(1)
                    # Assign it to object
                    brick.data.materials.append(mat)
                elif self.action == "INTERNAL":
                    brick.data.materials.pop(0)
                    # Assign it to object
                    brick.data.materials.append(mat)
                    for i in range(len(brick.data.materials)-1):
                        brick.data.materials.append(brick.data.materials.pop(0))

        redraw_areas(["VIEW_3D", "PROPERTIES", "NODE_EDITOR"])
        cm.materialIsDirty = False

    def execute(self, context):
        try:
            self.runApplyMaterial(context)
        except:
            self.handle_exception()

        return{"FINISHED"}

    def handle_exception(self):
        errormsg = print_exception('Rebrickr_log')
        # if max number of exceptions occur within threshold of time, abort!
        print('\n'*5)
        print('-'*100)
        print("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)")
        print('-'*100)
        print('\n'*5)
        showErrorMessage("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)", wrap=240)
