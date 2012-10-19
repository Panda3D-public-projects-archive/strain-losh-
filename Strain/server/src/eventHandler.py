'''
Created on 30 Jun 2012

@author: krav
'''
from share import *
from util import *
import copy
from weapon import SPECIAL_SILENCED



class EventHandler():
    
    
    def __init__(self, eng):
        self.engine = eng
    
        #for remembering events for different players during this session
        self.events = {}
            
        #observer events
        self.observer_events = []
            
        #units that have been modified while creating this action session
        self.units_changed = {}
    
    
    
    def initPlayers(self):
        #create empty list of events for each player in engine
        for p in self.engine.players:
            self.events[p.id] = []
    
        self.observer_events = []
        
        
    
    def sendSession(self):

        #update all units that changed this session
        self.addUnitEvents()
        
        #put header so client knows these are animation messages
        for p_id in self.events:
            if self.events[p_id]: 
                self.events[p_id].insert(0, ANIMATION)
        if self.observer_events:
            self.observer_events.insert(0, ANIMATION)
        
        
        #add events to db
        for p_id in self.events:
            if self.events[p_id]:
                self.engine.db_api.addGamePlayerEvent( self.engine.game_id, p_id, pickle.dumps(self.events[p_id])  ) 
        if self.observer_events:
            self.engine.db_api.addGameEvent( self.engine.game_id, pickle.dumps(self.observer_events)  )
        
        
        #send events to logged in clients
        for p_id in self.events:
            if self.events[p_id]:
                self.engine.to_network.append( (p_id, self.engine.game_id, self.events[p_id]) )
    

        #clear all lists
        for p in self.engine.players:
            self.events[p.id] = []
        self.observer_events = []
        
        
    
    def sendImmediately(self, player_list, msg, write2DB = True ):
        if write2DB:
            self.engine.db_api.addGameEvent( self.engine.game_id, pickle.dumps(msg) )
            
        for p in player_list:
            #add msg to db
            if write2DB:
                self.engine.db_api.addGamePlayerEvent( self.engine.game_id, p.id, pickle.dumps(msg) )
            #send msg to player
            self.engine.to_network.append( (p.id, self.engine.game_id, msg) )
        
        
    
    def addUnitEvents(self):
        
        for unit in self.units_changed:
            self.observer_events.append( (UNIT, compileUnit(unit)) )
            
            for p in self.engine.players:
                
                #sendToOwnerAndAllies
                if p == unit.owner or p.team == owner.owner.team:
                    self.events[p.id].append( (UNIT, compileUnit(unit)) )
                #sendToEnemyPlayersThatSeeThisUnit
                elif unit in p.visible_enemies:
                    self.events[p.id].append( (UNIT, compileEnemyUnit(unit)) )
                    
        self.units_changed = {}
            
            
    def addEvent(self, action):
        
        if action[0] == ROTATE:
            unit = action[1]
            new_heading = action[2]
            
            self.sendToPlayersThatKnowThisUnit( unit, (ROTATE, unit.id, new_heading))
            self.units_changed[unit] = 1
        

        
        elif action[0] == MOVE:
            unit = action[1]
            tile = action[2]

            self.sendToPlayersThatKnowThisUnit( unit, (MOVE, unit.id, tile) )
            self.units_changed[unit] = 1



        elif action[0] == USE:
            unit = action[1]
            self.sendToPlayersThatKnowThisUnit(unit, (USE, unit.id) )



        elif action[0] == TAUNT:
            unit = action[1]
            self.sendToPlayersThatKnowThisUnit(unit, (TAUNT, unit.id) )




        elif action[0] == VANISH:
            player = action[1]
            unit = action[2]
            
            self.events[player.id].append( (VANISH, unit.id) )

        
        elif action[0] == SPOT:
            player = action[1]
            compiled_enemy = compileEnemyUnit(action[2])

            self.events[player.id].append( (SPOT, compiled_enemy) )



        elif action[0] == UNIT:
            unit = action[1]
            self.units_changed[unit] = 1

            
            
            
        elif action[0] == OVERWATCH:
            self.parseShootEvent(action[1:], True)
        elif action[0] == SHOOT:
            self.parseShootEvent(action)

            
        elif action[0] == LEVEL:
            player = action[1]
            self.events[player.id].append( (LEVEL, compileLevelWithDifferentGrid(self.engine.level, self.engine._grid_player[player.id]) ) )
            self.observer_events.append( (LEVEL, compileLevel(self.engine.level)) )
            

        elif action[0] == DEPLOYMENT:
            player = action[1]
            status = action[2]
            #send to all players
            self.sendImmediately(self.engine.players, (DEPLOYMENT, player.id, status) )



            
        elif action[0] == ENGINE_STATE:
            self.engine.db_api.addGameEvent( self.engine.game_id, pickle.dumps( (ENGINE_STATE, compileObserverState(self.engine)) ) )
            
            for p in self.engine.players:
                msg = (ENGINE_STATE, compileState(self.engine, p))
                #add msg to db
                self.engine.db_api.addGamePlayerEvent( self.engine.game_id, p.id, pickle.dumps(msg) )
                #send msg to player
                self.engine.to_network.append( (p.id, self.engine.game_id, msg) )
            
        elif action[0] == NEW_TURN:
            self.engine.db_api.addGameEvent( self.engine.game_id, pickle.dumps( (NEW_TURN, compileObserverNewTurn(self.engine)) ) )
            
            for p in self.engine.players:
                msg = (NEW_TURN, compileNewTurn(self.engine, p))
                #add msg to db
                self.engine.db_api.addGamePlayerEvent( self.engine.game_id, p.id, pickle.dumps(msg) )
                #send msg to player
                self.engine.to_network.append( (p.id, self.engine.game_id, msg) )
            
            

        
        elif action[0] == INFO:
            player = action[1]
            message = action[2]
            self.sendImmediately( [player], (INFO, message) )
            
        elif action[0] == ERROR:
            player = action[1]
            message = action[2]
            self.sendImmediately( [player], (ERROR, message) )

        elif action[0] == PONG:
            player = action[1]
            message = action[2]
            self.sendImmediately( [player], (PONG, message), False )


        elif action[0] == CHAT:
            sender = action[1]
            message = action[2]
            to_allies = action[3]
            
            tmp_plyr_lst = self.engine.players[:]
            tmp_plyr_lst.remove( sender )
            
            if to_allies:
                for p in tmp_plyr_lst[:]:
                    if p.team != sender.team:
                        tmp_plyr_lst.remove( p )
            
            
            self.sendImmediately( tmp_plyr_lst, (CHAT, message, sender.name) )



    def sendToPlayersThatKnowThisUnit(self, unit, msg ):
        
        self.observer_events.append( msg )
        
        for p in self.engine.players:                
            if self.playerKnowsAbout(p, unit):
                self.events[p.id].append( msg )



    def parseShootEvent(self, action, overwatch = False):
        #example action = (SHOOT/MELEE, Unit, (4, 7), Weapon, [('bounce', Unit)])
        
        if overwatch:
            self.observer_events.append( (OVERWATCH,) + action )
        else:
            self.observer_events.append( action )
            
        
        for p in self.engine.players:
            tmp_event = self.parseShootEventForPlayer(action, p)
            if action:
                if overwatch:
                    self.events[p.id].append( (OVERWATCH,) + tmp_event )
                else:
                    self.events[p.id].append( tmp_event )



    def parseShootEventForPlayer(self, shoot_event, player): 
        tmp_shoot_event = copy.deepcopy(shoot_event)

        shoot, shooter_id, target_pos, wpn_id, res_list = tmp_shoot_event
        shooter = self.engine.units[shooter_id]
        
        self.units_changed[shooter] = 1
        
        #if this is not the owner of shooter, or his ally
        if not self.playerKnowsAbout(player, shooter):
            shooter_id = -1
            target_pos = None
            #TODO: krav: hearing range here
            
        #go through list of targets and if we dont see the target, remove it from the list
        for effect in res_list[:]:
            target_id = effect[1]
            target = self.engine.units[target_id]
            
            self.units_changed[target] = 1
            
            if not self.playerKnowsAbout(player, target):
                    res_list.remove( effect )
                
        return (shoot, shooter_id, target_pos, wpn_id, res_list)
    
    
    
    def playerKnowsAbout(self, player, unit):
        if player == unit.owner or player.team == owner.owner.team or unit in player.visible_enemies:
            return True
        return False
    
    
    
    pass