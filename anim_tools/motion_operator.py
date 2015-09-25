import bpy
import mathutils
import math


# ------------------------------------------------
#
# Blender bugs and how I work around them:
# ------------------------------------------------
#
# >Bug 1 - The same quaternion rotates bones and objects in a different way.
#          With objects, it works as expected, but with the bones, the Y and Z component
#          seem to be swapped, which makes the bone rotate about the wrong axis.
#          My solution is to swap the rotations I sample from and set on the bones
#          in order to unify them with "Object rotation quaterions"
#
# ------------------------------------------------

##################################################
# Motion operator interface
##################################################
class MotionOp:
    
    #
    # Samples the motion of the underlying object
    #
    def sampleMotion( self, animation ):
        raise NotImplementedError("Subclass must implement abstract method")

    #
    # Deletes the existing motion of the underlying object from the specified animation
    # 
    def deleteMotion( self, animation ):
        raise NotImplementedError("Subclass must implement abstract method")

    #
    # Sets the motion on the underlying object
    #
    def setMotion( self, animation, motion, includeRotation ):
        
        # delete curves we're about to replace
        self.deleteMotion( animation )

        self.prvSetMotion( animation, motion, includeRotation )

    # 
    # Protected template method called by 'setMotion'
    #
    def prvSetMotion( self, animation, motion, includeRotation ):
        raise NotImplementedError("Subclass must implement abstract method")

##################################################
# Motion operator for objects
##################################################
class ObjectMotionOp( MotionOp ):

    m_object = None

    #
    # Constructor
    #
    def __init__( self, object ):

        self.m_object = object
    
    # -------------------------------------------------------------------------
    # MotionOp implementation
    # -------------------------------------------------------------------------

    def sampleMotion( self, animation ):
        
        # store the original frame index to restore the scene to the previous state once we're done
        scene = bpy.context.scene
        originalFrameIdx = scene.frame_current

        framesCount = int( animation.frame_range[1] )
        print( "Extracting motion of '%s' from '%s': frames [1..%d] " % ( self.m_armature.name, animation.name, framesCount ) )

        # sample animation frames
        motionTransforms = []
        for frameIdx in range( framesCount ):

            scene.frame_set( frameIdx )

            loc, rot, scale = self.m_object.matrix_local.decompose()
            motionTransforms.append( (loc, rot) )

        # restore the scene to its previous state
        scene.frame_set( originalFrameIdx )

        return motionTransforms

    def deleteMotion( self, animation ):

        print( "Removing '%s' motion fcurves:" % self.m_object.name )

        curvesToRemove = []
        for fc in animation.fcurves:
            if fc.data_path == "location" or fc.data_path == "rotation_euler" or fc.data_path == "rotation_quaternion":
                curvesToRemove.append( fc )
        for curve in curvesToRemove:
            print( "\tcurve: ", curve.data_path )
            animation.fcurves.remove( curve )

    def prvSetMotion( self, animation, motion, includeRotation ):

        print( "Keyframing '%s'." % self.m_object.name )
       
        framesCount = len( motion )
        # location
        for axis_i in range(3):
            
            curve = animation.fcurves.new(data_path="location", index=axis_i, action_group="Location" )
            keyframePoints = curve.keyframe_points
            keyframePoints.add( framesCount )

            for frameIdx in range( framesCount ):
                loc, rot = motion[frameIdx]
                keyframePoints[frameIdx].co = (frameIdx + 1.0, loc[axis_i])
                keyframePoints[frameIdx].interpolation = 'LINEAR'

        # rotation
        if includeRotation:
            for axis_i in range(3):

                curve = animation.fcurves.new(data_path="rotation_euler", index=axis_i, action_group="Rotation" )
                keyframePoints = curve.keyframe_points
                keyframePoints.add( framesCount )

                for frameIdx in range( framesCount ):
                    loc, rot = motion[frameIdx]
                    rotEuler = rot.to_euler( 'XYZ' )
                    keyframePoints[frameIdx].co = (frameIdx + 1.0, rotEuler[axis_i])
                    keyframePoints[frameIdx].interpolation = 'LINEAR'

