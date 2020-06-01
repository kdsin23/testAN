import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode

arraymodeItems = [
    ("FLOATS", "Float List to Array", "", "", 0),
    ("VECTORS", "Vector List to Array", "", "", 1),
    ("COLORS", "Colors List to Array", "", "", 2),
    ("QUATERNIONS", "Quaternion List to Array", "", "", 3),
    ("MATRICES", "Matrix List to Array", "", "", 4)
]

class ConvertToArrayNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_ConvertToArray"
    bl_label = "Convert To Array"
    bl_width_default = 150
    dynamicLabelType = "ALWAYS"

    onlySearchTags = True
    searchTags = [(name, {"mode" : repr(type)}) for type, name, _,_,_ in arraymodeItems]

    mode : EnumProperty(name = "Type", default = "FLOATS",
        items = arraymodeItems, update = AnimationNode.refresh)

    def create(self):
        if self.mode == "FLOATS":
            self.newInput("Float List", "Float list", "floatList")
        if self.mode == "VECTORS":
            self.newInput("Vector List", "Vector list", "vectorList")
        if self.mode == "COLORS":
            self.newInput("Color List", "Color list", "colorList")
        if self.mode == "QUATERNIONS":
            self.newInput("Quaternion List", "Quaternion list", "quaternionList")
        if self.mode == "MATRICES":
            self.newInput("Matrix List", "Matrix list", "matrixList")
    
        self.newOutput("NDArray", "Array", "array")
        self.inputs[0].defaultDrawType = "PREFER_PROPERTY"  

    def draw(self, layout):
        layout.prop(self, "mode", text = "")

    def drawLabel(self):
        for item in arraymodeItems:
            if self.mode == item[0]: return item[1]                            
    
    def getExecutionCode(self, required):
        if self.mode == "FLOATS":    yield "array = floatList.asNumpyArray()"
        elif self.mode == "VECTORS":  yield "array = vectorList.asNumpyArray().reshape(len(vectorList), 3)"
        elif self.mode == "COLORS":  yield "array = colorList.asNumpyArray().reshape(len(colorList), 4)"
        elif self.mode == "QUATERNIONS":  yield "array = quaternionList.asNumpyArray().reshape(len(quaternionList), 4)"
        elif self.mode == "MATRICES":  yield "array = matrixList.asNumpyArray().reshape(len(matrixList), 4, 4)"
