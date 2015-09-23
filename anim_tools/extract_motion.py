﻿import bpy
from bpy.props import *
import mathutils
import math
from . import motion_operator
from . import transform_utils

##################################################
# Motion extraction functionality
##################################################
 
class MotionExtractionFilter:

    m_scene = None
    m_armatureObj = None
    m_oldMoverChannel = None

    m_movementDirection = ( True, True, False )
    m_upAxis = "Z"
    m_includeRotation = False

    #
    # Constructor
    #
    def __init__( self, scene, armatureObj, oldMoverChannel ):

        self.m_scene = scene
        self.m_armatureObj = armatureObj
        self.m_oldMoverChannel = oldMoverChannel

    #
    # Defines the directions in which translation should be included or filtered out.
    #
    def setMovementDirectionFilter( self, xAxis, yAxis, zAxis ):
        self.m_movementDirection = ( xAxis, yAxis, zAxis )

    #
    # Defines whether the extracted motion should include root rotation about the up axis.
    # Any other rotation will be filtered out
    #
    def setRotationFilter( self, includeRotation, upAxis ):
        self.m_includeRotation = includeRotation
        self.m_upAxis = upAxis

    #
    # Performs the motion extraction procedure
    #
    def execute( self ):

        print( "Extract motion running: ", self.m_oldMoverChannel, " --> ", self.m_armatureObj.name )

        if self.m_armatureObj.animation_data is None or self.m_armatureObj.animation_data.action is None:
            op.report( {'ERROR'}, self.m_armatureObj.name, " doesn't have any action assigned" )
            return False
        
        animation = self.m_armatureObj.animation_data.action

        armatureOp = motion_operator.ObjectMotionOp( self.m_armatureObj )
        moverChannelOp = motion_operator.BoneMotionOp( self.m_armatureObj, self.m_armatureObj.pose.bones[self.m_oldMoverChannel] )
                
        # Grab the motion of the mover channel
        motion = moverChannelOp.sampleMotion( animation )
        transform_utils.printMotion( motion, "Original motion" )

        # Filter out the motion we're interested in
        motion = self.filterMotion( motion )
        transform_utils.printMotion( motion, "Filtered motion" )

        # Keyframe the object with that motion
        armatureOp.setMotion( animation, motion, self.m_includeRotation )

        # Remove the extracted motion from the root bones
        for bone in self.m_armatureObj.pose.bones:
            if bone.parent is None:
                self.removeMotionFromBone( bone, motion, animation )


        return True

    #
    # Filters the motion according to the specified parameters
    #
    def filterMotion( self, motion ):

        filteredMotion = []
        for keyframe in motion:

            loc, rot = keyframe[0:2]

            for axisIdx in range(3):
                if self.m_movementDirection[axisIdx] == False:
                    loc[axisIdx] = 0.0

            if self.m_includeRotation == True:
                eulerRot = rot.to_euler('XYZ')
                if ( self.m_upAxis == "X" ):
                    eulerRot.y = 0.0
                    eulerRot.z = 0.0
                elif ( self.m_upAxis == "Y" ):
                    eulerRot.x = 0.0
                    eulerRot.z = 0.0
                elif ( self.m_upAxis == "Z" ):
                    eulerRot.x = 0.0
                    eulerRot.y = 0.0
                rot = eulerRot.to_quaternion()
            else:
                rot = mathutils.Quaternion( ( 1.0, 0.0, 0.0, 0.0 ) )

            filteredMotion.append( ( loc, rot ) )
         
        return filteredMotion
    
    #
    # Removes the specified motion from the bone
    #
    def removeMotionFromBone( self, bone, motion, animation ):
        
        boneMotionOp = motion_operator.BoneMotionOp( self.m_armatureObj, bone )
        prevMotion = boneMotionOp.sampleMotion( animation )
        newMotion = transform_utils.calcRelativeMotion( motion, prevMotion )
        boneMotionOp.setMotion( animation, newMotion, self.m_includeRotation )


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

    xTranslation = BoolProperty( 
        name="X Translation",
        description="Include translation along the X axis?",
        default=True )

    yTranslation = BoolProperty( 
        name="Y Translation",
        description="Include translation along the Y axis?",
        default=True )

    zTranslation = BoolProperty( 
        name="Z Translation",
        description="Include translation along the Z axis?",
        default=False )

    includeRotation = BoolProperty( 
        name="Rotation about up axis",
        description="Include rotation about up axis?",
        default=False )

    upAxis = EnumProperty(
        name="Up axis",
        description="World axis considered the up direction for the model",
        items=[
            ( "X", "X", "X" ),
            ( "Y", "Y", "Y" ),
            ( "Z", "Z", "Z" )],
        default="Z"
        )

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
        filter.setMovementDirectionFilter( op.xTranslation, op.yTranslation, op.zTranslation )
        filter.setRotationFilter( op.includeRotation, op.upAxis )

        if filter.execute() == True:
            return {'FINISHED'}
        else:
            return {'CANCELED'}
