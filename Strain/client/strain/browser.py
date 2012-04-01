#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from panda3d.core import TextNode#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectLabel#@UnresolvedImport


# strain related imports


class Browser():
    def __init__(self, parent):
        self.parent = parent
        font = loader.loadFont('frizqt__.ttf')
        self.label_username = DirectLabel(text = "Username:", scale=.05, frameColor=(0,0,0,0), text_font=font, text_align=TextNode.ARight, text_fg=(1,1,1,1))
        self.username = DirectLabel(text = self.parent.player, scale=.05, frameColor=(0,0,0,0), text_font=font, text_align=TextNode.ARight, text_fg=(1,1,1,1))
        self.label_username.reparentTo(aspect2d)
        self.label_username.setPos(-0.8, 0, 0.9)
        self.username.reparentTo(aspect2d)
        self.username.setPos(-0.7, 0, 0.9)
        
        self.but_new = DirectButton(text = ("Start new game"),scale=.05,command=self.newGame,text_font=font, text_align=TextNode.ACenter)
        self.but_cont = DirectButton(text = ("Continue game"),scale=.05,command=self.contGame,text_font=font, text_align=TextNode.ACenter)
        self.but_obs = DirectButton(text = ("Observe game"),scale=.05,command=self.obsGame,text_font=font, text_align=TextNode.ACenter)
        self.but_rep = DirectButton(text = ("View replay"),scale=.05,command=self.viewReplay,text_font=font, text_align=TextNode.ACenter)
        
        self.but_new.reparentTo(aspect2d)
        self.but_new.setPos(-0.8, 0, 0.7)
        self.but_cont.reparentTo(aspect2d)
        self.but_cont.setPos(-0.8, 0, 0.6)
        self.but_obs.reparentTo(aspect2d)
        self.but_obs.setPos(-0.8, 0, 0.5)
        self.but_rep.reparentTo(aspect2d)
        self.but_rep.setPos(-0.8, 0, 0.4)
    
    def cleanup(self):
        self.label_username.remove()
        self.username.remove()
        self.but_new.remove()
        self.but_cont.remove()
        self.but_obs.remove()
        self.but_rep.remove()
        
        self.parent = None
    
    def newGame(self):
        self.parent.fsm.request('NewGame')
        
    def contGame(self):
        self.parent.fsm.request('ContinueGame')
        
    def obsGame(self):
        None
        
    def viewReplay(self):
        None
        