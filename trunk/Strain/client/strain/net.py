#############################################################################
# IMPORTS
#############################################################################

# python imports
import cPickle as pickle
import time as time
import copy


# strain related imports
from client_messaging import *
import utils as utils


PING_TIMER =   42  #seconds

#========================================================================
#
class Net():
    def __init__(self, parent):
        self.parent = parent
        
        self.ping_timer = time.time()
        
        # Set logging through our global logger
        self.log = self.parent.parent.logger
        
               
           
    def startNet(self):
        # Create main network messaging task
        taskMgr.add(self.msgTask, "msg_task") 
        
    def startReplay(self, replay):
        self.replay_msg_list = pickle.load(open(replay, 'r'))
        self.replay_msg_num = 0
        taskMgr.add(self.replayMsgTask, "replay_msg_task")

    def handleMsg(self, msg):
        """Handles incoming messages."""
        self.log.info("Received message: %s", msg[0])
        
        print '--------START------------'
        print 'Incoming message', msg[0]
        print 'Message body', msg[1]
        print '----------END----------'
        
        #========================================================================
        #
        if msg[0] == DEPLOYMENT and self.parent.type == 'NewGame':
            self.parent.budget = msg[1]['army_size']
            self.parent.level = msg[1]['level']
            self.parent.fsm.request('Selector')
        elif msg[0] == ENGINE_STATE:
            if not self.parent._game_initialized:
                self.parent.fsm.request('Game')
            self.parent._message_in_process = True
            self.parent.level = pickle.loads(msg[1]['level'])
            self.parent.turn_number = msg[1]['turn']
            self.parent.players = pickle.loads(msg[1]['players'])
            self.parent.turn_player = self.parent.getPlayerName(msg[1]['active_player_id'])
            self.parent.units = pickle.loads(msg[1]['units'])
            self.parent.inactive_units = pickle.loads(msg[1]['dead_units'])
            self.parent.sgm.deleteLevel()
            self.parent.sgm.deleteUnits()
            self.parent.sgm.loadLevel(self.parent.level)
            self.parent.sgm.loadUnits()
            self.parent.deselectUnit()            
            self.parent.interface.refreshStatusBar()
            for unit_id in self.parent.units.iterkeys():
                if self.parent.isThisMyUnit(unit_id):
                    self.parent.interface.refreshUnitInfo(unit_id) 
            self.parent.sgm.level_model.setInvisibleTilesInThread()           
            self.parent._message_in_process = False
        #========================================================================
        #
        elif msg[0] == MOVE:
            self.parent._message_in_process = True
            self.parent.handleMove(msg[1])
        #========================================================================
        #
        elif msg[0] == NEW_TURN:
            if not self.parent._game_initialized:
                self.parent.fsm.request('Game')            
            self.parent._message_in_process = True  
            self.parent.level = pickle.loads(msg[1]['level']) 
            self.parent.players = pickle.loads(msg[1]['players'])         
            self.parent.turn_number = msg[1]['turn']
            self.parent.turn_player = self.parent.getPlayerName(msg[1]['active_player_id'])
            if not self.parent.sgm.comp_inited['level']:
                self.parent.sgm.loadLevel(self.parent.level)
            if not self.parent.sgm.comp_inited['units']:
                self.parent.units = pickle.loads(msg[1]['units'])               
                self.parent.sgm.loadUnits()
            units = pickle.loads(msg[1]['units'])
            self.parent.interface.refreshStatusBar()
            for unit in units.itervalues():
                self.parent.refreshUnit(unit)
            self.parent.inactive_units = pickle.loads(msg[1]['dead_units'])
            for unit_id in self.parent.units.iterkeys():
                if self.parent.isThisMyUnit(unit_id):
                    self.parent.interface.refreshUnitInfo(unit_id)
            self.parent.deselectUnit()
            self.parent.sgm.level_model.setInvisibleTilesInThread()
            # play new turn animation, _message_in_process will be set to false after this
            self.parent.handleNewTurn()
        #========================================================================
        #
        elif msg[0] == UNIT:
            self.parent._message_in_process = True            
            unit = msg[1]
            old_x = self.parent.units[unit['id']]['pos'][0]
            old_y = self.parent.units[unit['id']]['pos'][1]
            self.parent.refreshUnit(unit)
            if self.parent.isThisMyUnit(unit['id']):
                self.parent.interface.refreshUnitInfo(unit['id'])          
            if self.parent.sel_unit_id == unit['id']:
                self.parent.interface.processUnitData( unit['id'] )                  
                self.parent.interface.printUnitData( unit['id'] )
                self.parent.movement.calcUnitAvailMove( unit['id'] )
                self.parent.sgm.showVisibleEnemies(unit['id'])
                if unit['pos'][0] != old_x or unit['pos'][1] != old_y or unit['last_action']=='use':
                    self.parent.sgm.level_model.setInvisibleTilesInThread()
                    None
                self.parent.sgm.playUnitStateAnim( unit['id'] )
            self.parent._message_in_process = False
        #========================================================================
        #
        elif msg[0] == SHOOT:
            self.parent._message_in_process = True
            # play shoot animation, _message_in_process will be set to false after this
            self.parent.handleShoot(msg[1])       
        #========================================================================
        #
        elif msg[0] == SPOT:
            self.parent._message_in_process = True
            self.parent.handleSpot(msg[1])  
            self.parent.level.putUnitDict(msg[1])  
            if self.parent.player == self.parent.turn_player and self.parent.sel_unit_id != None:
                self.parent.movement.calcUnitAvailMove( self.parent.sel_unit_id )
                self.parent.sgm.showVisibleEnemies( self.parent.sel_unit_id )
        #========================================================================
        #
        elif msg[0] == VANISH:
            self.parent._message_in_process = True            
            unit_id = msg[1]
            self.parent.handleVanish(unit_id)
                
        #========================================================================
        #
        elif msg[0] == ERROR:
            return
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
            self.parent.old_level = self.parent.level
            level = msg[1]
            for unit in self.parent.units.itervalues():
                level.putUnitDict(unit)
            self.parent.level = level
            # if our enemy opens doors, we need to update visibility
            # enemy's visibility gets updated when he gets UNIT message
            if self.parent.player == self.parent.turn_player and self.parent.sel_unit_id != None:
                self.parent.movement.calcUnitAvailMove( self.parent.sel_unit_id )
                self.parent.sgm.showVisibleEnemies( self.parent.sel_unit_id )
            self.parent.sgm.level_model.setInvisibleTilesInThread()
            self.parent.sgm.level_model.setInvisibleWallsInThread()
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
        elif msg[0] == NEW_GAME_STARTED:
            self.parent.newGameStarted( msg[1] )
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
    
        if self.parent._message_in_process == False:
            msg = ClientMsg.readMsg()        
            if msg:
                print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                self.handleMsg(msg)
                
        t = time.time()
        if t - self.ping_timer >= PING_TIMER:
            self.ping_timer = t
            ClientMsg.ping()
                     
        return task.cont


#------------------------END OF NET CLASS---------------------------------------------


def handleConnection(task):
    # Needs to be called every frame, this takes care of connection
    ClientMsg.handleConnection()
    
    return task.cont
    