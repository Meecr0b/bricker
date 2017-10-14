bl_info = {
    "name"        : "Rebrickr",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (1, 0, 1),
    "blender"     : (2, 78, 0),
    "description" : "Turn any mesh into a 3D brick sculpture or simulation with the click of a button",
    "location"    : "View3D > Tools > Rebrickr",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "https://www.blendermarket.com/creator/products/rebrickr/",
    "tracker_url" : "https://github.com/bblanimation/rebrickr/issues",
    "category"    : "Object"}

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

def deleteUnprotected(context, use_global=False):
    scn = context.scene
    protected = []
    for obj in context.selected_objects:
        if obj.isBrickifiedObject or obj.isBrick:
            cm = None
            for cmCur in scn.cmlist:
                n = cmCur.source_name
                if "Rebrickr_%(n)s_bricks_combined" % locals() in obj.name:
                    cm = cmCur
                    break
                elif "Rebrickr_%(n)s_brick_" % locals() in obj.name:
                    bGroup = bpy.data.groups.get("Rebrickr_%(n)s_bricks" % locals())
                    if bGroup is not None and len(bGroup.objects) < 2:
                        cm = cmCur
                        break
            if cm is not None:
                RebrickrDelete.runFullDelete(cm=cm)
                scn.objects.active.select = False
            else:
                obj_users_scene = len(obj.users_scene)
                scn.objects.unlink(obj)
                if use_global or obj_users_scene == 1:
                    bpy.data.objects.remove(obj, True)
        elif not obj.protected:
            obj_users_scene = len(obj.users_scene)
            scn.objects.unlink(obj)
            if use_global or obj_users_scene == 1:
                bpy.data.objects.remove(obj, True)
        else:
            print(obj.name +' is protected')
            protected.append(obj.name)

    return protected

class delete_override(Operator):
    """OK?"""
    bl_idname = "object.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'INTERNAL'}

    use_global = BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        # return context.active_object is not None
        return True

    def runDelete(self, context):
        protected = deleteUnprotected(context, self.use_global)
        if len(protected) > 0:
            self.report({"WARNING"}, "Rebrickr is using the following object(s): " + str(protected)[1:-1])
        # push delete action to undo stack
        bpy.ops.ed.undo_push(message="Delete")

    def execute(self, context):
        self.runDelete(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        # Run confirmation popup for delete action
        confirmation_returned = context.window_manager.invoke_confirm(self, event)
        if confirmation_returned != {'FINISHED'}:
            return confirmation_returned
        else:
            self.runDelete(context)
            return {'FINISHED'}
