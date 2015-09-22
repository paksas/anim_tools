import bpy
import mathutils
import math


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

        objectName, locDataPathName, quatRotDataPathName = self.getMotionPaths()
        print( "Keyframing '%s'." % objectName )
       
        framesCount = len( motion )
        # location
        for axis_i in range(3):
            
            curve = animation.fcurves.new(data_path=locDataPathName, index=axis_i, action_group='Location' )
            keyframePoints = curve.keyframe_points
            keyframePoints.add( framesCount )

            for frameIdx in range( framesCount ):
                loc, rot = motion[frameIdx]
                keyframePoints[frameIdx].co = (frameIdx + 1.0, loc[axis_i])
                keyframePoints[frameIdx].interpolation = 'LINEAR'

        # rotation
        if includeRotation:
            for axis_i in range(4):

                curve = animation.fcurves.new(data_path=quatRotDataPathName, index=axis_i, action_group='Rotation')
                keyframePoints = curve.keyframe_points
                keyframePoints.add( framesCount )

                for frameIdx in range( framesCount ):
                    loc, rot = motion[frameIdx]
                    keyframePoints[frameIdx].co = (frameIdx + 1.0, rot[axis_i])
                    keyframePoints[frameIdx].interpolation = 'LINEAR'

    # 
    # Protected template method called by 'setMotion'
    #
    def getMotionPaths( self ):
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

    def getMotionPaths( self ):
        
        return ( self.m_object.name, "location", "rotation_quaternion" )


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

            motionBoneRefMtx = self.m_bone.bone.matrix_local
            motionBoneMtx = self.m_bone.matrix
            motionBoneLocMtx = motionBoneRefMtx.inverted() * motionBoneMtx
            loc, rot, scale = motionBoneLocMtx.decompose()

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
    
    def getMotionPaths( self ):
        
        return ( 
            '%s.%s' % ( self.m_armature.name, self.m_bone.name ),
            'pose.bones["%s"].location' % self.m_bone.name,
            'pose.bones["%s"].rotation_quaternion' % self.m_bone.name )


