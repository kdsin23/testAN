import bpy
import numpy as np
from ... base_types import AnimationNode
from bpy.props import *
from ... events import executionCodeChanged
from ... data_structures import DoubleList
from .c_utils import vector_lerp

class CW_MixVectorsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_MixVectors_2Node"
    bl_label = "Mix Vectors 2"

    clampFactor: BoolProperty(name = "Clamp Factors",
        description = "Clamp factors between 0 and 1",
        default = False, update = executionCodeChanged)


    def create(self):
        self.newInput("Float List", "Factors", "factors")
        self.newInput("Vector List", "A", "a")
        self.newInput("Vector List", "B", "b")
        self.newOutput("Vector List", "Results", "results")

    def draw(self, layout):
        layout.prop(self, "clampFactor")

    def execute(self, factors, a, b):
        
        if len(a) != len(b):
            return None

        if self.clampFactor:
            try:
                facs = np.clip(DoubleList.asNumpyArray(factors), 0, 1)

                return vector_lerp(a,b,DoubleList.fromNumpyArray(facs))
            except:
                return

        else:
            return vector_lerp(a,b,DoubleList.fromValues(factors))


#python code below is very slow,so use cython code vector_lerp is a cython function
"""V_results = []

        for f,v1,v2 in zip(factors, a, b):
            v = f*(v2-v1) + v1
            V_results.append(v)"""
