from panda3d.core import *
import random

class LevelRenderer():
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.node = self.parent_node.attachNewNode('LevelRendererNode')
        self.node_floor = self.node.attachNewNode('LevelRendererFloorNode')
        self.node_wall = self.node.attachNewNode('LevelRendererWallNode')        
        self.temp_node_floor = self.node_floor.attachNewNode('LevelRendererTempFloorNode')
        self.temp_node_wall = self.node_wall.attachNewNode('LevelRendererTempWallNode')
        self.ghost_node_floor = NodePath('LevelRendererGhostFloorNode')
        self.ghost_node_wall = NodePath('LevelRendererGhostWallNode')
        
        self.forcewall_tex_offset = 0
    
    def create(self, level, x, y, tile_size, zpos):        
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
                    model.reparentTo(self.ghost_node_floor)
                    model.setTag("pos", str(x)+"_"+str(y))
                elif self.level.getHeight( (x, y) ) == 1:                    
                    model = self.loadModel('FLOOR1', x, y, tile_size, zpos)
                    model.reparentTo(self.ghost_node_floor)
                    model.setTag("pos", str(x)+"_"+str(y))
                    model = self.loadModel('CUBE1', x, y, tile_size, zpos)
                    model.reparentTo(self.ghost_node_floor)                   
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )):
                        if i == 0:
                            model = self.loadModel('FLOOR1', x, y, tile_size, zpos)
                            model.reparentTo(self.ghost_node_floor)
                            model.setTag("pos", str(x)+"_"+str(y))                            
                        else:
                            model = self.loadModel('CUBE2', x, y, tile_size, zpos, i)
                            model.reparentTo(self.ghost_node_floor)
        
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
                    model.reparentTo(self.ghost_node_wall)
                    model.setTag("pos", str(my_x)+"_"+str(my_y)+"_"+str(h))  
        
        # Reparent all the models to main Level node
        self.redrawLights()
        self.switchNodes()
        self.flattenNodes()
        
        # Add level task
        taskMgr.add(self.forcewallTask, 'ForceWall_offset_Task')
    
    def switchNodes(self):
        self.temp_node_floor.removeNode()
        self.temp_node_wall.removeNode() 
        self.temp_node_floor = self.ghost_node_floor.copyTo(self.node_floor)
        self.temp_node_wall = self.ghost_node_wall.copyTo(self.node_wall)
    
    def updateLevelLos(self, tile_dict, wall_dict):
        for invisible_tile in tile_dict:
            x = str(invisible_tile[0])
            y = str(invisible_tile[1])
            if tile_dict[invisible_tile] == 0:
                n = self.temp_node_floor.find("**/=pos="+x+"_"+y)                   
                n.setColorScale(0.3,0.3,0.3,1)
            else:                  
                n = self.temp_node_floor.find("**/=pos="+x+"_"+y)                   
                n.setColorScale(1,1,1,1)
        for child in self.temp_node_wall.getChildren():
            child.setColorScale(0.3,0.3,0.3,1)
        for wall in wall_dict:
            x,y,h = self.getWallPosition(wall[0], wall[1])
            x = str(x)
            y = str(y)
            h = str(h)
            n = self.temp_node_wall.find("**/=pos="+x+"_"+y+"_"+h)                   
            n.setColorScale(1,1,1,1)           
       
    def flattenNodes(self):        
        for child in self.temp_node_floor.getChildren():
            child.clearTag('pos') 
        for child in self.temp_node_wall.getChildren():
            child.clearTag('pos')        
        self.temp_node_floor.clearModelNodes()
        self.temp_node_floor.flattenStrong()
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
            model = loader.loadModel('halfcube')
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
        elif type == 'CUBE2':    
            model = loader.loadModel('cube')
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, (i-1)*tile_size+zpos)
        return model
    
    def loadWallModel(self, type, x, y, h, tile_size, zpos):
        if type == 'Wall1' or type == 'Wall2' or type == 'HalfWall' or type == 'Ruin':
            model = loader.loadModel("wall")
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setH(h)
        elif type == 'OpenedDoor' or type == 'ClosedDoor':
            model = loader.loadModel("door")
            model.setScale(tile_size)
            model.setPos(x*tile_size, y*tile_size, zpos)
            model.setH(h)
            model.setScale(0.2,1,1)
            model.setColor(0.7,0.2,0.2,0.0)
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
        dlight1.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        self.dlnp1 = self.node.attachNewNode(dlight1)
        self.dlnp1.setHpr(0, -80, 0)
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
        taskMgr.remove('ForceWall_offset_Task')
        self.node.removeNode()