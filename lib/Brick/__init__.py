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
import bpy
import bmesh
import random
import time
import numpy as np

# Blender imports
from mathutils import Vector, Matrix

# Rebrickr imports
from .mesh_generators.standard_brick import *
from .mesh_generators.round_1x1 import *
from .get_brick_dimensions import *
from ...functions.general import *
from ...functions.common import *

class Bricks:
    @staticmethod
    def new_mesh(dimensions, size=[1,1,3], type="STANDARD", logo=False, all_vars=False, logo_type=None, logo_details=None, logo_scale=None, logo_inset=None, undersideDetail="Flat", stud=True, circleVerts=None):
        """ create unlinked Brick at origin """

        # create brick mesh
        if type == "STANDARD":
            _,cm,_ = getActiveContextInfo()
            brickBM = makeStandardBrick(dimensions=dimensions, brickSize=size, brickType=cm.brickType, circleVerts=circleVerts, detail=undersideDetail, stud=stud)
        elif type in ["CYLINDER", "CONE", "STUD", "STUD_HOLLOW"]:
            brickBM = makeRound1x1(dimensions=dimensions, circleVerts=circleVerts, type=type, detail=undersideDetail, stud=stud)
        else:
            raise ValueError("'new_mesh' function received unrecognized parameter '" + type + "'")

        # create list of brick bmesh variations
        if logo and stud and type in ["STANDARD", "STUD"]:
            bms = makeLogoVariations(dimensions, size, randS0, all_vars, logo_type, logo_details, logo_scale, logo_inset)
        else:
            bms = [bmesh.new()]

        # add brick mesh to bm mesh
        junkMesh = bpy.data.meshes.new('Rebrickr_junkMesh')
        brickBM.to_mesh(junkMesh)
        for bm in bms:
            bm.from_mesh(junkMesh)
        bpy.data.meshes.remove(junkMesh, do_unlink=True)

        # return bmesh objects
        return bms

    @staticmethod
    def splitAll(bricksDict, keys=None, cm=None):
        if cm is None:
            scn, cm, _ = getActiveContextInfo()
        if keys is None:
            keys = list(bricksDict.keys())
        zStep = getZStep(cm)
        for key in keys:
            # set all bricks as unmerged
            if bricksDict[key]["draw"]:
                bricksDict[key]["parent_brick"] = "self"
                bricksDict[key]["size"] = [1, 1, zStep]

    def split(bricksDict, key, loc=None, cm=None, v=True, h=True):
        # set up unspecified paramaters
        if cm is None:
            scn, cm, _ = getActiveContextInfo()
        if loc is None:
            loc = strToList(key)
        # initialize vars
        size = bricksDict[key]["size"]
        newSize = [1, 1, size[2]]
        zStep = getZStep(cm)
        if cm.brickType == "Bricks and Plates":
            if not v:
                zStep = 3
            else:
                newSize[2] = 1
        if not h:
            newSize[0] = size[0]
            newSize[1] = size[1]
            size[0] = 1
            size[1] = 1
        splitKeys = []
        x,y,z = loc
        # split brick into individual bricks
        for x0 in range(x, x + size[0]):
            for y0 in range(y, y + size[1]):
                for z0 in range(z, z + size[2], zStep):
                    curKey = listToStr([x0,y0,z0])
                    bricksDict[curKey]["size"] = newSize
                    bricksDict[curKey]["parent_brick"] = "self"
                    bricksDict[curKey]["top_exposed"] = bricksDict[key]["top_exposed"]
                    bricksDict[curKey]["bot_exposed"] = bricksDict[key]["bot_exposed"]
                    # add curKey to list of split keys
                    splitKeys.append(curKey)
        return splitKeys

    @staticmethod
    def get_dimensions(height=1, zScale=1, gap_percentage=0.01):
        return get_brick_dimensions(height, zScale, gap_percentage)

def makeLogoVariations(dimensions, size, randS0, all_vars, logo_type, logo_details, logo_scale, logo_inset):
    # get logo rotation angle based on size of brick
    rot_mult = 180
    rot_vars = 2
    rot_add = 0
    if size[0] == 1 and size[1] == 1:
        rot_mult = 90
        rot_vars = 4
    elif size[0] == 2 and size[1] > 2:
        rot_add = 90
    elif ((size[1] == 2 and size[0] > 2) or
          (size[0] == 2 and size[1] == 2)):
        pass
    elif size[0] == 1:
        rot_add = 90
    # set zRot to random rotation angle
    if all_vars:
        zRots = [i * rot_mult + rot_add for i in range(rot_vars)]
    else:
        randomSeed = int(time.time()*10**6) % 10000
        randS0 = np.random.RandomState(randomSeed)
        zRots = [randS0.randint(0,rot_vars) * rot_mult + rot_add]
    lw = dimensions["logo_width"] * logo_scale
    logoBM_ref = bmesh.new()
    logoBM_ref.from_mesh(logo.data)
    if logo_type == "LEGO Logo":
        smoothFaces(list(logoBM_ref.faces))
        # transform logo into place
        bmesh.ops.scale(logoBM_ref, vec=Vector((lw, lw, lw)), verts=logoBM_ref.verts)
        bmesh.ops.rotate(logoBM_ref, verts=logoBM_ref.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    else:
        # transform logo to origin (transform was (or should be at least) applied, origin is at center)
        for v in logoBM_ref.verts:
            v.co -= Vector((logo_details.x.mid, logo_details.y.mid, logo_details.z.mid))
            v.select = True
        # scale logo
        distMax = max(logo_details.x.dist, logo_details.y.dist)
        bmesh.ops.scale(logoBM_ref, vec=Vector((lw/distMax, lw/distMax, lw/distMax)), verts=logoBM_ref.verts)

    bms = [bm.copy() for zRot in zRots]
    for i,zRot in enumerate(zRots):
        for x in range(size[0]):
            for y in range(size[1]):
                logoBM = logoBM_ref.copy()
                # rotate logo around stud
                if zRot != 0:
                    bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(0.0, 0.0, 1.0), matrix=Matrix.Rotation(math.radians(zRot), 3, 'Z'))
                # transform logo to appropriate position
                zOffset = dimensions["logo_offset"]
                if logo_type != "LEGO Logo" and logo_details is not None:
                    zOffset += ((logo_details.z.dist * (lw / distMax)) / 2) * (1 - logo_inset * 2)
                xyOffset = dimensions["width"] + dimensions["gap"]
                for v in logoBM.verts:
                    v.co += Vector((x * xyOffset, y * xyOffset, zOffset))
                # add logoBM mesh to bm mesh
                junkMesh = bpy.data.meshes.new('Rebrickr_junkMesh')
                logoBM.to_mesh(junkMesh)
                bms[i].from_mesh(junkMesh)
                bpy.data.meshes.remove(junkMesh, do_unlink=True)
    return bms
