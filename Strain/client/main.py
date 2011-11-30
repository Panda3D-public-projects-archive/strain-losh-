#############################################################################
# IMPORTS
#############################################################################

# python imports
import os
import logging
import cPickle as pickle
from random import randint

# panda3D imports
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, WindowProperties, Texture, OrthographicLens, PerspectiveLens#@UnresolvedImport
from panda3d.core import TextNode, NodePath, Point2, Point3, VBase4, GeomNode, Vec3, Vec4#@UnresolvedImport
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight#@UnresolvedImport
from panda3d.core import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode#@UnresolvedImport
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, Func, Interval, Wait#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectLabel, DGG
from direct.gui.OnscreenText import OnscreenText

# strain related imports
from strain.client_messaging import *
#from strain.camera import Camera
from strain.cam2 import Camera
from strain.voxelgen import VoxelGenerator
from strain.unitmodel import UnitModel
from strain.interface import Interface
import strain.utils as utils

#############################################################################
# GLOBALS
#############################################################################

loadPrcFile(os.path.join("config","config.prc"))

"""
loadPrcFileData("", "model-path "+"./data/models")
loadPrcFileData("", "model-path "+"./data/sounds")
loadPrcFileData("", "model-path "+"./data/textures")

# config dictionary variable
config = {} 
cfile = open("data/config/user.cfg", "r")
while 1:
    string = cfile.readline()
    if (string == ""):
        break
    elif (string[0] == "#"):
        continue
    part = string.rsplit("=")
    config[part[0].strip()] = part[1].strip()
cfile.close()

loadPrcFileData("", "fullscreen "+config["fullscreen"])
loadPrcFileData("", "win-size "+config['resx']+" "+config["resy"])
loadPrcFileData("", "show-frame-rate-meter "+config["showfps"])
loadPrcFileData("", "model-cache-dir ./tmp")
loadPrcFileData("", "window-title Strain")
if config["scene-explorer"] == "1":
    loadPrcFileData("", "want-directtools #t")
    loadPrcFileData("", "want-tk #t")
"""
#############################################################################
# CLASSES
#############################################################################

