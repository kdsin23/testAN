import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode

dupliModeItems = [
    ("VERTS", "Vertices", "Instance on vertices", "", 0),
    ("FACES", "Faces", "Instance on Faces", "", 1),
    ("COLLECTION", "Collection", "Instance a collection", "", 2)
]

lastChild = {}

class DupliInstancerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_DupliInstancer"
    bl_label = "Dupli Instancer"
    errorHandlingType = "EXCEPTION"
    bl_width_default = 160

    useDisplay : BoolProperty(name = "Display Instancer", default = True, update = propertyChanged)
    useRender : BoolProperty(name = "Render Instancer", default = True, update = propertyChanged)

    mode : EnumProperty(name = "Mode", default = "VERTS",
        items = dupliModeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Object", "Parent", "parent")
        if self.mode == "COLLECTION":
            self.newInput("Collection", "Collection", "collection", defaultDrawType = "PROPERTY_ONLY")
        elif self.mode == "VERTS":
            self.newInput("Object", "Child", "child")
            self.newInput("Boolean", "Align to Normal", "align")
        elif self.mode == "FACES":
            self.newInput("Object", "Child", "child")
            self.newInput("Boolean", "Scale by Face", "scaleByFace")
            self.newInput("Float", "Factor", "factor", value = 1.0)

        self.newOutput("Object", "Parent", "object")

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "mode", text = "")
        subrow.prop(self, "useDisplay", index = 1, text = "", icon = "RESTRICT_VIEW_OFF")
        subrow.prop(self, "useRender", index = 2, text = "", icon = "RESTRICT_RENDER_OFF")

    def getExecutionFunctionName(self):
        if self.mode == "VERTS":
            return "execute_Verts"
        elif self.mode == "FACES":
            return "execute_Faces"
        elif self.mode == "COLLECTION":
            return "execute_Collection"                 

    def execute_Verts(self, parent, child, align):
        parentOut = parent
        if parent == None or child == None or parent == child:
            if parent != None and parent.instance_type:
                parent.instance_type = "NONE"   
        else:
            child.parent = parent
            parent.instance_type = "VERTS"
            parent.show_instancer_for_viewport = self.useDisplay
            parent.show_instancer_for_render = self.useRender
            parent.use_instance_vertices_rotation = align
        return parentOut

    def execute_Faces(self, parent, child, scaleByFace, factor):
        parentOut = parent
        if parent == None or child == None or parent == child:
            if parent != None and parent.instance_type:
                parent.instance_type = "NONE"
        else:
            child.parent = parent
            parent.instance_type = "FACES"
            parent.show_instancer_for_viewport = self.useDisplay
            parent.show_instancer_for_render = self.useRender
            parent.use_instance_faces_scale = scaleByFace
            parent.instance_faces_scale = factor
        return parentOut

    def execute_Collection(self, parent, collection):
        parentOut = parent
        if parent == None or collection == None:
            if parent != None and parent.instance_type:
                parent.instance_type = "NONE"
        else:
            try:
                parent.instance_type = "COLLECTION"
                parent.show_instancer_for_viewport = self.useDisplay
                parent.show_instancer_for_render = self.useRender
                parent.instance_collection = collection   
            except TypeError:
                self.raiseErrorMessage("Parent should be an Empty")
        return parentOut      
