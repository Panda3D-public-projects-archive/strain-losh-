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
        name = 'LevelTexturedBlockout'
        self.maxX = x
        self.maxY = y
        m = loader.loadModel(name)
        m.setPos(24, 24, 0)
        m.reparentTo(self.node)
        self.createGrid()
        self.fowImage = PNMImage(x, y)
        self.fowImage.fill(.1)
        self.fowBrush = PNMBrush.makeSpot(VBase4D(1), 1, False)
        self.fowPainter = PNMPainter(self.fowImage)
        self.fowPainter.setPen(self.fowBrush)
        self.fowTexture = Texture()
        self.fowTexture.load(self.fowImage)
        
        minb, maxb = self.node.getTightBounds()
        dim = maxb-minb
        maxDim = max(dim[0],dim[1])
        scale = 1./maxDim
        center = (minb+maxb)*.5
            
        self.fowTextureStage = TextureStage('')
        #self.node.setTexture(self.fowTextureStage, self.fowTexture)
        self.node.setTexGen(self.fowTextureStage, TexGenAttrib.MWorldPosition)
        self.node.setTexScale(self.fowTextureStage, scale)
        self.node.setTexOffset(self.fowTextureStage, -.5-center[0]*scale, -.5-center[1]*scale)

        # a dummy node to hold size & position of terrain to texture transform 
        self.texOrigin = render.attachNewNode('')
        self.texOrigin.setPos(center[0]-.5*maxDim, center[1]+.5*maxDim, 0)
        self.texOrigin.setScale(maxDim/32,-maxDim/32,1)
        
        cm = CardMaker('')
        cm.setFrame(-.4,0,0,.4)
        card = base.a2dBottomRight.attachNewNode(cm.generate())
        card.setTexture(self.fowTexture)
        
    def getInvisibleTiles(self):
        tile_dict = self.parent.parent.getInvisibleTiles()
        n = NodePath('')
        for invisible_tile in tile_dict:      
            n.setPos(utils.TILE_SIZE*(invisible_tile[0]+0.5), utils.TILE_SIZE*(invisible_tile[1]+0.5), utils.GROUND_LEVEL)
            x = n.getX(self.texOrigin)
            y = n.getY(self.texOrigin)
            print invisible_tile[0], invisible_tile[1], x,y
            self.fowPainter.drawPoint(x, y)
            self.fowTexture.load(self.fowImage)
    
    def createGrid(self, thickness=3.0, color=Vec4(1,1,0,0.5)):
        segs = LineSegs()
        segs.setThickness(thickness)
        segs.setColor(color)
        for i in xrange(self.maxX):
            segs.moveTo(i*utils.TILE_SIZE, 0, utils.GROUND_LEVEL)
            segs.drawTo(i*utils.TILE_SIZE, self.maxY*utils.TILE_SIZE, utils.GROUND_LEVEL+0.02)
        for j in xrange(self.maxY):
            segs.moveTo(0, j*utils.TILE_SIZE, utils.GROUND_LEVEL)
            segs.drawTo(self.maxX*utils.TILE_SIZE, j*utils.TILE_SIZE, utils.GROUND_LEVEL+0.02)
        self.grid = NodePath(segs.create())
        self.grid.setTransparency(TransparencyAttrib.MAlpha)
        self.grid.setLightOff()
        self.grid.setDepthOffset(2)
    
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
    