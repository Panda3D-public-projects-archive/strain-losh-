#############################################################################
# IMPORTS
#############################################################################

# python imports
import logging

# panda3D imports
from direct.showbase.ShowBase import ShowBase#@UnresolvedImport
from panda3d.core import loadPrcFile, WindowProperties, VBase4, ConfigVariableInt#@UnresolvedImport
from panda3d.core import PStatClient#@UnresolvedImport
from direct.fsm import FSM#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from panda3d.rocket import *

# strain related imports
from strain.loginscreen import LoginScreen
from strain.browser import Browser
from strain.client import Client
from strain.gametype import GameType

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
        #setup logger
        self.logger = logging.getLogger('ClientLog')
        hdlr = logging.FileHandler('Client.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.DEBUG)
            
        #PStatClient.connect()
        
        #setup screen (initialize ShowBase to create window)
        self.screen = Screen(self, (800,600))
        self.rRegion = RocketRegion.make('main_menu', base.win)
        self.rContext = self.rRegion.getContext()
        ih = RocketInputHandler()
        base.mouseWatcher.attachNewNode(ih)
        self.rRegion.setInputHandler(ih)
        #setup FSM
        self.fsm = AppFSM(self, 'AppFSM')
        
        #start with Login screen
        self.fsm.request('Login')

#========================================================================
#
class AppFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

        self.defaultTransitions = {
            'Login' : [ 'Browser' ],
            'Browser' : [ 'NewGame', 'ContinueGame', 'ReplayViewer' ],
            'NewGame' : ['Deploy']
            }
        
    def enterLogin(self):
        base.win.setClearColor(VBase4(0, 0, 0, 0))
        self.parent.login = LoginScreen(self.parent)
    
    def exitLogin(self):
        self.parent.login.cleanup()      
        del self.parent.login
        
    def enterBrowser(self):
        self.parent.browser = Browser(self.parent)
        
    def exitBrowser(self):
        self.parent.browser.cleanup()
        del self.parent.browser
        
    def enterNewGame(self):
        self.parent.gametype = GameType(self.parent)
    
    def exitNewGame(self):
        self.parent.gametype.cleanup()
        del self.parent.gametype
        
    def enterDeploy(self):
        self.parent.client = Client(self.parent, self.parent.player, self.parent.player_id, "NewGame")
    
    def exitDeploy(self):
        None
        
    def enterContinueGame(self):
        self.parent.client = Client(self.parent, self.parent.player, self.parent.player_id, "ContGame")
    
    def exitContinueGame(self):
        None
        
    def enterReplayViewer(self):
        None
        
    def exitReplayViewer(self):
        None


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
        win.setFullscreen(False)
        base.openDefaultWindow(win)
        
        base.accept('1', render.ls)
        base.accept('2', self.debug)
    
    def debug(self):
        print taskMgr

#############################################################################
# MAIN
#############################################################################

app = App()
run()
