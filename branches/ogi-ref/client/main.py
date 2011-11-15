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
from panda3d.core import loadPrcFile, WindowProperties, Texture, OrthographicLens, PerspectiveLens
from panda3d.core import NodePath, Point2, Point3, VBase4, GeomNode, Vec3, Vec4#@UnresolvedImport
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight#@UnresolvedImport
from panda3d.core import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode
from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM

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
        
        #initialize world
        self.client = Client(self, 'ultramarines')

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
    
    def loadLevel(self, level):
        if self.comp_inited['level']:
            return
        
        levelMesh = VoxelGenerator('level', 1, 0.3)
        for x in xrange(0, level['maxX']):
            for y in xrange(0, level['maxY']):
                for i in xrange(0, level['_level_data'][x][y]+1):
                    id = randint(1, 2) 
                    levelMesh.makeLeftFace(x, y, i, id)
                    levelMesh.makeRightFace(x, y, i, id)
                    levelMesh.makeBackFace(x, y, i, id)
                    levelMesh.makeFrontFace(x, y, i, id)
                    levelMesh.makeBottomFace(x, y, i, id) 
                    levelMesh.makeTopFace(x, y, i, id)

        self.level_node = self.node.attachNewNode(levelMesh.getGeomNode())
        self.level_node.setTag('type', 'level')
        t = loader.loadTexture('tex2.png')
        t.setMagfilter(Texture.FTLinearMipmapLinear)
        t.setMinfilter(Texture.FTLinearMipmapLinear)
        self.level_node.setTexture(t)
        self.comp_inited['level'] = True
        """
        
        for i in xrange(0, level['maxX']):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = render.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i+0.3, -0.3, 0.5)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
        for i in xrange(0, level['maxY']):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = render.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(-0.3, i+0.3, 0.5)
            tnp.setBillboardPointEye()
            tnp.setLightOff()         
        """
        
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
        
        self.unit_np_list = [[None] * self.parent.level['maxY'] for i in xrange(self.parent.level['maxX'])]
                    
        for unit in self.parent.units.itervalues():
            um = UnitModel(self, unit['id'])
            um.node.reparentTo(self.node)
            # Keep unit nodepath in dictionary of all unit nodepaths
            self.unit_np_dict[unit['id']] = um
            # Keep unit nodepath in list corresponding to level size
            # This will be dinamically altered when units change position
            self.unit_np_list[int(unit['pos'][0])][int(unit['pos'][1])] = um
            
        for unit in self.parent.enemy_units.itervalues():
            um = UnitModel(self, unit['id'])
            um.node.reparentTo(self.node)
            # Keep unit nodepath in dictionary of all unit nodepaths
            self.unit_np_dict[unit['id']] = um
            # Keep unit nodepath in list corresponding to level size
            # This will be dinamically altered when units change position
            self.unit_np_list[int(unit['pos'][0])][int(unit['pos'][1])] = um
                        
        self.comp_inited['units'] = True
    
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
        #self.off_model.play(self.off_model.getAnimName("idle"))
            
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
        self.enemy_units = {}
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
        
        # Create main update task
        taskMgr.add(self.updateTask, "update_task")
        
    def deselectUnit(self):
        self.sgm.clearAltRenderModel()
        self.interface.clearUnitData()
        self.sel_unit_id = None
        
    def selectUnit(self, unit_id):
        if self.sel_unit_id != unit_id:
            self.deselectUnit()
            self.sel_unit_id = unit_id
            #self.selected_unit.marker.loadAnims({"move":"ripple2"})  
            #self.selected_unit.marker.loop("move")
            #u = self.ge.unit_np_dict[int(unit.id)].unit
            self.sgm.loadAltRenderModel(unit_id)
            self.interface.printUnitData(unit_id)   
            
    def selectNextUnit(self):
        if self.sel_unit_id == None:
            last = 0
        else:
            last = self.sel_unit_id
        
        l = sorted(self.units.iterkeys())
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
        
        l = sorted(self.units.iterkeys())
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
        for u in units.itervalues():
            if u['owner_id'] == self.player_id:
                self.units[u['id']] = u
            else:
                self.enemy_units[u['id']] = u
    
    def getUnitData(self, unit_id):
        if self.units.has_key(unit_id):
            return self.units[unit_id]
        elif self.enemy_units.has_key(unit_id):
            return self.enemy_units[unit_id]
    
    def isThisMyUnit(self, unit_id):
        return self.units.has_key(unit_id)
    
    def getCoordsByUnit(self, unit_id):
        if self.units.has_key(unit_id):
            unit = self.units[unit_id]
        elif self.enemy_units.has_key(unit_id):
            unit = self.enemy_units[unit_id]
        return Point2(unit['pos'][0], unit['pos'][1])
    
    def getUnitByCoords(self, pos):
        for u in self.units.itervalues():
            if u['pos'][0] == pos.getX() and u['pos'][1] == pos.getY():
                return u['id']
        return None
    
    def endTurn(self):
        ClientMsg.endTurn()
    
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
        #========================================================================
        #
        if msg[0] == ENGINE_STATE:
            self.parent.level = pickle.loads(msg[1]['level'])
            self.parent.turn = msg[1]['turn']
            self.parent.players = pickle.loads(msg[1]['players'])
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
            unit = self.parent.sgm.unit_np_dict[unit_id]
            unit.moveUnitModel(tile_list)
        #========================================================================
        #
        elif msg[0] == NEW_TURN:
            None
        #========================================================================
        #
        elif msg[0] == UNIT:
            unit = msg[1]
            self.parent.refreshUnit(unit)
            # TODO: ogs: Ovaj refresh interface-a se poziva i kada unit koji dodje nije selektirani unit, to srediti
            self.parent.interface.refreshUnitData()
        #========================================================================
        #
        elif msg[0] == ERROR:
            self.parent.interface.console.consoleOutput(str(msg[1]), utils.CONSOLE_SYSTEM_ERROR)
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

    def enterGraphicsInit(self):
        self.parent.sgm.initLights()
        self.parent.sgm.initAltRender()
        self.parent.sgm.initCollisions()
    
    def exitGraphicsInit(self):
        None
        
    def enterEngineState(self):
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
        render.setShaderAuto()
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
