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
        self.game_id = ''
        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        
        self.doc = self.parent.rContext.LoadDocument('data/rml/main_menu.rml')

        element = self.doc.GetElementById('btn_new')
        element.AddEventListener('click', self.newGame, True)
        element = self.doc.GetElementById('btn_enter')
        element.AddEventListener('click', self.enterGame, True)
        element = self.doc.GetElementById('main_middle')
        for child in element.child_nodes:
            child.AddEventListener('click', self.selectGame, True)
#        element = self.doc.GetElementById('btn_obs')
#        element.AddEventListener('click', self.obsGame, True)
#        element = self.doc.GetElementById('btn_replay')
#        element.AddEventListener('click', self.viewReplay, True)
        
        self.updateGames()
        self.updateNews()
        
        element = self.doc.GetElementById('status_bar')
        element.inner_rml = 'Username: ' + self.parent.player
        
        self.doc.Show()
    
    def addGameItemEvents(self):
        element = self.doc.GetElementById('main_middle')
        for child in element.child_nodes:
            child.AddEventListener('click', self.selectGame, True)
                
    def selectGame(self):
        for child in event.current_element.parent_node.child_nodes:
            child.class_name = "game_item"
        event.current_element.class_name = "game_item_selected"
        self.game_id = int(event.current_element.id)
        self.parent.game_id = self.game_id
        self.showGameDetails()
        
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.parent = None
    
    def newGame(self):
        self.parent.fsm.request('NewGame')
        
    def enterGame(self):
        self.parent.fsm.request('ContinueGame')
        
    def obsGame(self):
        None
        
    def viewReplay(self):
        None
        
    def backToMain(self):
        self.parent.fsm.request('Login')
        
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
        element = self.doc.GetElementById('main_left')
        element.inner_rml = inner_rml
                    
    def updateGames(self):
        inner_rml = ' '
        if self.parent.unaccepted_games != None:
            for row in self.parent.unaccepted_games:
                game_id = str(row[0])
                game_name = row[10]
                map = row[1]
                turn = str(row[3])
                on_turn_id = row[4]
                for player in self.parent.players:
                    if player[0] == on_turn_id:
                        on_turn = player[1]
                inner_rml += '<div class="game_item" id="' + game_id + '"> \
                              <div class="game_item_text">' + game_name + '</div> \
                              <div class="game_item_text"> Turn: ' + turn + ', On turn: ' + on_turn + '</div> \
                              <div class="game_item_text">Status: Invited</div> \
                              </div>'
        
        if self.parent.active_games != None:
            for row in self.parent.active_games:
                game_id = str(row[0])
                game_name = row[10]
                map = row[1]
                turn = str(row[3])
                on_turn_id = row[4]
                for player in self.parent.players:
                    if player[0] == on_turn_id:
                        on_turn = player[1]
                inner_rml += '<div class="game_item" id="' + game_id + '"> \
                              <div class="game_item_text">' + game_name + '</div> \
                              <div class="game_item_text"> Turn: ' + turn + ', On turn: ' + on_turn + '</div> \
                              <div class="game_item_text">Status: Active</div> \
                              </div>'
        
        if self.parent.waiting_games != None:
            for row in self.parent.waiting_games:
                game_id = str(row[0])
                game_name = row[10]
                map = row[1]
                turn = str(row[3])
                on_turn_id = row[4]
                for player in self.parent.players:
                    if player[0] == on_turn_id:
                        on_turn = player[1]
                inner_rml += '<div class="game_item" id="' + game_id + '"> \
                              <div class="game_item_text">' + game_name + '</div> \
                              <div class="game_item_text"> Turn: ' + turn + ', On turn: ' + on_turn + '</div> \
                              <div class="game_item_text">Status: Waiting</div> \
                              </div>'
        
        element = self.doc.GetElementById('main_middle')
        element.inner_rml = inner_rml
        self.addGameItemEvents()
        
    def showGameDetails(self):
        inner_rml = ' '
        for row in self.parent.unaccepted_games:
            if self.game_id == row[0]:
                map = row[1]
                budget = str(row[2])
                created = str(row[6])
                name = row[10]
        for row in self.parent.active_games:
            if self.game_id == row[0]:
                map = row[1]
                budget = str(row[2])
                created = str(row[6])
                name = row[10]
               
        for row in self.parent.waiting_games:
            if self.game_id == row[0]:
                map = row[1]
                budget = str(row[2])
                created = str(row[6])
                name = row[10]
        
        inner_rml += '<div class="game_item_text">' + name + '</div> \
                      <div class="game_item_text">Created on ' + created + '</div>\
                      <div class="game_item_text">Map: ' + map + '</div>\
                      <div class="game_item_text">Budget: ' + budget + '</div>'
        element = self.doc.GetElementById('main_right')
        element.inner_rml = inner_rml