from panda3d.core import *
import strain.utils as utils
from direct.showbase.DirectObject import DirectObject

class LevelRenderer(DirectObject):
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.node = None
    
    def redraw(self, level, x, y, tile_size, zpos):
        if self.node != None:
            self.node.removeNode()
        self.node = self.parent_node.attachNewNode('LevelRendererNode')
        m = loader.loadModel('Level01')
        m.reparentTo(self.node)
        self.node.setShaderAuto()
        self.redrawLights()
        
    def redrawLights(self):
        #shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        #render.setAttrib(shade)
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        self.dlnp1 = self.node.attachNewNode(dlight1)
        self.dlnp1.setHpr(0, -80, 0)
        self.node.setLight(self.dlnp1)

        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        self.alnp = self.node.attachNewNode(alight)
        self.node.setLight(self.alnp)
    
    def cleanup(self):
        #taskMgr.remove('texTask')
        self.node.removeNode()
    