from panda3d.core import *
import strain.utils as utils
from direct.showbase.DirectObject import DirectObject

class LevelRenderer(DirectObject):
    def __init__(self, parent):
        self.parent = parent
        self.node = render.attachNewNode('main_level_node')
        self.grid = NodePath('grid_level_node')
        self.maxX = 0
        self.maxY = 0
        self.grid_display = False
        self.accept('z', self.toggleGrid)
    
    def load(self, name, x, y):
        name = 'LevelBlockout'
        self.maxX = x
        self.maxY = y
        m = loader.loadModel(name)
        m.setPos(33, 31, 0)
        m.reparentTo(self.node)
        self.createGrid()
    
    def createGrid(self, thickness=4.0, color=Vec4(1,1,0,0.5)):
        segs = LineSegs()
        segs.setThickness(thickness)
        segs.setColor(color)
        for i in xrange(self.maxX):
            segs.moveTo(i*utils.TILE_SIZE, 0, utils.GROUND_LEVEL)
            segs.drawTo(i*utils.TILE_SIZE, self.maxY*utils.TILE_SIZE, utils.GROUND_LEVEL)
        for j in xrange(self.maxY):
            segs.moveTo(0, j*utils.TILE_SIZE, utils.GROUND_LEVEL)
            segs.drawTo(self.maxX*utils.TILE_SIZE, j*utils.TILE_SIZE, utils.GROUND_LEVEL)
        self.grid = NodePath(segs.create())
        self.grid.setTransparency(TransparencyAttrib.MAlpha)
    
    def toggleGrid(self):
        if not self.grid_display:
            self.grid.reparentTo(self.node)
            self.grid_display = True
        else:
            self.grid.detachNode()
            self.grid_display = False
    
    def createCoordinateDisplay(self):
        for i in xrange(0, self.maxX):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i*utils.TILE_SIZE+0.3, -0.3, utils.GROUND_LEVEL)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i*utils.TILE_SIZE+0.3, self.maxY*utils.TILE_SIZE+0.3, utils.GROUND_LEVEL)
            tnp.setBillboardPointEye()
            tnp.setLightOff()            
        for i in xrange(0, self.maxY):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(-0.3, i*utils.TILE_SIZE+0.3, utils.GROUND_LEVEL)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(self.maxX+0.3, i*utils.TILE_SIZE+0.3, utils.GROUND_LEVEL)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
    