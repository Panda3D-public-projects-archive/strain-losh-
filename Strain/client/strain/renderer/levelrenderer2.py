from panda3d.core import *

class LevelRenderer():
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.node = None
    
    def redraw(self, level, x, y, tile_size, zpos):
        if self.node != None:
            self.node.removeNode()
        self.node = self.parent_node.attachNewNode('LevelRendererNode')
        
        self.level = level
        self.maxX = x
        self.maxY = y        
        
        #self.floor_tile_tex = loader.loadTexture("LowPolyPlane_diffuse.png")
        self.tex1 = loader.loadTexture("tile1.png")
        self.tex2 = loader.loadTexture("tile2.png")
        self.tex3 = loader.loadTexture("tile3.png")
        self.tex_fs = loader.loadTexture("rnbw.png")
        self.ts_fs = TextureStage('ts_fs')
        
        self.tex1.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex1.setMinfilter(Texture.FTLinearMipmapLinear)
        self.tex2.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex2.setMinfilter(Texture.FTLinearMipmapLinear)
        self.tex3.setMagfilter(Texture.FTLinearMipmapLinear)
        self.tex3.setMinfilter(Texture.FTLinearMipmapLinear)
        
        #self.floor_tile_tex.setMagfilter(Texture.FTLinearMipmapLinear)
        #self.floor_tile_tex.setMinfilter(Texture.FTLinearMipmapLinear)        
        
        ts = TextureStage('ts')
        for x in xrange(0, self.maxX):
            for y in xrange(0, self.maxY):
                if self.level.getHeight( (x, y) ) == 0:
                    model = loader.loadModel('flattile')
                    model.setScale(tile_size)
                    model.setPos(x*tile_size, y*tile_size, zpos)
                    #model.setTexture(self.floor_tile_tex)
                elif self.level.getHeight( (x, y) ) == 1:                    
                    model = loader.loadModel('halfcube')
                    model.setScale(tile_size)
                    model.setPos(x*tile_size, y*tile_size, 0)
                    model = loader.loadModel('halfcube')
                    model.setScale(tile_size)
                    model.setPos(x*tile_size, y*tile_size, zpos)
                    model.setTexture(ts, self.tex1) 
                else:
                    for i in xrange(0, self.level.getHeight( (x, y) )):
                        if i == 0:
                            model = loader.loadModel('flattile')
                            model.setScale(tile_size)
                            model.setPos(x*tile_size, y*tile_size, zpos)
                        else:
                            model = loader.loadModel('cube')
                            model.setScale(tile_size)
                            model.setPos(x*tile_size, y*tile_size, (i-1)*tile_size+zpos)
                            model.setTexture(ts, self.tex2)
                model.reparentTo(self.node)
        
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
                        model.setScale(tile_size)
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)                 
                    elif val2.name == "Wall2":
                        model = loader.loadModel("wall2")
                        model.setScale(tile_size)
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)
                        model.setColor(0,1,0,1)
                    elif val2.name == "HalfWall":
                        model = loader.loadModel("wall2")
                        model.setScale(tile_size)
                        model.flattenLight()
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)
                        model.setColor(0,0,0,1)
                        model.setScale(1,1,0.4)
                    elif val2.name == "Ruin":
                        model = loader.loadModel("wall2")
                        model.setScale(tile_size)
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)
                        model.setColor(0.5,0.8,1,0.6)
                        model.setTransparency(TransparencyAttrib.MAlpha)
                        model.reparentTo(self.node_forcewall_usable)
                        #s = Sequence(LerpColorInterval(model, 1, (0.13,0.56,0.78,0.6)),
                        #            LerpColorInterval(model, 1, (0.5,0.8,1,0.6)),
                        #            )  
                        #s.loop()  
                    elif val2.name == "ClosedDoor":
                        model = loader.loadModel("door")
                        model.setScale(tile_size)
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)
                        model.setColor(1,0.0,0,0.0)
                    elif val2.name == "OpenedDoor":
                        model = loader.loadModel("door")
                        model.setScale(tile_size)
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)
                        model.setScale(0.2,1,1)
                        model.setColor(0.7,0.2,0.2,0.0)
                    elif val2.name == "ForceField":
                        model = loader.loadModel("wall_fs")
                        model.setScale(tile_size)
                        model.setPos(my_x*tile_size, my_y*tile_size, zpos)
                        model.setH(h)                            
                        model.setTexture(self.ts_fs, self.tex_fs)
                        model.setTransparency(TransparencyAttrib.MAlpha)
                    model.reparentTo(self.node)
        #taskMgr.add(self.texTask,'texTask')
        self.redrawLights()
        #self.node.clearModelNodes()
        #self.node.flattenStrong()
    
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