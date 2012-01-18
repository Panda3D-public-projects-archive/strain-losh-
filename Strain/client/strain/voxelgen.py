#############################################################################
# IMPORTS
#############################################################################

# python imports
from time import time

# panda3D imports
from panda3d.core import Texture, NodePath, TextureStage
from panda3d.core import Vec4, Vec3, Point3, TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval#@UnresolvedImport

# strain related imports
import strain.utils as utils
 
#############################################################################
# METHODS
#############################################################################

class VoxelGenerator():
    def __init__(self, parent, level):        
        self.parent = parent
        self.level = level
        self.node_original = NodePath("voxgen_original")
        self.node_floor_original = NodePath("voxgen_floor_original")
        self.node_usable = None
        self.node_floor_usable = None

    def createLevel(self):
        tex1 = loader.loadTexture("tile1.png")
        tex2 = loader.loadTexture("tile2.png")
        tex3 = loader.loadTexture("tile3.png")
        
        self.tex_floor_b = loader.loadTexture("tile4.png")
        self.tex_floor_r = loader.loadTexture("tile5.png")

        tex1.setMagfilter(Texture.FTLinearMipmapLinear)
        tex1.setMinfilter(Texture.FTLinearMipmapLinear)
        tex2.setMagfilter(Texture.FTLinearMipmapLinear)
        tex2.setMinfilter(Texture.FTLinearMipmapLinear)
        tex3.setMagfilter(Texture.FTLinearMipmapLinear)
        tex3.setMinfilter(Texture.FTLinearMipmapLinear)  
        self.tex_floor_b.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex_floor_b.setMinfilter(Texture.FTLinearMipmapLinear)  
        self.tex_floor_r.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex_floor_r.setMinfilter(Texture.FTLinearMipmapLinear)                             

        
        ts = TextureStage('ts')
        self.ts2 = TextureStage('ts2')
        for x in xrange(0, self.level.maxX):
            for y in xrange(0, self.level.maxY):
                if self.level.getHeight( (x, y) ) == 0:
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, 0)
                    model.reparentTo(self.node_floor_original) 
                elif self.level.getHeight( (x, y) ) == 1:                    
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, 0)
                    model.reparentTo(self.node_floor_original) 
                    model2 = loader.loadModel('halfcube')
                    model2.setPos(x, y, utils.GROUND_LEVEL)
                    model2.setTexture(ts, tex1)
                    model2.reparentTo(self.node_original) 
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )-1):
                        if i == 0:
                            model = loader.loadModel('halfcube')
                            model.setPos(x, y, 0)
                            model.reparentTo(self.node_floor_original)
                        else:
                            model = loader.loadModel('cube')
                            model.setPos(x, y, i-1+utils.GROUND_LEVEL)
                            model.setTexture(ts, tex2)
                            model.reparentTo(self.node_original) 
        self.node_floor_original.setColor(0,0,0)             
        self.switchNodes()              
    
    def makeFloorCopy(self):
        if self.node_floor_usable != None:
            self.node_floor_usable.removeNode()
        np = NodePath("new")
        np = self.node_floor_original.copyTo(self.parent.level_node)
        return np
    
    def makeCopy(self):
        if self.node_usable != None:
            self.node_usable.removeNode()
        np = NodePath("new")
        np = self.node_original.copyTo(self.parent.level_node)
        return np
    
    def flattenCopy(self, np):
        np.clearModelNodes()
        np.flattenStrong()
    
    def switchNodes(self):
        np = self.makeCopy()
        self.flattenCopy(np)
        self.node_usable = np
        
        np2 = self.makeFloorCopy()
        self.flattenCopy(np2)
        self.node_floor_usable = np2
        
    def setFloorTex(self, color):
        self.node_floor_original.setColor(1,1,1)
        if color == 'RED':
            self.node_floor_original.setTexture(self.tex_floor_r)
        else:
            self.node_floor_original.setTexture(self.tex_floor_b)
        