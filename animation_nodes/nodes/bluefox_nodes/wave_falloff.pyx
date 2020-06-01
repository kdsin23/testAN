import bpy
cimport cython
from bpy.props import *
from ... math cimport abs as absNumber
from ... base_types import AnimationNode
from ... data_structures cimport BaseFalloff
from ... math cimport Vector3, setVector3, distanceVec3, sin

modeItems = [
    ("SINE", "Sine", "Sine wave", "", 0),
    ("SQUARE", "Square", "Square wave", "", 1),
    ("TRIANGULAR", "Triangular", "Triangular wave", "", 2),
    ("SAW", "Saw", "saw wave", "", 3)
]

class WaveFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_wavefalloff"
    bl_label = "Wave falloff"

    __annotations__ = {}
    __annotations__["mode"] = EnumProperty(name = "Type ", default = "SINE",
        items = modeItems, update = AnimationNode.refresh)

    __annotations__["EnableRipple"] = BoolProperty(update = AnimationNode.refresh)    

    def create(self):
        if self.EnableRipple:
            self.newInput("Vector", "Orgin", "orgin")
        self.newInput("Float", "Amplitude", "amplitude", value = 1.0)
        self.newInput("Float", "Frequency", "frequency", value = 5.0)
        self.newInput("Float", "Offset", "offset")
        self.newInput("Boolean", "Clamp", "clamp", value = False)
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "EnableRipple", text = "", icon = "PROP_ON")
        row2 = row.row(align = True)
        row2.prop(self, "mode", text = "")

    def getExecutionFunctionName(self):
        if self.EnableRipple: 
            return "executeRipple"
        else:
            return "executeBasic"

    def executeBasic(self, amplitude, frequency, offset, clamp):
        return WaveFalloff((0,0,0), frequency, amplitude, offset, clamp, self.mode, self.EnableRipple)

    def executeRipple(self, orgin, amplitude, frequency, offset, clamp):
        return WaveFalloff(orgin, frequency, amplitude, offset, clamp, self.mode, self.EnableRipple)    

cdef class WaveFalloff(BaseFalloff):
    cdef:
        Vector3 origin
        bint clamp, isRipple
        str mode
        float frequency, amplitude, offset

    def __cinit__(self, vector, float frequency, float amplitude, float offset, bint clamp, str mode, bint isRipple):
        self.isRipple = isRipple
        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.mode = mode
        self.clamp = clamp
        setVector3(&self.origin, vector)
        self.dataType = "LOCATION"
        
    cdef float evaluate(self, void *value, Py_ssize_t index):
        return wave(self, <Vector3*>value, index)    

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                            Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float value                                   
        for i in range(amount):
            value = i/amount
            if self.clamp:
                target[i] = max(min(wave(self, <Vector3*>values + i, value), 1), 0)
            else:
                target[i] = wave(self, <Vector3*>values + i, value)

@cython.cdivision(True)
cdef inline float wave(WaveFalloff self, Vector3 *v, float i):
    cdef float result, temp, offset, frequency
    offset = self.offset * -1
    frequency = self.frequency
    if self.isRipple:
        i = distanceVec3(&self.origin, v)
    else:    
        frequency *= 10
    if self.mode == "SINE":
        result = sin(i * frequency + offset)
    elif self.mode == "SQUARE":
        temp = sin(i * frequency + offset)
        if temp < 0:
            result = -1 
        else:
            result = 1   
    elif self.mode == "TRIANGULAR": #needs improvement
        offset = absNumber(offset)
        temp = (i * frequency + offset) / 6 * 2
        result = 2 * (((i * frequency + offset) / 6 * 2) % 1) - 1
        if not temp % 2 > 1:
            result *= -1
    elif self.mode == "SAW": #needs improvement
        result = 1 - ((i * frequency + offset) / 6 * 2) % 2  
    return result * self.amplitude
