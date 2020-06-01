import bpy
import numpy as np
from bpy.props import *
from mathutils import Matrix
from ... algorithms.rotations import directionsToMatrices
from .. matrix.c_utils import extractMatrixTranslations
from ... base_types import AnimationNode, VectorizedSocket
from .. number . c_utils import range_DoubleList_StartStop
from ... events import executionCodeChanged, propertyChanged
from .. spline . spline_evaluation_base import SplineEvaluationBase
from..bluefox_nodes.c_utils import matrix_lerp, vector_lerp, inheritanceCurveVector, inheritanceCurveMatrix
from ... data_structures import DoubleList, Matrix4x4List, Vector3DList, VirtualMatrix4x4List, VirtualVector3DList, FloatList

inheritancemodeItems = [
    ("VECTORS", "Vectors", "Vector list in", "", 0),
    ("MATRICES", "Matrices", "Matrix list in", "", 1)
]

selectModeItems = [
    ("LINEAR", "Linear", "Linear interpolation", "", 0),
    ("SPLINE", "Spline", "Along Curve", "", 1)
]

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

class Inheritanceffector(bpy.types.Node, AnimationNode, SplineEvaluationBase):
    bl_idname = "an_Inheritanceffector"
    bl_label = "Inheritance Effector"
    bl_width_default = 140
    errorHandlingType = "EXCEPTION"

    useV1List: VectorizedSocket.newProperty()
    useV2List: VectorizedSocket.newProperty()
    useM1List: VectorizedSocket.newProperty()
    useM2List: VectorizedSocket.newProperty()

    align: BoolProperty(name = "Align", default = False,
        description = "Align to Spline",
        update = AnimationNode.refresh) 

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    mode : EnumProperty(name = "Type", default = "VECTORS",
        items = inheritancemodeItems, update = AnimationNode.refresh)

    selectMode : EnumProperty(name = "Mode", default = "LINEAR",
        items = selectModeItems, update = AnimationNode.refresh)    

    def create(self):
        if self.mode == "VECTORS":
            self.newInput(VectorizedSocket("Vector", "useV1List",
            ("Vector A", "va"), ("Vectors A", "v1")))
            self.newInput(VectorizedSocket("Vector", "useV2List",
            ("Vector B", "vb"), ("Vectors B", "v2")))
            self.newOutput(VectorizedSocket("Vector", ["useV1List", "useV2List"],
            ("Vector out", "vec_out"), ("Vectors out", "vecs_out")))
            self.newOutput(VectorizedSocket("Float", ["useV1List", "useV2List"],
            ("Value", "value"), ("Values", "values")))
                
        elif self.mode == "MATRICES":
            self.newInput(VectorizedSocket("Matrix", "useM1List",
            ("Matrix A", "ma"), ("Matrices A", "m1")))
            self.newInput(VectorizedSocket("Matrix", "useM2List",
            ("Matrix B", "mb"), ("Matrices B", "m2")))
            self.newOutput(VectorizedSocket("Matrix", ["useM1List", "useM2List"],
            ("Matrix out", "mat_out"), ("Matrices out", "mats_out")))
            self.newOutput(VectorizedSocket("Float", ["useM1List", "useM2List"],
            ("Value", "value"), ("Values", "values")))

        if self.selectMode == "SPLINE":
            self.newInput("Spline", "Path", "path", defaultDrawType = "PROPERTY_ONLY")
            self.newInput("Integer", "Samples", "samples", value = 10)
            self.newInput("Float", "Randomness", "randomness", value = 0.5)    

        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "step gap", "step", hide = True)
    
    def draw(self, layout):
        layout.prop(self, "mode", text = "")
        layout.prop(self, "selectMode")
        if self.selectMode == "SPLINE" and self.mode == "MATRICES":
            layout.prop(self, "align")
            if self.align: 
                layout.prop(self, "trackAxis", expand = True)
                layout.prop(self, "guideAxis", expand = True)
                if self.trackAxis[-1:] == self.guideAxis[-1:]:
                    layout.label(text = "Must be different", icon = "ERROR")

    def getExecutionFunctionName(self):
        if self.mode == "VECTORS":
            if self.selectMode == "LINEAR":
                return "VectorLerpFunction"
            else:
                return "vectorCurveInheritance"        
        else:
            if self.selectMode == "LINEAR":
                return "MatrixLerpFunction"
            else:
                return "matrixCurveInheritance"              
    
    def MatrixLerpFunction(self, m1, m2, falloff, step ):
        if not self.useM1List: m1 = Matrix4x4List.fromValues([m1])
        if not self.useM2List: m2 = Matrix4x4List.fromValues([m2])
        if len(m1) == 0 or len(m2) == 0:
            return Matrix4x4List(), DoubleList()    
        if len(m1) != len(m2):    
            m1, m2 = self.matchLength(m1, m2, 1)
        falloffEvaluator = self.getFalloffEvaluator(falloff)    
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step))
        result = matrix_lerp(m1,m2,influences)
        if  self.useM1List == 0 and self.useM2List == 0:
            return result[0], influences[0] 
        else:
            return result, influences       

    def VectorLerpFunction( self, v1, v2, falloff, step ):
        if not self.useV1List: v1 = Vector3DList.fromValue(v1)
        if not self.useV2List: v2 = Vector3DList.fromValue(v2)
        if len(v1) == 0 or len(v2) == 0:
            return Vector3DList(), DoubleList()
        if len(v1) != len(v2):    
            v1, v2 = self.matchLength(v1, v2, 0)         
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step))
        result = vector_lerp(v1, v2, influences)
        if self.useV1List == 0 and self.useV2List == 0:
            return result[0], influences[0]
        else:
            return result, influences 

    def vectorCurveInheritance(self, v1, v2, path, samples, randomness, falloff, step):
        if not self.useV1List: v1 = Vector3DList.fromValue(v1)
        if not self.useV2List: v2 = Vector3DList.fromValue(v2)
        if len(v1) == 0 or len(v2) == 0 or len(path.points) == 0:
            return Vector3DList(), DoubleList()
        if len(v1) != len(v2):    
            v1, v2 = self.matchLength(v1, v2, 0)    
        pathPoints = self.evalSpline(path, samples, 0)      
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step))
        result = inheritanceCurveVector(v1, v2, pathPoints, randomness, influences)
        if self.useV1List == 0 and self.useV2List == 0:
            return result[0], influences[0]
        else:
            return result, influences  

    def matrixCurveInheritance(self, m1, m2, path, samples, randomness, falloff, step):
        if not self.useM1List: m1 = Matrix4x4List.fromValues([m1])
        if not self.useM2List: m2 = Matrix4x4List.fromValues([m2])
        if len(m1) == 0 or len(m2) == 0 or len(path.points) == 0:
            return Matrix4x4List(), DoubleList()
        if len(m1) != len(m2):    
            m1, m2 = self.matchLength(m1, m2, 1)    
        pathPoints, pathEulers = self.evalSpline(path, samples, 1)      
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step))
        result = inheritanceCurveMatrix(m1, m2, pathPoints, pathEulers, randomness, influences, self.align)
        if self.useM1List == 0 and self.useM2List == 0:
            return result[0], influences[0]
        else:
            return result, influences                  

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def snap_number( self, nums, step ):
        num=np.asarray(nums)
        step_result = np.round( num / step ) * step if step != 0 else num
        return FloatList.fromNumpyArray(step_result.astype('float32')) 

    def matchLength(self, a, b, isMatrix):
        lenA = len(a)
        lenB = len(b)
        lenmax = max(lenA, lenB)
        if lenA > lenB:
            if isMatrix:
                b = VirtualMatrix4x4List.create(b, Matrix.Identity(4)).materialize(lenmax)
            else:
                b = VirtualVector3DList.create(b,(0,0,0)).materialize(lenmax)      
        if lenA < lenB:
            if isMatrix:    
                a = VirtualMatrix4x4List.create(a, Matrix.Identity(4)).materialize(lenmax)
            else:
                a = VirtualVector3DList.create(a,(0,0,0)).materialize(lenmax)           
        return a, b       

    def evalSpline(self, spline, samples, withRotation):
        spline.ensureUniformConverter(self.resolution)
        spline.ensureNormals()
        evalRange = range_DoubleList_StartStop(samples, 0, 1)
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
