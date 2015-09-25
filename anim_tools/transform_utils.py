import mathutils
import math

# 
# General remarks regarding all functions presented here:
#
# Each motion is an array of transforms presented in form of tuples
# (loc:Vector, rot:Quaternion)
#

# =============================================================================

#
# Calculates a relative movement of 'childMotion' with respect to 'rootMotion'.
#
# The method works only if both motions have the exact same number of keyframes.
#
#
# @return  new motion if the operation was successful, or an empty motion otherwise
#
def calcRelativeMotion( rootMotion, childMotion ):

    resultingMotion = []

    framesCount = len( rootMotion )
    if framesCount != len( childMotion ):
        op.report( {'ERROR'}, "transform_utils.calcRelativeMotion: The method works only with motions with the same number of keyframes" )
        return resultingMotion

    for frameIdx in range( framesCount ):

        rootLoc, rootRot = rootMotion[frameIdx]
        childLoc, childRot = childMotion[frameIdx]
        invRootRot = rootRot.conjugated().normalized()
        
        # translation
        translation = childLoc - rootLoc
        translation.rotate( invRootRot )

        # rotation
        rotation = invRootRot * childRot

        resultingMotion.append( ( translation, rotation ) )


    return resultingMotion

#
# Calculates the rotation around the Z axis ( the yaw ) of the specified transform
#
def calcYaw( transform ):
    worldFwdDir = mathutils.Vector( ( 1.0, 0.0, 0.0 ) )

    rotatedVec = worldFwdDir.copy()
    rotatedVec.rotate( transform[1] )
    rotatedVec.z = 0.0
    rotatedVec.normalize()

    worldFwdDir2D = worldFwdDir.to_2d()
    rotatedVec2D = rotatedVec.to_2d()
    yawAngle = -worldFwdDir2D.angle_signed( rotatedVec2D, 0.0 )

    return yawAngle

#
# Prints the motion definition
#
def printMotion( motion, header ):

    print( header )

    frameIdx = 1
    for keyframe in motion:

        loc, rot = keyframe[0:2]
        print( "Frame ", frameIdx, ". loc", loc, "; rot", rot )
        frameIdx += 1
