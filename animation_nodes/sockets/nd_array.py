import bpy
import numpy as np
from .. base_types import AnimationNodeSocket, PythonListSocket

class NDArraySocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_NDArraySocket"
    bl_label = "NDArray Socket"
    dataType = "NDArray"
    drawColor = (0.2, 0.7, 0.7, 1)
    storable = False
    comparable = True

    @classmethod
    def getDefaultValue(cls):
        return np.array(0)

    @classmethod
    def correctValue(cls, value):
        if isinstance(value, np.ndarray) or value is None:
            return value, 0
        return cls.getDefaultValue(), 2

class NDArrayListSocket(bpy.types.NodeSocket, PythonListSocket):
    bl_idname = "an_NDArrayListSocket"
    bl_label = "NDArray List Socket"
    dataType = "NDArray List"
    baseType = NDArraySocket
    drawColor = (0.2, 0.7, 0.7, 0.5)
    storable = False
    comparable = False

    @classmethod
    def getCopyExpression(cls):
        return "value[:]"
