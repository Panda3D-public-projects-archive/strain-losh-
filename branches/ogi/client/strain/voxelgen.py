#############################################################################
# IMPORTS
#############################################################################

# python imports
from time import time

# panda3D imports
from panda3d.core import Texture, NodePath, TextureStage
from panda3d.core import Vec4, Vec3, Point3

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
        self.node_usable = None

    def createLevel(self):
        tex1 = loader.loadTexture("tile1.png")
        tex2 = loader.loadTexture("tile2.png")
        tex3 = loader.loadTexture("tile3.png")

        tex1.setMagfilter(Texture.FTLinearMipmapLinear)
        tex1.setMinfilter(Texture.FTLinearMipmapLinear)
        tex2.setMagfilter(Texture.FTLinearMipmapLinear)
        tex2.setMinfilter(Texture.FTLinearMipmapLinear)
        tex3.setMagfilter(Texture.FTLinearMipmapLinear)
        tex3.setMinfilter(Texture.FTLinearMipmapLinear)        

        
        ts = TextureStage('ts')
        #ts2 = TextureStage('ts2')
        #ts2.setMode(TextureStage.MGlow)
        for x in xrange(0, self.level.maxX):
            for y in xrange(0, self.level.maxY):
                if self.level.getHeight( (x, y) ) == 0:
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, 0)
                    model.setTexture(ts, tex3)
                    model.reparentTo(self.node_original) 
                elif self.level.getHeight( (x, y) ) == 1:                    
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, 0)
                    model.setTexture(ts, tex3)
                    model.reparentTo(self.node_original) 
                    model2 = loader.loadModel('halfcube')
                    model2.setPos(x, y, utils.GROUND_LEVEL)
                    model2.setTexture(ts, tex1)
                    model2.reparentTo(self.node_original) 
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )-1):
                        if i == 0:
                            model = loader.loadModel('halfcube')
                            model.setPos(x, y, 0)
                            model.setTexture(ts, tex3)
                        else:
                            model = loader.loadModel('cube')
                            model.setPos(x, y, i-1+utils.GROUND_LEVEL)
                            model.setTexture(ts, tex2)
                        model.reparentTo(self.node_original)                 
        self.switchNodes()              
    
    def makeCopy(self):
        if self.node_usable != None:
            self.node_usable.removeNode()
        np = NodePath("new")
        np = self.node_original.copyTo(self.parent.level_node)
        return np
    
    def flattenCopy(self, np):
        ftime = time()
        np.clearModelNodes()
        np.flattenStrong()
        self.node_usable = np
    
    def switchNodes(self):
        #ftime = time()
        np = self.makeCopy()
        #print time() - ftime, ' step1'
        self.flattenCopy(np)
        #print time() - ftime, ' switched'
        