#========================================================================
#
class App():
    def __init__(self):
        #setup logger
        self.logger = logging.getLogger('GraphicsLog')
        hdlr = logging.FileHandler('Graphics.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.DEBUG)
        
        #setup screen
        self.screen = Screen(self, (800,600))
        
        #setup FSM
        self.fsm = AppFSM(self, 'AppFSM')
        
        self.startLogin()
    
    def startLogin(self):
        #go to login screen
        self.fsm.request('LoginScreen')
        
    def startClient(self):
        #start client
        self.fsm.request('Client')
#========================================================================
#
class AppFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

    def enterLoginScreen(self):
        base.win.setClearColor(VBase4(0, 0, 0, 0))
        self.parent.login = LoginScreen(self.parent)
    
    def exitLoginScreen(self):
        self.parent.login.parent = None
        self.parent.login.label_username.remove()
        self.parent.login.label_password.remove()
        self.parent.login.entry_username.remove()          
        self.parent.login.entry_password.remove()        
        self.parent.login.button.remove()
        self.parent.login.commoner1.delete()
        self.parent.login.commoner2.delete()
        self.parent.login.commander.delete()
        self.parent.login.heavy.delete()
        self.parent.login.assault.delete()
        self.parent.login.assault2.delete()
        self.parent.login.assault3.delete() 
        self.parent.login.textObject.remove()       
        del self.parent.login

    def enterClient(self):
        base.win.setClearColor(VBase4(0.5, 0.5, 0.5, 0))
        self.parent.client = Client(self.parent, self.parent.player)
        
    def exitClient(self):
        None
        

#========================================================================
#
class LoginScreen():
    def __init__(self, parent):
        self.parent = parent
        font = loader.loadFont('frizqt__.ttf')
        self.label_username = DirectLabel(text = "Username:", scale=.05, frameColor=(0,0,0,0), text_font=font, text_align=TextNode.ARight, text_fg=(1,1,1,1))
        self.label_password = DirectLabel(text = "Password:", scale=.05, frameColor=(0,0,0,0), text_font=font, text_align=TextNode.ARight, text_fg=(1,1,1,1))
        self.button = DirectButton(text = ("Login"),scale=.05,command=self.loginButPressed, text_font=font, text_align=TextNode.ACenter)
        self.entry_username = DirectEntry(scale=.05,initialText="", numLines = 1,focus=1,command=self.loginButPressed, text_font=font)
        self.entry_password = DirectEntry(scale=.05,initialText="", numLines = 1,command=self.loginButPressed, text_font=font)
        self.label_username.reparentTo(aspect2d)
        self.label_username.setPos(-0.2, 0, -0.4)
        self.label_password.reparentTo(aspect2d)
        self.label_password.setPos(-0.2, 0, -0.5)        
        self.entry_username.reparentTo(aspect2d)
        self.entry_username.setPos(-0.1, 0, -0.4)    
        self.entry_password.reparentTo(aspect2d)
        self.entry_password.setPos(-0.1, 0, -0.5)
        self.button.reparentTo(aspect2d)
        self.button.setPos(0, 0, -0.6) 
        
        ground_level = -1.6
        self.commoner1 = utils.loadUnit('common')
        self.commoner1.setPos(-3, 25, ground_level)
        self.commoner1.loop('idle_combat01')
        self.commoner2 = utils.loadUnit('common')
        self.commoner2.setPos(-4.5, 23.5, ground_level)
        self.commoner2.loop('idle_combat02')           
        self.heavy = utils.loadUnit('heavy')
        self.heavy.setPos(-2, 27, ground_level)
        self.heavy.loop('idle_stand03')             
        self.commander = utils.loadUnit('commander')
        self.commander.setPos(0, 20, ground_level)
        self.commander.loop('idle_stand02') 
        self.assault = utils.loadUnit('assault')
        self.assault.setPos(4, 25, ground_level)
        self.assault.loop('idle_stand01')
        self.assault2 = utils.loadUnit('assault')
        self.assault2.setPos(2.5, 23, ground_level)
        self.assault2.loop('idle_stand02')  
        self.assault3 = utils.loadUnit('assault')
        self.assault3.setPos(6, 23, ground_level)
        self.assault3.loop('idle_stand03')  
        
        self.textObject = OnscreenText(text = 'STRAIN', pos = (0, 0.4), scale = 0.2, font=font, fg = (1,0,0,1))
    
    def loginButPressed(self, text=None):
        self.parent.player = self.entry_username.get()
        if self.parent.player != "ultramarines" and self.parent.player != "blood angels":
            self.parent.player = "blood angels"
        self.parent.startClient()
#========================================================================
#
class SceneGraph():
    def __init__(self, parent):
        self.parent = parent
        
        # Main node in a scene graph. Everything should be reparented to this node or another node under this node
        # This node is reparented to render
        self.node = render.attachNewNode("master")
        
        # Set up flag dictionary
        self.comp_inited = {}
        self.comp_inited['level'] = False
        self.comp_inited['lights'] = False
        self.comp_inited['units'] = False
        self.comp_inited['alt_render'] = False
        
        # Set up dictionary and list for unit nodepaths
        self.unit_np_dict = {}
        self.unit_np_list = []
        
        self.off_model = None
        
        self.turn_np = NodePath("turn_arrows_np")
        self.turn_np.reparentTo(render)
        self.dummy_turn_pos_node = NodePath("dummy_turn_pos_node")
        self.dummy_turn_dest_node = NodePath("dummy_turn_dest_node")        
        self.unit_move_destination = None
        self.unit_move_orientation = utils.HEADING_NONE
        self.move_timer = 0
        self.movetext_np = None
        
        # Create main update task
        taskMgr.add(self.animTask, "anim_task")        
        
        print "base.win.getGsg().getMaxTextureStages() = "+str(base.win.getGsg().getMaxTextureStages())
    
    def loadLevel(self, level):
        if self.comp_inited['level']:
            return
        
        levelMesh = VoxelGenerator('level', 1, 0.3)
        for x in xrange(0, level['maxX']):
            for y in xrange(0, level['maxY']):
                for i in xrange(0, level['_level_data'][x][y]+1):
                    if i == 0:
                        id = 1
                    else:
                        id = 2 
                    levelMesh.makeLeftFace(x, y, i, id)
                    levelMesh.makeRightFace(x, y, i, id)
                    levelMesh.makeBackFace(x, y, i, id)
                    levelMesh.makeFrontFace(x, y, i, id)
                    levelMesh.makeBottomFace(x, y, i, id) 
                    levelMesh.makeTopFace(x, y, i, id)

        self.level_node = self.node.attachNewNode(levelMesh.getGeomNode())
        self.level_node.setTag('type', 'level')
        t = loader.loadTexture('tex3.png')
        t.setMagfilter(Texture.FTLinearMipmapLinear)
        t.setMinfilter(Texture.FTLinearMipmapLinear)
        self.level_node.setTexture(t)
        self.comp_inited['level'] = True
        
        for i in xrange(0, level['maxX']):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.level_node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i+0.3, -0.3, 0.5)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
        for i in xrange(0, level['maxY']):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.level_node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(-0.3, i+0.3, 0.5)
            tnp.setBillboardPointEye()
            tnp.setLightOff()         
        
    def deleteLevel(self):
        if self.comp_inited['level'] == False:
            return
        
        self.level_node.removeNode()
        self.comp_inited['level'] = False
    
    def initLights(self):
        if self.comp_inited['lights']:
            return
        
        shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        render.setAttrib(shade)
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(1.0, 1.0, 1.0, 1.0))
        dlnp1 = render.attachNewNode(dlight1)
        dlnp1.setPos(10, 10, 5)
        dlnp1.lookAt(10, 10, 0.3)
        #a = loader.loadModel("camera")
        #a.reparentTo(dlnp1)
        #a.setScale(0.4, 0.4, 0.4)
        render.setLight(dlnp1)
        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.7, 0.7, 0.7, 1.0))
        alnp = render.attachNewNode(alight)
        alnp.setPos(10, 10, 2)
        render.setLight(alnp) 
        self.comp_inited['lights'] = True
        
    def initCollisions(self):
        self.coll_trav = CollisionTraverser()
        self.coll_queue = CollisionHandlerQueue()
        self.coll_node = CollisionNode("mouse_ray")
        self.coll_nodepath = base.camera.attachNewNode(self.coll_node)
        self.coll_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.coll_ray = CollisionRay()
        self.coll_node.addSolid(self.coll_ray)
        self.coll_trav.addCollider(self.coll_nodepath, self.coll_queue)
    
    def loadUnits(self):
        if self.comp_inited['units']:
            return
        
        self.unit_node = self.node.attachNewNode('unit_node')
        self.unit_np_list = [[None] * self.parent.level['maxY'] for i in xrange(self.parent.level['maxX'])]
                    
        for unit in self.parent.units.itervalues():
            unit_model = self.loadUnit(unit)
            self.showUnit(unit_model)
                        
        self.comp_inited['units'] = True  
        
    def loadUnit(self, unit):
        um = UnitModel(self, unit['id'])
        # Keep unit nodepath in dictionary of all unit nodepaths
        self.unit_np_dict[unit['id']] = um
        # Keep unit nodepath in list corresponding to level size
        # This will be dinamically altered when units change position
        self.unit_np_list[int(unit['pos'][0])][int(unit['pos'][1])] = um
        return um
    
    def showUnit(self, unit_model):
        unit_model.node.reparentTo(self.unit_node)
        
    def hideUnit(self, unit_id):
        unit_model = self.unit_np_dict[unit_id] 
        cd = self.parent.getCoordsByUnit(unit_id)       
        self.parent.units.pop(unit_id)
        self.unit_np_dict.pop(unit_id)
        self.unit_np_list[int(cd.getX())][int(cd.getY())] = None
        unit_model.node.remove()
        del unit_model
    
    def deleteUnits(self):
        if self.comp_inited['units'] == False:
            return
        
        self.unit_node.removeNode()
        self.unit_np_list = []
        self.unit_np_dict = {}
        self.comp_inited['units'] = False
          
    
    def initAltRender(self):
        """Initializes off screen buffer used to render models and animations for unit portraits."""
        if self.comp_inited['alt_render']:
            return
        
        self.alt_buffer = base.win.makeTextureBuffer("texbuf", 256, 256)
        self.alt_render = NodePath("offrender")
        self.alt_cam = base.makeCamera(self.alt_buffer)
        self.alt_cam.reparentTo(self.alt_render)        
        self.alt_cam.setPos(0,0,0)
        #lens = PerspectiveLens()#OrthographicLens()
        #lens.setFilmSize(20*.5, 15*.5) # or whatever is appropriate for your scene
        #self.alt_cam.node().setLens(lens)
        #base.cam.node().getLens().setNear(0.1)
        #base.cam.node().getLens().setFar(32*1.5)
        #lens.setFov(20)
        self.alt_render.setLightOff()
        self.alt_render.setFogOff() 
        self.parent.interface.unit_card.setTexture(self.alt_buffer.getTexture())  
        self.comp_inited['alt_render'] = True
    
    def clearAltRenderModel(self):
        if not self.comp_inited['alt_render']:
            return
        
        if self.off_model:
            self.off_model.cleanup()
            self.off_model.remove()
        
        
    def loadAltRenderModel(self, unit_id):
        if not self.comp_inited['alt_render']:
            return
        self.off_model = UnitModel(self, unit_id, off=True)
        self.off_model.reparentTo(self.alt_render)
        self.off_model.model.play('idle_stand01')
        
    def showUnitAvailMove(self, unit_id):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        self.hideUnitAvailMove()
        unit = self.parent.units[unit_id]
        if unit:
            self.parent.units[unit_id]['move_dict'] = self.parent.getMoveDict(unit_id)
            move_dict = unit['move_dict']
            self.movetext_np = NodePath("movetext_np")
            for tile in move_dict:
                text = TextNode('node name')
                text.setText( "%s" % move_dict[tile])
                textNodePath = self.movetext_np.attachNewNode(text)
                textNodePath.setColor(0, 0, 0)
                textNodePath.setScale(0.4, 0.4, 0.4)
                textNodePath.setPos(tile[0]+0.2, tile[1]+0.2, 0.5)
                textNodePath.lookAt(tile[0]+0.2, tile[1]+0.2, -100)
            self.movetext_np.flattenStrong()
            self.movetext_np.reparentTo(self.node)  

    def hideUnitAvailMove(self):
        if self.movetext_np:
            self.movetext_np.removeNode() 
    
    def setBullet(self, b):
        b.reparentTo(render)
    
    def deleteBullet(self, b):
        b.removeNode()
        
    def setDamageNode(self, d):
        d.reparentTo(render)
        
    def deleteDamageNode(self, d):
        d.removeNode()  
        
    def playUnitStateAnim(self, unit_id):
        # Check if we have toggled overwatch
        unit = self.parent.units[unit_id]
        unit_model = self.unit_np_dict[unit_id]
        if unit_model.last_overwatch != unit['overwatch']:
            unit_model.last_overwatch = unit['overwatch']
            if unit['overwatch'] == True:
                unit_model.model.play('overwatch')
            else:
                unit_model.model.play('idle_stand01')
    
    def deleteTurnNode(self, d):
        d.removeNode()
    
    def playNewTurnAnim(self):
        text = TextNode('new turn node')
        text.setText("TURN: "+self.parent.turn_player)
        textnp = NodePath("textnp")
        textNodePath = textnp.attachNewNode(text)
        textNodePath.setColor(1, 0, 0)
        textNodePath.setScale(0.01, 0.01, 0.01)
        textNodePath.setPos(-0.7, 0, 0)
        textNodePath.reparentTo(aspect2d)
        s = Sequence(textNodePath.scaleInterval(.3, textNodePath.getScale()*20,blendType='easeIn'),
                     Wait(1.0),
                     textNodePath.scaleInterval(.3, textNodePath.getScale()*0.05,blendType='easeIn'),
                     Func(self.deleteTurnNode, textNodePath))
        s.start()
    
    def animTask(self, task):
        """Task to animate draw units while they are idling."""
        """
        dt = globalClock.getDt()#@UndefinedVariable
        for unit in self.unit_np_dict.itervalues():
            if self.parent.isUnitAlive(int(unit.id)) == True:
                unit.passtime += dt
    
                if unit.passtime > unit.idletime:
                    unit.model.play('idle_stand01')
                    unit.passtime = 0
                    unit.setIdleTime()
        """    
        return task.cont
    
    """
    def initOutlineShader(self):  
        self.light_dummy = NodePath("outline_light_dummy_node")      
        self.light_input = NodePath("outline_light_input_node")#self.loader.loadModel('misc/sphere') 
        self.light_input.reparentTo(self.light_dummy) 
        self.light_input.setPos(5,0,1) 
        self.light_dummy.setShaderOff(1) 
        self.light_dummy.hprInterval(1,Vec3(360,0,0)).loop() 
        self.SHA_outline = Shader.load('./data/shaders/facingRatio1.sha') 

    def setOutlineShader(self, np, color=Vec4(1, 0, 0, 0)):
        facingRatioPower = 1.5
        envirLightColor = color    

        self.light_dummy.reparentTo(np)
        self.light_dummy.setPos(np, 0, 0, 1)
        
        np.setShader(self.SHA_outline) 
        np.setShaderInput('cam', self.camera) 
        np.setShaderInput('light', self.light_input) 
        np.setShaderInput('envirLightColor', envirLightColor * facingRatioPower) 
        np.setAntialias(AntialiasAttrib.MMultisample) 
        
    def clearOutlineShader(self, np):
        self.light_dummy.detachNode()
        np.setShaderOff()
    """
