from panda3d.core import *

class LevelRenderer():
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.node = self.parent_node.attachNewNode('LevelRendererNode')
        
        # Create nodepath collections to hold wall and floor nodes
        self.nodecoll_floor = NodePathCollection()
        self.nodecoll_wall = NodePathCollection()
    
    def create(self, level, x, y, tile_size, zpos):        
        self.level = level
        self.maxX = x
        self.maxY = y        
        
        self.floor_tex_C = loader.loadTexture("floortile_C.png")
        self.floor_tex_N = loader.loadTexture("floortile_N.png")
        
        self.floor_tex_C.setMagfilter(Texture.FTLinearMipmapLinear)
        self.floor_tex_C.setMinfilter(Texture.FTLinearMipmapLinear)
        self.floor_tex_N.setMagfilter(Texture.FTLinearMipmapLinear)
        self.floor_tex_N.setMinfilter(Texture.FTLinearMipmapLinear)        
        
        self.texstage_normal = TextureStage('TextureStage_Normal')
        self.texstage_normal.setMode(TextureStage.MNormal)
                
        for x in xrange(0, self.maxX):
            for y in xrange(0, self.maxY):
                if self.level.getHeight( (x, y) ) == 0:
                    self.nodecoll_floor.append(self.loadModel('FLOOR1', x, y, tile_size, zpos))
                elif self.level.getHeight( (x, y) ) == 1:                    
                    self.nodecoll_floor.append(self.loadModel('FLOOR1', x, y, tile_size, zpos))
                    self.nodecoll_floor.append(self.loadModel('CUBE1', x, y, tile_size, zpos))
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )):
                        if i == 0:
                            self.nodecoll_floor.append(self.loadModel('FLOOR1', x, y, tile_size, zpos))
                        else:
                            self.nodecoll_floor.append(self.loadModel('CUBE2', x, y, tile_size, zpos, i))
        
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
                    self.nodecoll_wall.append(self.loadWallModel(val2.name, my_x, my_y, h, tile_size, zpos)) 
        self.nodecoll_floor.reparentTo(self.node)
        self.nodecoll_wall.reparentTo(self.node)
        self.redrawLights()
        self.node.clearModelNodes()
        self.node.flattenStrong()
    
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
            #model.setTexture(self.ts_fs, self.tex_fs)
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
    
    def texTask(self, task):
        dt = globalClock.getDt()
        self.tex_offset += dt * 0.5
        self.node.setTexOffset(self.level_mesh.ts_fs, 0, self.tex_offset)
        return task.cont
    
    def cleanup(self):
        #taskMgr.remove('texTask')
        self.node.removeNode()