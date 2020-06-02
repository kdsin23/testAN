import bpy
import numpy as np
from bpy.props import *
from ... base_types import AnimationNode
from mathutils import Vector,Euler
from .. bluefox_nodes.c_utils import matrix_lerp
from .. spline . spline_evaluation_base import SplineEvaluationBase
from ... data_structures import Vector3DList,VirtualVector3DList,VirtualEulerList
#from .. number . c_utils import mapRange_DoubleList
from .. number . c_utils import range_DoubleList_StartStop
from .. matrix.c_utils import *
from ... events import propertyChanged, executionCodeChanged
from ... data_structures import Matrix4x4List, DoubleList, Vector3DList, EulerList
from . c_utils import SplineEffector

class SplineEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SplineEffector"
    bl_label = "Spline Effector"
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
        self.newInput("Spline", "Spline", "spline", defaultDrawType = "PROPERTY_ONLY")
        self.newInput("Float", "Start", "start", value = 0.0).setRange(0.0, 1.0)
        self.newInput("Float", "End", "end", value = 1.0).setRange(0.0, 1.0)
        self.newInput("Integer", "Samples", "samples", value = 10)
        self.newInput("Falloff", "Falloff", "falloff",value = 1.0) 
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
              
    def execute(self, matrices, location, rotation, scale, spline, start, end, samples, falloff):

        if len(matrices) == 0:
            return Matrix4x4List()   
        else:
            falloffEvaluator = self.getFalloffEvaluator(falloff)
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(matrices)))
            if not self.useLocation:
                location = [0,0,0]
            if not self.useRotation:
                rotation = [0,0,0]
            if not self.useScale:
                scale = [0,0,0]

            v = Vector3DList.fromValue(location)
            e = EulerList.fromValue(rotation)
            s = Vector3DList.fromValue(scale)

            pathPoints = self.evalSpline(spline, samples, start, end, 0)


        return SplineEffector(matrices, v, e, s, pathPoints, influences)

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def evalSpline(self, spline, samples, start, end, withRotation):
        spline.ensureUniformConverter(self.resolution)
        spline.ensureNormals()
        evalRange = range_DoubleList_StartStop(samples, start, end)
        parameters = FloatList.fromValues(evalRange)
        parameters = spline.toUniformParameters(parameters)
        locations = spline.samplePoints(parameters, False, 'RESOLUTION')
        if withRotation:
            tangents = spline.sampleTangents(parameters, False, 'RESOLUTION')
            normals = spline.sampleNormals(parameters, False, 'RESOLUTION')
            rotationMatrices = directionsToMatrices(tangents, normals, self.trackAxis, self.guideAxis)
            return locations, rotationMatrices.toEulers(isNormalized = True)
        else:
            return locations