#========================================================================
#
class Client(DirectObject):
    def __init__(self, parent, player):
        self.parent = parent
        self.player = player
        self.player_id = None
        
        # Set up important game logic variables
        self.level = None
        self.units = {}
        self.players = {}
        self.sel_unit_id = None
        
        # Init Client FSM
        self.fsm = ClientFSM(self, 'ClientFSM')
        
        # Init SceneGraph manager
        self.sgm = SceneGraph(self)
        
        # Init Camera
        #self.camera = Camera(self)
        self.camera = Camera(20, 20)
        
        # Init Interface
        self.interface = Interface(self)
        
        # All of our graphics components are initialized, request graphics init
        self.fsm.request('GraphicsInit')
        
        # Init Network
        self.net = Net(self)
        self.net.startNet()
        
        # Flags
        self.unit_move_playing = False
        
        # Turn number and player on turn
        self.turn_number = 0
        self.turn_player = None
        
        # Create main update task
        taskMgr.add(self.updateTask, "update_task")
    
    def newTurn(self):
        self.deselectUnit()
    
    def deselectUnit(self):
        self.clearState()
        
    def selectUnit(self, unit_id):
        if self.unit_move_playing == True:
            return
        
        if self.sel_unit_id != unit_id:
            self.deselectUnit()
            self.sel_unit_id = unit_id
            #self.selected_unit.marker.loadAnims({"move":"ripple2"})  
            #self.selected_unit.marker.loop("move")
            self.sgm.loadAltRenderModel(unit_id)
            self.interface.refreshUnitData(unit_id) 
            # If it is our turn, display available move tiles
            if self.player == self.turn_player:
                self.sgm.showUnitAvailMove(unit_id)

            
    def selectNextUnit(self):
        if self.sel_unit_id == None:
            last = 0
        else:
            last = self.sel_unit_id
        
        d = {}
        for unit_id in self.units.iterkeys():
            if self.isThisMyUnit(unit_id):
                d[unit_id] = self.units[unit_id]
        
        l = sorted(d.iterkeys())
        if len(l) <= 1:
            return
        else:
            if l[-1] == last:
                new_unit_id = l[0]
            else:
                for i in l:
                    if i > last:
                        new_unit_id = i
                        break
            self.selectUnit(new_unit_id)
        
    def selectPrevUnit(self):
        if self.sel_unit_id == None:
            # TODO: ogs: Kaj fakat?
            last = 9999999
        else:
            last = self.sel_unit_id
            
        d = {}
        for unit_id in self.units.iterkeys():
            if self.isThisMyUnit(unit_id):
                d[unit_id] = self.units[unit_id]
        
        l = sorted(d.iterkeys())
        l.reverse()
        if len(l) <= 1:
            return
        else:
            if l[-1] == last:
                new_unit_id = l[0]
            else:
                for i in l:
                    if i < last:
                        new_unit_id = i
                        break
            self.selectUnit(new_unit_id)
    
    def refreshUnit(self, unit):
        self.units[unit['id']] = unit
    
    def setupUnitLists(self, units):
        self.units = {}
        for u in units.itervalues():
            self.units[u['id']] = u
    
    def getUnitData(self, unit_id):
        if self.units.has_key(unit_id):
            return self.units[unit_id]
    
    def isThisMyUnit(self, unit_id):
        if self.units[unit_id]['owner_id'] == self.player_id:
            return True
        else:
            return False
    
    def isThisEnemyUnit(self, unit_id):
        if self.units[unit_id]['owner_id'] != self.player_id:
            return True
        else:
            return False
        
    def isUnitAlive(self, unit_id):
        return self.units[unit_id]['alive']
    
    def getCoordsByUnit(self, unit_id):
        if self.units.has_key(unit_id):
            unit = self.units[unit_id]
        return Point2(unit['pos'][0], unit['pos'][1])
    
    def getUnitByCoords(self, pos):
        for u in self.units.itervalues():
            if u['pos'][0] == pos.getX() and u['pos'][1] == pos.getY():
                return u['id']
        return None

    def outOfLevelBounds(self, x, y):
        if(x < 0 or y < 0 or x >= self.level['maxX'] or y >= self.level['maxY']):
            return True
        else:
            return False

    def canIMoveHere(self, unit, position, dx, dy):
        dx = int(dx)
        dy = int(dy)
              
        if( (dx != 1 and dx != 0 and dx != -1) and 
            (dy != 1 and dy != 0 and dy != -1) ):
            print ( "Invalid dx (%d) or dy (%d)" %(dy ,dy) )
        
        ptx = int(position[0])
        pty = int(position[1])
        
        if self.outOfLevelBounds(ptx+dx, pty+dy):
            return False

        #check if the level is clear at that tile
        if(self.level['_level_data'][ptx + dx][pty + dy] != 0):
            return False
        
        #check if there is a dynamic obstacle in the way
        if self.sgm.unit_np_list[ptx+dx][pty+dy]:
            return False
        """
        if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][0] != DYNAMICS_EMPTY ):
            #ok if it a unit, it may be the current unit so we need to check that
            if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][0] == DYNAMICS_UNIT ):
                if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][1] != unit.id ):
                    return False
        """
        
        #check diagonal if it is clear
        if( dx != 0 and dy != 0 ):
            
            #if there is something in level in the way
            if( self.level['_level_data'][ ptx + dx ][ pty ] != 0 or 
                self.level['_level_data'][ ptx ][ pty + dy ] != 0 ):
                return False
        
            #check if there is a dynamic thing in the way 
            """
            if( self.dynamic_obstacles[ ptx + dx ][ pty ][0] != DYNAMICS_EMPTY ):
                #see if it is a unit
                if( self.dynamic_obstacles[ ptx + dx ][ pty ][0] == DYNAMICS_UNIT ):
                    #so its a unit, see if it is friendly
                    unit_id = self.dynamic_obstacles[ ptx + dx ][ pty ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
                        return False
                    
            if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] != DYNAMICS_EMPTY ):
                if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] == DYNAMICS_UNIT ):
                    unit_id = self.dynamic_obstacles[ ptx ][ pty + dy ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
                        return False
            """
            
        return True
        
    def getMoveDict(self, unit_id, returnOrigin=False):
        unit = self.units[unit_id]
        final_dict = {}
        open_list = [(unit['pos'], unit['ap'])]
        for tile, actionpoints in open_list:
            for dx in xrange(-1,2):
                for dy in xrange( -1,2 ):            
                    if( dx == 0 and dy == 0):
                        continue
                    #we can't check our starting position
                    if( tile[0] + dx == unit['pos'][0] and tile[1] + dy == unit['pos'][1] ):
                        continue
                    x = int( tile[0] + dx )
                    y = int( tile[1] + dy )
                    if self.outOfLevelBounds(x, y):
                        continue
                    if not self.canIMoveHere(unit, tile, dx, dy):
                        continue                   
                    #if we are checking diagonally
                    if( dx == dy or dx == -dy ):
                        ap = actionpoints - 1.5
                    else:
                        ap = actionpoints - 1
                    
                    if( ap < 0 ):
                        continue
                    
                    pt = (x,y) 
                    
                    if pt in final_dict:
                        if( final_dict[pt] < ap ):
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
                    else: 
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
        if( returnOrigin ):
            final_dict[unit.pos] = unit.ap
            return final_dict
        
        return final_dict
    
    def beforeUnitMoveHook(self, unit_id):
        self.unit_move_playing = True
        self.sgm.hideUnitAvailMove()
    
    def afterUnitMoveHook(self, unit_id, start_pos, end_pos):
        if end_pos != None:
            if self.sgm.unit_np_dict.has_key(unit_id):
                self.sgm.unit_np_list[int(start_pos.getX())][int(start_pos.getY())] = None
                self.sgm.unit_np_list[int(end_pos.getX())][int(end_pos.getY())] = self.sgm.unit_np_dict[unit_id]
        if self.player == self.turn_player: 
            self.sgm.showUnitAvailMove(unit_id)
        self.unit_move_playing = False
        
    def beforeUnitShootHook(self, unit_id):
        self.unit_move_playing = True
        
    def afterUnitShootHook(self, unit_id):
        self.unit_move_playing = False
        
    def endTurn(self):
        ClientMsg.endTurn()
    
    def clearState(self):
        self.sgm.clearAltRenderModel()
        self.sgm.hideUnitAvailMove()
        self.interface.clearUnitData()
        self.sel_unit_id = None
    
