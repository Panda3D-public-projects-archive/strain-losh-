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
from direct.actor.Actor import Actor

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
        self.cuber = Actor('cuber', {'no':'cuber-noway', 'yes':'cuber-yay'})
        self.cuber.reparentTo(render)
        self.cuber.setPos(-4, 20, -2)
        self.cuber.setColor(1, 0, 0)
        self.cuber.loop('no')
        self.cuber2 = Actor('cuber', {'no':'cuber-noway', 'yes':'cuber-yay'})
        self.cuber2.reparentTo(render)
        self.cuber2.setPos(4, 20, -2)
        self.cuber2.setColor(0, 0, 1)
        self.cuber2.loop('yes')        
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(0.7, 0.7, 0.7, 1.0))
        self.dlnp1 = render.attachNewNode(dlight1)
        self.dlnp1.setHpr(0, -50, 0)
        render.setLight(self.dlnp1)
        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        self.alnp = render.attachNewNode(alight)
        render.setLight(self.alnp)        

    
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.cuber.cleanup()
        self.cuber.remove()
        self.cuber2.cleanup()
        self.cuber2.remove()
        render.setLightOff()
        self.dlnp1.remove()
        self.alnp.remove()
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
        self.parent.fsm.request('Lobby')


    def loginButRedPressed(self):
        username = 'Red'
        login_error = ClientMsg.login(username, username) 
        if not login_error:
            self.parent.player_id = ClientMsg.loggedIn()
        else:
            print "LOGIN FAILED: - ", login_error
            return 
        
        self.parent.player = username
        self.parent.fsm.request('Lobby')
        
        
    def loginButBluePressed(self):
        username = 'Blue'
        login_error = ClientMsg.login(username, username) 
        if not login_error:
            self.parent.player_id = ClientMsg.loggedIn()
        else:
            print "LOGIN FAILED: - ", login_error
            return 
        
        self.parent.player = username
        self.parent.fsm.request('Lobby')
        