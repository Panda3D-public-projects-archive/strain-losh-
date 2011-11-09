#############################################################################
# IMPORTS
#############################################################################

# python imports
import os
import logging
import cPickle as pickle

# panda3D imports
from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import loadPrcFile, WindowProperties
from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM

# strain related imports
from strain.client_messaging import *
from strain.camera import Camera
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

        # Main level node in a scene graph
        self.level_node = self.node.attachNewNode("levelnode")
        # Disable default Panda3d camera implementation
        #base.disableMouse()
    
    def loadLevel(self, level):
        # List to store nodepaths of all tiles in a level
        self.tile_np_list = []
        # List to store nodepaths of all units
        # List indices equal level coordinates
        # Empty coordinates are stored as None values
        # Here we just allocate the list and fill it with None values
        self.unit_np_list = [[None] * level['maxY'] for i in xrange(level['maxX'])]
        for x in xrange(0, level['maxX']): 
            tile_nodes = []
            for y in xrange(0, level['maxY']): 
                tag = level['_level_data'][x][y]
                c = loader.loadModel("tile")
                if tag != 0:
                    c.setScale(1, 1, tag + 1)
                    #TODO: ogs: Srediti ovaj colorScale, izgleda da ne radi dobro s ovom teksturom
                    coef = 1 + 0.05 * tag
                    c.setColorScale(coef, coef, coef, 1)
                    c.flattenLight()
                c.setPos(x, y, 0)
                c.setTag("pos", "%(X)s-%(Y)s" % {"X":x, "Y":y})
                c.setTag("type", "tile")                     
                c.reparentTo(self.level_node)
                tile_nodes.append(c)
            self.tile_np_list.append(tile_nodes)
        self.level2_node = utils.flattenReallyStrong(self.level_node)
        self.level_node.removeNode()
        self.level2_node.reparentTo(self.node)
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
