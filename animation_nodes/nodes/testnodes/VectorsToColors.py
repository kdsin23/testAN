import bpy
import math
from ... base_types import AnimationNode,VectorizedSocket
from ... data_structures import Color, ColorList, VirtualColorList
from . c_utils import VectorsToColors

class CW_VectorsToColorsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_VectorsToColorsNode"
    bl_label = "Vectors To Colors"
    codeEffects = [VectorizedSocket.CodeEffect]

    useColorList: VectorizedSocket.newProperty()
    useVectorList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Vector", "vector", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Vectors", "vectors", dict(defaultDrawType = "PROPERTY_ONLY"))))
        self.newOutput(VectorizedSocket("Color", "useColorList",
            ("Color", "color"), ("Colors", "colors")))


    def getExecutionFunctionName(self):
        if self.useVectorList:
            return "executeVectors"
        else:
            return "executeVector"

    def executeVector(self,vector):

        return Color(([getpointnumber(vector[0]),getpointnumber(vector[1]),getpointnumber(vector[2]),1.0]))

    def executeVectors(self,vectors):
    
        return VectorsToColors(vectors)


a = 0.0
def getpointnumber(a):

    t = math.fabs(a)-math.floor(math.fabs(a))
    
    return round(t,2)