#========================================================================
# Client animation handler methods
    
    def handleMove(self, unit_id, action_list):
        s = Sequence()
        d = 0.0
        unit_model = None
        spotted_unit_model = None
        
        if self.units.has_key(unit_id):
            unit_model = self.sgm.unit_np_dict[unit_id]
            # We will change start_pos variable on tile-per-tile basis
            start_pos = unit_model.node.getPos()
            # We need initial position of the entire animation so we can correctly change nps in unit_np_list
            animation_start_pos = start_pos
            start_h = unit_model.node.getH(render)
        else:
            # This is the first time we see this unit, we have no record of it in client.units dict or sgm nodepath list and dict
            # First action we MUST receive here is 'spot', otherwise client will break as we dont have unit_model defined
            None
            
        for idx, action in enumerate(action_list):
            action_type = action[0]
            if action_type == "move":
                end_pos = Point3(action[1][0] + 0.5, action[1][1] + 0.5, utils.GROUND_LEVEL)
                i, duration, start_pos, start_h = self.buildMoveMoveAnim(unit_model, start_pos, end_pos, start_h)
                d += duration
                s.append(i)
            elif action_type == "rotate":
                end_pos = Point3(action[1][0] + 0.5, action[1][1] + 0.5, utils.GROUND_LEVEL)
                i, duration, start_pos, start_h = self.buildMoveRotateAnim(unit_model, start_pos, end_pos, start_h)
                d += duration
                s.append(i)
            elif action_type == "spot":
                spotted_unit = action[1]
                self.units[spotted_unit['id']] = spotted_unit
                # Check if we have this unit in our scene graph records
                if self.sgm.unit_np_dict.has_key(spotted_unit['id']):
                    spotted_unit_model = self.sgm.unit_np_dict[spotted_unit['id']]
                # This is the first time we see this unit, fill out starting variables for move and rotate actions
                else:
                    spotted_unit_model = self.sgm.loadUnit(spotted_unit)
                
                if unit_model == None:
                    unit_model = spotted_unit_model
                    
                start_pos = unit_model.node.getPos()
                animation_start_pos = start_pos
                start_h = unit_model.node.getH(render)
                i = self.buildMoveSpotAnim(spotted_unit_model)
                s.append(i)
            elif action_type == "vanish":
                vanish_unit_id = action[1]
                i = self.buildMoveVanishAnim(vanish_unit_id)
                s.append(i)
                    
        end_pos = start_pos  
        anim = ActorInterval(unit_model.model, 'run', loop = 1, duration = d)
        anim_end = ActorInterval(unit_model.model, 'idle_stand01', startFrame=1, endFrame=1)
        move = Sequence(Func(self.beforeUnitMoveHook, unit_id),
                        Parallel(anim, s),
                        Sequence(anim_end),
                        Func(self.afterUnitMoveHook, unit_id, animation_start_pos, end_pos)
                        )
        move.start()
    
    def buildMoveSpotAnim(self, unit_model):
        return Sequence(Func(self.sgm.showUnit, unit_model), Wait(0.5))
    
    def buildMoveVanishAnim(self, unit_id):
        return Sequence(Func(self.sgm.hideUnit, unit_id), Wait(0.5))
    
    def buildMoveRotateAnim(self, unit_model, start_pos, end_pos, start_h):
        dummy_start = NodePath("dummy_start")
        dummy_end = NodePath("dummy_end")
        duration = 0.0
        dummy_start.setPos(start_pos)
        dummy_end.setPos(end_pos)
        dummy_start.lookAt(dummy_end)
        end_h = dummy_start.getH(render)
        interval = unit_model.node.quatInterval(0.2, hpr = Point3(end_h, 0, 0), startHpr = Point3(start_h, 0, 0))
        duration += 0.2
        return interval, duration, start_pos, end_h
    
    def buildMoveMoveAnim(self, unit_model, start_pos, end_pos, start_h):
        dummy_start = NodePath("dummy_start")
        dummy_end = NodePath("dummy_end")
        duration = 0.0
        p = None   
        dummy_start.setPos(start_pos)
        dummy_end.setPos(end_pos)
        dummy_start.lookAt(dummy_end) 
        end_h = dummy_start.getH(render)               
        # Model heading is different than movement heading, first create animation that turns model to his destination
        i_h = None
        if end_h != start_h:
            i_h = unit_model.node.quatInterval(0.2, hpr = Point3(end_h, 0, 0), startHpr = Point3(start_h, 0, 0))
        i = unit_model.node.posInterval(0.5, end_pos, start_pos)
        duration += 0.5
        if i_h:
            p = Parallel(i, i_h)
        else:
            p = i
        return p, duration, end_pos, end_h 
    
    def handleShoot(self, action_list):
        s = Sequence()
        d = 0.0                
        for idx, action in enumerate(action_list):
            action_type = action[0]
            if action_type == "shoot":
                # TODO: ogs: hendlati da je shooter_id = 1 (znaci da ga ne vidimo, a puca na nas)
                shooter_id = action[1] # unit_id of the shooter
                shoot_tile = action[2] # (x,y) pos of targeted tile
                weapon = action[3] # weapon id
                damage_list = action[4] # list of all damaged/missed/bounced/killed units
                shooter_model = self.sgm.unit_np_dict[shooter_id]
                i = self.buildShootShootAnim(shooter_model, shoot_tile, weapon)
                s.append(i)
                i = self.buildShootDamageAnim(damage_list, shooter_id)
                s.append(i)
            elif action_type == "melee":
                shooter_id = action[1] # unit_id of the shooter
                shoot_tile = action[2] # (x,y) pos of targeted tile
                weapon = action[3] # weapon id
                damage_list = action[4] # list of all damaged/missed/bounced/killed units
                shooter_model = self.sgm.unit_np_dict[shooter_id]
                i = self.buildShootMeleeAnim(shooter_model, shoot_tile, weapon)
                s.append(i)
                i = self.buildShootDamageAnim(damage_list, shooter_id)
                s.append(i)
            elif action_type == "rotate":
                unit_id = action[1]
                heading = action[2]
                unit_model = self.sgm.unit_np_dict[unit_id]
                start_h = unit_model.node.getH(render)
                i, duration, start_h = self.buildShootRotateAnim(unit_model, start_h, heading)
                s.append(i)
        
        # Start our shoot sequence
        shoot = Sequence(Func(self.beforeUnitShootHook, int(shooter_id)),
                         s
                         )
        shoot.start()        

    def buildShootRotateAnim(self, unit_model, start_h, heading):
        duration = 0.0
        end_h = utils.getHeadingAngle(heading)
        interval = unit_model.node.quatInterval(0.2, hpr = Point3(end_h, 0, 0), startHpr = Point3(start_h, 0, 0))
        duration += 0.2
        return interval, duration, end_h
    
    def buildShootShootAnim(self, unit_model, target_tile, weapon):
        # First we create shooting animation
        shoot_anim = ActorInterval(unit_model.model, 'shoot')
        # Then we create the bullet and its animation
        self.bullet = loader.loadModel("sphere")
        self.bullet.setScale(0.05)
        start_pos = Point3(unit_model.node.getX(render), unit_model.node.getY(render), 0.9)
        end_pos = Point3(target_tile[0] + 0.5, target_tile[1] + 0.5, 0.9)
        dest_node = NodePath("dest_node")
        dest_node.setPos(end_pos)
        time = round(unit_model.node.getDistance(dest_node) / 5, 2)
        bullet_sequence = Sequence(Func(self.sgm.setBullet, self.bullet),
                                   self.bullet.posInterval(time, end_pos, start_pos),
                                   Func(self.sgm.deleteBullet, self.bullet)
                                   )
        # Pack unit shoot animation and bullet animation in parallel
        shoot_parallel = Parallel(shoot_anim, bullet_sequence)
        return shoot_parallel

    def buildShootMeleeAnim(self, unit_model, target_tile, weapon):
        # First we create melee animation
        melee_anim = ActorInterval(unit_model.model, 'melee')
        return melee_anim
    
    def buildShootDamageAnim(self, damage_list, shooter_id):
        # Find all damaged units and play their damage/kill/miss animation
        damage_parallel = Parallel()
        for action in damage_list:
            damage_type = action[0]
            target_unit_id = action[1]
            target_unit = self.sgm.unit_np_dict[target_unit_id]
            t = TextNode('dmg')
            if damage_type == "bounce":
                target_anim = ActorInterval(target_unit.model, "damage")
                dmg = 'bounce'
            elif damage_type == "miss":
                target_anim = ActorInterval(target_unit.model, "damage")
                dmg = 'miss'                
            elif damage_type == "damage":
                target_anim = ActorInterval(target_unit.model, "damage")
                dmg = str(action[2])
            elif damage_type == "kill":
                target_anim = ActorInterval(target_unit.model, "die")
                dmg = str(action[2])
            t.setText( "%s" % dmg)
            t.setTextColor(1, 0, 0, 1)
            t.setAlign(TextNode.ACenter)
            textNodePath = NodePath("textnp")
            textNodePath.attachNewNode(t)
            textNodePath.setScale(0.25)
            textNodePath.setBillboardPointEye()
            start_pos = Point3(target_unit.node.getX(render), target_unit.node.getY(render), 0.9)
            end_pos = start_pos + Point3(0, 0, 3)
            damage_text_sequence = Sequence(Func(self.sgm.setDamageNode, textNodePath),
                                            textNodePath.posInterval(1.5, end_pos, start_pos),
                                            Func(self.sgm.deleteDamageNode, textNodePath)
                                            )
            damage_parallel.append(Parallel(target_anim, damage_text_sequence, Func(self.afterUnitShootHook, int(shooter_id))))        
        return damage_parallel
    
    def handleVanish(self, unit_id):
        s = Sequence()
        i = self.buildMoveVanishAnim(unit_id)
        s.append(i)
        s.start()


