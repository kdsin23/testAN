import bpy
from ... base_types import AnimationNode
from . c_utils import FilterParticles

class FilterParticlesNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_FilterParticlesNode"
    bl_label = "Filter Particles"

    def create(self):
        self.newInput("Generic List", "Particles", "particles")
        self.newInput("Boolean", "Alive", "Alive", value = True)
        self.newInput("Boolean", "Unborn", "Unborn", value= False)
        self.newInput("Boolean", "Dying", "Dying", value= False)
        self.newInput("Boolean", "Dead", "Dead", value= False)
        self.newOutput("Generic List", "Filtered", "filtered")

    def execute(self, particles, Alive, Unborn, Dying, Dead):

        if particles is None:
            return None

        return FilterParticles(particles, Alive, Unborn, Dying, Dead)