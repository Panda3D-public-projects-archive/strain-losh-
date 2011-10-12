from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from panda3d.core import NodePath, Point2, Point3, CardMaker, VBase4, Vec3, GeomNode
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight, TransparencyAttrib
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from Camera import Camera
from Interface import Interface
from UnitModel import UnitModel
from Messaging import EngMsg, Messaging, ClientMsg, Message
import sys

#===============================================================================
# Panda3D parameter file handling
#===============================================================================

loadPrcFileData("", "model-path "+"$MAIN_DIR/models")
loadPrcFileData("", "model-path "+"$MAIN_DIR/sounds")
loadPrcFileData("", "model-path "+"$MAIN_DIR/textures")

# config dictionary variable
config = {} 
cfile = open("etc/user.cfg", "r")
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

#===============================================================================
# CLASS GraphicsEngine --- DEFINITION
#===============================================================================
class GraphicsEngine(ShowBase):
    """Class implementing graphics engine. Inherits from Panda3d ShowBase class. 
       Handles scene graph objects and runs a main draw loop.
    """
    
    def __init__(self, engine):
        """Initializes all components of scene graph and Panda3d ShowBase class which creates window for us."""
        ShowBase.__init__(self)
        #PStatClient.connect()
        
        # Instance of the main game engine
        # TODO: ogs: Prebaciti komunikaciju na messaging
        self.engine = engine
        
        # Main node in a scene graph. Everything should be reparented to this node or another node under this node
        # This node is reparented to render
        self.node = self.render.attachNewNode("master")

        self.initAll(engine.level)
        
        # Initialize custom app camera implementation
        # Disable default Panda3d camera implementation
        self.disableMouse()
        self.app_camera = Camera(self.camera, self.mouseWatcherNode, engine.level.maxX, engine.level.maxY)
        # Initialize graphical user interface elements
        self.interface = Interface(self)
        
        self.accept("window-event", self.windowEvent)
        self.accept('aspectRatioChanged', self.redraw)
        self.accept("escape", self.destroy)
        
        # debug
        self.accept("i", self.info)
        
        # Create messaging task
        self.taskMgr.add(self.msgTask, "msg_task")
        

    def initAll(self, level):
        """Initializes all the components of scene graph."""
        # TODO: ogs: Napraviti proceduru i za deinicijalizaciju svega i testirati kroz pstats
        self.initLevel(level)
        self.initUnits()
        self.initLights()
        self.initAltBuffer()
        self.initCollision()     
    
    def initLevel(self, level):
        # Main level node in a scene graph
        self.level_node = self.node.attachNewNode("levelnode")
        # List to store nodepaths of all tiles in a level
        self.tile_np_list = []
        # List to store nodepaths of all units
        # List indices equal level coordinates
        # Empty coordinates are stored as None values
        # Here we just allocate the list and fill it with None values
        self.unit_np_list = [[None] * level.maxX for i in xrange(level.maxY)]
        for x in xrange(0, level.maxX): 
            tile_nodes = []
            for y in xrange(0, level.maxY): 
                tag = level._level_data[x][y]
                c = self.loader.loadModel("tile")
                c.setPos(x, y, 0)
                c.setTag("pos", "%(X)s-%(Y)s" % {"X":x, "Y":y})
                c.setTag("type", "tile") 
                if tag != 0:
                    c.setScale(1, 1, tag + 1)
                    #TODO: ogs: Srediti ovaj colorScale, izgleda da ne radi dobro s ovom teksturom
                    coef = 1 + 0.05 * tag
                    c.setColorScale(coef, coef, coef, 1)
                    c.flattenLight()
                c.reparentTo(self.level_node)
                tile_nodes.append(c)
            self.tile_np_list.append(tile_nodes)

    def initUnits(self):
        # Set up dictionaries for player and unit nodepaths
        self.player_np_dict = {}
        self.unit_np_dict = {}
        
        for player in self.engine.players:
            # Create a node in the scene graph for each player
            player_node = self.node.attachNewNode(str(player.id) + "_playernode")
            self.player_np_dict[player.id] = player_node 
            for unit in player.unitlist:
                um = UnitModel(unit, player)
                um.node.reparentTo(self.node)
                # Keep unit nodepath in dictionary of all unit nodepaths
                self.unit_np_dict[unit.id] = um
                # Keep unit nodepath in list corresponding to level size
                # This will be dinamically altered when units change position
                self.unit_np_list[unit.x][unit.y] = um

    def initLights(self):
        shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        self.render.setAttrib(shade)
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(1.0, 1.0, 1.0, 1.0))
        dlnp1 = self.render.attachNewNode(dlight1)
        dlnp1.setHpr(-10, -30, 0)
        self.render.setLight(dlnp1)
        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1.0))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

    def initAltBuffer(self):
        """Initializes off screen buffer used to render models and animations for unit portraits."""
        self.alt_buffer = self.win.makeTextureBuffer("texbuf", 256, 256)
        self.alt_render = NodePath("offrender")
        self.alt_cam = self.makeCamera(self.alt_buffer)
        self.alt_cam.reparentTo(self.alt_render)        
        self.alt_cam.setPos(0,-10,0)
        self.alt_render.setLightOff()
        self.alt_render.setFogOff()

    def initCollision(self):
        """Initializes objects needed to perform panda collisions."""
        self.coll_trav = CollisionTraverser()
        self.coll_queue = CollisionHandlerQueue()
        self.coll_node = CollisionNode("mouse_ray")
        self.coll_nodepath = self.camera.attachNewNode(self.coll_node)
        self.coll_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.coll_ray = CollisionRay()
        self.coll_node.addSolid(self.coll_ray)
        self.coll_trav.addCollider(self.coll_nodepath, self.coll_queue)

    def destroyUnit(self, unit):
        """Removes unit nodepath from scenegraph. It will eventually be collected by gc and destroyed."""
        unit.cleanup()
        unit.remove()
    
    def windowEvent(self, win):
        pass
        if win.isClosed():
            self.destroy()

    def redraw(self):
        pass
        
    def info(self):
        #print render.ls()
        print self.render.analyze()
        
    def destroy(self):
        # TODO: ogs: Nekad se na izlazu javlja:debug('feeder thread got sentinel -- exiting') - vjerovatno vezano uz threading, provjeriti
        if self.interface.selected_unit:
            self.interface.deselectUnit()
        else:
            ClientMsg.shutdownEngine()            
            sys.exit()

    def msgTask(self, task):
        return task.cont
    