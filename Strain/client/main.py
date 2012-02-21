#############################################################################
# IMPORTS
#############################################################################

# python imports
import logging
import logging.handlers

# panda3D imports
from direct.showbase.ShowBase import ShowBase#@UnresolvedImport
from panda3d.core import loadPrcFile, WindowProperties#@UnresolvedImport
from panda3d.core import TextNode, VBase4, AntialiasAttrib#@UnresolvedImport
from panda3d.core import ConfigVariableInt#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject#@UnresolvedImport
from direct.fsm import FSM#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectLabel#@UnresolvedImport
from direct.gui.OnscreenText import OnscreenText#@UnresolvedImport
from pandac.PandaModules import PStatClient#@UnresolvedImport


# strain related imports
from strain.client import Client
from strain.squadselector import Squadselector
import strain.utils as utils

#############################################################################
# GLOBALS
#############################################################################

loadPrcFile("./config/config.prc")

#############################################################################
# CLASSES
#############################################################################

#========================================================================
#
class App():
    def __init__(self):
        #from pandac.PandaModules import Thread
        #print 'Threading', Thread.isThreadingSupported()
        
        #setup logger
        self.logger = logging.getLogger('ClientLog')        
        hdlr = logging.handlers.RotatingFileHandler('Client.log', maxBytes = 1024*1024*3 )
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.DEBUG)
            
        #PStatClient.connect()
        
        #setup screen
        self.screen = Screen(self, (800,600))
        
        #setup FSM
        self.fsm = AppFSM(self, 'AppFSM')
        
        self.startLogin()
    
    def startLogin(self):
        #go to login screen
        self.fsm.request('LoginScreen')
        
    def startClient(self, type):
        #start client
        self.fsm.request('Client', type)
        
    def startSquadSelection(self):
        self.fsm.request('SquadSelection')
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
        self.parent.login.button_ultras.remove()
        self.parent.login.button_obs.remove()
        self.parent.login.button_replay.remove()
        self.parent.login.button_selector.remove()
        self.parent.login.commander.delete()
        self.parent.login.jumper.delete()
        self.parent.login.textObject.remove()       
        del self.parent.login

    def enterSquadSelection(self):
        base.win.setClearColor(VBase4(0.5, 0.5, 0.5, 0))
        self.parent.squad_selector = Squadselector(self.parent, self.parent.player)
        
    def exitSquadSelection(self):
        None
    
    def enterClient(self, type):
        base.win.setClearColor(VBase4(0, 0, 0, 0))
        self.parent.client = Client(self.parent, self.parent.player, type=type)
        
    def exitClient(self):
        None
        

#========================================================================
#
class LoginScreen():
    def __init__(self, parent):
        self.parent = parent
        font = loader.loadFont('frizqt__.ttf')
        legofont = loader.loadFont('legothick.ttf')
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
        
        self.button_ultras = DirectButton(text = ("Login as BLUE"),scale=.02,command=self.loginButUltrasPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_ultras.reparentTo(aspect2d)
        self.button_ultras.setPos(0.5, 0, -0.6) 
        
        self.button_obs = DirectButton(text = ("Login as Observer"),scale=.02,command=self.loginButObsPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_obs.reparentTo(aspect2d)
        self.button_obs.setPos(0.5, 0, -0.7)
        
        self.button_replay = DirectButton(text = ("Replay Viewer"),scale=.04,command=self.loginReplayPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_replay.reparentTo(aspect2d)
        self.button_replay.setPos(0.5, 0, -0.8)        
        
        self.button_selector = DirectButton(text = ("Squad selection"),scale=.04,command=self.loginSelectorPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_selector.reparentTo(aspect2d)
        self.button_selector.setPos(0.5, 0, -0.9)   

        ground_level = 0
        self.commander = utils.loadUnit('marine', 'sergeant', '1')
        self.commander.setPos(0, 20, -2)
        self.commander.reparentTo(render)
        self.commander.loop('overwatch')  
        
        self.jumper = utils.loadUnit('marine', 'sergeant', '1')
        self.jumper.setPos(2, 20, -2)
        self.jumper.reparentTo(render)
        self.jumper.loop('overwatch')   
        #self.jumper.setAntialias(AntialiasAttrib.MMultisample)       
        
        self.textObject = OnscreenText(text = 'STRAIN', pos = (0, 0.4), scale = 0.2, font=legofont, fg = (1,0,0,1))
    
    def loginButPressed(self, text=None):
        self.parent.player = self.entry_username.get()
        if self.parent.player != "Blue" and self.parent.player != "Red":
            self.parent.player = "Red"
        self.parent.startClient(type="Game")
        
    def loginButUltrasPressed(self, text=None):
        self.parent.player = "Blue"
        self.parent.startClient(type="Game")
        
    def loginButObsPressed(self, text=None):
        self.parent.player = "observer"
        self.parent.startClient(type="Game")    
        
    def loginReplayPressed(self, text=None):
        self.parent.player = "observer"
        self.parent.startClient(type="Replay")
        
    def loginSelectorPressed(self, text=None):
        self.parent.player = "Red"
        self.parent.startSquadSelection()

#========================================================================
#
class Screen(DirectObject):
    """The Screen Class manages window."""
    def __init__(self, parent, res=(1024,768)):
        self.parent = parent
        # Init pipe
        ShowBase()
        base.makeDefaultPipe()
        screen = (base.pipe.getDisplayWidth(), base.pipe.getDisplayHeight())
        win = WindowProperties.getDefault()
        xsize = ConfigVariableInt("resx", res[0]).getValue()
        ysize = ConfigVariableInt("resy", res[1]).getValue()
        win.setSize(xsize, ysize)
        #win.setOrigin(screen[0]/2 - res[0]/2, screen[1]/2 - res[1]/2)
        win.setFullscreen(False)
        base.openDefaultWindow(win)        
        #base.setBackgroundColor(.05,.05,.05)
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
