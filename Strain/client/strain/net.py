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


PING_TIMER = 42  #seconds

#========================================================================
#
class Net():
    def __init__(self, parent):
        self.parent = parent
        
        self.ping_timer = time.time()
        
        # Set logging through our global logger
        self.log = self.parent.logger
        
        # This handles message queue - we will process messages in sync one by one
        self._message_in_process = False
           
    def startNet(self):
        # Create main network messaging task
        taskMgr.add(self.msgTask, "msg_task") 

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
            None
        #========================================================================
        #        
        elif msg[0] == ENGINE_STATE:
            self._message_in_process = True      
            # Set important game instance parameters
            self.parent.game_instance.turn_number = msg[1]['turn'] 
            self.parent.game_instance.turn_player = msg[1]['active_player_id']                       
            # Update local copy of engine data
            self.parent.game_instance.local_engine.level = pickle.loads(msg[1]['level'])
            self.parent.game_instance.local_engine.players = pickle.loads(msg[1]['players'])
            self.parent.game_instance.local_engine.units = pickle.loads(msg[1]['units'])
            self.parent.game_instance.local_engine.inactive_units = pickle.loads(msg[1]['dead_units'])
            self.parent.game_instance.local_engine.refreshLevelUnitDict()            
            
            # Update renderers
            self.parent.game_instance.render_manager.refresh()
            
            # Update interface
            self.parent.game_instance.interface.refreshStatusBar()
            for unit in self.parent.game_instance.local_engine.units.itervalues():
                if unit['owner_id'] == self.parent.game_instance.player_id:
                    self.parent.game_instance.interface.refreshUnitInfo(unit['id']) 
            #self.parent.sgm.level_model.setInvisibleTilesInThread()              

            self._message_in_process = False
        #========================================================================
        #
        elif msg[0] == MOVE:
            self._message_in_process = True
            # Animation manager sets _message_in_process to False when the animation is done
            self.parent.game_instance.render_manager.animation_manager.handleMove(msg[1])
        #========================================================================
        #
        elif msg[0] == NEW_TURN:      
            self._message_in_process = True  
            # Set important game instance parameters
            self.parent.game_instance.turn_number = msg[1]['turn'] 
            self.parent.game_instance.turn_player = msg[1]['active_player_id'] 
            
            # Update local copy of engine data
            self.parent.game_instance.local_engine.level = pickle.loads(msg[1]['level']) 
            self.parent.game_instance.local_engine.players = pickle.loads(msg[1]['players'])
            self.parent.game_instance.local_engine.units = pickle.loads(msg[1]['units'])            
            self.parent.game_instance.local_engine.inactive_units = pickle.loads(msg[1]['dead_units'])
            
            # Update interface
            self.parent.game_instance.interface.refreshStatusBar()
            for unit in self.parent.game_instance.local_engine.units.itervalues():
                if unit['owner_id'] == self.parent.game_instance.player_id:
                    self.parent.game_instance.interface.refreshUnitInfo(unit['id'])

            self.parent.game_instance.deselectUnit()
            #self.parent.sgm.level_model.setInvisibleTilesInThread()
            # Animation manager sets _message_in_process to False when the animation is done
            self.parent.game_instance.render_manager.animation_manager.handleNewTurn()
        #========================================================================
        #
        elif msg[0] == UNIT:
            self._message_in_process = True            
            unit = msg[1]
            old_x = self.parent.game_instance.local_engine.units[unit['id']]['pos'][0]
            old_y = self.parent.game_instance.local_engine.units[unit['id']]['pos'][1]
            self.parent.game_instance.local_engine.refreshUnit(unit)
            if self.parent.game_instance.local_engine.isThisMyUnit(unit['id']):
                self.parent.game_instance.interface.refreshUnitInfo(unit['id'])          
            if self.parent.game_instance.sel_unit_id == unit['id']:
                self.parent.game_instance.interface.processUnitData( unit['id'] )                  
                self.parent.game_instance.interface.printUnitData( unit['id'] )
                self.parent.game_instance.movement.calcUnitAvailMove( unit['id'] )
                #self.parent.sgm.showVisibleEnemies(unit['id'])
                if unit['pos'][0] != old_x or unit['pos'][1] != old_y or unit['last_action']=='use':
                    #self.parent.game_instance.render_manager.level_model.setInvisibleTilesInThread()
                    None
                #self.parent.sgm.playUnitStateAnim( unit['id'] )
            self._message_in_process = False
        #========================================================================
        #
        elif msg[0] == SHOOT:
            self._message_in_process = True
            # Animation manager sets _message_in_process to False when the animation is done
            self.parent.game_instance.render_manager.animation_manager.handleShoot(msg[1])       
        #========================================================================
        #
        elif msg[0] == SPOT:
            self._message_in_process = True
            # Animation manager sets _message_in_process to False when the animation is done
            self.parent.game_instance.render_manager.animation_manager.handleSpot(msg[1])  
            self.parent.game_instance.local_engine.level.putUnitDict(msg[1])  
            if self.parent.game_instance.player_id == self.parent.game_instance.turn_player and self.parent.game_instance.sel_unit_id != None:
                self.parent.game_instance.movement.calcUnitAvailMove( self.parent.game_instance.sel_unit_id )
                #self.parent.sgm.showVisibleEnemies( self.parent.sel_unit_id )
        #========================================================================
        #
        elif msg[0] == VANISH:
            self._message_in_process = True            
            # Animation manager sets _message_in_process to False when the animation is done
            self.parent.game_instance.render_manager.animation_manager.handleVanish(msg[1])
                
        #========================================================================
        #
        elif msg[0] == ERROR:
            return
            self._message_in_process = True            
            self.parent.interface.console.consoleOutput(str(msg[1]), utils.CONSOLE_SYSTEM_ERROR)
            self.parent.interface.console.show()
            self._message_in_process = False
        #========================================================================
        #
        elif msg[0] == CHAT:
            self._message_in_process = True            
            sender_name = msg[2]
            self.parent.interface.console.consoleOutput( sender_name + ":" + str(msg[1]), utils.CONSOLE_SYSTEM_MESSAGE)
            self.parent.interface.console.show()
            self._message_in_process = False            
        #========================================================================
        #
        elif msg[0] == LEVEL:
            self.parent.game_instance.local_engine.old_level = self.parent.game_instance.local_engine.level
            level = msg[1]
            for unit in self.parent.game_instance.local_engine.units.itervalues():
                level.putUnitDict(unit)
            self.parent.game_instance.local_engine.level = level
            # if our enemy opens doors, we need to update visibility
            # enemy's visibility gets updated when he gets UNIT message
            if self.parent.game_instance.player_id == self.parent.game_instance.turn_player and self.parent.game_instance.sel_unit_id != None:
                self.parent.game_instance.movement.calcUnitAvailMove( self.parent.game_instance.sel_unit_id )
                #self.parent.sgm.showVisibleEnemies( self.parent.sel_unit_id )
            #self.parent.sgm.level_model.setInvisibleTilesInThread()
            #self.parent.sgm.level_model.setInvisibleWallsInThread()
        #========================================================================
        #
        elif msg[0] == USE:
            self.parent.game_instance.render_manager.unit_renderer_dict[msg[1]].model.play('use')    
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
            self._message_in_process = True
            self.log.error("Unknown message Type: %s", msg[0])
            self._message_in_process = False
    
    
    def msgTask(self, task):
        """Task that listens for messages on client queue."""
        if self._message_in_process == False:
            msg = ClientMsg.readMsg()        
            if msg:
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
    