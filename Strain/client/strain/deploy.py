from panda3d.core import *

class Deploy():
    def __init__(self, parent, username, user_id):
        self.parent = parent
        
        # Initialize RenderManager class which handles all of the rendering
        from strain.renderer.RenderManager import RenderManager
        self.parent.render_manager = RenderManager(self.parent)
        self.parent.render_manager.renderDeployLevel(self.parent.local_engine.level)
        
        # Initialize CameraManager class
        from strain.renderer.CameraManager import CameraManager
        self.parent.camera_manager = CameraManager(self.parent, 20, 20)
                
        self.parent.deploy_dict = {}
        for idx, l in enumerate(self.parent.level._deploy):
            for idy, val in enumerate(l):
                if str(val) == self.parent.player_id:
                    self.parent.deploy_dict[(idx, idy)] = None
        
        self.parent.sgm.showDeployTiles()
        self.parent.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, utils.GROUND_LEVEL)) 
        self.parent.accept('mouse1', self.parent.deployUnit)
        self.parent.accept('g', self.parent.endDeploy)
        self.parent.deploySquadScreen()
    
    def cleanup(self):
        self.parent.sgm.clearLights()
        self.parent.sgm.node.removeNode()
        taskMgr.remove("texTask")
        taskMgr.remove("camera_update_task")
        taskMgr.remove("flatten_task")
        self.parent.deploy_unit_np.removeNode()
        for child in self.parent.sgm.tile_cards_np.getChildren():
            child.detachNode()
        self.parent.sgm.deleteLevel()            
        del self.parent.sgm
        self.parent.camera.node.removeNode()
        self.parent.camera.ignore('w')
        self.parent.camera.ignore('w-up')
        self.parent.camera.ignore('s')
        self.parent.camera.ignore('s-up')                   
        self.parent.camera.ignore('a')
        self.parent.camera.ignore('a-up')
        self.parent.camera.ignore('d')
        self.parent.camera.ignore('d-up')
        self.parent.camera.ignore('wheel_down')
        self.parent.camera.ignore('wheel_up')
        self.parent.camera.ignore('mouse3')
        self.parent.camera.ignore('mouse3-up')
        self.parent.camera.ignore('space')
        self.parent.camera.ignore('f5')        
        del self.parent.camera
        base.win.removeDisplayRegion(self.parent.dr2)
    
    def deploySquadScreen(self):
        self.dr2 = base.win.makeDisplayRegion(0.0, 0.5, 0.65, 1.0)
        self.dr2.setClearColor(VBase4(0, 0, 0, 0.3))
        self.dr2.setClearColorActive(False)
        self.dr2.setClearDepthActive(True)

        self.render2 = NodePath('render2')
        self.cam2 = self.render2.attachNewNode(Camera('cam2'))
        self.cam2.node().getLens().setAspectRatio(1.8)
        self.dr2.setCamera(self.cam2)
        
        self.floor2np = self.render2.attachNewNode('floor2')
        tex = loader.loadTexture('scifi_floor.png')  
        tex.setMagfilter(Texture.FTLinearMipmapLinear)
        tex.setMinfilter(Texture.FTLinearMipmapLinear)
        cm = CardMaker('cm_floor')
        cm.setFrame(0, 1, 0, 1)        
        for x in xrange(10):
            for y in xrange(10):        
                cpos = self.floor2np.attachNewNode(cm.generate())
                cpos.setPos(x-5, y-5, 0)
                cpos.setP(-90)
                cpos.setTexture(tex)
        self.floor2np.flattenStrong()
        self.cam2.setPos(0, -10, 5)
        self.cam2.setP(-20)
        
        for idx, u in enumerate(self.deploy_queue):
            unit = utils.loadUnit('marine', u.lower(), self.player_id)
            unit.reparentTo(self.render2)
            unit.setScale(1)
            if idx == 0:
                unit.setPos(0, 0, 0)
            elif idx == 1:
                unit.setPos(1.5, 1.5, 0)
                unit.setH(-20)
            elif idx == 2:
                unit.setPos(-1.5, 1.8, 0)
                unit.setH(-10)
            elif idx == 3:
                unit.setPos(2.2, 2.5, 0)
                unit.setH(-20)
            elif idx == 4:
                unit.setPos(-1.4, 3.5, 0)
            elif idx == 5:
                unit.setPos(3.5, -0.5, 0)
                unit.setH(-35)
            elif idx == 6:
                unit.setPos(-2.6, 2.5, 0)
                unit.setH(30)
            elif idx == 7:
                unit.setPos(-4.5, 0, 0)
                unit.setH(40)
            unit.setTag('id', str(idx))
            unit.setTag('type', u.lower())
        
        self.altalight = AmbientLight("alight")
        self.altalight.setColor(VBase4(0.2, 0.2, 0.2, 1.0))
        self.altalnp = self.render2.attachNewNode(self.altalight)
        self.render2.setLight(self.altalnp)
        
        self.altalight2 = AmbientLight("alight2")
        self.altalight2.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        self.altalnp2 = self.render2.attachNewNode(self.altalight2)
        

        self.altslight = Spotlight('slight')
        self.altslight.setColor(VBase4(0.6, 0.6, 0.6, 1))
        self.altslnp = self.render2.attachNewNode(self.altslight)
        self.altslnp.setPos(5, 1, 15)
        self.altslnp.lookAt(0, 0, 0)
        self.render2.setLight(self.altslnp) 
        
        self.render2.setShaderAuto()
        
        self.deploy_index = 0
        self.deploy_unit_np = render.attachNewNode('deploy_unit_np')
        self.getDeployee()
        
    def getDeployee(self):
        if len(self.deploy_queue) > self.deploy_index:
            self.deploy_unit = self.render2.find('=id='+str(self.deploy_index))
            self.deploy_unit.setLight(self.altalnp2)
            self.deploy_index += 1
        else:
            self.deploy_unit = None
    
    def deployUnit(self):
        if self.deploy_unit != None:
            if base.mouseWatcherNode.hasMouse():
                mpos = base.mouseWatcherNode.getMouse()
                pos3d = Point3()
                nearPoint = Point3()
                farPoint = Point3()
                base.camLens.extrude(mpos, nearPoint, farPoint)
                if self.plane.intersectsLine(pos3d, render.getRelativePoint(camera, nearPoint), render.getRelativePoint(camera, farPoint)):
                    pos = (int(pos3d.getX()), int(pos3d.getY()))
                    if self.deploy_dict.has_key(pos) and self.deploy_dict[pos] == None:
                        unit = self.deploy_unit
                        unit.reparentTo(self.deploy_unit_np)                        
                        unit.setScale(0.3)
                        unit.setPos(int(pos3d.getX()) + 0.5, int(pos3d.getY()) + 0.5, utils.GROUND_LEVEL)
                        self.deploy_dict[pos] = unit.getTag('type') 
                        self.deploy_unit.setLightOff()
                        self.getDeployee()
        
        
    def endDeploy(self):
        if len(self.deploy_queue) > self.deploy_index:
            print "You must deploy all units"
        else:
            army_list = []
            for key in self.deploy_dict:
                if self.deploy_dict[key] != None:
                    tup = (key[0], key[1], 'marine_'+self.deploy_dict[key])
                    army_list.append(tup)
            ClientMsg.armyList(army_list)