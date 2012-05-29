from panda3d.core import *

class ShaderManager():
    def __init__(self, parent):
        """
        self.node = NodePath("OutlineShaderNode")      
        self.light_input = self.node.attachNewNode("OutlineShaderLightNode")
        self.light_input.reparentTo(self.node) 
        self.light_input.setPos(5, 0, 1) 
        self.node.setShaderOff() 
        self.node.hprInterval(1,Vec3(360,0,0)).loop() 
        """
        self.parent = parent
        self.outline_shader = Shader.load('./data/shaders/facingRatio1.sha') 
        
    def setOutlineShader(self, node, color=Vec4(1, 1, 1, 0), power=1.1):
        facingRatioPower = power
        envirLightColor = color        
        node.setShader(self.outline_shader) 
        node.setShaderInput('cam', base.camera) 
        #node.setShaderInput('light', self.light_input) 
        node.setShaderInput('envirLightColor', envirLightColor * facingRatioPower) 
        node.setAntialias(AntialiasAttrib.MMultisample) 
        
    def clearOutlineShader(self, node):
        node.clearShader()        
        