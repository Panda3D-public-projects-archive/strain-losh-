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
from pandac.PandaModules import loadPrcFile, WindowProperties, Texture
from panda3d.core import NodePath, Point2, Point3, VBase4, GeomNode, Vec3, Vec4#@UnresolvedImport
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM

# strain related imports
from strain.client_messaging import *
from strain.camera import Camera
from strain.voxelgen import VoxelGenerator

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
        self.screen = Screen(self, (1024,768))
        
        #initialize world
        self.client = Client(self)

#========================================================================
#
class SceneGraph():
    def __init__(self, parent):
        self.parent = parent
        
        # Main node in a scene graph. Everything should be reparented to this node or another node under this node
        # This node is reparented to render
        self.node = render.attachNewNode("master")
    
    def loadLevel(self, level):
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
        t = loader.loadTexture('tex.png')
        t.setMagfilter(Texture.FTLinearMipmapLinear)
        t.setMinfilter(Texture.FTLinearMipmapLinear)
        self.level_node.setTexture(loader.loadTexture("tex.png"))
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
#========================================================================
#
class Client(DirectObject):
    def __init__(self, parent):
        self.parent = parent
        
        # Set up important game logic variables
        self.level = None
        self.units = {}
        self.enemy_units = {}
        
        # Set logging through our global logger
        self.log = self.parent.logger
        ClientMsg.log = self.parent.logger
        
        # Init Client FSM
        self.fsm = ClientFSM(self, 'ClientFSM')
        
        # Init SceneGraph manager
        self.sgm = SceneGraph(self)
        
        # Init Camera
        self.camera = Camera(self)
        
        # Create main network messaging task which initiates connection
        taskMgr.add(self.msgTask, "msg_task")
        
        # Create main update task
        taskMgr.add(self.updateTask, "update_task")
        
        
    def handleMsg(self, msg):
        """Handles incoming messages."""
        self.log.info("Received message: %s", msg[0])
        #========================================================================
        #
        if msg[0] == ENGINE_STATE:
            self.level = pickle.loads(msg[1]['level'])
            self.turn = msg[1]['turn']
            units = pickle.loads(msg[1]['units'])
            self.fsm.request('GraphicsInit')
        #========================================================================
        #
        elif msg[0] == MOVE:
            unit_id = msg[1][0]
            tile_list = msg[1][1]
            unit = self.unit_np_dict[unit_id]
            self.playUnitAnim(self.unit_np_dict[unit_id], tile_list)
        #========================================================================
        #
        elif msg[0] == NEW_TURN:
            None
        #========================================================================
        #
        elif msg[0] == UNIT:
            if self.engineLoaded:
                unit = msg[1]
                self.updateUnit(unit)
                self.interface.printUnitData()
        #========================================================================
        #
        elif msg[0] == ERROR:
            self.interface.console.consoleOutput(str(msg[1]), CONSOLE_SYSTEM_ERROR)
            self.interface.console.show()
        #========================================================================
        #
        else:
            self.log.error("Unknown message Type: %s", msg[0])
    
    def msgTask(self, task):
        """Task that listens for messages on client queue."""
        # Needs to be called every frame, this takes care of connection
        ClientMsg.handleConnection()
        
        msg = ClientMsg.readMsg()        
        if msg:
            self.handleMsg(msg)            
        return task.cont
    
    def updateTask(self, task):
        """Main update Client task."""
        self.camera.update()
        return task.cont


#========================================================================
#
class ClientFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

    def enterGraphicsInit(self):
        self.parent.sgm.loadLevel(self.parent.level)
        self.parent.sgm.initLights()
    
    def exitGraphicsInit(self):
        None

#========================================================================
#
class Screen(DirectObject):
    """The Screen Class manages window."""
    def __init__(self, parent, res=(1024,768)):
        #record vars
        self.parent = parent
        #init pipe
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
        #setup keys
        self.setupKeys()

    def setupKeys(self):
        self.accept('f2', base.toggleWireframe)
        self.accept('f3', base.toggleTexture)
        self.accept('f12', base.screenshot, ["Snapshot"])
        self.accept('i', render.analyze)

#############################################################################
# MAIN
#############################################################################

app = App()
run()
