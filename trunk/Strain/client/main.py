#############################################################################
# IMPORTS
#############################################################################

# python imports
import logging

# panda3D imports
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, WindowProperties#@UnresolvedImport
from panda3d.core import TextNode, VBase4#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectLabel
from direct.gui.OnscreenText import OnscreenText

# strain related imports
from strain.client import Client
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
        #setup logger
        self.logger = logging.getLogger('ClientLog')
        hdlr = logging.FileHandler('Client.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr) 
        self.logger.setLevel(logging.DEBUG)
        
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
        self.parent.login.commoner1.delete()
        self.parent.login.commoner2.delete()
        self.parent.login.commander.delete()
        self.parent.login.heavy.delete()
        self.parent.login.assault.delete()
        self.parent.login.assault2.delete()
        self.parent.login.assault3.delete() 
        self.parent.login.textObject.remove()       
        del self.parent.login

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
        
        self.button_ultras = DirectButton(text = ("Login as Ultramarines"),scale=.02,command=self.loginButUltrasPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_ultras.reparentTo(aspect2d)
        self.button_ultras.setPos(0.5, 0, -0.6) 
        
        self.button_obs = DirectButton(text = ("Login as Berserker"),scale=.02,command=self.loginButObsPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_obs.reparentTo(aspect2d)
        self.button_obs.setPos(0.5, 0, -0.7)
        
        self.button_replay = DirectButton(text = ("Replay Viewer"),scale=.04,command=self.loginReplayPressed, text_font=font, text_align=TextNode.ACenter)
        self.button_replay.reparentTo(aspect2d)
        self.button_replay.setPos(0.5, 0, -0.8)        
        
        ground_level = -1.6
        self.commoner1 = utils.loadUnit('common', 'Bolter')
        self.commoner1.setPos(-3, 25, ground_level)
        self.commoner1.loop('idle_combat01')
        self.commoner2 = utils.loadUnit('common', 'Bolter')
        self.commoner2.setPos(-4.5, 23.5, ground_level)
        self.commoner2.loop('idle_combat02')           
        self.heavy = utils.loadUnit('heavy', 'Heavy Bolter')
        self.heavy.setPos(-2, 27, ground_level)
        self.heavy.loop('idle_stand03')             
        self.commander = utils.loadUnit('commander', 'Thunder Hammer')
        self.commander.setPos(0, 20, ground_level)
        self.commander.loop('idle_stand02') 
        self.assault = utils.loadUnit('assault', 'Chain Sword,Bolt Pistol')
        self.assault.setPos(4, 25, ground_level)
        self.assault.loop('idle_stand01')
        self.assault2 = utils.loadUnit('assault', 'Power Axe,Bolt Pistol')
        self.assault2.setPos(2.5, 23, ground_level)
        self.assault2.loop('idle_stand02')  
        self.assault3 = utils.loadUnit('assault', 'Chain Sword,Plasma Pistol')
        self.assault3.setPos(6, 23, ground_level)
        self.assault3.loop('idle_stand03')  
        
        self.textObject = OnscreenText(text = 'STRAIN', pos = (0, 0.4), scale = 0.2, font=legofont, fg = (1,0,0,1))
    
    def loginButPressed(self, text=None):
        self.parent.player = self.entry_username.get()
        if self.parent.player != "ultramarines" and self.parent.player != "blood angels":
            self.parent.player = "blood angels"
        self.parent.startClient(type="Game")
        
    def loginButUltrasPressed(self, text=None):
        self.parent.player = "ultramarines"
        self.parent.startClient(type="Game")
        
    def loginButObsPressed(self, text=None):
        self.parent.player = "observer"
        self.parent.startClient(type="Game")    
        
    def loginReplayPressed(self, text=None):
        self.parent.player = "observer"
        self.parent.startClient(type="Replay")

#========================================================================
#
class Screen(DirectObject):
    """The Screen Class manages window."""
    def __init__(self, parent, res=(800,600)):
        self.parent = parent
        # Init pipe
        ShowBase()
        base.makeDefaultPipe()
        screen = (base.pipe.getDisplayWidth(), base.pipe.getDisplayHeight())
        win = WindowProperties.getDefault()
        win.setSize(res[0], res[1])
        #win.setOrigin(screen[0]/2 - res[0]/2, screen[1]/2 - res[1]/2)
        win.setFullscreen(False)
        base.openDefaultWindow(win)        
        #base.setBackgroundColor(.05,.05,.05)
        # TODO: ogs: enableati auto shader samo na odredjenim nodepathovima
        #render.setShaderAuto()
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
