import bpy
from ... math cimport Vector3
from ... base_types import AnimationNode
from ... data_structures cimport BaseFalloff
from .. falloff.remap_falloff import RemapFalloff

class StepFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_StepFalloffNode"
    bl_label = "Step Falloff"

    def create(self):
        self.newInput("Float", "Strength", "strength",value = 1.0)
        self.newInput("Float", "Min", "minValue", value = 0)
        self.newInput("Float", "Max", "maxValue", value = 1.0)
        self.newOutput("Falloff", "Falloff", "falloff")

    def execute(self, strength, minValue, maxValue):
        return RemapFalloff(StepFalloff(strength), 0, 1, minValue, maxValue)


cdef class StepFalloff(BaseFalloff):
    cdef:
        float strength

    def __cinit__(self, float strength):
        self.strength = strength
        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return self.strength

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                            Py_ssize_t amount, float *target):

        cdef Py_ssize_t i                                 
        for i in range(amount):
            target[i] = ((i+1)/amount) * self.strength
