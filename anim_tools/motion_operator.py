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
        pass

    #
    # Sets the motion on the underlying object
    #
    def setMotion( self, animation, motion ):
        pass

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
        pass

    def setMotion( self, animation, motion ):
        pass

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
        pass

    def setMotion( self, animation, motion ):
        pass

