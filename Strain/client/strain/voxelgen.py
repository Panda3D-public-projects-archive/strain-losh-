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
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, LerpColorInterval, Wait#@UnresolvedImport

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
        self.node_forcewall_usable  = self.parent.level_node.attachNewNode("voxgen_force_wall_usable") 
        # Nodepath for dynamic wall models. These nodepaths will need to be changed
        self.node_dynamic_wall_usable = self.parent.level_node.attachNewNode("voxgen_dynamic_wall_usable")    
        self.dynamic_wall_dict = {}
        
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
        self.frames_between = 3
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
        self.tex_fs = loader.loadTexture("rnbw.png")
        self.ts_nm = TextureStage('ts_nm')
        self.ts_nm.setMode(TextureStage.MNormal)
        self.ts_fs = TextureStage('ts_fs')

        
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
        
        #Calculate and place walls between tiles
        for x, val in enumerate(self.level._grid):
            for y, val2 in enumerate(val):
                if val2 != None:
                    # prvi parni, drugi neparni
                    if (x%2==0 and y%2!=0):
                        tile1_x = (x-2)/2
                        tile1_y = (y-1)/2
                        tile2_x = x/2
                        tile2_y = (y-1)/2
                        h = 90
                    # prvi neparni, drugi parni
                    elif (x%2!=0 and y%2==0):
                        tile1_x = (x-1)/2
                        tile1_y = (y-2)/2
                        tile2_x = (x-1)/2
                        tile2_y = y/2
                        h = 0
                    else:
                        continue
                    
                    my_x= tile2_x
                    my_y=tile2_y
                    if val2.name == "Wall1":
                        model = loader.loadModel("wall")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.reparentTo(self.node_wall_usable)
                    elif val2.name == "Wall2":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(0,1,0,1)
                        model.reparentTo(self.node_wall_usable)
                    elif val2.name == "Wall3":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(0,0,0,1)
                        model.reparentTo(self.node_wall_usable)
                    elif val2.name == "Ruin":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(0.5,0.8,1,0.6)
                        model.setTransparency(TransparencyAttrib.MAlpha)
                        model.reparentTo(self.node_forcewall_usable)
                        s = Sequence(LerpColorInterval(model, 1, (0.13,0.56,0.78,0.6)),
                                    LerpColorInterval(model, 1, (0.5,0.8,1,0.6)),
                                    )  
                        s.loop()
                        model.setLightOff()   
                    elif val2.name == "ClosedDoor":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(1,0.0,0,0.0)
                        self.dynamic_wall_dict[(my_x, my_y)] = model
                        model.reparentTo(self.node_dynamic_wall_usable)
                    elif val2.name == "OpenedDoor":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(0.7,0.2,0.2,0.0)
                        self.dynamic_wall_dict[(my_x, my_y)] = model
                        model.reparentTo(self.node_dynamic_wall_usable)
                    elif val2.name == "ForceField":
                        model = loader.loadModel("wall_fs")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)                            
                        model.setTexture(self.ts_fs, self.tex_fs)
                        model.setTransparency(TransparencyAttrib.MAlpha)
                        model.reparentTo(self.node_forcewall_usable)
                        model.setLightOff()                                         
         
        self.node_wall_usable.clearModelNodes()
        self.node_wall_usable.flattenStrong()
        self.node_wall_usable.setShaderAuto()
        #self.floor_usable_np.setShaderAuto()
        self.markAllChunksDirty()
        
    def processLevel(self):
        self.level = self.parent.parent.level
        for x, val in enumerate(self.level._grid):
            for y, val2 in enumerate(val):
                if val2 != None:
                    # prvi parni, drugi neparni
                    if (x%2==0 and y%2!=0):
                        tile1_x = (x-2)/2
                        tile1_y = (y-1)/2
                        tile2_x = x/2
                        tile2_y = (y-1)/2
                        my_x= tile2_x
                        my_y=tile2_y
                        if val2.name == "ClosedDoor" and val2.name != self.parent.parent.old_level_grid[x][y].name:
                            self.dynamic_wall_dict[(my_x, my_y)].removeNode()
                            self.dynamic_wall_dict[(my_x, my_y)] = None
                            model = loader.loadModel("wall2")
                            model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                            model.setH(90)
                            model.setColor(1,0.0,0,0.0)
                            self.dynamic_wall_dict[(my_x, my_y)] = model
                            model.reparentTo(self.node_dynamic_wall_usable)
                        elif val2.name == "OpenedDoor" and val2.name != self.parent.parent.old_level_grid[x][y].name:
                            self.dynamic_wall_dict[(my_x, my_y)].removeNode()
                            self.dynamic_wall_dict[(my_x, my_y)] = None
                            model = loader.loadModel("wall2")
                            model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                            model.setH(90)
                            model.setColor(0.7,0.2,0.2,0.0)
                            self.dynamic_wall_dict[(my_x, my_y)] = model
                            model.reparentTo(self.node_dynamic_wall_usable)                                                   
                    # prvi neparni, drugi parni
                    elif (x%2!=0 and y%2==0):
                        tile1_x = (x-1)/2
                        tile1_y = (y-2)/2
                        tile2_x = (x-1)/2
                        tile2_y = y/2
                        my_x= tile2_x
                        my_y=tile2_y 
                        if val2.name == "ClosedDoor" and val2.name != self.parent.parent.old_level_grid[x][y].name:
                            self.dynamic_wall_dict[(my_x, my_y)].removeNode()
                            self.dynamic_wall_dict[(my_x, my_y)] = None
                            model = loader.loadModel("wall2")
                            model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                            model.setColor(1,0.0,0,0.0)
                            self.dynamic_wall_dict[(my_x, my_y)] = model
                            model.reparentTo(self.node_dynamic_wall_usable)
                        elif val2.name == "OpenedDoor" and val2.name != self.parent.parent.old_level_grid[x][y].name:
                            self.dynamic_wall_dict[(my_x, my_y)].removeNode()
                            self.dynamic_wall_dict[(my_x, my_y)] = None
                            model = loader.loadModel("wall2")
                            model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                            model.setColor(0.7,0.2,0.2,0.0)
                            self.dynamic_wall_dict[(my_x, my_y)] = model
                            model.reparentTo(self.node_dynamic_wall_usable) 
                    else:
                        continue
    
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
                np = chunk_tupple[0].copyTo(NodePath())
                np.clearModelNodes()
                np.flattenStrong()
                self.floor_usable_np_list[chunk_tupple[1]][chunk_tupple[2]].removeNode()
                self.floor_usable_np_list[chunk_tupple[1]][chunk_tupple[2]] = np
                self.floor_usable_np_list[chunk_tupple[1]][chunk_tupple[2]].reparentTo(self.floor_usable_np)
                self.frames_counter = 0
        return task.cont