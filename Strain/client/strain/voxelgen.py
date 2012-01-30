#############################################################################
# IMPORTS
#############################################################################

# python imports
import time
import math
from collections import deque

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
    def __init__(self, parent, level, chunk_size=(7,7,1)):        
        self.parent = parent
        self.level = level
        self.chunk_size = chunk_size
        # We need just one original nodepath for walls, and one usable in scenegraph
        # Wall will never need to be flattened
        self.node_wall_usable = self.parent.level_node.attachNewNode("voxgen_wall_usable")        
        
        # For floors we will create a list of nodepaths, each list member will parent one chunk of tiles
        x = int((level.maxX-1) / chunk_size[0]) + 1
        y = int((level.maxY-1) / chunk_size[1]) + 1
        self.floor_np = NodePath("voxgen_floor_original")
        self.floor_usable_np = self.parent.level_node.attachNewNode("voxgen_floor_usable")        
        self.floor_np_list = []
        self.floor_usable_np_list = []
        for i in xrange(x):
            temp_list = []
            temp_list_usable = []
            for j in xrange(y):
                n = self.floor_np.attachNewNode('n_'+str(i)+'_'+str(j))
                temp_list.append(n)
                n2 = self.floor_usable_np.attachNewNode('n_usable_'+str(i)+'_'+str(j))
                temp_list_usable.append(n2)
            self.floor_np_list.append(temp_list)
            self.floor_usable_np_list.append(temp_list_usable)

        self.floor_tile_dict = {}
        
        # We need a FIFO struct to hold pointers to dirty chunks that need flattening
        self.dirty_chunks = deque()
        
        self.old_tile_dict = None
        
        # Create flatten task
        self.pause_flatten_task = True
        self.frames_between = 10
        self.frames_counter = 0
        taskMgr.add(self.flattenTask, "flatten_task")  
        

    def markChunkDirty(self, x, y):
        chunk_x = int(x / self.chunk_size[0])
        chunk_y = int(y / self.chunk_size[0])
        payload = (self.floor_np_list[chunk_x][chunk_y], chunk_x, chunk_y)
        if not payload in self.dirty_chunks:
            self.dirty_chunks.append(payload)
    
    def markAllChunksDirty(self):
        self.pause_flatten_task = True
        self.markChunkDirty(0, 0)
        self.markChunkDirty(0, 1)
        self.markChunkDirty(0, 2)
        self.markChunkDirty(1, 0)
        self.markChunkDirty(1, 1)
        self.markChunkDirty(1, 2)
        self.markChunkDirty(2, 0)
        self.markChunkDirty(2, 1)
        self.markChunkDirty(2, 2)
        self.pause_flatten_task = False
    
    def createLevel(self):
        self.tex1 = loader.loadTexture("tile1.png")
        self.tex2 = loader.loadTexture("tile2.png")
        self.tex3 = loader.loadTexture("tile3.png")
        self.tex_tile_nm = loader.loadTexture("tile2nm.png")
        self.ts_nm = TextureStage('ts_nm')
        self.ts_nm.setMode(TextureStage.MNormal)
        
        self.tex_floor_transparent = loader.loadTexture("trans_tex.png")

        self.tex1.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex1.setMinfilter(Texture.FTLinearMipmapLinear)
        self.tex2.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex2.setMinfilter(Texture.FTLinearMipmapLinear)
        self.tex3.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex3.setMinfilter(Texture.FTLinearMipmapLinear)
        self.tex_tile_nm.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex_tile_nm.setMinfilter(Texture.FTLinearMipmapLinear)
        
        ts = TextureStage('ts')
        for x in xrange(0, self.level.maxX):
            for y in xrange(0, self.level.maxY):
                if self.level.getHeight( (x, y) ) == 0:
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, 0)
                    model.reparentTo(self.floor_np_list[int(x/self.chunk_size[0])][int(y/self.chunk_size[1])])
                    self.floor_tile_dict[(x,y)] = model
                elif self.level.getHeight( (x, y) ) == 1:                    
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, 0)
                    model.reparentTo(self.floor_np_list[int(x/self.chunk_size[0])][int(y/self.chunk_size[1])]) 
                    self.floor_tile_dict[(x,y)] = model
                    model = loader.loadModel('halfcube')
                    model.setPos(x, y, utils.GROUND_LEVEL)
                    model.setTexture(ts, self.tex1)
                    model.setTexture(self.ts_nm, self.tex_tile_nm)
                    model.reparentTo(self.node_wall_usable) 
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )):
                        if i == 0:
                            model = loader.loadModel('halfcube')
                            model.setPos(x, y, 0)
                            model.reparentTo(self.floor_np_list[int(x/self.chunk_size[0])][int(y/self.chunk_size[1])])
                            self.floor_tile_dict[(x,y)] = model
                        else:
                            model = loader.loadModel('cube')
                            model.setPos(x, y, i-1+utils.GROUND_LEVEL)
                            model.setTexture(ts, self.tex2)
                            model.setTexture(self.ts_nm, self.tex_tile_nm) 
                            model.reparentTo(self.node_wall_usable) 
        self.floor_np.setTexture(self.tex3)  
        self.node_wall_usable.clearModelNodes()
        self.node_wall_usable.flattenStrong()
        self.node_wall_usable.setShaderAuto()
        self.markAllChunksDirty()
        
    def setInvisibleTiles(self, tile_dict):
        for invisible_tile in tile_dict:
            if self.old_tile_dict == None or tile_dict[invisible_tile] != self.old_tile_dict[invisible_tile]:
                if tile_dict[invisible_tile] == 0:
                    self.floor_tile_dict[invisible_tile].clearTexture()
                    self.floor_tile_dict[invisible_tile].setTexture(self.tex_floor_transparent)
                    self.floor_tile_dict[invisible_tile].setTransparency(TransparencyAttrib.MAlpha)
                    self.markChunkDirty(invisible_tile[0], invisible_tile[1])
                else:
                    self.floor_tile_dict[invisible_tile].clearTexture()
                    self.floor_tile_dict[invisible_tile].setTexture(self.tex3)
                    self.floor_tile_dict[invisible_tile].setTransparency(TransparencyAttrib.MNone) 
                    self.markChunkDirty(invisible_tile[0], invisible_tile[1])            
        self.old_tile_dict = tile_dict
    
    def flattenTask(self, task):
        if self.pause_flatten_task:
            return task.cont
        
        if self.frames_counter < self.frames_between:
            self.frames_counter += 1
        
        if len(self.dirty_chunks) > 0:
            if self.frames_counter == self.frames_between:
                chunk_tupple = self.dirty_chunks.popleft()
                print chunk_tupple[1], chunk_tupple[2]
                print time.clock()
                np = chunk_tupple[0].copyTo(NodePath())
                np.clearModelNodes()
                np.flattenStrong()
                self.floor_usable_np_list[chunk_tupple[1]][chunk_tupple[2]].removeNode()
                self.floor_usable_np_list[chunk_tupple[1]][chunk_tupple[2]] = np
                self.floor_usable_np_list[chunk_tupple[1]][chunk_tupple[2]].reparentTo(self.floor_usable_np)
                print time.clock()
                self.frames_counter = 0
        return task.cont