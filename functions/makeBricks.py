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
import bmesh
import math
import time
import sys
import random
import json
import numpy as np

# Blender imports
import bpy
from mathutils import Vector, Matrix

# Addon imports
from .hashObject import hash_object
from ..lib.Brick import Bricks
from ..lib.bricksDict import *
from .common import *
from .wrappers import *
from .general import bounds
from ..lib.caches import bricker_bm_cache
from ..lib.abs_plastic_materials import getAbsPlasticMaterialNames
from .makeBricks_utils import *


@timed_call('Time Elapsed')
def makeBricks(source, parent, logo, logo_details, dimensions, bricksDict, cm=None, split=False, brickScale=None, customData=None, group_name=None, clearExistingGroup=True, frameNum=None, cursorStatus=False, keys="ALL", printStatus=True, redraw=False):
    # set up variables
    scn = bpy.context.scene
    cm = cm or scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    zStep = getZStep(cm)

    # reset brickSizes/TypesUsed
    if keys == "ALL":
        cm.brickSizesUsed = ""
        cm.brickTypesUsed = ""

    mergeVertical = keys != "ALL" or cm.brickType == "BRICKS AND PLATES"

    # get bricksDict keys in sorted order
    if keys == "ALL":
        keys = list(bricksDict.keys())
    keys.sort(key=lambda x: (strToList(x)[0], strToList(x)[1]))
    # get dictionary of keys based on z value
    keysDict = {}
    for k0 in keys:
        z = strToList(k0)[2]
        if bricksDict[k0]["draw"]:
            if z in keysDict:
                keysDict[z].append(k0)
            else:
                keysDict[z] = [k0]
    denom = sum([len(keysDict[z0]) for z0 in keysDict.keys()])
    # store first key to active keys
    if cm.activeKey[0] == -1 and len(keys) > 0:
        loc = strToList(keys[0])
        cm.activeKey = loc

    # get brick group
    group_name = group_name or 'Bricker_%(n)s_bricks' % locals()
    bGroup = bpy.data.groups.get(group_name)
    # create new group if no existing group found
    if bGroup is None:
        bGroup = bpy.data.groups.new(group_name)
    # else, replace existing group
    elif clearExistingGroup:
        for obj0 in bGroup.objects:
            bGroup.objects.unlink(obj0)

    brick_mats = []
    if cm.materialType == "RANDOM":
        matObj = getMatObject(cm, typ="RANDOM")
        brick_mats = list(matObj.data.materials.keys())

    # initialize random states
    randS1 = np.random.RandomState(cm.mergeSeed)  # for brickSize calc
    randS2 = np.random.RandomState(cm.mergeSeed+1)
    randS3 = np.random.RandomState(cm.mergeSeed+2)

    mats = []
    allMeshes = bmesh.new()
    lowestZ = -1
    availableKeys = []
    maxBrickHeight = 1 if zStep == 3 else max(legalBricks.keys())
    connectThresh = 1 if cm.brickType == "CUSTOM" else cm.connectThresh
    # set up internal material for this object
    internalMat = None if len(source.data.materials) == 0 else bpy.data.materials.get(cm.internalMatName) or bpy.data.materials.get("Bricker_%(n)s_internal" % locals()) or bpy.data.materials.new("Bricker_%(n)s_internal" % locals())
    if internalMat is not None and cm.materialType == "SOURCE" and cm.matShellDepth < cm.shellThickness:
        mats.append(internalMat)
    # initialize bricksCreated
    bricksCreated = []
    # set number of times to run through all keys
    numIters = 2 if cm.brickType == "BRICKS AND PLATES" else 1
    i = 0
    # if merging unnecessary, simply update bricksDict values
    if not cm.customized and not (mergableBrickType(cm, up=zStep == 1) and (cm.maxDepth != 1 or cm.maxWidth != 1)):
        size = [1, 1, zStep]
        updateBrickSizesAndTypesUsed(cm, listToStr(size), bricksDict[keys[0]]["type"])
        availableKeys = keys
        for key in keys:
            bricksDict[key]["parent"] = "self"
            bricksDict[key]["size"] = size.copy()
            topExposed, botExposed = getBrickExposure(cm, bricksDict, key)
            bricksDict[key]["top_exposed"] = topExposed
            bricksDict[key]["bot_exposed"] = botExposed
            setFlippedAndRotated(bricksDict, key, [key])
            if bricksDict[key]["type"] == "SLOPE" and cm.brickType == "SLOPES":
                setBrickTypeForSlope(bricksDict, key, [key])
    else:
        # initialize progress bar around cursor
        old_percent = updateProgressBars(printStatus, cursorStatus, 0, -1, "Merging")
        # run merge operations (twice if flat brick type)
        for timeThrough in range(numIters):
            # iterate through z locations in bricksDict (bottom to top)
            for z in sorted(keysDict.keys()):
                # skip second and third rows on first time through
                if numIters == 2 and cm.alignBricks:
                    # initialize lowestZ if not done already
                    if lowestZ == -0.1:
                        lowestZ = z
                    if skipThisRow(cm, timeThrough, lowestZ, z):
                        continue
                # get availableKeys for attemptMerge
                availableKeysBase = []
                for ii in range(maxBrickHeight):
                    if ii + z in keysDict:
                        availableKeysBase += keysDict[z + ii]
                # get small duplicate of bricksDict for variations
                if connectThresh > 1:
                    bricksDictsBase = {}
                    for k4 in availableKeysBase:
                        bricksDictsBase[k4] = deepcopy(bricksDict[k4])
                    bricksDicts = [deepcopy(bricksDictsBase) for j in range(connectThresh)]
                    numAlignedEdges = [0 for idx in range(connectThresh)]
                else:
                    bricksDicts = [bricksDict]
                # calculate build variations for current z level
                for j in range(connectThresh):
                    availableKeys = availableKeysBase.copy()
                    numBricks = 0
                    if cm.mergeType == "RANDOM":
                        random.seed(cm.mergeSeed + i)
                        random.shuffle(keysDict[z])
                    # iterate through keys on current z level
                    for key in keysDict[z]:
                        i += 1 / connectThresh
                        brickD = bricksDicts[j][key]
                        # skip keys that are already drawn or have attempted merge
                        if brickD["attempted_merge"] or brickD["parent"] not in [None, "self"]:
                            # remove ignored keys from availableKeys (for attemptMerge)
                            if key in availableKeys:
                                availableKeys.remove(key)
                            continue

                        # initialize loc
                        loc = strToList(key)

                        # merge current brick with available adjacent bricks
                        brickSize = mergeWithAdjacentBricks(cm, brickD, bricksDicts[j], key, availableKeys, [1, 1, zStep], zStep, randS1, mergeVertical=mergeVertical)
                        brickD["size"] = brickSize
                        # iterate number aligned edges and bricks if generating multiple variations
                        if connectThresh > 1:
                            numAlignedEdges[j] += getNumAlignedEdges(cm, bricksDict, brickSize, key, loc, zStep)
                            numBricks += 1
                        # add brickSize to cm.brickSizesUsed if not already there
                        brickSizeStr = listToStr(sorted(brickSize[:2]) + [brickSize[2]])
                        updateBrickSizesAndTypesUsed(cm, brickSizeStr, brickD["type"])

                        # print status to terminal and cursor
                        cur_percent = (i / denom)
                        old_percent = updateProgressBars(printStatus, cursorStatus, cur_percent, old_percent, "Merging")

                        # remove keys in new brick from availableKeys (for attemptMerge)
                        updateKeysLists(cm, brickSize, loc, availableKeys, key)

                    if connectThresh > 1:
                        # if no aligned edges / bricks found, skip to next z level
                        if numAlignedEdges[j] == 0:
                            i += (len(keysDict[z]) * connectThresh - 1) / connectThresh
                            break
                        # add double the number of bricks so connectivity threshold is weighted towards larger bricks
                        numAlignedEdges[j] += numBricks * 2

                # choose optimal variation from above for current z level
                if connectThresh > 1:
                    optimalTest = numAlignedEdges.index(min(numAlignedEdges))
                    for k3 in bricksDicts[optimalTest]:
                        bricksDict[k3] = bricksDicts[optimalTest][k3]

        # end 'Merging' progress bar
        updateProgressBars(printStatus, cursorStatus, 1, 0, "Merging", end=True)

    # begin 'Building' progress bar
    old_percent = updateProgressBars(printStatus, cursorStatus, 0, -1, "Building")

    # draw merged bricks
    for i, k2 in enumerate(keys):
        if bricksDict[k2]["draw"] and bricksDict[k2]["parent"] == "self":
            loc = strToList(k2)
            # create brick based on the current brick info
            drawBrick(cm, bricksDict, k2, loc, i, dimensions, zStep, bricksDict[k2]["size"], split, customData, brickScale, bricksCreated, allMeshes, logo, logo_details, mats, brick_mats, internalMat, randS1, randS2, randS3)
            # print status to terminal and cursor
            old_percent = updateProgressBars(printStatus, cursorStatus, i/len(bricksDict.keys()), old_percent, "Building")

    # end progress bars
    updateProgressBars(printStatus, cursorStatus, 1, 0, "Building", end=True)

    # remove duplicate of original logoDetail
    if cm.logoDetail != "LEGO" and logo is not None:
        bpy.data.objects.remove(logo)

    # combine meshes, link to scene, and add relevant data to the new Blender MESH object
    if split:
        # iterate through keys
        old_percent = 0
        for i, key in enumerate(keys):
            # print status to terminal and cursor
            old_percent = updateProgressBars(printStatus, cursorStatus, i/len(bricksDict), old_percent, "Linking to Scene")

            if bricksDict[key]["parent"] == "self" and bricksDict[key]["draw"]:
                name = bricksDict[key]["name"]
                brick = bpy.data.objects.get(name)
                # create vert group for bevel mod (assuming only logo verts are selected):
                vg = brick.vertex_groups.get("%(name)s_bvl" % locals())
                if vg:
                    brick.vertex_groups.remove(vg)
                vg = brick.vertex_groups.new("%(name)s_bvl" % locals())
                vertList = [v.index for v in brick.data.vertices if not v.select]
                vg.add(vertList, 1, "ADD")
                # set up remaining brick info if brick object just created
                if clearExistingGroup or brick.name not in bGroup.objects.keys():
                    bGroup.objects.link(brick)
                brick.parent = parent
                if not brick.isBrick:
                    scn.objects.link(brick)
                    brick.isBrick = True
        # end progress bars
        updateProgressBars(printStatus, cursorStatus, 1, 0, "Linking to Scene", end=True)
    else:
        m = bpy.data.meshes.new("newMesh")
        allMeshes.to_mesh(m)
        name = 'Bricker_%(n)s_bricks_combined' % locals()
        if frameNum:
            name = "%(name)s_f_%(frameNum)s" % locals()
        allBricksObj = bpy.data.objects.get(name)
        if allBricksObj:
            allBricksObj.data = m
        else:
            allBricksObj = bpy.data.objects.new(name, m)
            allBricksObj.cmlist_id = cm.id
            # add edge split modifier
            if cm.brickType != "CUSTOM":
                addEdgeSplitMod(allBricksObj)
        if cm.brickType != "CUSTOM":
            # create vert group for bevel mod (assuming only logo verts are selected):
            vg = allBricksObj.vertex_groups.get("%(name)s_bvl" % locals())
            if vg:
                allBricksObj.vertex_groups.remove(vg)
            vg = allBricksObj.vertex_groups.new("%(name)s_bvl" % locals())
            vertList = [v.index for v in allBricksObj.data.vertices if not v.select]
            vg.add(vertList, 1, "ADD")
        if cm.materialType == "CUSTOM":
            mat = bpy.data.materials.get(cm.materialName)
            if mat is not None:
                allBricksObj.data.materials.append(mat)
        elif cm.materialType == "SOURCE" or (cm.materialType == "RANDOM" and len(brick_mats) > 0):
            for mat in mats:
                allBricksObj.data.materials.append(mat)
        # set parent
        allBricksObj.parent = parent
        # add bricks obj to scene and bricksCreated
        bGroup.objects.link(allBricksObj)
        if not allBricksObj.isBrickifiedObject:
            scn.objects.link(allBricksObj)
            # protect allBricksObj from being deleted
            allBricksObj.isBrickifiedObject = True
        bricksCreated.append(allBricksObj)

    # reset 'attempted_merge' for all items in bricksDict
    for key0 in bricksDict:
        bricksDict[key0]["attempted_merge"] = False

    return bricksCreated, bricksDict
