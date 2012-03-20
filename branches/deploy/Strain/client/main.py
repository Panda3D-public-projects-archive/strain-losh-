#############################################################################
# IMPORTS
#############################################################################

# python imports
import logging

# panda3D imports
from direct.showbase.ShowBase import ShowBase#@UnresolvedImport
from panda3d.core import loadPrcFile, WindowProperties, VBase4, ConfigVariableInt#@UnresolvedImport
from direct.fsm import FSM#@UnresolvedImport
from panda3d.core import PStatClient#@UnresolvedImport


# strain related imports
from strain.loginscreen import LoginScreen


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
            'Login' : [ 'Login2Browser' ],
            'Login2Browser' : [ 'Browser' ],
            'Browser' : [ 'Browser2NewGame', 'Browser2ContinueGame', 'Browser2ReplayViewer' ],
            'Browser2NewGame' : [ 'NewGame' ],
            'Browser2ContinueGame' : [ 'ContinueGame' ],
            'Browser2ReplayViewer' : [ 'ReplayViewer' ]
            }

    def enterLogin(self):
        base.win.setClearColor(VBase4(0, 0, 0, 0))
        self.parent.login = LoginScreen(self.parent)
    
    def exitLogin(self):
        self.parent.login.cleanup()      
        del self.parent.login


#========================================================================
#
class Screen():
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
