import bpy
from bpy.props import *

##################################################
# Motion extraction functionality
##################################################
 
class MotionExtractionFilter:

    m_armatureObj = None
    m_oldMoverChannel = None

    # Constructor
    def __init__( self, armatureObj, oldMoverChannel ):

        self.m_armatureObj = armatureObj
        self.m_oldMoverChannel = oldMoverChannel

    def execute( self ):
        print( "Extract motion running... ", self.m_armatureObj.name, " ", self.m_oldMoverChannel )
        return True

##################################################
# Motion extraction operator
##################################################

def armaturesList( scene, context ):

    items = []
    armature = context.object
    if armature is not None and armature.type == "ARMATURE":
        items.append( ( armature.name, armature.name, armature.name ) )

    return items


def bonesList( scene, context ):

    items = []
    armature = context.object
    if armature is not None and armature.type == "ARMATURE":
        for bone in armature.data.bones:
            items.append( ( bone.name, bone.name, bone.name ) )

    return items

class ExtractMotionOp(bpy.types.Operator):
    
    bl_idname = 'anim.extract_motion_animtools'
    bl_description = 'Extracts motion accumulated in one bone to another'
    bl_options = {'REGISTER', 'UNDO'}
    bl_label = 'Extract motion'

    #
    # Properties
    #
    #armature = StringProperty(
    #    name="Armature",
    #    description="Armature being animated",
    #    default="")
    armature = EnumProperty(
        name="Armature",
        description="Armature being animated",
        items=armaturesList)

    old_mover_channel = EnumProperty(
        name="Old mover channel",
        description="Name of the bone that currently accumulates the motion",
        items=bonesList)

    #
    # Operator implementation
    #

    # on mouse up:
    def invoke(self, context, event):

        # if an object is selected, and it's an armature, then set it as the default
        if ( context.object is not None and context.object.type == "ARMATURE" ):
            self.armature = context.object.name

        # show the properties
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    # on Invoke
    def execute(op, context):
        if len(op.armature) == 0:
            op.report( {'ERROR'}, "Extract Motion: No armature object specified" )
            return {"CANCELLED"}

        if len(op.old_mover_channel) == 0:
            op.report( {'ERROR'}, "Extract Motion: No bone specified as the mover channel" )
            return {"CANCELLED"}

        armatureObj = context.scene.objects[op.armature]
        if armatureObj is None:
            op.report( {'ERROR'}, "Extract Motion: The selected armature doesn't exist" )
            return {"CANCELLED"}

        filter = MotionExtractionFilter( armatureObj, op.old_mover_channel )
        if filter.execute() == True:
            return {'FINISHED'}
        else:
            return {'CANCELED'}