#========================================================================
# Client tasks
   
    def updateTask(self, task):
        """Main update Client task."""
        return task.cont

#========================================================================
#
class Net():
    def __init__(self, parent):
        self.parent = parent
        
        # Set logging through our global logger
        self.log = self.parent.parent.logger
        ClientMsg.log = self.parent.parent.logger
       
    def startNet(self):
        # Create main network messaging task which initiates connection
        taskMgr.add(self.msgTask, "msg_task") 

    def handleMsg(self, msg):
        """Handles incoming messages."""
        self.log.info("Received message: %s", msg[0])
        print msg
        #========================================================================
        #
        if msg[0] == ENGINE_STATE:
            self.parent.level = pickle.loads(msg[1]['level'])
            self.parent.turn_number = msg[1]['turn']
            self.parent.players = pickle.loads(msg[1]['players'])
            self.parent.turn_player = msg[1]['active_player'].name 
            # TODO: ogs: Inace cu znati player_id kad se ulogiram pa necu morati ovako dekodirati
            for p in self.parent.players:
                if p['name'] == self.parent.player:
                    self.parent.player_id = p['id']
            self.parent.setupUnitLists(pickle.loads(msg[1]['units']))
            self.parent.fsm.request('EngineState')
        #========================================================================
        #
        elif msg[0] == MOVE:
            unit_id = msg[1][0]
            tile_list = msg[1][1]
            self.parent.handleMove(unit_id, tile_list)
        #========================================================================
        #
        elif msg[0] == NEW_TURN:
            self.parent.newTurn()
            self.parent.turn_number = msg[1]['turn']
            self.parent.turn_player = msg[1]['active_player'].name 
            units = pickle.loads(msg[1]['units'])
            for unit in units.itervalues():
                self.parent.refreshUnit(unit)
            self.parent.sgm.playNewTurnAnim()                
            #self.parent.interface.refreshUnitData( unit['id'] )
        #========================================================================
        #
        elif msg[0] == UNIT:
            unit = msg[1]
            self.parent.refreshUnit(unit)
            # TODO: ogs: Ovaj refresh interface-a se poziva i kada unit koji dodje nije selektirani unit, to srediti
            if self.parent.sel_unit_id == unit['id']:
                self.parent.interface.refreshUnitData( unit['id'] )
                #self.parent.sgm.showUnitAvailMove( unit['id'] )
                self.parent.sgm.playUnitStateAnim( unit['id'] )
        #========================================================================
        #
        elif msg[0] == SHOOT:
            action_list = msg[1]
            self.parent.handleShoot(action_list)       
        #========================================================================
        #
        elif msg[0] == 'vanish':
            unit_id = msg[1]
            self.parent.handleVanish(unit_id)
                
        #========================================================================
        #
        elif msg[0] == ERROR:
            self.parent.interface.console.consoleOutput(str(msg[1]), utils.CONSOLE_SYSTEM_ERROR)
            self.parent.interface.console.show()
        #========================================================================
        #
        elif msg[0] == CHAT:
            sender_name = msg[2]
            self.parent.interface.console.consoleOutput( sender_name + ":" + str(msg[1]), utils.CONSOLE_SYSTEM_MESSAGE)
            self.parent.interface.console.show()
        #========================================================================
        #
        else:
            self.log.error("Unknown message Type: %s", msg[0])
    
    
    def msgTask(self, task):
        """Task that listens for messages on client queue."""
        # Needs to be called every frame, this takes care of connection
        ClientMsg.handleConnection(self.parent.player)
        
        msg = ClientMsg.readMsg()        
        if msg:
            self.handleMsg(msg)            
        return task.cont

