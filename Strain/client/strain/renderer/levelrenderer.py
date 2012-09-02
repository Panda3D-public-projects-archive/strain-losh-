from panda3d.core import *
import random

class LevelRenderer():
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node  
        
        self.wall_dict = {}
        self.door_dict = {}
        
        self.forcewall_tex_offset = 0
        
        self._initialized = 0
    
    def create(self, level, x, y, tile_size, zpos):
        self.node = self.parent_node.attachNewNode('LevelRendererNode')
        self.node_floor = self.node.attachNewNode('LevelRendererFloorNode')
        self.node_wall = self.node.attachNewNode('LevelRendererWallNode')        
        self.temp_node_floor = self.node_floor.attachNewNode('LevelRendererTempFloorNode')
        self.temp_node_wall = self.node_wall.attachNewNode('LevelRendererTempWallNode')
        self.ghost_node_wall = NodePath('LevelRendererGhostWallNode')
        self.node_door = self.node.attachNewNode('LevelRendererDoorNode') 
                        
        self.level = level
        self.maxX = x
        self.maxY = y        
        
        self.floor_tex_C = loader.loadTexture("tile3.png")
        #self.floor_tex_N = loader.loadTexture("floortile_N.png")
        
        self.forcewall_tex_C = loader.loadTexture("rnbw.png")
        
        self.floor_tex_C.setMagfilter(Texture.FTLinearMipmapLinear)
        self.floor_tex_C.setMinfilter(Texture.FTLinearMipmapLinear)
        #self.floor_tex_N.setMagfilter(Texture.FTLinearMipmapLinear)
        #self.floor_tex_N.setMinfilter(Texture.FTLinearMipmapLinear)        
        self.forcewall_tex_C.setMagfilter(Texture.FTLinearMipmapLinear)
        self.forcewall_tex_C.setMinfilter(Texture.FTLinearMipmapLinear)        
        
        self.texstage_normal = TextureStage('TextureStage_Normal')
        self.texstage_normal.setMode(TextureStage.MNormal)
        self.texstage_forcewall = TextureStage('TextureStage_ForceWall')        
                
        for x in xrange(0, self.maxX):
            for y in xrange(0, self.maxY):
                if self.level.getHeight( (x, y) ) == 0:
                    model = self.loadModel('FLOOR1', x, y, tile_size, zpos)
                    model.reparentTo(self.temp_node_floor)
                elif self.level.getHeight( (x, y) ) == 1:                    
                    model = self.loadModel('FLOOR1', x, y, tile_size, zpos)
                    model.reparentTo(self.temp_node_floor)
                    model = self.loadModel('CUBE1', x, y, tile_size, zpos)
                    model.reparentTo(self.temp_node_floor)                   
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )):
                        if i == 0:
                            model = self.loadModel('FLOOR1', x, y, tile_size, zpos)
                            model.reparentTo(self.temp_node_floor)                           
                        else:
                            model = self.loadModel('CUBE2', x, y, tile_size, zpos, i)
                            model.reparentTo(self.temp_node_floor)
        
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
                    model = self.loadWallModel(val2.name, my_x, my_y, h, tile_size, zpos)
                    if val2.name == 'ClosedDoor' or val2.name == 'OpenedDoor':
                        self.door_dict[(my_x, my_y, h)] = model
                        model.reparentTo(self.node_door)
                    else:
                        self.wall_dict[(my_x, my_y, h)] = model
                        model.reparentTo(self.ghost_node_wall)
        
        # Reparent all the models to main Level node
        self.redrawLights()
        self.temp_node_floor.clearModelNodes()
        self.temp_node_floor.flattenStrong()
        self.switchNodes()
        self.flattenNodes()
        
        # Add level task
        taskMgr.add(self.forcewallTask, 'ForceWall_offset_Task')
        
        # Initialize fow texture       
        self.initializeFowTexture(self.temp_node_floor)
        for child in self.ghost_node_wall.getChildren():
            child.setColorScale(0.3, 0.3, 0.3, 1.0)
        
        self._initialized = 1
    
    def switchNodes(self):
        self.temp_node_wall.removeNode() 
        self.temp_node_wall = self.ghost_node_wall.copyTo(self.node_wall)
    
    def initializeFowTexture(self, node):
        self.fow_node = node
        self.fow_coef = 16
        
        self.fowImage = PNMImage(self.maxX*self.fow_coef, self.maxY*self.fow_coef)
        self.fowImage.fill(.4)
        
        self.fowBrush = PNMBrush.makePixel((1, 1, 1, 1))
        #self.fowBrush = PNMBrush.makeSpot(VBase4D(1), int(self.fow_coef/2), fuzzy=False)
        self.fowPainter = PNMPainter(self.fowImage)
        self.fowPainter.setPen(self.fowBrush)
        self.fowTexture = Texture()
        self.fowTexture.load(self.fowImage)
            
        minb, maxb = self.fow_node.getTightBounds()
        dim = maxb-minb

        maxDim = max(dim[0],dim[1])
        scale = 1./maxDim
        center = (minb+maxb)*.5
        self.fowTextureStage = TextureStage('')
        self.fow_node.setTexGen(self.fowTextureStage, RenderAttrib.MWorldPosition)
        self.fow_node.setTexScale(self.fowTextureStage, 1./dim[0], 1./dim[1])
        #self.fow_node.setTexOffset(self.fowTextureStage, -.5-center[0]*scale, -.5-center[1]*scale)  
        
        self.fow_node.setTexture(self.fowTextureStage, self.fowTexture)
        """
        cm = CardMaker('')
        cm.setFrame(-.8,-.2,0,.6)
        card = base.a2dBottomRight.attachNewNode(cm.generate())
        card.setTexture(self.fowTexture)
        """
    
    def updateLevelLos(self, tile_dict, wall_dict):
        # Reset
        self.fowImage.fill(.3)
        for child in self.ghost_node_wall.getChildren():
            child.setColorScale(0.3, 0.3, 0.3, 1.0)
        
        for child in self.node_door.getChildren():
            child.setColorScale(0.3, 0.3, 0.3, 1.0)
        
        # Paint floor FoW
        for invisible_tile in tile_dict:
            if tile_dict[invisible_tile] != 0:                  
                self.fowPainter.drawRectangle(invisible_tile[0]*self.fow_coef, (self.maxY-1-invisible_tile[1])*self.fow_coef, (invisible_tile[0]+1)*self.fow_coef-1, (self.maxY-invisible_tile[1])*self.fow_coef-1)                                                                                                                              

        # Paint wall FoW
        
        for wall in wall_dict:
            x,y,h = self.getWallPosition(wall[0], wall[1])
            if self.wall_dict.has_key((x, y, h)):
                n = self.wall_dict[(x, y, h)]                
                n.setColorScale(1,1,1,1) 
            elif self.door_dict.has_key((x, y, h)):
                n = self.door_dict[(x, y, h)]                
                n.setColorScale(1,1,1,1)
        
        self.fowTexture.load(self.fowImage)          
       
    def flattenNodes(self):
        self.temp_node_wall.clearModelNodes()
        self.temp_node_wall.flattenStrong() 
    
    def loadModel(self, type, x, y, tile_size, zpos, i=None):
        if type == 'FLOOR1':
            model = loader.loadModel('floortile')
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setTexture(self.floor_tex_C)
            #model.setTexture(self.texstage_normal, self.floor_tex_N)
        elif type == 'CUBE1':
            model = loader.loadModel('cube')
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
        elif type == 'CUBE2':    
            model = loader.loadModel('cube')
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, (i-1)*tile_size+zpos)
        return model
    
    def loadWallModel(self, type, x, y, h, tile_size, zpos):
        if type == 'Wall1' or type == 'Wall2' or type == 'HalfWall' or type == 'Ruin':
            model = loader.loadModel("WallA")
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setH(h)
        elif type == 'ClosedDoor':
            model = loader.loadModel("DoorA")
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setH(h)
            frame = model.find("**/Frame*")
            frame.setColor(1, 0, 0, 0)
            door = model.find("**/Door*")
            door.setColor(0.7,0.2,0.2,0.0)
        elif type == 'OpenedDoor':
            model = loader.loadModel("DoorA")
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setH(h)
            frame = model.find("**/Frame*")
            frame.setColor(1, 0, 0, 0)
            door = model.find("**/Door*")
            door.setColor(0.7,0.2,0.2,0.0) 
            door.setPos(model, 0.5, 0, -0.72)           
        elif type == 'ForceField':
            model = loader.loadModel("wall_fs")
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setH(h)                            
            model.setTexture(self.texstage_forcewall, self.forcewall_tex_C)
            model.setTransparency(TransparencyAttrib.MAlpha)
        return model

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
    
    def redrawLights(self):
        #shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        #render.setAttrib(shade)
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(0.7, 0.7, 0.7, 1.0))
        self.dlnp1 = self.node.attachNewNode(dlight1)
        self.dlnp1.setHpr(0, -50, 0)
        self.node.setLight(self.dlnp1)

        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        self.alnp = self.node.attachNewNode(alight)
        self.node.setLight(self.alnp)
    
    def forcewallTask(self, task):
        dt = globalClock.getDt()
        self.forcewall_tex_offset += dt * 0.5
        self.node.setTexOffset(self.texstage_forcewall, 0, self.forcewall_tex_offset)
        return task.cont
    
    def cleanup(self):
        if self._initialized == 1:
            taskMgr.remove('ForceWall_offset_Task')
            self.node.setLightOff(self.alnp)
            self.node.setLightOff(self.dlnp1)
            self.ghost_node_wall.removeNode()
            self.node.removeNode()
            self.door_dict = {}
            self.wall_dict = {}
            self._initialized = 0
        
    def __del__(self):
        print("Level deleted!")
