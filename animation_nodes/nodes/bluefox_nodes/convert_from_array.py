import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode
from ...data_structures import ColorList, DoubleList, Matrix4x4List, QuaternionList, Vector3DList

arraymodeItems = [
    ("FLOATS", "Float List from Array", "", "", 0),
    ("VECTORS", "Vector List from Array", "", "", 1),
    ("COLORS", "Colors List from Array", "", "", 2),
    ("QUATERNIONS", "Quaternion List from Array", "", "", 3),
    ("MATRICES", "Matrix List from Array", "", "", 4)
]

class ConvertFromArrayNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_ConvertFromArray"
    bl_label = "Convert From Array"
    bl_width_default = 150
    dynamicLabelType = "ALWAYS"
    errorHandlingType = "EXCEPTION"

    onlySearchTags = True
    searchTags = [(name, {"mode" : repr(type)}) for type, name, _,_,_ in arraymodeItems]

    mode : EnumProperty(name = "Type", default = "FLOATS",
        items = arraymodeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("NDArray", "Array", "array")

        if self.mode == "FLOATS":
            self.newOutput("Float List", "Float list", "floatList")
        if self.mode == "VECTORS":
            self.newOutput("Vector List", "Vector list", "vectorList")
        if self.mode == "COLORS":
            self.newOutput("Color List", "Color list", "colorList")
        if self.mode == "QUATERNIONS":
            self.newOutput("Quaternion List", "Quaternion list", "quaternionList")
        if self.mode == "MATRICES":
            self.newOutput("Matrix List", "Matrix list", "matrixList")
    
        self.inputs[0].defaultDrawType = "PREFER_PROPERTY"  

    def draw(self, layout):
        layout.prop(self, "mode", text = "")

    def drawLabel(self):
        for item in arraymodeItems:
            if self.mode == item[0]: return item[1]                            
    
    def execute(self, array):
        if array.ndim == 0:
            return
        else:
            shape = array.shape    
            try:
                if self.mode == "FLOATS":
                    if len(shape) != 1: 
                        self.raiseErrorMessage("Expected Array of Shape (n,)")  
                    return DoubleList.fromNumpyArray(array.astype('double'))
                elif self.mode == "VECTORS":
                    if len(shape) != 2 or shape[-1] != 3: 
                        self.raiseErrorMessage("Expected Array of Shape (n,3)")     
                    return Vector3DList.fromNumpyArray(array.astype('float32').flatten())
                elif self.mode == "COLORS":
                    if len(shape) != 2 or shape[-1] != 4: 
                        self.raiseErrorMessage("Expected Array of Shape (n,4)")   
                    return ColorList.fromNumpyArray(array.astype('float32').flatten())
                elif self.mode == "QUATERNIONS":
                    if len(shape) != 2 or shape[-1] != 4: 
                        self.raiseErrorMessage("Expected Array of Shape (n,4)")  
                    return QuaternionList.fromNumpyArray(array.astype('float32').flatten())
                elif self.mode == "MATRICES":
                    if len(shape) != 3 or shape[-1] != 4 or shape[-2] != 4: 
                        self.raiseErrorMessage("Expected Array of Shape (n,4,4)")  
                    return Matrix4x4List.fromNumpyArray(array.astype('float32').flatten())
            except IndexError:
                self.raiseErrorMessage("Index Out of Bound")
                return
