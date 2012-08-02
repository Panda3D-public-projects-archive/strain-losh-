'''
Created on 30 Jun 2012

@author: krav
'''
from strain.share import *
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
            
        #units that have been modified while creating this event session
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
                self.engine.to_network.append( (p_id, self.events[p_id]) )
    

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
            self.engine.to_network.append( (p.id, msg) )
        
        
    
    def addUnitEvents(self):
        
        for unit in self.units_changed:
            self.observer_events.append( (UNIT, compileUnit(unit)) )
            
            for p in self.engine.players:
                
                #sendToOwnerAndAllies
                if p == unit.owner or p.team == unit.owner.team:
                    self.events[p.id].append( (UNIT, compileUnit(unit)) )
                #sendToEnemyPlayersThatSeeThisUnit
                elif unit in p.visible_enemies:
                    self.events[p.id].append( (UNIT, compileEnemyUnit(unit)) )
                    
        self.units_changed = {}
            
            
    def addEvent(self, event):
        
        if event[0] == ROTATE:
            unit = event[1]
            new_heading = event[2]
            
            self.sendToPlayersThatKnowThisUnit( unit, (ROTATE, unit.id, new_heading))
            self.units_changed[unit] = 1
        

        
        elif event[0] == MOVE:
            unit = event[1]
            tile = event[2]

            self.sendToPlayersThatKnowThisUnit( unit, (MOVE, unit.id, tile) )
            self.units_changed[unit] = 1



        elif event[0] == USE:
            unit = event[1]
            self.sendToPlayersThatKnowThisUnit(unit, (USE, unit.id) )



        elif event[0] == TAUNT:
            unit = event[1]
            self.sendToPlayersThatKnowThisUnit(unit, (TAUNT, unit.id) )




        elif event[0] == VANISH:
            player = event[1]
            unit = event[2]
            
            self.events[player.id].append( (VANISH, unit.id) )

        
        elif event[0] == SPOT:
            player = event[1]
            compiled_enemy = compileEnemyUnit(event[2])

            self.events[player.id].append( (SPOT, compiled_enemy) )



        elif event[0] == UNIT:
            unit = event[1]
            self.units_changed[unit] = 1

            
            
            
        elif event[0] == OVERWATCH:
            self.parseShootEvent(event[1:], True)
        elif event[0] == SHOOT:
            self.parseShootEvent(event)

            
        elif event[0] == LEVEL:
            player = event[1]
            self.events[player.id].append( (LEVEL, compileLevelWithDifferentGrid(self.engine.level, self.engine._grid_player[player.id]) ) )
            self.observer_events.append( (LEVEL, compileLevel(self.engine.level)) )
            

        elif event[0] == DEPLOYMENT:
            player = event[1]
            status = event[2]
            #send to all players
            self.sendImmediately(self.engine.players, (DEPLOYMENT, player.id, status) )



            
        elif event[0] == ENGINE_STATE:
            self.engine.db_api.addGameEvent( self.engine.game_id, pickle.dumps( (ENGINE_STATE, compileObserverState(self.engine)) ) )
            
            for p in self.engine.players:
                msg = (ENGINE_STATE, compileState(self.engine, p))
                #add msg to db
                self.engine.db_api.addGamePlayerEvent( self.engine.game_id, p.id, pickle.dumps(msg) )
                #send msg to player
                self.engine.to_network.append( (p.id, msg) )
            
        elif event[0] == NEW_TURN:
            self.engine.db_api.addGameEvent( self.engine.game_id, pickle.dumps( (NEW_TURN, compileObserverNewTurn(self.engine)) ) )
            
            for p in self.engine.players:
                msg = (NEW_TURN, compileNewTurn(self.engine, p))
                #add msg to db
                self.engine.db_api.addGamePlayerEvent( self.engine.game_id, p.id, pickle.dumps(msg) )
                #send msg to player
                self.engine.to_network.append( (p.id, msg) )
            
            

        
        elif event[0] == INFO:
            player = event[1]
            message = event[2]
            self.sendImmediately( [player], (INFO, message) )
            
        elif event[0] == ERROR:
            player = event[1]
            message = event[2]
            self.sendImmediately( [player], (ERROR, message) )

        elif event[0] == PONG:
            player = event[1]
            message = event[2]
            self.sendImmediately( [player], (PONG, message), False )


        elif event[0] == CHAT:
            sender = event[1]
            message = event[2]
            to_allies = event[3]
            
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



    def parseShootEvent(self, event, overwatch = False):
        #example event = (SHOOT/MELEE, Unit, (4, 7), Weapon, [('bounce', Unit)])
        
        if overwatch:
            self.observer_events.append( (OVERWATCH,) + event )
        else:
            self.observer_events.append( event )
            
        
        for p in self.engine.players:
            tmp_event = self.parseShootEventForPlayer(event, p)
            if event:
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
        if player == unit.owner or player.team == unit.owner.team or unit in player.visible_enemies:
            return True
        return False
    
    
    
    pass