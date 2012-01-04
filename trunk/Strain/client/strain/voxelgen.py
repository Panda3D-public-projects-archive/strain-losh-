#############################################################################
# IMPORTS
#############################################################################

# python imports

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
        self.tile_list = [[None] * level.maxY for i in xrange(level.maxX)]

    def createLevel(self):
        tex = loader.loadTexture("tex3.png")
        tex.setMagfilter(Texture.FTLinearMipmapLinear)
        tex.setMinfilter(Texture.FTLinearMipmapLinear)
        ts = TextureStage('ts')
        #ts2 = TextureStage('ts2')
        #ts2.setMode(TextureStage.MGlow)
        for x in xrange(0, self.level.maxX):
            for y in xrange(0, self.level.maxY):
                for i in xrange(0, self.level.getHeight( (x, y) )+1):
                    model = loader.loadModel('tile')
                    if self.level.getHeight( (x, y) ) > 0:
                        model.setTexOffset(ts, 0.5, 0.0)
                    else:
                        model.setTexOffset(ts, 0.0, 0.0)                   
                    model.setPos(x, y, i*utils.GROUND_LEVEL)
                    model.setTexture(ts, tex)   
                    #model.setTexture(ts2, tex2, 2)
                    model.reparentTo(self.node_original)                 
                    self.tile_list[x][y] = model
        self.switchNodes()
                    
    
    def makeCopy(self):
        if self.node_usable != None:
            self.node_usable.removeNode()
        np = NodePath("new")
        np = self.node_original.copyTo(self.parent.level_node)
        return np
    
    def flattenCopy(self, np):
        np.clearModelNodes()
        np.flattenStrong()
        self.node_usable = np
    
    def switchNodes(self):
        np = self.makeCopy()
        self.flattenCopy(np)
        