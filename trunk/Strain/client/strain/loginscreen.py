#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from panda3d.core import TextNode, BitMask32, TextureStage, NodePath, DirectionalLight, AmbientLight, Vec4, Vec3, VBase4#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectLabel#@UnresolvedImport
from direct.gui.OnscreenText import OnscreenText#@UnresolvedImport
from direct.gui.OnscreenImage import OnscreenImage
from direct.filter.CommonFilters import CommonFilters#@UnresolvedImport
from panda3d.rocket import *

# strain related imports
import strain.utils as utils
from strain.client_messaging import ClientMsg


class LoginScreen():
    
    def __init__(self, parent):
        self.parent = parent   
        
        LoadFontFace("data/fonts/Delicious-Roman.otf")
        LoadFontFace("data/fonts/verdana.ttf")        
        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        
        #context.LoadDocument('assets/background.rml').Show()
        
        self.doc = self.parent.rContext.LoadDocument('data/rml/login_screen.rml')
        self.doc.Show()
        
        element = self.doc.GetElementById('log_in')
        element.AddEventListener('click', self.loginButPressed, True)
        element = self.doc.GetElementById('log_in_red')
        element.AddEventListener('click', self.loginButRedPressed, True)
        element = self.doc.GetElementById('log_in_blue')
        element.AddEventListener('click', self.loginButBluePressed, True)
    
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.parent = None
    
    def loginButPressed(self):
        username = self.doc.GetElementById("username").value
        password = self.doc.GetElementById("password").value
        print "Username:", username
        print "Password:", password
        
        #TODO: ogi_net: ovdje sredit kaj se desi ak ne uspije logirat
        #----<<<<<<<<---oprez! ClientMsg.login() vraca 0 ak je uspio, inace vraca error msg ------->>>>>>>>------- 
        login_error = ClientMsg.login(username, password) 
        if not login_error:
            #sve je ok
            self.parent.player_id = ClientMsg.loggedIn()
            pass
        else:
            #greska
            print "LOGIN FAILED: - ", login_error
            return 
        
        self.parent.player = username
        self.parent.fsm.request('Browser')


    def loginButRedPressed(self):
        username = 'Red'
        login_error = ClientMsg.login(username, '') 
        if not login_error:
            self.parent.player_id = ClientMsg.loggedIn()
        else:
            print "LOGIN FAILED: - ", login_error
            return 
        
        self.parent.player = username
        self.parent.fsm.request('Browser')
        
        
    def loginButBluePressed(self):
        username = 'Blue'
        login_error = ClientMsg.login(username, '') 
        if not login_error:
            self.parent.player_id = ClientMsg.loggedIn()
        else:
            print "LOGIN FAILED: - ", login_error
            return 
        
        self.parent.player = username
        self.parent.fsm.request('Browser')
        