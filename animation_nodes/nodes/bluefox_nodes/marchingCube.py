import bpy
import numpy as np
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode
from . utils.mcalgorithm import isosurface_np
from ... data_structures.meshes.validate import createValidEdgesList
from ... data_structures import Vector3DList, PolygonIndicesList, EdgeIndicesList, Mesh

class MarchingCubes(bpy.types.Node, AnimationNode):
    bl_idname = "an_MarchingCubes"
    bl_label = "Marching Cubes"
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Generic", "MC Data","mcData")
        self.newInput("Generic", "Field","field")
        self.newInput("Float", "ISO Value","isoValue", value = 0.3)

        self.newOutput("an_MeshSocket", "Mesh", "meshData")
    
    def execute(self, mcData, field, isoValue):
        try:
            if mcData is None or field is None:
                return Mesh()
            else: 
                samples = mcData[0]
                b1n, b2n = mcData[1], mcData[2]
                if not type(field) is np.ndarray:
                    func_values = field.asNumpyArray()
                else:
                    func_values = field
                func_values = func_values.reshape((samples, samples, samples))
                vertices, faces = isosurface_np(func_values, isoValue)
                vertexLocations = Vector3DList.fromValues((vertices / samples) * (b2n - b1n) + b1n)
                polygonIndices = PolygonIndicesList.fromValues(faces)
                edgeIndices = createValidEdgesList(polygons = polygonIndices)
                return Mesh(vertexLocations, edgeIndices, polygonIndices, skipValidation = True)
        except (TypeError, ValueError):
            self.raiseErrorMessage("Wrong value or type")
            return Mesh()       
                   