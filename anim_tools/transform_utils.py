import mathutils
import math


#
# Calculates a relative movement of 'childMotion' with respect to 'rootMotion'.
# Each motion is an array of transforms presented in form of tuples
# (loc:Vector, rot:Quaternion)
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
        invRootRot = rootRot.conjugated()
        
        # translation
        translation = childLoc - rootLoc
        translation.rotate( invRootRot )

        # rotation
        rotation = childRot * invRootRot

        resultingMotion.append( ( translation, rotation ) )


    return resultingMotion


#
# Prints the motion definition
#
# Each motion is an array of transforms presented in form of tuples
# (loc:Vector, rot:Quaternion)
#
def printMotion( motion, header ):

    print( header )

    frameIdx = 1
    for keyframe in motion:

        loc, rot = keyframe[0:2]
        print( "Frame ", frameIdx, ". loc", loc, "; rot", rot )
        frameIdx += 1
