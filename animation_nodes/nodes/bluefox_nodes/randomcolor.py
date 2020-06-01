import bpy
import random
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode
from . c_utils import generateRandomColors

class RandomColor(bpy.types.Node, AnimationNode):
    bl_idname = "an_RandomColor"
    bl_label = "Random Color"

    nodeSeed: IntProperty(name = "Node Seed", update = propertyChanged, max = 1000, min = 0)

    createList: BoolProperty(name = "Create List", default = False,
        description = "Create a list of random colors",
        update = AnimationNode.refresh)

    def setup(self):
        self.randomizeNodeSeed()    

    def create(self):
        if self.createList:
            self.newInput("Integer", "Count", "count", value = 5, minValue = 0)
            self.newInput("Integer", "Seed", "seed")
            self.newOutput("Color List", "Colors", "randomColors")
        else:
            self.newInput("Integer", "Seed", "seed")
            self.newOutput("Color", "Color", "color")
        self.newInput("Boolean", "Normalized", "normalized", value = False, hide = True)
        self.newInput("Float", "Scale", "scale", value = 1, hide = True)    

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "nodeSeed", text = "Node Seed")
        row.prop(self, "createList", text = "", icon = "LINENUMBERS_ON") 

    def getExecutionFunctionName(self):
        if self.createList:
            return "execute_List"
        else:
            return "execute_Single"       
                   
    def execute_List(self, count, seed, normalized, scale):
        finalSeed = seed + 25642 * self.nodeSeed
        return generateRandomColors(count, seed, scale, normalized)

    def execute_Single(self, seed, normalized, scale):
        finalSeed = seed + 25642 * self.nodeSeed
        return self.execute_List(1, finalSeed, normalized, scale)[0]    

    def duplicate(self, sourceNode):
        self.randomizeNodeSeed()

    def randomizeNodeSeed(self):
        self.nodeSeed = int(random.random() * 100)       
        