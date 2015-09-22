import bpy
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
        framesCount = int( animation.frame_range[1] )
                
        # Grab the motion of the mover channel
        motion = self.collectMotionTransforms( animation, framesCount )
        self.printMotion( motion, "Original motion" )

        # Filter out the motion we're interested in
        self.filterMotion( motion )
        self.printMotion( motion, "Filtered motion" )

        # Keyframe the object with that motion
        self.keyframeAnimationRoot( animation, motion )

        # Remove the extracted motion from the root bones
        for bone in self.m_armatureObj.data.bones:
            if bone.parent is not None:
                self.removeMotionFromBone( bone, motion, animation )


        return True

    #
    # Filters the motion according to the specified parameters
    #
    def filterMotion( self, motion ):

        filteredMotion = []
        for keyframe in motion:

            loc, rot, scale = keyframe[0:3]

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

            filteredMotion.append( ( loc, rot, scale ) )
         
        motion = filteredMotion

    #
    # Keyframes the movement of armature root
    #
    def keyframeAnimationRoot( self, animation, motion ):

        # store the original frame index to restore the scene to the previous state once we're done
        originalFrameIdx = self.m_scene.frame_current

        # delete curves we're about to replace
        self.deleteObjectMotionFCurves( animation )

        print( "Keyframing the armature object."  )
        framesCount = len( motion )
        # location
        for axis_i in range(3):
            
            # if a curve already exists, delete it
            #curve = animation.fcurves.find( "location" )
            #if ( curve is not None ):
            #    animation.fcurves.remove( curve )

            curve = animation.fcurves.new(data_path="location", index=axis_i, action_group='Location' )
            keyframePoints = curve.keyframe_points
            keyframePoints.add( framesCount )

            for frameIdx in range( framesCount ):
                loc, rot, scale = motion[frameIdx]
                keyframePoints[frameIdx].co = (frameIdx + 1.0, loc[axis_i])
                keyframePoints[frameIdx].interpolation = 'LINEAR'

        # rotation
        if self.m_includeRotation:
            for axis_i in range(4):

                curve = animation.fcurves.new(data_path="rotation_quaternion", index=axis_i, action_group='Rotation')
                keyframePoints = curve.keyframe_points
                keyframePoints.add( framesCount )

                for frameIdx in range( framesCount ):
                    loc, rot, scale = motion[frameIdx]
                    keyframePoints[frameIdx].co = (frameIdx + 1.0, rot[axis_i])
                    keyframePoints[frameIdx].interpolation = 'LINEAR'

        # restore the scene to its previous state
        self.m_scene.frame_set( originalFrameIdx )

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

        # restore the scene to its previous state
        self.m_scene.frame_set( originalFrameIdx )

        return motionTransforms

    
    #
    # Removes the specified motion from the bone
    #
    def removeMotionFromBone( self, bone, motion, animation ):
        
        boneMotionOp = motion_operator.BoneMotionOp( self.m_armatureObj, bone )
        prevMotion = boneMotionOp.sampleMotion( animation )
        newMotion = transform_utils.calcRelativeMotion( motion, prevMotion )
        boneMotionOp.setMotion( animation, newMotion )

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------

    #
    # Prints the motion definition
    #
    def printMotion( self, motion, header ):

        print( header )
        frameIdx = 1
        for keyframe in motion:

            loc, rot, scale = keyframe[0:3]
            print( "Frame ", frameIdx, ". loc", loc, "; rot", rot, "; scale", scale )
            frameIdx += 1

    #
    # A utility method that removes fcurves pertaining to object's motion from the specified animation.
    #
    def deleteObjectMotionFCurves( self, animation ):

        # delete curves we're about to replace
        print( "Removing object motion fcurves:" )

        curvesToRemove = []
        for fc in animation.fcurves:
            if fc.data_path == "location" or fc.data_path == "rotation_euler" or fc.data_path == "rotation_quaternion":
                curvesToRemove.append( fc )
        for curve in curvesToRemove:
            print( "\tRemoving curve: ", curve.data_path )
            animation.fcurves.remove( curve )

    #
    # A utility method that removes fcurves pertaining to the specified bone's motion from the specified animation.
    #
    def deleteBoneMotionFCurves( self, animation, bone ):

        # delete curves we're about to replace
        print( 'Removing bone "%s" motion fcurves:' % bone.name )

        locDataPathName =   'pose.bones["%s"].location' % bone.name
        eulerRotDataPathName = 'pose.bones["%s"].rotation_euler' % bone.name
        quatRotDataPathName = 'pose.bones["%s"].rotation_quaternion' % bone.name

        curvesToRemove = []
        for fc in animation.fcurves:
            if fc.data_path == locDataPathName or fc.data_path == eulerRotDataPathName or fc.data_path == quatRotDataPathName:
                curvesToRemove.append( fc )
        for curve in curvesToRemove:
            print( "\tRemoving curve: ", curve.data_path )
            animation.fcurves.remove( curve )

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
