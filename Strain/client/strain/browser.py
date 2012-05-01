#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from panda3d.core import TextNode#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectLabel#@UnresolvedImport
from panda3d.rocket import *

# strain related imports


class Browser():
    def __init__(self, parent):
        self.parent = parent
        
        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        
        doc = self.parent.rContext.LoadDocument('data/rml/game.rml')

        element = doc.GetElementById('btn_new')
        element.AddEventListener('click', self.newGame, True)
        element = doc.GetElementById('btn_continue')
        element.AddEventListener('click', self.contGame, True)
        element = doc.GetElementById('btn_obs')
        element.AddEventListener('click', self.obsGame, True)
        element = doc.GetElementById('btn_replay')
        element.AddEventListener('click', self.viewReplay, True)
        
        element = doc.GetElementById('status_bar')
        element.inner_rml = 'Username: ' + self.parent.player
        
        doc.Show()
        
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.parent = None
    
    def newGame(self):
        self.parent.fsm.request('NewGame')
        
    def contGame(self):
        self.parent.fsm.request('ContinueGame')
        
    def obsGame(self):
        None
        
    def viewReplay(self):
        None
        
    def backToMain(self):
        self.parent.fsm.request('Login')