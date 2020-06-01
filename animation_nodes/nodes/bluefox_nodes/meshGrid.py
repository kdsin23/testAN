import bpy
import numpy as np
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode
from ... data_structures import Vector3DList

class MeshGridNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_MeshGrid"
    bl_label = "Mesh Grid"

    def create(self):
        self.newInput("Vector List", "Bounding Box","boundingBox")
        self.newInput("Integer", "Samples","samples", minValue = 0)
        
        self.newOutput("Generic", "Grid", "grid")
        self.newOutput("Generic", "Grid.X", "gridX", hide = True)
        self.newOutput("Generic", "Grid.Y", "gridY", hide = True)
        self.newOutput("Generic", "Grid.Z", "gridZ", hide = True)
        self.newOutput("Generic", "MC Data", "mcData")
    
    def execute(self, boundingBox, samples):
        if len(boundingBox) == 0:
            return None, None, None, None, None
        else:    
            b1, b2 = self.get_bounds(boundingBox)
            b1n, b2n = np.array(b1), np.array(b2) 
            x_range = np.linspace(b1[0], b2[0], num=samples)
            y_range = np.linspace(b1[1], b2[1], num=samples)
            z_range = np.linspace(b1[2], b2[2], num=samples)
            grid = np.vstack([np.meshgrid(x_range, y_range, z_range, indexing='ij')]).reshape(3,-1).T 
            return grid, grid[:,0], grid[:,1], grid[:,2], [samples, b1n, b2n]

    def get_bounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()      

