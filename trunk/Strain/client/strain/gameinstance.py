from panda3d.core import *
from direct.fsm import FSM
from strain.client_messaging import ClientMsg
from strain.share import *

class GameInstance():
    def __init__(self, parent, event, game_id):
        self.parent = parent
        self.fsm = GameInstanceFSM(self, 'GameInstanceFSM')

        # Initialize client-side copy of server data
        from strain.local.localengine import LocalEngine
        self.local_engine = LocalEngine(self)

        self.player = self.parent.player
        self.player_id = self.parent.player_id
        
        # Initialize game instance variables:
        # Selected unit ID
        self.sel_unit_id = None
        # Current turn number
        self.turn_number = 0
        # ID of player currently on turn
        self.turn_player = 0
        # Flag to check if animation is in process
        self._anim_in_process = False

        #ClientMsg.setGameId(game_id)        
        
        if event == 'New':
            self.fsm.request('NewGame', game_id)
        elif event == 'Continue':
            self.fsm.request('ContinueGame', game_id)
        
    def deselectUnit(self):
        self.movement.deleteUnitAvailMove()
        #self.sgm.hideVisibleEnemies()
        self.interface.clearUnitData()
        
        if self.sel_unit_id != None:
            self.render_manager.unit_marker_renderer.clearSelected(self.sel_unit_id)
        self.sel_unit_id = None
    
    def selectUnit(self, unit_id):
        if self._anim_in_process == True:
            return
        
        if not self.local_engine.units.has_key(unit_id):
            return
        
        if self.sel_unit_id != unit_id:
            self.deselectUnit()
            self.sel_unit_id = unit_id
            self.interface.processUnitData(unit_id)
            self.interface.printUnitData(unit_id)
            self.interface.refreshUnitInfo(unit_id)
            # If it is our turn, display available move tiles
            if self.player_id == self.turn_player:
                self.render_manager.unit_marker_renderer.setSelected(unit_id)
                self.movement.calcUnitAvailMove(unit_id)
                #self.sgm.showVisibleEnemies(unit_id)        

    def selectNextUnit(self):
        if self.sel_unit_id == None:
            last = 0
        else:
            last = self.sel_unit_id
        
        d = {}
        for unit_id in self.local_engine.units.iterkeys():
            if self.isThisMyUnit(unit_id):
                d[unit_id] = self.local_engine.units[unit_id]
        
        l = sorted(d.iterkeys())
        if len(l) <= 1:
            return
        else:
            if l[-1] == last:
                new_unit_id = l[0]
            else:
                for i in l:
                    if i > last:
                        new_unit_id = i
                        break
            self.selectUnit(new_unit_id)
        
    def selectPrevUnit(self):
        if self.sel_unit_id == None:
            # TODO: ogs: Kaj fakat?
            last = 9999999
        else:
            last = self.sel_unit_id
            
        d = {}
        for unit_id in self.local_engine.units.iterkeys():
            if self.isThisMyUnit(unit_id):
                d[unit_id] = self.local_engine.units[unit_id]
        
        l = sorted(d.iterkeys())
        l.reverse()
        if len(l) <= 1:
            return
        else:
            if l[-1] == last:
                new_unit_id = l[0]
            else:
                for i in l:
                    if i < last:
                        new_unit_id = i
                        break
            self.selectUnit(new_unit_id)           

class GameInstanceFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

    def enterNewGame(self, game_id):
        from strain.renderer.cameramanager import CameraManager
        self.parent.camera_manager = CameraManager(self.parent)
        
        from strain.renderer.rendermanager import RenderManager
        self.parent.render_manager = RenderManager(self.parent) 
        
        from strain.interface import Interface
        self.parent.interface = Interface(self.parent)
        
        from strain.movement import Movement
        self.parent.movement = Movement(self.parent)
        
        #ClientMsg.forceFirstTurn()
        ClientMsg.enterGame(game_id)
        
    def exitNewGame(self):
        None
        
    def enterDeploy(self):
        None
        """
        from strain.deploy import Deploy
        self.parent.deploy = Deploy(self.parent, self.parent.username, self.parent.user_id)
        """
    
    def exitDeploy(self):
        None
    
    def enterContinueGame(self, game_id):
        from strain.renderer.cameramanager import CameraManager
        self.parent.camera_manager = CameraManager(self.parent)
        
        from strain.renderer.rendermanager import RenderManager
        self.parent.render_manager = RenderManager(self.parent) 
        
        from strain.interface import Interface
        self.parent.interface = Interface(self.parent)
        
        from strain.movement import Movement
        self.parent.movement = Movement(self.parent)
        
        #TODO: ogs: maknuti jednom kad profunkcionira veza s bazom
        #ClientMsg.forceFirstTurn()
        ClientMsg.enterGame( game_id )
        #taskMgr.doMethodLater(1, ClientMsg.forceFirstTurn, 'ForceTurn', extraArgs = [])
        
    def exitContinueGame(self):
        None
        
      