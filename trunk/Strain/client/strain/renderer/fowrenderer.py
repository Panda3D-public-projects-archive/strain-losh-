from panda3d.core import *

class FowRenderer():    
    def __init__(self, parent):
        self.parent = parent
        
    def initializeTexture(self, parent_node, x, y):
        self.parent_node = parent_node
        self.x = x
        self.y = y

        self.fow_coef = 16   
        self.display = False     
        
        self.fowImage = PNMImage(x*self.fow_coef, y*self.fow_coef)
        self.fowImage.fill(.4)
        
        self.fowBrush = PNMBrush.makePixel((1, 1, 1, 1))
        #self.fowBrush = PNMBrush.makeSpot(VBase4D(1), int(self.fow_coef/2), fuzzy=False)
        self.fowPainter = PNMPainter(self.fowImage)
        self.fowPainter.setPen(self.fowBrush)
        self.fowTexture = Texture()
        self.fowTexture.load(self.fowImage)
            
        minb, maxb = self.parent_node.getTightBounds()
        dim = maxb-minb
        maxDim = max(dim[0],dim[1])
        scale = 1./maxDim
        center = (minb+maxb)*.5
        self.fowTextureStage = TextureStage('')
        self.parent_node.setTexGen(self.fowTextureStage, RenderAttrib.MWorldPosition)
        self.parent_node.setTexScale(self.fowTextureStage, scale)
        self.parent_node.setTexOffset(self.fowTextureStage, -.5-center[0]*scale, -.5-center[1]*scale)  
        
        
        cm = CardMaker('')
        cm.setFrame(-.8,-.2,0,.6)
        card = base.a2dBottomRight.attachNewNode(cm.generate())
        card.setTexture(self.fowTexture)
                
    
    def reset(self):
        self.fowImage.fill(.4)
        self.fowTexture.load(self.fowImage)
        
    def redraw(self, tile_dict):
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
        self.fowPainter.drawRectangle(5*self.fow_coef+k, 1*self.fow_coef+k, 5*self.fow_coef+k, 1*self.fow_coef+k) 
        self.fowTexture.load(self.fowImage)                                                              
        return
        """
        
        
        for invisible_tile in tile_dict:
            if tile_dict[invisible_tile] != 0:
                #self.fowPainter.drawPoint(invisible_tile[0]*self.fow_coef+k, (self.y-1-invisible_tile[1])*self.fow_coef+k)
                self.fowPainter.drawRectangle(invisible_tile[0]*self.fow_coef, (self.y-1-invisible_tile[1])*self.fow_coef, (invisible_tile[0]+1)*self.fow_coef-1, (self.y-invisible_tile[1])*self.fow_coef-1)                                                                                                                              
        self.fowTexture.load(self.fowImage)
        
    
    
    def toggle(self):
        if not self.display:
            self.parent_node.setTexture(self.fowTextureStage, self.fowTexture)
            self.display = True
    
        else:
            self.parent_node.clearTexture(self.fowTextureStage)
            self.display = False
    