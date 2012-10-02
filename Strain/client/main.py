#############################################################################
# IMPORTS
#############################################################################

# python imports
import logging

# panda3D imports
from direct.showbase.ShowBase import ShowBase#@UnresolvedImport
from panda3d.core import loadPrcFile, WindowProperties, VBase4, ConfigVariableInt, ConfigVariableString#@UnresolvedImport
from panda3d.core import PStatClient#@UnresolvedImport
from direct.fsm import FSM#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from panda3d.rocket import *

# strain related imports
from strain.loginscreen import LoginScreen
from strain.browser import Browser
from strain.lobby import Lobby
from strain.gametype import GameType
from strain.client_messaging import ClientMsg
from strain.net import Net

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
        
        #menu data
        self.players = None
        self.active_games = None
        self.unaccepted_games = None
        self.waiting_games = None
        self.news_items = None
        self.levels = None
        self.game_id = None
        self.map = None
        self.budget = None
        self.game_name = None
        self.browser = None
        self.lobby = None
        
        #setup screen (initialize ShowBase to create window)
        self.screen = Screen(self, (980,720))
        self.rRegion = RocketRegion.make('main_menu', base.win)
        self.rContext = self.rRegion.getContext()
        ih = RocketInputHandler()
        base.mouseWatcher.attachNewNode(ih)
        self.rRegion.setInputHandler(ih)
        
        # Setup FSM
        self.fsm = AppFSM(self, 'AppFSM')
        
        # Init Network parameters
        server_ip = ConfigVariableString("server-ip", "127.0.0.1").getValue()
        server_port = ConfigVariableInt("server-port", "56005").getValue()         
        ClientMsg.setupAddress(server_ip, server_port)
        ClientMsg.notify = self.logger

        # Initialize network communicator
        self.net_manager = Net(self)
        self.net_manager.startNet()

        base.accept('i', render.ls)
        
        # Start with Login screen
        self.fsm.request('Login')
        
    def newGameStarted(self, game_id):
        from strain.gameinstance import GameInstance
        self.game_instance = GameInstance(self, 'New', game_id)

#========================================================================
#
class AppFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

        self.defaultTransitions = {
            'Login' : [ 'Lobby' ],
            'Lobby' : ['Browser', 'NewGame'],
            'Browser' : [ 'ContinueGame' ],
            'NewGame' : [ 'Deploy' ]
            }
        
    def enterLogin(self):
        base.win.setClearColor(VBase4(0, 0, 0, 0))
        self.parent.login = LoginScreen(self.parent)
    
    def exitLogin(self):
        self.parent.login.cleanup()      
        del self.parent.login

    def enterLobby(self):
        self.parent.lobby = Lobby(self.parent)
        
    def exitLobby(self):
        self.parent.lobby.cleanup()
        del self.parent.lobby
        
    def enterBrowser(self):
        self.parent.browser = Browser(self.parent)
        
    def exitBrowser(self):
        self.parent.browser.cleanup()
        del self.parent.browser
        
    def enterNewGame(self):
        #ClientMsg.startNewGame('base2', 1000, [ClientMsg.loggedIn(), 0], 0, "game #1")
        #ClientMsg.startNewGame('level2', 1000, [ClientMsg.loggedIn(), 0], 1, '')
        self.parent.gametype = GameType(self.parent)
    
    def exitNewGame(self):
        self.parent.gametype.cleanup()
        del self.parent.gametype
        
    def enterContinueGame(self):
        from strain.gameinstance import GameInstance
        self.parent.game_instance = GameInstance(self.parent, 'Continue', self.parent.game_id)
        
    def enterDeploy(self):
        ClientMsg.startNewGame(self.parent.map, self.parent.budget, [ClientMsg.loggedIn(), 0], 0, self.parent.game_name)
    
    def exitContinueGame(self):
        #TODO: ogs: kod za brisanje i deinicijalizaciju GameInstance
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

#############################################################################
# MAIN
#############################################################################

app = App()
run()
