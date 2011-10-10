from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from Interface import Interface
from Engine import Engine
from GraphicsEngine import GraphicsEngine
        
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
        
        self.engine = Engine()
        self.interface = Interface()  
        self.graphics_engine = GraphicsEngine(self.engine)


        self.accept('i', self.info)
        self.accept('escape', self.escape)
        self.accept('aspectRatioChanged', self.redraw)
    
    def escape(self):
        if self.interface.selected_unit:
            self.interface.deselectUnit()
        else:
            taskMgr.stop()
    
    def redraw(self):
        self.graphics_engine.redraw()

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
 