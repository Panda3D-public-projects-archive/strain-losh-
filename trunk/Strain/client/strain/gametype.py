#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from panda3d.core import TextNode#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectLabel#@UnresolvedImport
from panda3d.rocket import *
from gametypedatasource import *
# strain related imports


class GameType():
    def __init__(self, parent):
        self.parent = parent

        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        self.previous_element = None
        self.levelData = LevelListDataSource("level_list")
        self.armySize = ArmySizeDataSource("army_size")
        self.playerNumber = PlayerNumberDataSource("player_number")
        
        self.doc = self.parent.rContext.LoadDocument('data/rml/game_type.rml')
        
        element = self.doc.GetElementById('status_bar')
        element.inner_rml = 'Username: ' + self.parent.player
        
        element = self.doc.GetElementById('deploy')
        element.AddEventListener('click', self.deployUnits, True)
        
        self.datagrid = self.doc.GetElementById('datagrid')
        self.datagrid.AddEventListener('click', self.rowSelected, True)
        
        self.doc.Show()
        
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.parent = None
    
    def deployUnits(self):
        self.parent.fsm.request('Deploy')

    def rowSelected(self):
        if event.target_element.parent_node.tag_name == "datagridrow":
            for child in self.datagrid.child_nodes:
                if child.tag_name == "datagridbody":
                    for row in child.child_nodes:
                        row.class_name = ""
            event.target_element.parent_node.class_name = "selected"
            self.setLevelInfo(event.target_element.parent_node.table_relative_index)
        
    def setLevelInfo(self, index):
        image = self.doc.GetElementById("level_info_left")
        image.inner_rml = '<img height="215px" width="215px" src="../levels/' + self.levelData.levels[index]['name'] + '.png"/>'
        name = self.doc.GetElementById("name")
        name.inner_rml = 'Map name: ' + self.levelData.levels[index]['name']
        players = self.doc.GetElementById("players")
        players.inner_rml = 'Max players: ' + str(self.levelData.levels[index]['players'])
        size = self.doc.GetElementById("size")
        size.inner_rml = 'Map size: ' + self.levelData.levels[index]['size']
        description = self.doc.GetElementById("description")
        description.inner_rml = self.levelData.levels[index]['description']
        