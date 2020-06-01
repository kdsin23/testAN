import bpy
import numpy
from math import *
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode
from .. falloff . custom_falloff import CustomFalloff
from ... data_structures import DoubleList, FloatList

class Formulafalloff(bpy.types.Node, AnimationNode):
    bl_idname = "an_Formulafalloff"
    bl_label = "Formula falloff"
    bl_width_default = 300
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Integer", "Count", "count", value = 1.0, minValue = 0)
        self.newInput("Text", "Formula", "formula", value = "a*(sin(((id / count) + t) * f * 360.0))", update = propertyChanged) 
        self.newInput("Float", "t-Time", "time", value = 0.1)      
        self.newInput("Float", "f-frequency", "f", value = 0.01)
        self.newInput("Float", "a-amplitude", "a", value = 1.0, minValue = 0.00001)
        self.newInput("Float", "Fallback", "fallback", hide = True)

        self.newOutput("Falloff", "Falloff", "outFalloff")
        self.newOutput("Float List", "strengths", "strengths")

    def drawAdvanced(self, layout):
        box = layout.box()
        col = box.column(align = True)
        col.label(text = "Variables", icon = "INFO")
        col.label(text = "id - index")
        col.label(text = "count - total amount")
        col.label(text = "f - frequency")
        col.label(text = "t - time")
        col.label(text = "a - amplitude")
        box = layout.box()
        col = box.column(align = True)
        col.label(text = "Operators", icon = "INFO")
        col.label(text = "All math operators are supported")
        col.label(text = "eg: +, -, *, /, sin(), cos(), tan(), etc")
        col.label(text = "Numpy functions are also supported")
        col.label(text = "eg: numpy.mod(id,2)")

    def execute(self, count, formula, time, f, a, fallback):
        frameinfo=bpy.context.scene.frame_current
        t = frameinfo*time
        out = self.formula_fun(count, formula, t, f, a, fallback)

        falloff_out = CustomFalloff(FloatList.fromValues([0.00]), fallback)
        strength_out = DoubleList.fromValues([0.00])

        try:
            falloff_out = CustomFalloff(FloatList.fromValues(out), fallback)
            strength_out = DoubleList.fromValues(out)
            return falloff_out, strength_out
        except (TypeError, NameError, ValueError, SyntaxError):
            self.raiseErrorMessage("Incorrect formula")
            return falloff_out, strength_out

    def formula_fun(self, count, formula, t, f, a, fallback):
        res=[]
        for id in range(count):
            try:
                result = eval(formula) #Todo make eval safe
            except (TypeError, NameError, ValueError, SyntaxError, AttributeError):
                result=0
                self.raiseErrorMessage("Incorrect formula")
            except ZeroDivisionError:
                result=0
                self.raiseErrorMessage("Division by zero")
            res.append(result)
        return res