#========================================================================
#
class ClientFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

    def enterLoginScreen(self):
        None
    
    def exitLoginScreen(self):
        None

    def enterGraphicsInit(self):
        self.parent.sgm.initLights()
        self.parent.sgm.initAltRender()
        self.parent.sgm.initCollisions()
    
    def exitGraphicsInit(self):
        None
        
    def enterEngineState(self):
        self.parent.clearState()
        self.parent.sgm.deleteLevel()
        self.parent.sgm.deleteUnits()
        self.parent.sgm.loadLevel(self.parent.level)
        self.parent.sgm.loadUnits()

    def exitEngineState(self):
        None
        
#========================================================================
#
class Screen(DirectObject):
    """The Screen Class manages window."""
    def __init__(self, parent, res=(800,600)):
        self.parent = parent
        # Init pipe
        ShowBase()
        base.makeDefaultPipe()
        screen = (base.pipe.getDisplayWidth(), base.pipe.getDisplayHeight())
        win = WindowProperties.getDefault()
        win.setSize(res[0], res[1])
        win.setOrigin(screen[0]/2 - res[0]/2, screen[1]/2 - res[1]/2)
        win.setFullscreen(False)
        base.openDefaultWindow(win)        
        #base.setBackgroundColor(.05,.05,.05)
        # TODO: ogs: enableati auto shader samo na odredjenim nodepathovima
        #render.setShaderAuto()
        self.setupKeys()

    def setupKeys(self):
        self.accept('f2', base.toggleWireframe)
        self.accept('f3', base.toggleTexture)
        self.accept('f12', base.screenshot, ["Snapshot"])
        self.accept('i', render.ls)
        self.accept('u', render.analyze)

#############################################################################
# MAIN
#############################################################################

app = App()
run()
