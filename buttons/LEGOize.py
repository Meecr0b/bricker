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

# system imports
import bpy
import random
import time
import bmesh
import os
import math
from ..functions import *
from .delete import legoizerDelete
from mathutils import Matrix, Vector, Euler
props = bpy.props

class legoizerLegoize(bpy.types.Operator):
    """Select objects layer by layer and shift by given values"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_legoize"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create Build Animation"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        # scn = context.scene
        # cm = scn.cmlist[scn.cmlist_index]
        # objIndex = bpy.data.objects.find(cm.source_name)
        # if objIndex == -1:
        #     return False
        return True

    action = bpy.props.EnumProperty(
        items=(
            ("CREATE", "Create", ""),
            ("UPDATE_MODEL", "Update Model", ""),
            ("UPDATE_ANIM", "Update Animation", ""),
            ("ANIMATE", "Animate", ""),
            ("RUN_MODAL", "Run Modal Operator", "")
        )
    )

    def modal(self, context, event):
        """ ??? """
        scn = context.scene

        if len(self.lastFrame) != len(scn.cmlist):
            self.lastFrame = [scn.frame_current-1]*len(scn.cmlist)

        for i,cm in enumerate(scn.cmlist):
            if cm.animated:
                if context.scene.frame_current != self.lastFrame[i]:
                    fn0 = self.lastFrame[i]
                    fn1 = scn.frame_current
                    if fn1 < cm.lastStartFrame:
                        fn1 = cm.lastStartFrame
                    elif fn1 > cm.lastStopFrame:
                        fn1 = cm.lastStopFrame
                    self.lastFrame[i] = fn1
                    if self.lastFrame[i] == fn0:
                        continue
                    n = cm.source_name

                    try:
                        curBricks = bpy.data.groups["LEGOizer_%(n)s_bricks_frame_%(fn1)s" % locals()]
                        for brick in curBricks.objects:
                            brick.hide = False
                            # scn.objects.link(brick)
                    except Exception as e:
                        print(e)
                    try:
                        lastBricks = bpy.data.groups["LEGOizer_%(n)s_bricks_frame_%(fn0)s" % locals()]
                        for brick in lastBricks.objects:
                            brick.hide = True
                            # scn.objects.unlink(brick)
                            brick.select = False
                    except Exception as e:
                        print(e)

        if event.type in {"ESC"} and event.shift:
            scn.modalRunning = False
            bpy.context.window_manager["modal_running"] = False
            self.report({"INFO"}, "Modal Finished")
            return{"FINISHED"}
        return {"PASS_THROUGH"}

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if self.action in ["CREATE","ANIMATE"]:
            if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
                objToLegoize = bpy.context.active_object
            else:
                objToLegoize = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        else:
            cm = scn.cmlist[scn.cmlist_index]
            objToLegoize = bpy.data.objects.get(cm.source_name)
        return objToLegoize

    def getDimensionsAndBounds(self, source, skipDimensions=False):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        # get dimensions and bounds
        source_details = bounds(source)
        if not skipDimensions:
            if cm.brickType == "Plates" or cm.brickType == "Bricks and Plates":
                zScale = 0.333
            elif cm.brickType in ["Bricks", "Custom"]:
                zScale = 1
            dimensions = Bricks.get_dimensions(cm.brickHeight, zScale, cm.gap)
            return source_details, dimensions
        else:
            return source_details

    def getParent(self, LEGOizer_parent_on, loc):
        parent = bpy.data.objects.get(LEGOizer_parent_on)
        if parent is None:
            m = bpy.data.meshes.new(LEGOizer_parent_on + "_mesh")
            parent = bpy.data.objects.new(LEGOizer_parent_on, m)
            parent.location = loc
            safeScn = getSafeScn()
            safeScn.objects.link(parent)
        return parent


    def getRefLogo(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        # update refLogo
        if cm.logoDetail == "None":
            refLogo = None
        else:
            decimate = False
            r = cm.logoResolution
            refLogoImport = bpy.data.objects.get("LEGOizer_refLogo")
            if refLogoImport is not None:
                refLogo = bpy.data.objects.get("LEGOizer_refLogo_%(r)s" % locals())
                if refLogo is None:
                    refLogo = bpy.data.objects.new("LEGOizer_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                    decimate = True
            else:
                # import refLogo and add to group
                refLogoImport = importLogo()
                refLogoImport.name = "LEGOizer_refLogo"
                safeUnlink(refLogoImport)
                refLogo = bpy.data.objects.new("LEGOizer_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                decimate = True
            # decimate refLogo
            # TODO: Speed this up, if possible
            if refLogo is not None and decimate and cm.logoResolution < 1:
                dMod = refLogo.modifiers.new('Decimate', type='DECIMATE')
                dMod.ratio = cm.logoResolution * 1.6
                scn.objects.link(refLogo)
                select(refLogo, active=refLogo)
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Decimate')
                safeUnlink(refLogo)

        return refLogo

    def createNewBricks(self, source, parent, source_details, dimensions, refLogo, curFrame=None):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if cm.brickType == "Custom":
            customObj0 = bpy.data.objects[cm.customObjectName]
            select(customObj0, active=customObj0)
            bpy.ops.object.duplicate()
            customObj = scn.objects.active
            select(customObj, active=customObj)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            customObj_details = bounds(customObj)
            customData = customObj.data
            bpy.data.objects.remove(customObj, True)
            scale = cm.brickHeight/customObj_details.z.distance
            R = (scale * customObj_details.x.distance + dimensions["gap"], scale * customObj_details.y.distance + dimensions["gap"], scale * customObj_details.z.distance + dimensions["gap"])
        else:
            customData = None
            customObj_details = None
            R = (dimensions["width"]+dimensions["gap"], dimensions["width"]+dimensions["gap"], dimensions["height"]+dimensions["gap"])
        bricksDict = makeBricksDict(source, source_details, dimensions, R)
        if curFrame is not None:
            group_name = 'LEGOizer_%(n)s_bricks_frame_%(curFrame)s' % locals()
        else:
            group_name = None
        makeBricks(parent, refLogo, dimensions, bricksDict, cm.splitModel, R=R, customData=customData, customObj_details=customObj_details, group_name=group_name, frameNum=curFrame)
        if int(round((source_details.x.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on X axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.y.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Y axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.z.distance)/(dimensions["height"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Z axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        return group_name

    def isValid(self, source, LEGOizer_bricks_gn,):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if cm.brickType == "Custom":
            if cm.customObjectName == "":
                self.report({"WARNING"}, "Custom brick type object not specified.")
                return False
            if bpy.data.objects.find(cm.customObjectName) == -1:
                self.report({"WARNING"}, "Custom brick type object '%(n)s' could not be found" % locals())
                return False
            if bpy.data.objects[cm.customObjectName].type != "MESH":
                self.report({"WARNING"}, "Custom brick type object is not of type 'MESH'. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        if self.action in ["CREATE", "ANIMATE"]:
            # verify function can run
            if groupExists(LEGOizer_bricks_gn):
                self.report({"WARNING"}, "LEGOized Model already created.")
                return False
            # verify source exists and is of type mesh
            if cm.source_name == "":
                self.report({"WARNING"}, "Please select a mesh to LEGOize")
                return False
            if cm.source_name[:9] == "LEGOizer_" and (cm.source_name[-7:] == "_bricks" or cm.source_name[-9:] == "_combined"):
                self.report({"WARNING"}, "Cannot LEGOize models created with the LEGOizer")
                return False
            if source == None:
                n = cm.source_name
                self.report({"WARNING"}, "'%(n)s' could not be found" % locals())
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be LEGOized. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        if self.action in ["ANIMATE", "UPDATE_ANIM"]:
            # verify start frame is less than stop frame
            if cm.startFrame > cm.stopFrame:
                self.report({"ERROR"}, "Start frame must be less than or equal to stop frame (see animation tab below).")
                return False
            # TODO: Alert user to bake fluid/cloth simulation before attempting to LEGOize

        if self.action == "UPDATE_MODEL":
            # make sure 'LEGOizer_[source name]_bricks' group exists
            if not groupExists(LEGOizer_bricks_gn):
                self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
                return False

        success = False
        for i in range(20):
            if source.layers[i] == True and scn.layers[i] == True:
                success = True
        if not success:
            self.report({"WARNING"}, "Object is not on active layer(s)")
            return False

        return True

    def legoizeAnimation(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        cm.splitModel = False
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()

        # if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
        #     sourceOrig = bpy.context.active_object
        # else:
        #     sourceOrig = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        #
        sourceOrig = self.getObjectToLegoize()
        if self.action == "UPDATE_ANIM":
            safeLink(sourceOrig)

        # if there are no changes to apply, simply return "FINISHED"
        if not cm.modelIsDirty and not cm.buildIsDirty and not cm.bricksAreDirty and (cm.materialType == "Custom" or not cm.materialIsDirty):
            return "FINISHED"

        # delete old bricks if present
        if self.action == "UPDATE_ANIM":
            legoizerDelete.cleanUp("ANIMATION")
        dGroup = bpy.data.groups.new(LEGOizer_source_dupes_gn)
        pGroup = bpy.data.groups.new(LEGOizer_parent_on)

        parent0 = self.getParent(LEGOizer_parent_on, sourceOrig.location.to_tuple())

        if cm.brickType != "Custom":
            refLogo = self.getRefLogo()
        else:
            refLogo = None

        # iterate through frames of animation and generate lego model
        for i in range(cm.stopFrame - cm.startFrame + 1):
            # duplicate source for current frame and apply transformation data
            # scn.layers = getLayersList(0)
            # source = bpy.data.objects.new(sourceOrig.name + "_" + str(i), sourceOrig.data.copy())
            # copyAnimationData(sourceOrig, source)
            select(sourceOrig, active=sourceOrig)
            bpy.ops.object.duplicate()
            source = scn.objects.active
            dGroup.objects.link(source)
            source.name = sourceOrig.name + "_" + str(i)
            # source.layers = getLayersList(i+1)
            # scn.layers = getLayersList(i+1)
            # apply animated transform data
            curFrame = cm.startFrame + i
            scn.frame_set(curFrame)
            source.matrix_world = sourceOrig.matrix_world
            source.animation_data_clear()
            scn.update()
            # scn.layers[0] = False
            # scn.objects.link(source)
            source["previous_location"] = source.location.to_tuple()
            select(source, active=source)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
            safeUnlink(source)

            # get source_details and dimensions
            source_details, dimensions = self.getDimensionsAndBounds(source)

            if self.action == "CREATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.z.distance

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            parent = bpy.data.objects.new(LEGOizer_parent_on + "_" + str(i), source.data.copy())
            if "Fluidsim" in sourceOrig.modifiers:
                parent.location = (source_details.x.mid + source["previous_location"][0] - parent0.location.x, source_details.y.mid + source["previous_location"][1] - parent0.location.y, source_details.z.mid + source["previous_location"][2] - parent0.location.z)
            else:
                parent.location = (source_details.x.mid - parent0.location.x, source_details.y.mid - parent0.location.y, source_details.z.mid - parent0.location.z)
            parent.parent = parent0
            pGroup = bpy.data.groups[LEGOizer_parent_on] # TODO: This line was added to protect against segmentation fault in version 2.78. Once you're running 2.79, try it without this line!
            pGroup.objects.link(parent)
            scn.objects.link(parent)
            scn.update()
            safeUnlink(parent)

            # create new bricks
            group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, curFrame=curFrame)
            for obj in bpy.data.groups[group_name].objects:
                obj.hide = True

            print("completed frame " + str(curFrame))

        safeUnlink(sourceOrig)
        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(cm.lastStartFrame)
        cm.animated = True

    def legoizeModel(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        source = self.getObjectToLegoize()
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()

        # if there are no changes to apply, simply return "FINISHED"
        if not self.action == "CREATE" and not cm.modelIsDirty and not cm.buildIsDirty and not cm.bricksAreDirty and (cm.materialType == "Custom" or not cm.materialIsDirty) and not (self.action == "UPDATE_MODEL" and len(bpy.data.groups[LEGOizer_bricks_gn].objects) == 0):
            return{"FINISHED"}

        # delete old bricks if present
        if self.action == "UPDATE_MODEL":
            legoizerDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)

        if self.action == "CREATE":
            source["previous_location"] = source.location.to_tuple()
            rot = source.rotation_euler.copy()
            s = source.scale.to_tuple()
            source.location = (0,0,0)
            select(source, active=source)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            scn.update()

        # update scene so mesh data is available for ray casting
        if source.name not in scn.objects.keys():
            safeLink(source)
        scn.update()

        if source.name in scn.objects.keys():
            safeUnlink(source)

        # get source_details and dimensions
        source_details, dimensions = self.getDimensionsAndBounds(source)

        if self.action == "CREATE":
            # set source model height for display in UI
            cm.modelHeight = source_details.z.distance

        parentLoc = (source_details.x.mid + source["previous_location"][0], source_details.y.mid + source["previous_location"][1], source_details.z.mid + source["previous_location"][2])
        parent = self.getParent(LEGOizer_parent_on, parentLoc)

        # update refLogo
        if cm.brickType != "Custom":
            refLogo = self.getRefLogo()
        else:
            refLogo = None

        # create new bricks
        self.createNewBricks(source, parent, source_details, dimensions, refLogo)

        cm.modelCreated = True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()

        if self.action == "RUN_MODAL" and not modalRunning():
            self.lastFrame = []
            bpy.context.window_manager["modal_running"] = True
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}

        source = self.getObjectToLegoize()
        if not self.isValid(source, LEGOizer_bricks_gn):
            return {"CANCELLED"}

        if self.action not in ["ANIMATE", "UPDATE_ANIM"]:
            self.legoizeModel()
        else:
            self.legoizeAnimation()

        # # set final variables
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.lastSplitModel = cm.splitModel
        cm.materialIsDirty = False
        cm.modelIsDirty = False
        cm.buildIsDirty = False
        cm.bricksAreDirty = False

        disableRelationshipLines()

        # STOPWATCH CHECK
        stopWatch("Total Time Elapsed", time.time()-startTime)

        if not modalRunning():
            self.lastFrame = []
            bpy.context.window_manager["modal_running"] = True
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            return{"FINISHED"}

    def cancel(self, context):
        scn = context.scene
        bpy.context.window_manager["modal_running"] = False
