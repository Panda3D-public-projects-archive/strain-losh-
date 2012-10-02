#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from panda3d.core import TextNode#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectLabel#@UnresolvedImport
from panda3d.rocket import *

# strain related imports

class Lobby():
    def __init__(self, parent):
        self.parent = parent
#        self.game_id = ''
#        self.game_list = []
#        self.game_list_position = 'top'
#        self.top_game_index = 0
        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        
        self.doc = self.parent.rContext.LoadDocument('data/rml/lobby.rml')

        element = self.doc.GetElementById('btn1')
        element.AddEventListener('click', self.newGame, True)
        element = self.doc.GetElementById('btn2')
        element.AddEventListener('click', self.continueGame, True)
#        element = self.doc.GetElementById('btn_new')
#        element.AddEventListener('click', self.newGame, True)
#        element = self.doc.GetElementById('btn_enter')
#        element.AddEventListener('click', self.enterGame, True)
#        element = self.doc.GetElementById('main_middle')
#        for child in element.child_nodes:
#            child.AddEventListener('click', self.selectGame, True)
#        element = self.doc.GetElementById('btn_obs')
#        element.AddEventListener('click', self.obsGame, True)
#        element = self.doc.GetElementById('btn_replay')
#        element.AddEventListener('click', self.viewReplay, True)
        
#        self.updateGames()
#        self.updateNews()
#        
#        element = self.doc.GetElementById('status_bar')
#        element.inner_rml = 'Username: ' + self.parent.player
        
        element = self.doc.GetElementById('first_chatline')
        element.ScrollIntoView(False)
        
        self.updateNews()
        
        self.doc.Show()
        
        
    def newGame(self):
        self.parent.fsm.request('NewGame')
        
    def continueGame(self):
        self.parent.fsm.request('Browser')
        
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.parent = None
    
    def updateNews(self):
        inner_rml = ' '
        if self.parent.news_items != None:
            for row in self.parent.news_items:
                date = str(row[1])
                text = row[2]
                inner_rml += '<div class="news_item">\
                                 <div class="news_item_date">' + date + '</div>\
                                 <div class="news_item_text">' + text + '</div>\
                              </div>'
        element = self.doc.GetElementById('news_item_container')
        element.inner_rml = inner_rml