##################################################
# Motion operator for bones
##################################################
class BoneMotionOp( MotionOp ):

    m_armature = None
    m_bone = None

    #
    # Constructor
    #
    def __init__( self, armature, bone ):

        self.m_armature = armature
        self.m_bone = bone

    #
    # Factory method
    #
    @staticmethod
    def createInstance( self, armatureObjName, boneName ):

        armature = bpy.context.scene.objects[armatureObjName]
        if self.armature is None:
            op.report( {'ERROR'}, "BoneMotionOp: armature '%s' doesn't exist" % armatureObjName )
            return None

        bone = armature.pose.bones[boneName]
        if bone is None:
            op.report( {'ERROR'}, "BoneMotionOp: armature %s doesn't contain a bone '%s'" % ( armatureObjName, boneName ) )
            return None

        return BoneMotionOp( armature, bone )

    # -------------------------------------------------------------------------
    # MotionOp implementation
    # -------------------------------------------------------------------------

    def sampleMotion( self, animation ):

        # store the original frame index to restore the scene to the previous state once we're done
        scene = bpy.context.scene
        originalFrameIdx = scene.frame_current

        framesCount = int( animation.frame_range[1] )
        print( "Extracting motion of '%s.%s' from '%s': frames [1..%d] " % ( self.m_armature.name, self.m_bone.name, animation.name, framesCount ) )

        # sample animation frames
        motionTransforms = []
        for frameIdx in range( framesCount ):

            scene.frame_set( frameIdx )

            boneRefPoseMtx = self.m_bone.bone.matrix_local
            bonePoseMtx = self.m_bone.matrix
            boneLocMtx = bonePoseMtx * boneRefPoseMtx.inverted()

            loc, rot, scale = boneLocMtx.decompose()

            motionTransforms.append( ( loc, rot ) )

        # restore the scene to its previous state
        scene.frame_set( originalFrameIdx )

        return motionTransforms

    def deleteMotion( self, animation ):

        print( "Removing '%s.%s' motion fcurves:" % ( self.m_armature.name, self.m_bone.name ) )

        locDataPathName =   'pose.bones["%s"].location' % self.m_bone.name
        eulerRotDataPathName = 'pose.bones["%s"].rotation_euler' % self.m_bone.name
        quatRotDataPathName = 'pose.bones["%s"].rotation_quaternion' % self.m_bone.name

        curvesToRemove = []
        for fc in animation.fcurves:
            if fc.data_path == locDataPathName or fc.data_path == eulerRotDataPathName or fc.data_path == quatRotDataPathName:
                curvesToRemove.append( fc )
        for curve in curvesToRemove:
            print( "\tRemoving curve: ", curve.data_path )
            animation.fcurves.remove( curve )
    

    def prvSetMotion( self, animation, motion, includeRotation ):

        print( "Keyframing '%s.%s'." % ( self.m_armature.name, self.m_bone.name ) )
       
        locDataPath = 'pose.bones["%s"].location' % self.m_bone.name
        rotDataPath = 'pose.bones["%s"].rotation_quaternion' % self.m_bone.name

        # TODO: Care to explain why?
        refPoseRot = self.m_bone.bone.matrix_local.inverted().to_quaternion()
        boneTransforms = []
        for transform in motion:

            rotatedLoc = transform[0].copy()
            rot = transform[1].copy()
            rotatedLoc.rotate( refPoseRot )
            boneTransforms.append( (rotatedLoc, rot) )


        framesCount = len( motion )
        # location
        for axis_i in range(3):
            
            curve = animation.fcurves.new(data_path=locDataPath, index=axis_i, action_group=self.m_bone.name )
            keyframePoints = curve.keyframe_points
            keyframePoints.add( framesCount )

            for frameIdx in range( framesCount ):
                loc = boneTransforms[frameIdx][0]
                keyframePoints[frameIdx].co = (frameIdx + 1.0, loc[axis_i])
                keyframePoints[frameIdx].interpolation = 'LINEAR'

        # rotation
        if includeRotation:
            for axis_i in range(4):

                curve = animation.fcurves.new(data_path=rotDataPath, index=axis_i, action_group=self.m_bone.name )
                keyframePoints = curve.keyframe_points
                keyframePoints.add( framesCount )

                for frameIdx in range( framesCount ):
                    rot = boneTransforms[frameIdx][1]

                    keyframePoints[frameIdx].co = (frameIdx + 1.0, rot[axis_i])
                    keyframePoints[frameIdx].interpolation = 'LINEAR'
