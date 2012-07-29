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
        taskMgr.add(self.netTask, "net_task") 

    def handleMsg(self, msg_list):
        """Handles incoming messages."""
        self.log.info("Received message: %s", msg_list)
        
        print '--------START------------'
        print 'Incoming message', msg_list
        print '----------END----------'
        
        #========================================================================
        #
        if msg_list[0] == ALL_PLAYERS:
            None
        elif msg_list[0] == ALL_LEVELS:
            None
        elif msg_list[0] == MY_ACTIVE_GAMES:
            None
        elif msg_list[0] == MY_UNACCEPTED_GAMES:
            None
        elif msg_list[0] == MY_WAITING_GAMES:
            None
        elif msg_list[0] == EMPTY_PUBLIC_GAMES:
            None            
        elif msg_list[0] == NEWS_FEED:
            None 
        elif msg_list[0] == NEW_GAME_STARTED:
            None    
        elif msg_list[0] == PONG:
            None       
        else:
            if msg_list[0][0] == ENGINE_STATE:
                msg = msg_list[0]
                self._message_in_process = True      
                # Set important game instance parameters
                self.parent.game_instance.turn_number = msg[1]['turn'] 
                self.parent.game_instance.turn_player = msg[1]['active_player_id']                       
                # Update local copy of engine data
                self.parent.game_instance.local_engine.level = pickle.loads(msg[1]['level'])
                self.parent.game_instance.local_engine.players = pickle.loads(msg[1]['players'])
                self.parent.game_instance.local_engine.units = pickle.loads(msg[1]['units'])
                self.parent.game_instance.local_engine.inactive_units = pickle.loads(msg[1]['dead_units'])
                # Update level dynamic lists for accurate calculation of walkable tiles
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
            elif msg_list[0][0] == NEW_TURN:
                msg = msg_list[0]                  
                self._message_in_process = True
                # Set important game instance parameters
                self.parent.game_instance.turn_number = msg[1]['turn'] 
                self.parent.game_instance.turn_player = msg[1]['active_player_id'] 
                
                # Update local copy of engine data
                self.parent.game_instance.local_engine.level = pickle.loads(msg[1]['level']) 
                self.parent.game_instance.local_engine.players = pickle.loads(msg[1]['players'])
                self.parent.game_instance.local_engine.units = pickle.loads(msg[1]['units'])            
                self.parent.game_instance.local_engine.inactive_units = pickle.loads(msg[1]['dead_units'])
                # Update level dynamic lists for accurate calculation of walkable tiles
                self.parent.game_instance.local_engine.refreshLevelUnitDict()
                
                # Update interface
                self.parent.game_instance.interface.refreshStatusBar()
                for unit in self.parent.game_instance.local_engine.units.itervalues():
                    if unit['owner_id'] == self.parent.game_instance.player_id:
                        self.parent.game_instance.interface.refreshUnitInfo(unit['id'])
    
                self.parent.game_instance.deselectUnit()
                #self.parent.sgm.level_model.setInvisibleTilesInThread()
                # Animation manager sets _message_in_process to False when the animation is done
                self.parent.game_instance.render_manager.animation_manager.handleNewTurn()
            else:
                # Msg received is now a session - a list of events which we need to parse one by one        
                self.parent.game_instance.render_manager.animation_manager.createSequence(msg_list)
                """
                for msg in msg_list:
                    #========================================================================
                    #
                    if msg[0] == MOVE:
                        self._message_in_process = True
                        # Animation manager sets _message_in_process to False when the animation is done
                        self.parent.game_instance.render_manager.animation_manager.addMoveAnim(msg)
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
                            self.parent.game_instance.render_manager.refreshEnemyUnitMarkers()
                            if unit['pos'][0] != old_x or unit['pos'][1] != old_y or unit['last_action']=='use':
                                self.parent.game_instance.render_manager.refreshFow()
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
                        self.parent.game_instance.render_manager.refreshFow()
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
                    
                    self.parent.game_instance.render_manager.animation_manager.finishEventSequence()
                """
    
    def netTask(self, task):
        """Task that handles connection and listens for messages on client queue."""
        
        #check if everything is ok with connection
        if not ClientMsg.handleConnection():
            return task.cont
        
        if self._message_in_process == False:
            msg = ClientMsg.readMsg()        
            if msg:
                self.handleMsg(msg)
                
        t = time.time()
        if t - self.ping_timer >= PING_TIMER:
            self.ping_timer = t
            ClientMsg.ping()
                     
        return task.cont


