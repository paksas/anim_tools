# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "AnimTools",
    "author": "Piotr Trochim <ptrochim@gmail.com>",
    "version": (0, 1),
    "blender": (2, 75),
    "location": "Tool bar > Animation tab > AnimTools",
    "description": "A set of animation tools",
    "warning": "",
    "category": "Animation",
}

if "bpy" in locals():
    import importlib
    if "extract_motion" in locals():
        importlib.reload(extract_motion)

import bpy
from bpy.props import *

from . import extract_motion

#
# GUI
#
class ExtractMotionGUI(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Animation"
    bl_label = 'Animation Tools'

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "select", text="")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('anim.extract_motion_animtools', text="Extract Motion")
        # << Register other animation filters here


##################################################
# Plugin registration
##################################################
def register():
    bpy.utils.register_module(__name__)

    pass
    
def unregister():
    bpy.utils.unregister_module(__name__)

    pass
    
if __name__ == "__main__":
    register()
