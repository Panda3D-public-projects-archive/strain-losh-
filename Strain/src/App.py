from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from Interface import Interface
from Unit import Unit
from Level import Level
from Grid import Grid
from SoundManager import SoundManager
        
loadPrcFileData("", "model-path "+"$MAIN_DIR/models")
loadPrcFileData("", "model-path "+"$MAIN_DIR/sounds")
loadPrcFileData("", "model-path "+"$MAIN_DIR/textures")

# Loading global config data
config = {} # config dictionary variable
file = open("etc/user.cfg", 'r')
while 1:
    string = file.readline()
    if (string == ""):
        break
    elif (string[0] == "#"):
        continue
    part = string.rsplit('=')
    config[part[0].strip()] = part[1].strip()
file.close()

loadPrcFileData("", "fullscreen "+config['fullscreen'])
loadPrcFileData("", "win-size "+config['resx']+" "+config['resy'])
loadPrcFileData("", "show-frame-rate-meter "+config['showfps'])
loadPrcFileData("", "model-cache-dir ./tmp")
loadPrcFileData("", "window-title Strain")
if config['scene-explorer'] == "1":
    loadPrcFileData("", "want-directtools #t")
    loadPrcFileData("", "want-tk #t")


class App(ShowBase):
    """Main ShowBase class of the application. Handles initialization of all objects and runs a main loop."""
    def __init__(self):        
        ShowBase.__init__(self)
        #PStatClient.connect()
        
        self.node = None
        self.level = None
        self.level_name = None
        self.tile_size = None
        self.units = {} 
        
        self.sound_manager = SoundManager()
        
        self.level_name = 'level3.txt'
        self.init_world()

        #self.setBackgroundColor(Vec4(0.0,0.0,0.0,1.0))    

        self.interface = Interface()
        #self.c = clPickerTool()
        
        wp = self.win.getProperties() 
        aspect = float(wp.getXSize()) / wp.getYSize()        
        cm = CardMaker('unit')
        cm.setFrame(0, 0.3, 0, 0.3)
        self.unit_cm = aspect2d.attachNewNode(cm.generate())
        self.unit_cm.setPos(-aspect, 0, 0.7)
        self.init_alt_render()

        self.accept('g', self.switch_grid)
        self.accept('i', self.info)
        self.accept('escape', self.escape)
    
    def escape(self):
        if self.interface.selected_unit:
            self.interface.deselect()
        else:
            taskMgr.stop()
    
    def init_world(self):
        """Initializes all objects needed to start a new level."""
        self.node = render.attachNewNode('master')
        self.level = Level()
        self.level.load(self.level_name)
        self.tile_size = 1
        #self.level.create()
        self.level.create()
        self.level.show(self.node)
        #self.grid = Grid(self.level.maxX, self.level.maxY)
        #self.grid.show(self.node)
        self.init_lights()
        self.init_units()
        #render.setTransparency(TransparencyAttrib.MAlpha)
    
    def clear_world(self):
        """Clears all objects in a current app context."""
        del self.grid
        if self.node:
            self.node.removeNode()
            
    def init_lights(self):
        shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        render.setAttrib(shade)
        dlight1 = DirectionalLight('dlight1')
        dlight1.setColor(VBase4(1.0, 1.0, 1.0, 1.0))
        dlnp1 = render.attachNewNode(dlight1)
        dlnp1.setHpr(-10, -30, 0)
        render.setLight(dlnp1)
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1.0))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp) 

    def init_units(self):
        self.units = {}
        u = Unit('Unit01', 'terminator', 'Team01', 3, 4, self.node)
        u.model.setLightOff()
        self.units['Unit01'] = u
        u = Unit('Unit02', 'marine_b', 'Team02', 8, 9, self.node)
        u.model.setLightOff()
        self.units['Unit02'] = u           

    def init_alt_render(self):  
        alt_buffer = self.win.makeTextureBuffer("texbuf", 256, 256)
        self.alt_render = NodePath("off render")
        self.alt_cam = base.makeCamera(alt_buffer)
        self.alt_cam.reparentTo(self.alt_render)        
        self.alt_cam.setPos(0,-10,0)
        self.alt_render.setLightOff()
        self.alt_render.setFogOff()     
        self.unit_cm.setTexture(alt_buffer.getTexture())
        #self.alt_cam.node().getDisplayRegion(0).setClearColor(Vec4(0,0,0,1))
        
    def switch_grid(self):
        """Toggles display of the grid."""
        if self.grid.visible == False:
            self.grid.show(self.node)
        elif self.grid.visible == True:
            self.grid.hide()
    
    def calc_world_pos(self, mappos):
        x = int(mappos.x)
        y = int(mappos.y)
        return Point3(x, y, 0)
    
    def calc_unit_pos(self, mappos):
        x = int(mappos.x)
        y = int(mappos.y)
        return Point3(x + (base.tile_size/2.0), y + (base.tile_size/2.0), 0.3)
    
    """ 
    -----------------------------------
    debugging procedures and tasks
    -----------------------------------
    """ 
        
    def info(self):
        print render.ls()
        #print render.analyze()
        
    def printer(self, task):
        return task.cont    
 