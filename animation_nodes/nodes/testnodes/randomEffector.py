import bpy
import numpy as np
from bpy.props import *
from ... base_types import AnimationNode
from mathutils import Vector,Euler
from ... data_structures import Vector3DList,VirtualVector3DList,VirtualEulerList
from .. matrix.c_utils import *
from ... events import propertyChanged, executionCodeChanged
from ... data_structures import Matrix4x4List, DoubleList, Vector3DList, EulerList
from . c_utils import RandomEffector

class RandomEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_RandomEffector"
    bl_label = "Random Effector"
    bl_width_default = 150
    errorHandlingType = "EXCEPTION"

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useLocation: BoolProperty(update = checkedPropertiesChanged)
    useRotation: BoolProperty(update = checkedPropertiesChanged)
    useScale: BoolProperty(update = checkedPropertiesChanged)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput("Vector", "Location", "location")
        self.newInput("Euler", "Rotation", "rotation")
        self.newInput("Vector", "Scale", "scale")
        self.newInput("Float", "Seed", "seed", value = 123456)
        self.newInput("Float", "ScaleMin", "scalemin", value = 0.1, hide=True)
        self.newInput("Float", "ScaleMax", "scalemax", value = 1.0, hide=True)
        self.newInput("Float", "Factor", "factor", value = 1.0)
        self.newInput("Falloff", "Falloff", "falloff",value = 1.0)
        self.newInput("Interpolation", "Interpolation", "interpolation", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        #self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)
        #self.newOutput("Float List", "Falloff Strength", "falloffStrength", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "useLocation", index = 0, text = "Loc", toggle = True, icon = "EXPORT")
        subrow.prop(self, "useRotation", index = 1, text = "Rot", toggle = True, icon = "FILE_REFRESH") 
        subrow.prop(self, "useScale", index = 2, text = "Scale", toggle = True, icon = "FULLSCREEN_ENTER") 

    def updateSocketVisibility(self):
        self.inputs[1].hide = not self.useLocation
        self.inputs[2].hide = not self.useRotation
        self.inputs[3].hide = not self.useScale
              
    def execute(self, matrices, location, rotation, scale, seed, scalemin, scalemax, factor, falloff, interpolation):

        if len(matrices) == 0:
            return Matrix4x4List()
        
        else:

            count = len(matrices)

            falloffEvaluator = self.getFalloffEvaluator(falloff)
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(matrices)))

            intval = interpolation(max(min(f, 1.0), 0.0))
            iary = np.full((1,count),intval)
            iarys = DoubleList.fromNumpyArray(iary.flatten())
            
            if not self.useLocation:
                location = [0,0,0]
            if not self.useRotation:
                rotation = [0,0,0]
            if not self.useScale:
                scale = [0,0,0]         

            v = Vector3DList.fromValue(location)
            e = EulerList.fromValue(rotation)
            s = Vector3DList.fromValue(scale)

        return RandomEffector(matrices, v, e, s, newinfs, seed, scale, factor, scalemin, scalemax, influences, iarys)

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

        
