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
        
        self.levelData = LevelListDataSource("level_list")
        self.armySize = ArmySizeDataSource("army_size")
        self.playerNumber = PlayerNumberDataSource("player_number")
        
        doc = self.parent.rContext.LoadDocument('data/rml/game_type.rml')
        doc.Show()
        
        element = doc.GetElementById('deploy')
        element.AddEventListener('click', self.deployUnits, True)
        
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        self.parent = None
    
    def deployUnits(self):
        self.parent.fsm.request('Deploy')
        