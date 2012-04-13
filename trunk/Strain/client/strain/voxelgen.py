#############################################################################
# IMPORTS
#############################################################################

# python imports
import time
import math
from collections import deque

# panda3D imports
from panda3d.core import Texture, NodePath, TextureStage, OccluderNode
from panda3d.core import Vec4, Vec3, Point3, TransparencyAttrib, LineSegs
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, LerpColorInterval, Wait#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject

# strain related imports
import strain.utils as utils
 
#############################################################################
# METHODS
#############################################################################

class VoxelGenerator(DirectObject):
    def __init__(self, parent, level, chunk_size=(7,7,1)):        
        self.parent = parent
        self.level = level
        self.chunk_size = chunk_size
        self.node_wall_original = NodePath('wall_original')
        self.node_wall_usable = self.parent.level_node.attachNewNode("voxgen_wall_usable")    
        self.node_forcewall_usable  = self.parent.level_node.attachNewNode("voxgen_force_wall_usable") 
        self.node_dynamic_wall_usable = self.parent.level_node.attachNewNode("voxgen_dynamic_wall_usable")    
        self.wall_dict= {}
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
        self.dirty_walls = 0
        
        self.old_tile_dict = None
        self.old_invisible_walls= []
        
        # Create flatten task
        self.pause_flatten_task = True
        self.frames_between = 3
        self.frames_counter = 0
        taskMgr.add(self.flattenTask, "flatten_task")  
        self.grid_display = False
        self.createGrid()
        self.accept('z', self.toggleGrid)
    
    def createGrid(self):
        segs = LineSegs( )
        segs.setThickness( 4.0 )
        segs.setColor( Vec4(1,1,0,0.3) )
        for i in xrange(self.level.maxX):
            segs.moveTo(i+1, 0, utils.GROUND_LEVEL)
            segs.drawTo(i+1, self.level.maxY, utils.GROUND_LEVEL+0.02)
        for j in xrange(self.level.maxY):
            segs.moveTo(0, j+1, utils.GROUND_LEVEL)
            segs.drawTo(self.level.maxX, j+1, utils.GROUND_LEVEL+0.02)
        self.grid = NodePath(segs.create( ))
        self.grid.setTransparency(TransparencyAttrib.MAlpha)
    
    def toggleGrid(self):
        if not self.grid_display:
            self.grid.reparentTo(self.parent.level_node)
            self.grid_display = True
        else:
            self.grid.detachNode()
            self.grid_display = False
    
    def markChunkDirty(self, x, y):
        chunk_x = int(x / self.chunk_size[0])
        chunk_y = int(y / self.chunk_size[0])
        payload = (self.floor_np_list[chunk_x][chunk_y], chunk_x, chunk_y)
        if not payload in self.dirty_chunks:
            self.dirty_chunks.append(payload)
    
    def markAllChunksDirty(self):
        self.pause_flatten_task = True
        for idx, val in enumerate(self.floor_np_list):
            for idy, v in enumerate(val):
                payload = self.floor_np_list[idx][idy], idx, idy
                self.dirty_chunks.append(payload)
        self.pause_flatten_task = False
    
    def createLevel(self):
        self.tex1 = loader.loadTexture("tile1.png")
        self.tex2 = loader.loadTexture("tile2.png")
        self.tex3 = loader.loadTexture("tile3.png")
        self.tex_tile_nm = loader.loadTexture("tile2nm.png")
        self.tex_fs = loader.loadTexture("rnbw.png")
        self.ts_fs = TextureStage('ts_fs')

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
                    
                    if (x == 0 or x == self.level.maxX-1) or (y==0 or y==self.level.maxY-1):
                        model = loader.loadModel('halfcube')
                        model.setPos(x, y, 0)
                    else:
                        model = loader.loadModel('flattile')
                        model.setPos(x, y, utils.GROUND_LEVEL)
                    
                    #model = loader.loadModel('halfcube')
                    #model.setPos(x, y, 0)                        
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
                            
                            if (x == 0 or x == self.level.maxX-1) or (y==0 or y==self.level.maxY-1):
                                model = loader.loadModel('halfcube')
                                model.setPos(x, y, 0)
                            else:
                                model = loader.loadModel('flattile')
                                model.setPos(x, y, utils.GROUND_LEVEL)
                            
                            model.reparentTo(self.floor_np_list[int(x/self.chunk_size[0])][int(y/self.chunk_size[1])])
                            self.floor_tile_dict[(x,y)] = model
                        else:
                            model = loader.loadModel('cube')
                            model.setPos(x, y, i-1+utils.GROUND_LEVEL)
                            model.setTexture(ts, self.tex2)
                            #model.setTexture(self.ts_nm, self.tex_tile_nm) 
                            model.reparentTo(self.node_wall_usable) 
        self.floor_np.setTexture(self.tex3) 
        
        #Calculate and place walls between tiles
        for x, val in enumerate(self.level._grid):
            for y, val2 in enumerate(val):
                if val2 != None:
                    # prvi parni, drugi neparni
                    tile2_x, tile2_y, h = self.getWallPosition(x, y)
                    if tile2_x == None:
                        continue
                    
                    my_x= tile2_x
                    my_y=tile2_y
                    if val2.name == "Wall1":
                        model = loader.loadModel("wall")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        self.wall_dict[(my_x, my_y, h)] = model                        
                        model.reparentTo(self.node_wall_original)                    
                    elif val2.name == "Wall2":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(0,1,0,1)
                        self.wall_dict[(my_x, my_y, h)] = model                        
                        model.reparentTo(self.node_wall_original)
                    elif val2.name == "HalfWall":
                        model = loader.loadModel("wall2")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(0,0,0,1)
                        model.setScale(1,1,0.4)
                        self.wall_dict[(my_x, my_y, h)] = model                             
                        model.reparentTo(self.node_wall_original)
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
                        model = loader.loadModel("door")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setColor(1,0.0,0,0.0)
                        self.dynamic_wall_dict[(my_x, my_y, h)] = model
                        model.reparentTo(self.node_dynamic_wall_usable)
                    elif val2.name == "OpenedDoor":
                        model = loader.loadModel("door")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)
                        model.setScale(0.2,1,1)
                        model.setColor(0.7,0.2,0.2,0.0)
                        self.dynamic_wall_dict[(my_x, my_y, h)] = model
                        model.reparentTo(self.node_dynamic_wall_usable)
                    elif val2.name == "ForceField":
                        model = loader.loadModel("wall_fs")
                        model.setPos(my_x, my_y, utils.GROUND_LEVEL)
                        model.setH(h)                            
                        model.setTexture(self.ts_fs, self.tex_fs)
                        model.setTransparency(TransparencyAttrib.MAlpha)
                        model.reparentTo(self.node_forcewall_usable)
                        self.dynamic_wall_dict[(my_x, my_y, h)] = model
                        model.setLightOff()                                         
         
        #self.floor_usable_np.setShaderAuto()
        self.floor_usable_np.setTexture(self.tex3)   
        self.markAllChunksDirty()
        self.dirty_walls = 1
        
    def getWallPosition(self, x, y):
        if (x%2==0 and y%2!=0):
            pos_x = x/2
            pos_y = (y-1)/2
            h = 90
        # prvi neparni, drugi parni
        elif (x%2!=0 and y%2==0):
            pos_x = (x-1)/2
            pos_y = y/2
            h = 0
        else:
            pos_x = None
            pos_y = None
            h = None
        return pos_x, pos_y, h
    
    def processLevel(self, invisible_walls):
        self.level = self.parent.parent.level
        for x, val in enumerate(self.level._grid):
            for y, val2 in enumerate(val):
                if val2 != None:
                    my_x, my_y, h = self.getWallPosition(x, y)
                    # prvi parni, drugi neparni
                    if my_x == None:
                        continue
                    
                    if val2.name == "ClosedDoor" and val2.name != self.parent.parent.old_level._grid[x][y].name:
                        if not (x,y) in self.old_invisible_walls:
                            self.dynamic_wall_dict[(my_x, my_y, h)].setScale(1)
                        else:
                            i = self.dynamic_wall_dict[(my_x, my_y, h)].scaleInterval(1, Vec3(1,1,1))
                            i.start()
                    elif val2.name == "OpenedDoor" and val2.name != self.parent.parent.old_level._grid[x][y].name:
                        if not (x,y) in self.old_invisible_walls:
                            self.dynamic_wall_dict[(my_x, my_y, h)].setScale(0.2,1,1)
                        else:
                            i = self.dynamic_wall_dict[(my_x, my_y, h)].scaleInterval(1, Vec3(0.2,1,1))
                            i.start() 
        self.old_invisible_walls = invisible_walls

    def setInvisibleTilesInThread(self):
        taskMgr.add(self.setInvisibleTiles, 'invis_tiles', extraArgs = [], taskChain = 'thread_1')
    
    def setInvisibleTiles(self):
        tile_dict = self.parent.parent.getInvisibleTiles()
        for invisible_tile in tile_dict:
            if self.old_tile_dict == None or tile_dict[invisible_tile] != self.old_tile_dict[invisible_tile]:
                if tile_dict[invisible_tile] == 0:                   
                    self.floor_tile_dict[invisible_tile].setColorScale(0.3,0.3,0.3,1)
                    self.markChunkDirty(invisible_tile[0], invisible_tile[1])
                else:                  
                    self.floor_tile_dict[invisible_tile].setColorScale(1,1,1,1)
                    self.markChunkDirty(invisible_tile[0], invisible_tile[1])            
        self.old_tile_dict = tile_dict
    
    def setInvisibleWallsInThread(self):
        taskMgr.add(self.setInvisibleWalls, 'invis_walls', extraArgs = [], taskChain = 'thread_1')
    
    def setInvisibleWalls(self):
        visible_wall_list = self.parent.parent.getInvisibleWalls()
        self.processLevel(visible_wall_list)
        new_list = []
        for l in visible_wall_list:
            x,y,h = self.getWallPosition(l[0], l[1])
            new_list.append((x,y,h))
        for wall in self.wall_dict:
            # If we have key in visible_wall_dict, the wall is visible
            if wall in new_list:
                self.wall_dict[wall].setColorScale(1,1,1,1)
            else:
                self.wall_dict[wall].setColorScale(0.3,0.3,0.3,1)
        for wall in self.dynamic_wall_dict:
            if wall in new_list:
                self.dynamic_wall_dict[wall].setColorScale(1,1,1,1)
            else:
                self.dynamic_wall_dict[wall].setColorScale(0.3,0.3,0.3,1)
        self.dirty_walls = 1
                
    
    def flattenTask(self, task):
        if self.pause_flatten_task:
            return task.cont
        
        if self.frames_counter < self.frames_between:
            self.frames_counter += 1
        
        if self.dirty_walls == 1:
            np = self.node_wall_original.copyTo(NodePath())
            np.clearModelNodes()
            np.flattenStrong()
            self.node_wall_usable.removeNode()
            self.node_wall_usable = np
            self.node_wall_usable.reparentTo(self.parent.level_node)
            #self.node_wall_usable.setShaderAuto()
            self.dirty_walls = 0
        
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