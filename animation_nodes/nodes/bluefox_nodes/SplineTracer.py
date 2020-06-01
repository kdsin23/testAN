import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Vector3DList, PolySpline, BezierSpline

tracerPointTypeItems = [
    ("POLY", "Poly Spline", "Append point to poly spline", "NONE", 0),
    ("BEZIER_POINT", "Bezier Spline", "Append point to bezier spline", "NONE", 1)]

class StoreSpline(object):
    def __init__(self, spline):
        self.polyspline = PolySpline()
        self.bezierspline = BezierSpline()

p = {}

class SplineTracerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_splinetracer"
    bl_label = "Spline Tracer"
    bl_width_default = 160

    tracerpointType: EnumProperty(name = "Spline Type", default = "POLY",
        items = tracerPointTypeItems, update = AnimationNode.refresh)

    usevectorlist: VectorizedSocket.newProperty()
 
    def create(self):
        self.newInput(VectorizedSocket("Vector", "usevectorlist",
            ("Point ", "point"), ("Points", "points")))   
        self.newInput("Integer", "Reset Frame", "resetframe", value = 1, hide = True)
        self.newInput("Integer", "Start Frame", "start", value = 1)
        self.newInput("Integer", "End Frame", "end", value = 250)
        self.newInput("Float", "Radius", "radius", value = 0.1, minValue = 0)
        self.newInput("Float", "Tilt", "tilt")
        if self.tracerpointType == "BEZIER_POINT":
            self.newInput("Float", "Smoothness", "smoothness", value = 0.33)
        self.newInput("Float", "Min Distance", "minDistance", value = 0.01, minValue = 0)     
        self.newInput("Boolean", "Append Condition", "appendCondition", value = 1, hide = True)
        self.newInput("Boolean", "Use Custom Identifier", "useCustomIdentifier", value = 0, hide = True)
        self.newInput("Text", "Custom Identifier", "customIdentifier", value = "abcd", hide = True)

        self.newOutput(VectorizedSocket("Spline", "usevectorlist",
            ("Spline", "spline"), ("Splines", "splines")))

    def draw(self, layout):
        layout.prop(self, "tracerpointType", text = "")

    def getExecutionFunctionName(self):
        if self.usevectorlist and self.tracerpointType == "BEZIER_POINT":
            return "execute_beziersplines"
        elif self.usevectorlist and self.tracerpointType != "BEZIER_POINT":
            return "execute_polysplines"    
        elif self.usevectorlist == False and self.tracerpointType == "BEZIER_POINT":
            return "execute_bezierspline"
        elif self.usevectorlist == False and self.tracerpointType != "BEZIER_POINT":
            return "execute_polyspline"    

    def execute_polysplines(self, points, resetframe, start, end, radius, tilt, minDistance, appendCondition, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        vecDistance = minDistance

        identifier = self.identifier + "poly"
        if useCustomIdentifier:
            identifier = customIdentifier + "poly"  
        if T == resetframe:
            p[identifier] = []
        p_object = p.get(identifier, [])

        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            return splinelist
           
        for i, point in enumerate(points):
            p_object.append(StoreSpline(i))
            if len(p_object[i].polyspline.points)!=0:
                vecDistance = (p_object[i].polyspline.points[-1] - point).length    
            if T >= start and T <= end and appendCondition and vecDistance >= minDistance :
                p_object[i].polyspline.appendPoint(point, radius, tilt)   
            splinelist.append(p_object[i].polyspline)
        p[identifier] = p_object

        return splinelist

    def execute_beziersplines(self, points, resetframe, start, end, radius, tilt, smoothness, minDistance, appendCondition, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        vecDistance = minDistance

        identifier = self.identifier + "bezier"
        if useCustomIdentifier:
            identifier = customIdentifier + "bezier" 
        if T == resetframe:
            p[identifier] = []
        p_object = p.get(identifier, [])

        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            return splinelist

        for i, point in enumerate(points):
            p_object.append(StoreSpline(i))
            if len(p_object[i].bezierspline.points)!=0:
                vecDistance = (p_object[i].bezierspline.points[-1] - point).length
            if T >= start and T <= end and appendCondition and vecDistance >= minDistance :
                p_object[i].bezierspline.appendPoint(point, (0,0,0), (0,0,0), radius, tilt)
            splinelist.append(p_object[i].bezierspline)
            splinelist[i].smoothAllHandles(smoothness)
        p[identifier] = p_object

        return splinelist    

    def execute_polyspline(self, point, resetframe, start, end, radius, tilt, minDistance, appendCondition, useCustomIdentifier, customIdentifier):
        points = Vector3DList.fromValues([point])
        splines = self.execute_polysplines(points, resetframe, start, end, radius, tilt, minDistance, appendCondition, useCustomIdentifier, customIdentifier)
        if len(splines) == 0: 
            return PolySpline()
        else:    
            return splines[0]

    def execute_bezierspline(self, point, resetframe, start, end, radius, tilt, smoothness, minDistance, appendCondition, useCustomIdentifier, customIdentifier):
        points = Vector3DList.fromValues([point])
        splines = self.execute_beziersplines(points, resetframe, start, end, radius, tilt, smoothness, minDistance, appendCondition, useCustomIdentifier, customIdentifier)
        if len(splines) == 0: 
            return BezierSpline()
        else:    
            return splines[0] 
               