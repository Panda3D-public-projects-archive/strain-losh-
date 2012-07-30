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

    def handleMsg(self, msg):
        """Handles incoming messages."""
        self.log.info("Received message: %s", msg)
        
        print '--------START------------'
        print 'Incoming message', msg
        print '----------END----------'
        
        #========================================================================
        #
        if msg[0] == ALL_PLAYERS:
            None
        elif msg[0] == ALL_LEVELS:
            None
        elif msg[0] == MY_ACTIVE_GAMES:
            None
        elif msg[0] == MY_UNACCEPTED_GAMES:
            None
        elif msg[0] == MY_WAITING_GAMES:
            None
        elif msg[0] == EMPTY_PUBLIC_GAMES:
            None            
        elif msg[0] == NEWS_FEED:
            None 
        elif msg[0] == NEW_GAME_STARTED:
            None    
        elif msg[0] == PONG:
            None       
        elif msg[0] == ANIMATION:       
            # Msg received is now a session - a list of events which we need to parse one by one        
            self.parent.game_instance.render_manager.animation_manager.createSequence(msg[1:])               
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
            None
    
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


