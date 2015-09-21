import bpy
from bpy.props import *

##################################################
# Motion extraction functionality
##################################################
 
class MotionExtractionFilter:

    m_scene = None
    m_armatureObj = None
    m_oldMoverChannel = None

    #
    # Constructor
    #
    def __init__( self, scene, armatureObj, oldMoverChannel ):

        self.m_scene = scene
        self.m_armatureObj = armatureObj
        self.m_oldMoverChannel = oldMoverChannel

    #
    # Performs the motion extraction procedure
    #
    def execute( self ):

        print( "Extract motion running: ", self.m_oldMoverChannel, " --> ", self.m_armatureObj.name )

        if self.m_armatureObj.animation_data is None or self.m_armatureObj.animation_data.action is None:
            op.report( {'ERROR'}, self.m_armatureObj.name, " doesn't have any action assigned" )
            return False
        
        animation = self.m_armatureObj.animation_data.action
        framesCount = int( animation.frame_range[1] )
                
        motionTransforms = self.collectMotionTransforms( animation, framesCount )

        return True

    #
    # Collects motion transforms from the old mover channel bone
    #
    def collectMotionTransforms( self, animation, framesCount ):

        # store the original frame index to restore the scene to the previous state once we're done
        originalFrameIdx = self.m_scene.frame_current

        print( "Extracting motion from action: ", animation.name, "; frames [1..", framesCount, "]" )

        # find the motion extraction track idx
        motionTrackIdx = self.m_armatureObj.pose.bones.find( self.m_oldMoverChannel )
        print( "Motion track idx = ", motionTrackIdx )

        motionBone = self.m_armatureObj.pose.bones[self.m_oldMoverChannel]

        # sample animation frames
        motionTransforms = []
        for frameIdx in range( framesCount ):

            self.m_scene.frame_set( frameIdx )

            motionBoneRefMtx = motionBone.bone.matrix_local
            motionBoneMtx = motionBone.matrix
            motionBoneLocMtx = motionBoneRefMtx.inverted() * motionBoneMtx
            loc, rot, scale = motionBoneLocMtx.decompose()

            motionTransforms.append( (loc, rot, scale) )
            print( "Frame ", frameIdx, ". loc", loc, "; rot", rot, "; scale", scale )

        # restore the scene to its previous state
        self.m_scene.frame_set( originalFrameIdx )

        return motionTransforms



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
            if bone.parent is None: # limit selection to root bones only
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

    #
    # on mouse up:
    #
    def invoke(self, context, event):

        # if an object is selected, and it's an armature, then set it as the default
        if ( context.object is not None and context.object.type == "ARMATURE" ):
            self.armature = context.object.name

        # show the properties
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    #
    # on Invoke
    #
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

        filter = MotionExtractionFilter( context.scene, armatureObj, op.old_mover_channel )
        if filter.execute() == True:
            return {'FINISHED'}
        else:
            return {'CANCELED'}
