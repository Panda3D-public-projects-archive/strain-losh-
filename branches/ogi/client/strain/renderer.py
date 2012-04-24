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
        self.fow_display = False
        self.accept('z', self.toggleGrid)
        self.accept('b', self.toggleFow)
        
        self.fow_coef = 2
    
    def load(self, name, x, y):
        name = 'LevelTexturedBlockout'
        self.maxX = x
        self.maxY = y
        m = loader.loadModel(name)
        m.setPos(24, 24, 0)
        m.reparentTo(self.node)

        plane = self.node.find("**/Plane.001")
        plane.removeNode()
        
        plane = self.node.find("**/Plane.003")
        plane.removeNode()
        
        plane = self.node.find("**/Plane.004")
        plane.removeNode()
        
        plane = self.node.find("**/Plane.007")
        plane.removeNode()
        
        self.createGrid()
        
        self.fowImage = PNMImage(x*self.fow_coef, y*self.fow_coef)
        self.fowImage.fill(.4)

        #self.fowBrush = PNMBrush.makePixel((1, 1, 1, 1))
        self.fowBrush = PNMBrush.makeSpot(VBase4D(1), int(self.fow_coef/2), False)
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
        self.node.setTexGen(self.fowTextureStage, RenderAttrib.MWorldPosition)
        self.node.setTexScale(self.fowTextureStage, scale)
        self.node.setTexOffset(self.fowTextureStage, -.5-center[0]*scale, -.5-center[1]*scale)  
        
        cm = CardMaker('')
        cm.setFrame(-.8,-.2,0,.6)
        card = base.a2dBottomRight.attachNewNode(cm.generate())
        card.setTexture(self.fowTexture)
        
    def getInvisibleTiles(self):
        self.fowImage.fill(.4)
        
        k = int(self.fow_coef/2) - 0.5
        """
        self.fowPainter.drawPoint((0)*self.fow_coef+k, (0)*self.fow_coef+k)
        self.fowPainter.drawPoint((5)*self.fow_coef+k, (0)*self.fow_coef+k)  
        self.fowPainter.drawPoint((10)*self.fow_coef+k, (0)*self.fow_coef+k)  
        self.fowPainter.drawPoint((15)*self.fow_coef+k, (0)*self.fow_coef+k)
        
        self.fowPainter.drawPoint((20)*self.fow_coef+k, (23)*self.fow_coef+k)    
        self.fowTexture.load(self.fowImage)       
        return
        
        """
        
        """
        self.fowPainter.drawRectangle(32, 32, 47, 47) 
        self.fowTexture.load(self.fowImage)                                                              
        return
        """
        
        
        tile_dict = self.parent.parent.getInvisibleTiles()
        for invisible_tile in tile_dict:
            if tile_dict[invisible_tile] != 0:
                self.fowPainter.drawPoint(invisible_tile[0]*self.fow_coef+k, (23-invisible_tile[1])*self.fow_coef+k)
                #self.fowPainter.drawRectangle(invisible_tile[0]*self.fow_coef, (23-invisible_tile[1])*self.fow_coef, (invisible_tile[0]+1)*self.fow_coef-1, (24-invisible_tile[1])*self.fow_coef-1)                                                               
        self.fowTexture.load(self.fowImage)
    
    def createGrid(self, thickness=1.0, color=Vec4(0.96,0.64,0.37,1)):
        segs = LineSegs()
        segs.setThickness(thickness)
        segs.setColor(color)
        for i in xrange(self.maxX):
            segs.moveTo(i*utils.TILE_SIZE, 0, utils.GROUND_LEVEL+0.05)
            segs.drawTo(i*utils.TILE_SIZE, self.maxY*utils.TILE_SIZE, utils.GROUND_LEVEL+0.05)
        for j in xrange(self.maxY):
            segs.moveTo(0, j*utils.TILE_SIZE, utils.GROUND_LEVEL+0.05)
            segs.drawTo(self.maxX*utils.TILE_SIZE, j*utils.TILE_SIZE, utils.GROUND_LEVEL+0.05)
        self.grid = NodePath(segs.create())
        #self.grid.setTransparency(TransparencyAttrib.MAlpha)
        self.grid.setLightOff()
        self.grid.setDepthOffset(3)
     
    def toggleGrid(self):
        if not self.grid_display:
            self.grid.reparentTo(render)
            self.grid_display = True
        else:
            self.grid.detachNode()
            self.grid_display = False
            
    def toggleFow(self):
        if not self.fow_display:
            self.node.setTexture(self.fowTextureStage, self.fowTexture)
            self.fow_display = True
    
        else:
            self.node.clearTexture(self.fowTextureStage)
            self.fow_display = False
    
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
    