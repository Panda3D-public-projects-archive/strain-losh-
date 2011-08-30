from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from Interface import clPickerTool, Interface
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

        self.picked_unit = None
        self.game_state = {}
        self.game_state['movement'] = 0        

        self.a = Interface()
        self.c = clPickerTool()
        
        self.accept('m', self.toggle_state, ['movement'])
        self.accept('g', self.switch_grid)
        self.accept('i', self.info)
        #self.accept('w', self.change)
        self.accept('escape', self.end)
    
    def end(self):
        """Exits the application by stopping the ShowBase task manager."""
        taskMgr.stop()
    
    def init_world(self):
        """Initializes all objects needed to start a new level."""
        self.node = render.attachNewNode('master')
        self.level = Level()
        self.level.load(self.level_name)
        self.tile_size = 1
        #self.level.create()
        self.level.create2()
        self.level.show(self.node)
        self.grid = Grid(self.level.x, self.level.y)
        self.grid.show(self.node)
        self.init_lights()
        self.init_units()
    
    def clear_world(self):
        """Clears all objects in a current app context."""
        del self.grid
        if self.node:
            self.node.removeNode()
            
    def init_lights(self):
        # Set flat shading
        flatShade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        render.setAttrib(flatShade)
        # Create directional light
        dlight1 = DirectionalLight('dlight1')
        dlight1.setColor(VBase4(1.0, 1.0, 1.0, 1.0))
        dlnp1 = render.attachNewNode(dlight1)
        dlnp1.setHpr(-10, -30, 0)
        render.setLight(dlnp1)
        # Create second directional light
        dlight2 = DirectionalLight('dlight2')
        dlight2.setColor(VBase4(0.0, 0.1, 0.2, 1.0))
        dlnp2 = render.attachNewNode(dlight2)
        dlnp2.setHpr(170, 0, 0)
        render.setLight(dlnp2)
        # Create ambient light
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1.0))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp) 

    def init_units(self):
        self.units = {}
        u = Unit('Unit01', 'terminator', 'Team01', 3, 4, self.node)
        self.units['Unit01'] = u
        u = Unit('Unit02', 'marine_b', 'Team02', 8, 9, self.node)
        self.units['Unit02'] = u           
        
    def switch_grid(self):
        """Toggles display of the grid."""
        if self.grid.visible == False:
            self.grid.show(self.node)
        elif self.grid.visible == True:
            self.grid.hide()
    
    def toggle_state(self, state):
        if self.game_state[state] == 0:
            self.game_state[state] = 1
            self.picked_unit.find_path()
        else:
            self.game_state[state] = 0
            self.c.hide_move_tile()
    
    def calc_world_pos(self, mappos):
        x = int(mappos.x)
        y = int(mappos.y)
        return Point3(x, y, 0)
    
    def calc_unit_pos(self, mappos):
        x = int(mappos.x)
        y = int(mappos.y)
        return Point3(x + (base.tile_size/2.0), y + (base.tile_size/2.0), 0)
    
    """ 
    -----------------------------------
    debugging procedures and tasks
    -----------------------------------
    """ 
    def change(self):
        print "a"
        self.clear_world()
        if self.level_name == 'level2.txt':
            self.level_name = 'level.txt'
        else:
            self.level_name = 'level2.txt'
        self.init_world()
        
    def info(self):
        #print render.ls()
        #print render.analyze()
        print self.units[0].model.ls()
        
    def printer(self, task):
        return task.cont    
 