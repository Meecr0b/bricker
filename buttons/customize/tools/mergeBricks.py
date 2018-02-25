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
import copy

# Blender imports
import bpy
from bpy.types import Operator

# Rebrickr imports
from ..undo_stack import *
from ..functions import *
from ...brickify import *
from ...brickify import *
from ....lib.bricksDict.functions import getDictKey
from ....lib.Brick.legal_brick_sizes import *
from ....functions import *


class mergeBricks(Operator):
    """Merge selected bricks"""
    bl_idname = "rebrickr.merge_bricks"
    bl_label = "Merge Bricks"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        i = 0
        # check that at least 2 objects are selected and are bricks
        for obj in objs:
            if obj.isBrick:
                # get cmlist item referred to by object
                cm = getItemByID(scn.cmlist, obj.cmlist_id)
                if cm.lastBrickType != "CUSTOM" and not cm.buildIsDirty:
                    i += 1
                    if i == 2:
                        return True
        return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects

            # initialize objsD (key:cm_idx, val:list of brick objects)
            objsD = createObjsD(selected_objects)

            # iterate through keys in objsD
            for cm_idx in objsD.keys():
                cm = scn.cmlist[cm_idx]
                self.undo_stack.iterateStates(cm)
                # initialize vars
                bricksDict = copy.deepcopy(self.bricksDicts[cm_idx])
                parent_brick = None
                allSplitKeys = []

                # iterate through objects in objsD[cm_idx]
                for obj in objsD[cm_idx]:
                    # initialize vars
                    dictKey, dictLoc = getDictKey(obj.name)
                    x0, y0, z0 = dictLoc

                    # split brick in matrix
                    splitKeys = Bricks.split(bricksDict, dictKey, cm=cm)
                    allSplitKeys += splitKeys
                    # delete the object that was split
                    delete(obj)

                # run self.mergeBricks
                keysToUpdate = mergeBricks.mergeBricks(bricksDict, allSplitKeys, cm)

                # draw modified bricks
                drawUpdatedBricks(cm, bricksDict, keysToUpdate)

                # model is now customized
                cm.customized = True
        except:
            handle_exception()
        return{"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('merge')
        selected_objects = bpy.context.selected_objects
        _, self.bricksDicts = createObjNamesAndBricksDictDs(selected_objects)

    ###################################################
    # class variables

    # variables
    bricksDicts = {}

    #############################################
    # class methods

    @staticmethod
    def getSortedKeys(keys):
        """ sort bricks by (x+y) location for best merge """
        keys.sort(key=lambda k: (strToList(k)[0] * strToList(k)[1] * strToList(k)[2]))
        return keys

    @staticmethod
    def mergeBricks(bricksDict, keys, cm, mergeVertical=True, targetType="BRICK", height3Only=False):
        # initialize vars
        updatedKeys = []
        zStep = getZStep(cm)
        randState = np.random.RandomState(cm.mergeSeed)

        keys = mergeBricks.getSortedKeys(keys)

        for key in keys:
            if bricksDict[key]["parent_brick"] in [None, "self"]:
                # attempt to merge current brick with other bricks in keys, according to available brick types
                # TODO: improve originalIsBrick argument (currently hardcoded to False)
                loc = strToList(key)
                parentD = bricksDict[getParentKey(bricksDict, key)]
                tallType = targetType if targetType in getBrickTypes(height=3) else parentD["type"]
                shortType = targetType if targetType in getBrickTypes(height=1) else parentD["type"]
                brickSize = attemptMerge(cm, bricksDict, key, keys, loc, [parentD["size"]], zStep, randState, preferLargest=True, mergeVertical=mergeVertical, shortType=shortType, tallType=tallType, height3Only=height3Only)
                # bricksDict[key]["size"] = brickSize
                # set exposure of current [merged] brick
                topExposed, botExposed = getBrickExposure(cm, bricksDict, key, loc)
                bricksDict[key]["top_exposed"] = topExposed
                bricksDict[key]["bot_exposed"] = botExposed
                updatedKeys.append(key)
        return updatedKeys

    #############################################