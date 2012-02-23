#############################################################################
# IMPORTS
#############################################################################

# python imports
import cPickle as pickle
import time as time
import copy

# panda3D imports


# strain related imports
from client_messaging import *
import utils as utils

#========================================================================
#
class Net():
    def __init__(self, parent):
        self.parent = parent
        
        # Set logging through our global logger
        self.log = self.parent.parent.logger
        ClientMsg.log = self.parent.parent.logger
       
    def startNet(self):
        # Create main network messaging task which initiates connection
        taskMgr.add(self.msgTask, "msg_task") 
        
    def startReplay(self, replay):
        self.replay_msg_list = pickle.load(open(replay, 'r'))
        self.replay_msg_num = 0
        taskMgr.add(self.replayMsgTask, "replay_msg_task")

    def handleMsg(self, msg):
        """Handles incoming messages."""
        self.log.info("Received message: %s", msg[0])
        #print '--------START------------'
        #print 'Incoming message', msg[0]
        #print 'Message body', msg[1]
        #print '----------END----------'
        #========================================================================
        #
        if msg[0] == ENGINE_STATE:
            self.parent._message_in_process = True
            self.parent.level = pickle.loads(msg[1]['level'])
            self.parent.turn_number = msg[1]['turn']
            self.parent.players = pickle.loads(msg[1]['players'])
            # TODO: ogs: Inace cu znati player_id kad se ulogiram pa necu morati ovako dekodirati
            for p in self.parent.players:
                if p['name'] == self.parent.player:
                    self.parent.player_id = p['id']
            self.parent.turn_player = self.parent.getPlayerName(msg[1]['active_player_id'])
            self.parent.units = pickle.loads(msg[1]['units'])
            self.parent.inactive_units = pickle.loads(msg[1]['dead_units'])
            self.parent.sgm.deleteLevel()
            self.parent.sgm.deleteUnits()
            self.parent.sgm.loadLevel(self.parent.level)
            self.parent.sgm.loadUnits()
            self.parent.clearState()            
            self.parent.interface.refreshStatusBar()
            for unit_id in self.parent.units.iterkeys():
                if self.parent.isThisMyUnit(unit_id):
                    self.parent.interface.refreshUnitInfo(unit_id) 
            m = self.parent.getInvisibleTiles()
            self.parent.sgm.level_mesh.setInvisibleTiles(m)           
            self.parent._message_in_process = False
        #========================================================================
        #
        elif msg[0] == MOVE:
            self.parent._message_in_process = True
            self.parent.handleMove(msg[1])
        #========================================================================
        #
        elif msg[0] == NEW_TURN:
            self.parent._message_in_process = True            
            self.parent.newTurn()
            self.parent.turn_number = msg[1]['turn']
            self.parent.turn_player = self.parent.getPlayerName(msg[1]['active_player_id'])
            units = pickle.loads(msg[1]['units'])
            self.parent.interface.refreshStatusBar()
            for unit in units.itervalues():
                self.parent.refreshUnit(unit)
            self.parent.inactive_units = pickle.loads(msg[1]['dead_units'])
            for unit_id in self.parent.units.iterkeys():
                if self.parent.isThisMyUnit(unit_id):
                    self.parent.interface.refreshUnitInfo(unit_id)
            self.parent.handleNewTurn()
        #========================================================================
        #
        elif msg[0] == UNIT:
            self.parent._message_in_process = True            
            unit = msg[1]
            old_x = self.parent.units[unit['id']]['pos'][0]
            old_y = self.parent.units[unit['id']]['pos'][1]
            self.parent.refreshUnit(unit)
            if self.parent.sel_unit_id == unit['id']:
                self.parent.interface.refreshUnitData( unit['id'] )
                self.parent.sgm.showUnitAvailMove( unit['id'] )
                self.parent.sgm.showVisibleEnemies(unit['id'])
                if unit['pos'][0] != old_x or unit['pos'][1] != old_y:
                    m = self.parent.getInvisibleTiles()
                    self.parent.sgm.level_mesh.setInvisibleTiles(m)
                self.parent.sgm.playUnitStateAnim( unit['id'] )
            self.parent._message_in_process = False
        #========================================================================
        #
        elif msg[0] == SHOOT:
            self.parent._message_in_process = True
            self.parent.handleShoot(msg[1])       
        #========================================================================
        #
        elif msg[0] == VANISH:
            self.parent._message_in_process = True            
            unit_id = msg[1]
            self.parent.handleVanish(unit_id)
                
        #========================================================================
        #
        elif msg[0] == ERROR:
            self.parent._message_in_process = True            
            self.parent.interface.console.consoleOutput(str(msg[1]), utils.CONSOLE_SYSTEM_ERROR)
            self.parent.interface.console.show()
            self.parent._message_in_process = False
        #========================================================================
        #
        elif msg[0] == CHAT:
            self.parent._message_in_process = True            
            sender_name = msg[2]
            self.parent.interface.console.consoleOutput( sender_name + ":" + str(msg[1]), utils.CONSOLE_SYSTEM_MESSAGE)
            self.parent.interface.console.show()
            self.parent._message_in_process = False            
        #========================================================================
        #
        elif msg[0] == LEVEL:
            self.parent.old_level_grid = self.parent.level._grid[:]
            self.parent.level._grid = msg[1]._grid
            self.parent.sgm.level_mesh.processLevel()
        #========================================================================
        #
        elif msg[0] == USE:
            self.parent.sgm.unit_np_dict[msg[1]].model.play('use')    
        #========================================================================
        #
        elif msg[0] == TAUNT:
            self.parent.sgm.unit_np_dict[msg[1][0]].model.play('taunt')
            if msg[1][1]:
                self.parent.handleShoot(msg[1][1]) 
        #========================================================================
        #        
        else:
            self.parent._message_in_process = True
            self.log.error("Unknown message Type: %s", msg[0])
            self.parent._message_in_process = False
    
    def replayMsgTask(self, task):
        # Read msg from file and send to handleMsg
        if self.parent._message_in_process == False:
            if self.replay_msg_num <= len(self.replay_msg_list)-1:
                msg = self.replay_msg_list[self.replay_msg_num]
                self.handleMsg(msg)
                self.replay_msg_num += 1
        return task.cont
    
    
    def msgTask(self, task):
        """Task that listens for messages on client queue."""
        # Needs to be called every frame, this takes care of connection
        ClientMsg.handleConnection(self.parent.player, self.parent.server_ip, self.parent.server_port)
        
        if self.parent._message_in_process == False:
            msg = ClientMsg.readMsg()        
            if msg:
                self.handleMsg(msg)         
        return task.cont