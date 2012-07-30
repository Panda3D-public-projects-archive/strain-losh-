from xml.dom import minidom
import unit
import math
from server_messaging import *
from threading import Thread
import time
import logging
import logging.handlers
import sys, traceback
import cPickle as pickle
import util
from player import Player
from util import compileEnemyUnit, compileUnit, compileState, compileAllUnits
import copy
from util import OBSERVER_ID
from strain.share import *
import eventHandler
from eventHandler import EventHandler


LEVELS_ROOT = "./data/levels/"


######################################################################################################
######################################################################################################
class EngineThread( Thread ):
    
    
    def __init__( self, game_id, from_network, to_network, notify, db_api ):
        Thread.__init__(self)
        
        self.name = ("EngineThread-" + str(game_id))
            
        self.setDaemon(True)
        self.stop = False

        #this will be set by thread handler if we need to suspend this game for some reason
        self.suspend = False

        self.game_id = game_id
        self.notify = notify
        self.db_api = db_api
           
        self.last_active_time = time.time()
        
        #check if we need to load Engine from db..
        db_game = self.db_api.getGame( self.game_id )
        
        #if there is no such game in db, write an error and quit this thread
        if not db_game:
            self.notify.critical( "Sterner tried to start EngineThread with game_id=%d, but there is no suh entry in db!" %self.game_id )
            return
        
        level = db_game[1]
        budget = db_game[2]
        #get players ids in a list
        players = [ g_p[2] for g_p in self.db_api.getGameAllPlayers(db_game[0])]
        
        if db_game[12]:
            self.engine = loadFromPickle( str(db_game[12]), from_network, to_network, notify, db_api )
        else:
            self.engine = Engine( game_id, from_network, to_network, notify, self.db_api )
            self.engine.Init( level, budget, players )


        
    def run(self):

        
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        while True:
            
            #check if thread handler told us to suspend                
            if self.suspend:
                print "++++++++++++++ pickling!!!!!!"
                if self.engine.pickleSelf():
                    break

            #run one tick                
            if self.engine.runOneTick():
                self.last_active_time = time.time()

                
            #if we need to stop immediately than do so
            if self.stop:
                break
            
            time.sleep( 0.1 )
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
            
        tmp_msg = "++++++++++ " + self.name + " stopped ++++++++++"
        self.notify.info( tmp_msg )
        
       
    
########################################################################################################
########################################################################################################
########################################################################################################
########################################################################################################
########################################################################################################
class Engine():
    
        
    __index_uid = 0

    def getUID(self):
        Engine.__index_uid += 1
        return Engine.__index_uid -1
    

        
    #====================================init======================================0
    def __init__(self, game_id, from_network, to_network, notify, db_api):
        self.notify = notify
        self.notify.info("------------------------Engine Starting game_id:%d------------------------" %game_id)

        self.game_id = game_id
        self.from_network = from_network
        self.to_network = to_network
        self.db_api = db_api
        
        self.stop = False
        self.level = None         
        self.players = []
        self.units = {}
        self.dead_units = {}
        
        #K-player.id V-grid that player with that id saw last
        self._grid_player = {}
        
        #we will put events that happened as a reaction to an action by player here
        #than we will parse them and send messages to different players accordingly
        self.events = []
        
        
        self.turn = 0
        self.active_player = None

        self.army_size = 1000

        self.event_handler = EventHandler( self )
        
        print "Engine started"


  

    def Init(self, level, budget, players):
        level_filename = level + ".txt"
        self.level = Level( LEVELS_ROOT + level_filename )
        self.notify.info("Loaded level:%s", level_filename )

        self.loadArmyList()
        

    def runOneTick(self):
        """Returns 0 if idling, 1 otherwise"""

        #get messages if there are any
        msg_list = self.from_network.getMyMsgs( self.game_id )
        if msg_list:
            for msg in msg_list:
                print "engine dobio:", msg
                self.handleMsg( msg[1:], msg[0] )
            return 1

        return 0


    def handleMsg(self, msg, source):
        """This method is the main method for handling incoming messages to the Engine"""     
 
        if( msg[0] == ENGINE_SHUTDOWN ):
            self.error("Engine is shutting down")
            self.stop = True
            
        elif( msg[0] == MOVE ):            
            self.moveUnit( msg[1]['unit_id'], msg[1]['new_position'], msg[1]['orientation'], source )
            
        #elif( msg[0] == LEVEL ):                
        #    self.sendLevel( util.compileLevel( self.level ), source )
                        
        #elif( msg[0] == ENGINE_STATE ):                
        #    self.sendState( util.compileState( self, self.findPlayer( source ) ), source )
            
        elif( msg[0] == ARMY_LIST ):                
            self.handleArmyListMsg( msg[1], source )
            
        elif( msg[0] == FORCE_FIRST_TURN ):                
            self.firstTurn()
            
        elif( msg[0] == END_TURN ):
            self.endTurn( source )
                        
        elif( msg[0] == CHAT ):
            self.chat( msg[1], source, msg[2] )
                        
        elif( msg[0] == OVERWATCH ):
            self.unitUpdate( msg[1], OVERWATCH, source)
                        
        elif( msg[0] == SET_UP ):
            self.unitUpdate( msg[1], SET_UP, source)
                        
        elif( msg[0] == USE ):
            self.unitUpdate( msg[1], USE, source)
                        
        elif( msg[0] == TAUNT ):
            self.unitUpdate( msg[1], TAUNT, source)
                        
        elif( msg[0] == PING ):
            #print "ping: %2.2fms" % ((time.time() - msg[1]) * 1000)
            self.pong( source, msg[1] )            
                        
        elif( msg[0] == UNDEFINED_MSG_1 ):
            self.error("Engine is shutting down")
            self.stop = True            
            pass
                        
        elif( msg[0] == UNDEFINED_MSG_2 ):
            pass
                        
        elif( msg[0] == SHOOT ):
            self.handleShoot( msg[1]['shooter_id'], msg[1]['target_id'], source )
                        
        else:
            self.notify.error( "Unknown message Type: %s", msg )
            return
 
        self.event_handler.sendSession()
            
        
 
    def handleArmyListMsg(self, army_list, source ):
        
        if self.turn != 0:
            self.error( "Cannot deploy now, game already in progress", source )
            return
        
        player = self.findPlayer( source )
        
        if player.deployed:
            self.error( "Already deployed.", source)
            return
        
        #TODO: krav: check army size 
        #TODO: krav: check position 

        #delete old units
        for u in player.units:
            del self.units[u.id]
        player.units = []


        try:        
            for x, y, unit_type in army_list:
                tmpUnit = unit.loadUnit(unit_type, self)
                
                #check if this is legal position for deployment
                if self.level._deploy[x][y] != int(player.id):
                    raise Exception( "Illegal position for deployment for unit " + tmpUnit.name + "@" + str( (x,y) ) )
                
                tmpUnit.init( self.getUID(), player, x, y )                
                tmpUnit.heading = util.getHeading(tmpUnit.pos, self.level.center)
                
                if not self.level.putUnit( tmpUnit ):
                    raise Exception( "Unit:" + tmpUnit.name + "@" + str( (x,y) ) + " cannot be put on level.")                            
                
                player.units.append( tmpUnit )                
                self.units[tmpUnit.id] = tmpUnit
                self.checkUnitCanUse( tmpUnit )
        except Exception:
            self.notify.critical( "Exception:%s", sys.exc_info()[1] )
            self.error( sys.exc_info()[1], source )
            return   

        player.deployed = True
        self.error( "Deployment ok.", source)
        
        self.event_handler.addEvent( (DEPLOYMENT, player, 1) )
 
        #if at least 1 more player needs to deploy, than wait for him
        for plyr in self.players:
            if not plyr.deployed:
                return
 
        #otherwise - start first turn
        self.firstTurn()
        
        
    def unitUpdate(self, unit_id, param, source ):

        unit = self.findAndValidateUnit( unit_id, source )
        player = self.findPlayer( source )
        
        if player != self.active_player:
            self.error( "It is not your turn.", source )
            return                    
        
        if param == OVERWATCH:
            if unit.ap >= 2:
                unit.overwatch = not unit.overwatch
            else:
                self.error("Not enough AP for overwatch.", source)

        elif param == SET_UP:
            if not unit.hasHeavyWeapon():
                self.error( "The unit does not have any heavy weapons.", source )
                return

            if unit.set_up:
                msg = unit.tearDown()
                if msg:
                    self.error( msg, source )
                    return
            else:
                msg = unit.setUp()
                if msg:
                    self.error( msg, source )
                    return
                    
        elif param == USE:
            if not unit.can_use:
                self.error( "Unit cannot use anything.", source )
                return
                    
            if unit.ap < 1:
                self.error( "Not enough AP for using.", source )
                return
                    
            if self.use( unit ):
                unit.use()
                self.event_handler( (USE, unit) )
            else:
                return
                    
        elif param == TAUNT:
            if unit.ap < 1:
                self.error( "Not enough AP for taunting.", source )
                return
                    
            unit.taunt()            
            self.taunt( unit )

                    
        self.event_handler.addEvent( (UNIT, unit) )
        self.checkLevel()
        self.updateVisibility()
        
        
    def taunt(self, unit):

        self.event_handler.addEvent( (TAUNT, unit) )
        
        self.checkForAndDoOverwatch( unit )           
                                
        self.removeDeadUnits()
        
        
        
    def chat(self, msg, source, to_allies):
        sender = self.findPlayer( source )
        
        self.event_handler( (CHAT, sender, msg, to_allies) )      
            
                
    def loadArmyList(self):
        
        self.notify.debug( "Army lists loading" )
        
        xmldoc = minidom.parse('data/base/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( int(p.attributes['id'].value), p.attributes['name'].value, p.attributes['team'].value, self )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                
                x = int( u.attributes['x'].value )
                y = int( u.attributes['y'].value )
                
                unittype = u.attributes['type'].value
                
                #check to see level boundaries
                if( self.level.outOfBounds(x, y) ):
                    print "This unit is out of level bounds", unittype, x, y
                    continue
                
                
                tmpUnit = unit.loadUnit(unittype, self)
                tmpUnit.init( self.getUID(), player, x, y )                
                tmpUnit.heading = util.getHeading(tmpUnit.pos, self.level.center)

                
                if not self.level.putUnit( tmpUnit ):
                    continue                            
                
                player.units.append( tmpUnit )                
                self.units[tmpUnit.id] = tmpUnit
                self.checkUnitCanUse( tmpUnit )
                
            self.players.append( player )
    
        xmldoc.unlink()

        self.event_handler.initPlayers()
        
        self.notify.info( "Army lists loaded OK" )


    def endTurn(self, source):
        
#        player = self.findPlayer( source )       
#        if player != self.active_player:
#            self.error( "It's not your turn.", source)
#            return
        
        if self.checkVictoryConditions():
            self.error( "Game over, engine stopping" )
            time.sleep(3)
            self.stop = True
            return

        self.beginTurn()
                
        
    def checkLevel(self):
        vis_walls = {}
        changes = {}

        #calculate visible walls for every player and store it in vis_walls dict        
        for p in self.players:
            vis_walls[p.id] = visibleWalls( compileAllUnits( p.units ).values() , self.level)
            #print "player:", p.name, "walls:", vis_walls[p.id]
            
            
        #go through all walls in level
        for x in xrange( self.level.maxgridX ):
            for y in xrange( self.level.maxgridY ):
                if not self.level._grid[x][y]:
                    continue

                #go through all players and check if this wall can be seen (if it is in vis_walls)
                for p in self.players:
                    
                    #if there is a change from what this player last saw, note it 
                    if (x,y) in vis_walls[p.id]:
                        if self.level._grid[x][y] != self._grid_player[p.id][x][y]:
                            self._grid_player[p.id][x][y] = self.level._grid[x][y]
                            changes[p.id] = p
                            
                            
        for p in changes.values():
            self.event_handler.addEvent( (LEVEL, p) )

        
        
        
        
    def checkVictoryConditions(self):
        
        #mark all defeated players
        for p in self.players:
            if p.defeated:
                continue
            if not p.units:
                self.event_handler.addEvent( (INFO, p, 'U have no more units... hahahhhah') )
                self.error( p.name + ' was defeated!!!' )
                p.defeated = True
                
        
        #find a player who is alive, and check if only he/his team are alive
        for p in self.players:
            if not p.defeated:                
                for p2 in self.players:
                    if p == p2 or p.team == p2.team:
                        continue
                    if not p2.defeated:
                        return False
                
                
        #if we came to here, than we have a winning player/team
        #find a winner
        winner = None
        winning_team = None
        for p in self.players:
            if not p.defeated:
                if not winner:
                    winner = p
                else:
                    winning_team = p.team
                    break

        #draw!?
        if not winner and not winning_team:
            for p in self.players:
                self.event_handler.addEvent( (INFO, p, 'a draw.... pathetic...') )
                return True

        #send derogatory messages to losers
        for p in self.players:
            
            #a team won
            if winning_team:            
                if p.team == winning_team:
                    self.event_handler.addEvent( (INFO, p, 'YOU WIN!!!') )
                else:
                    self.event_handler.addEvent( (INFO, p, 'team ' + winning_team + ' WINS! ...and you lose!') )
            #just one player won
            else:
                if p == winner:
                    self.event_handler.addEvent( (INFO, p, 'YOU WIN!!!') )
                else:
                    self.event_handler.addEvent( (INFO, p, 'player ' + winner.name + ' WINS! ...and you lose!') )

        if winning_team:
            print "winning team:", winning_team
        else:
            print "winner:", winner.name
        return True



    def firstTurn(self):
        self.active_player = self.players[0]
        self.turn = 1

        print "turn:", self.turn, "\tplayer:", self.active_player.name

        #fill grid_player with default walls
        for p in self.players:
            self._grid_player[p.id] = []
            for line in self.level._grid:
                #copy the whole line, not just reference                
                self._grid_player[p.id].append(line[:])
                


        #go through all units of active player and reset them
        for unit in self.units.itervalues():   
            if unit.owner == self.active_player:            
                unit.newTurn( self.turn )
                
        #send ENGINE_STATE to all players
        self.event_handler.addEvent( (ENGINE_STATE,) )
        
        #send NEW_TURN to all players
        self.event_handler.addEvent( (NEW_TURN,) )
        
                                     
        #check visibility
        self.updateVisibility()
                                     
        self.checkLevel()
        

    def findNextPlayer(self):
        
        i = 0
        
        if self.active_player == self.players[-1]:
            i = -1
            self.turn += 1
        else:
            i = self.players.index( self.active_player )
        
        tmp_p = None

        for p in self.players[i+1:]:
            if p.defeated:
                continue
            tmp_p = p
            break
        
        if not tmp_p:
            self.turn += 1
            for p in self.players:
                if p.defeated:
                    continue
                self.active_player = p
                return
        else:
            self.active_player = tmp_p
        
             

    def beginTurn(self):

        self.findNextPlayer()

        print "turn:", self.turn, "\tplayer:", self.active_player.name

        #check visibility
        self.updateVisibility()
        
        #go through all units of active player and reset them
        for unit in self.active_player.units:               
            unit.newTurn( self.turn )

        #send NEW_TURN to all players
        self.event_handler.addEvent( (NEW_TURN,) )
        
        

    def getLOS(self, beholder, target ):
        return getLOSOnLevel( beholder.__dict__, target.__dict__, self.level )     

    def _giveDictUnits(self):
        tmp_units = {}
        
        for unt in self.units.itervalues():
            tmp_units[unt.id] = unt.__dict__ 

        return tmp_units


    def _mvdict(self, unit, returnOriginTile):
        
        return getMoveDict(unit.__dict__, self.level, self._giveDictUnits(), returnOriginTile)



    def getPath(self, unit, target_tile ):
        
        #if we are trying to find a path to the tile we are on
        if( target_tile == unit.pos ):
            return[]
        
        moveDict = self._mvdict(unit, True)

        #if target_tile tile is not in the move list
        if target_tile not in moveDict:
            self.notify.critical("getPath() got an invalid target tile:%s", target_tile )
            raise Exception( "Trying to move to an invalid target_tile:%s", target_tile )
        
        x = target_tile[0]
        y = target_tile[1]
        
        path_list = [ (target_tile, moveDict[target_tile]) ]
        
        tmp_dict_units = self._giveDictUnits()
        
        while( 1 ):
        
            biggest_ap = ( 0, 0 )
            
            #find a tile with biggest remaining AP next to this one
            for dx in xrange(-1,2):
                for dy in xrange(-1,2):
                    
                    if( dx == 0 and dy == 0 ):
                        continue
                    
                    pt = ( x+dx, y+dy )
                    
                    #check if the point is even in the list
                    if (pt in moveDict) == False:
                        continue
                    
                    #if we can't move here just skip
                    if( canIMoveHere( unit.__dict__, (x,y), dx, dy, self.level, tmp_dict_units ) == False ):
                        continue
                    
                    #if we are looking at the origin, and we can move there, we just checked that, stop
                    if( x + dx == unit.pos[0] and y + dy == unit.pos[1] ):
                        path_list.reverse()
                        return path_list
                    
                    #finally we can check the tile 
                    if( moveDict[pt] > biggest_ap[1] ):
                        biggest_ap =  (pt, moveDict[pt])
                    
            
            path_list.append( biggest_ap )
            x = biggest_ap[0][0]
            y = biggest_ap[0][1]
        
      
        raise Exception( "hahahah how did you get to this part of code?" )
        
                
    def findAndValidateUnit(self, unit_id, source):
        if( unit_id in self.units ) == False:
            self.notify.critical( "Got wrong unit id:%s", unit_id )
            self.error( "Wrong unit id.", source )
            return None

        unit = self.units[unit_id]

        #check to see if this is the owner
        if unit.owner.id != source:
            self.notify.critical( "Client:%s\ttried to do an action with unit that he does not own" % source.getAddress() )
            self.error( "You cannot do this to a unit you do not own.", source )
            return None

        return unit
        
        
    def validatePlayer(self, source):
        if self.active_player.id == source:
            return self.active_player
        
        self.error( 'It is not your turn.', source )
        return None
        
        
    def moveUnit(self, unit_id, new_position, new_heading, source ):

        owner = self.validatePlayer( source )
        if not owner: 
            return
        
        unit = self.findAndValidateUnit( unit_id, source )
        if not unit:
            return
        
        #check if we are unable to move
        if unit.pos != new_position:
            msg = unit.amIStuck()
            if msg:
                self.error( msg, source )            
                return 
        
        #special case if we just need to rotate the unit
        if unit.pos == new_position:
            
            #see if we actually need to rotate the unit
            if unit.rotate( new_heading ):
                self.event_handler.addEvent( (ROTATE, unit, new_heading ) )
            #if not, than do nothing
            else:
                return
            
        #otherwise do the whole moving thing
        else:
            try:
                path = self.getPath( unit, new_position )
            except Exception:
                self.notify.critical( "Exception:%s", sys.exc_info()[1] )
                self.error( sys.exc_info()[1], source )
                return   
            
            #everything checks out, do the actual moving
            for tile, ap_remaining in path:
                
                #do low level moving of unit
                self.level.removeUnit( unit )
                unit.rotate( tile )                
                unit.move( tile, ap_remaining )
                self.level.putUnit( unit )            
                                    
                #add event that unit moved
                self.event_handler.addEvent( (MOVE, unit, tile) )
                
                #check enemies vision to this unit
                self.checkEnemyVision(unit)
                
                #check if this unit spotted any new enemy
                spot = self.didISpotAnyoneNew( unit )
                
                #check for overwatch
                res_overwatch = self.checkForAndDoOverwatch( unit )
                
                #if there was a spotting or overwatch, stop movement 
                if spot or res_overwatch:
                    break

                
                #if this is the last tile than apply last orientation change
                if( tile == path[-1][0] ):
                    if unit.rotate( new_heading ):
                        self.event_handler.addEvent( (ROTATE, unit, new_heading ) )
        #---------------------------------------------------------------------------
                                        
        #check to see if unit can use at this new location
        self.checkUnitCanUse( unit )
        
        #refresh this unit's data
        self.event_handler.addEvent( (UNIT, unit) )

        self.removeDeadUnits()
        self.checkLevel()
            
        
        
    def checkEnemyVision(self, unit ):
        """Iterates over all players and checks and updates their visible_enemies list, also adds SPOT and VANISH events if needed"""
        
        #go through all enemy players, if we see this unit we need to spot or vanish someone
        for p in self.players:
            if p == unit.owner or p.team == unit.owner.team:
                continue
            
            seen = 0
            
            for enemy in p.units:
                if self.getLOS( enemy, unit ):
                    seen = 1
                    break
            
            if seen:
                if unit not in p.visible_enemies:
                    p.visible_enemies.append( unit )
                    self.event_handler.addEvent( (SPOT, p, unit) )
            else:
                if unit in p.visible_enemies:
                    p.visible_enemies.remove( unit )
                    self.event_handler.addEvent( (VANISH, p, unit) )
                
    
        

            
    def checkForAndDoOverwatch(self, unit):
        overwatch = False
        
        for p in self.players:
            if p == unit.owner or p.team == unit.owner.team:
                continue
            
            for enemy in p.units:  
                to_hit, msg = toHit( util.compileUnit(enemy), util.compileUnit(unit), self.level) #@UnusedVariable
                if to_hit:
                    if enemy.overwatch and enemy.inFront( unit.pos ) and enemy.alive:
                        if enemy.doOverwatch( unit, to_hit ):
                            overwatch = True
                        #if unit died, return
                        if not unit.alive:
                            break
        
        return overwatch
    
    
    
    
    def didISpotAnyoneNew(self, unit ):
        """Return True is a new enemy is spotted, False otherwise."""
        spotted = False
        owner = unit.owner
           
        for player in self.players:
            if player == owner or player.team == owner.team:
                continue        
        
            for enemy in player.units:
                if enemy not in owner.visible_enemies and self.getLOS( unit, enemy ):
                    owner.visible_enemies.append( enemy )
                    self.event_handler.addEvent( (SPOT, owner, enemy) )
                    spotted = True
                        
        return spotted
    
    

    def handleShoot(self, shooter_id, target_id, source ):
        
        owner = self.validatePlayer( source )
        if not owner:
            return
        
        shooter = self.findAndValidateUnit( shooter_id, source )
        if not shooter:
            return
        
        if target_id not in self.units:
            self.notify.critical( "Got wrong target id:%s", target_id )
            self.error( "Wrong target id.", source )
            return

        target = self.units[target_id]

        #check to see if the owner is trying to shoot his own or his allies units
        if target.owner == owner or target.owner.team == owner.team:
            self.notify.critical( "Client:%s\ttried to shoot his own unit." % source.getAddress() )
            self.error( "You cannot shoot you own units.", source )
            return
        
         
        to_hit, msg = toHit( util.compileUnit(shooter), util.compileUnit(target), self.level)
        if not to_hit:
            self.error( msg, source)
            return
                 
        
        if shooter.hasHeavyWeapon() and not shooter.set_up:
            if distanceTupple(shooter.pos, target.pos) >= 2:
                self.error( "Need to set up heavy weapon before shooting.", source )
                return
        
        #---------------- main shoot event ------------------------
        #if nothing happened, just return
        if not shooter.shoot( target, to_hit ):
            return
        
        self.checkForAndDoOverwatch( shooter )
                
        self.removeDeadUnits()        
                
        self.updateVisibility()
        self.checkLevel()
        
        
    def updateVisibility(self):
        
        #remove enemies that we don't see anymore, and send vanish messages
        for p in self.players:
            
            tmp_enemy_list = []
            for enemy in p.visible_enemies:
                for myunit in p.units:
                    if enemy not in tmp_enemy_list and self.getLOS( myunit, enemy ):
                        tmp_enemy_list.append( enemy )
                        
            #compare tmp_enemy_list with old enemy list
            for enemy in p.visible_enemies[:]:
                
                #if there is an enemy that vanished, send a message to player and remove it from visible list 
                if enemy not in tmp_enemy_list:
                    self.event_handler.addEvent( (VANISH, p, enemy) )
                    p.visible_enemies.remove( enemy )
                    
        
        #add new enemies
        for p in self.players:
            for enemy in self.units.itervalues():
                if enemy.owner == p or enemy.owner.team == p.team:
                    continue
                
                for myunit in p.units:
                    if enemy not in p.visible_enemies and self.getLOS( myunit, enemy ):
                        p.visible_enemies.append( enemy )
                        self.event_handler.addEvent( (SPOT, p, enemy) )

        
        
    def removeDeadUnits(self):
        
        for unit in self.units.values():
            if unit.alive:
                continue
                
            self.notify.info("Unit:%s died", unit.id )
            print "unit died:", unit.id
            
            del self.units[unit.id]
            
            self.level.removeUnit( unit )
            
            for p in self.players:            
                if unit in p.units:
                    p.units.remove( unit )
                if unit in p.visible_enemies:
                    p.visible_enemies.remove( unit )
                if unit in p.detected_enemies:
                    p.detected_enemies.remove( unit )
                
            self.dead_units[ unit.id ] = unit
            
            self.event_handler.addEvent( (UNIT, unit) )
            

    def findPlayer( self, source ):
        for p in self.players:
            if p.id == source:
                return p


    def checkUnitCanUse(self, cur_unit):        
        cur_unit.can_use = self._getUnitCanUse( cur_unit )
        
        
    def _getUnitCanUse(self, cur_unit):
        """For now checks only walls"""
        x = int(cur_unit.pos[0])
        y = int(cur_unit.pos[1])
        
        _2x = 2*x
        _2y = 2*y
        
        
        if cur_unit.heading == unit.HEADING_N:
            if self.level.gridCanUse( _2x+1, _2y+2 ):
                return True
        elif cur_unit.heading == unit.HEADING_S:
            if self.level.gridCanUse( _2x+1, _2y ):
                return True
        elif cur_unit.heading == unit.HEADING_E:
            if self.level.gridCanUse( _2x+2, _2y+1 ):
                return True
        elif cur_unit.heading == unit.HEADING_W:
            if self.level.gridCanUse( _2x, _2y+1 ):
                return True
            
        elif cur_unit.heading == unit.HEADING_NW:
            if self.level.gridCanUse( _2x-1, _2y+2 ):
                if self.level.gridMoveBlocked( _2x, _2y+1 ) or self.level.getHeight2( x-1, y ) > 1:
                    return False
                else:
                    return True
            if self.level.gridCanUse( _2x, _2y+3 ):
                if self.level.gridMoveBlocked( _2x+1, _2y+2 ) or self.level.getHeight2( x, y+1 ) > 1:
                    return False
                else:
                    return True

        elif cur_unit.heading == unit.HEADING_NE:
            if self.level.gridCanUse( _2x+3, _2y+2 ):
                if self.level.gridMoveBlocked( _2x+2, _2y+1 ) or self.level.getHeight2( x+1, y ) > 1:
                    return False
                else:
                    return True
            if self.level.gridCanUse( _2x+2, _2y+3 ):
                if self.level.gridMoveBlocked( _2x+1, _2y+2 ) or self.level.getHeight2( x, y+1 ) > 1:
                    return False
                else:
                    return True
               
        elif cur_unit.heading == unit.HEADING_SE:
            if self.level.gridCanUse( _2x+3, _2y ):
                if self.level.gridMoveBlocked( _2x+2, _2y+1 ) or self.level.getHeight2( x+1, y ) > 1:
                    return False
                else:
                    return True
            if self.level.gridCanUse( _2x+2, _2y-1 ):
                if self.level.gridMoveBlocked( _2x+1, _2y ) or self.level.getHeight2( x, y-1 ) > 1:
                    return False
                else:
                    return True
               
        elif cur_unit.heading == unit.HEADING_SW:
            if self.level.gridCanUse( _2x-1, _2y ):
                if self.level.gridMoveBlocked( _2x, _2y+1 ) or self.level.getHeight2( x-1, y ) > 1:
                    return False
                else:
                    return True
            if self.level.gridCanUse( _2x, _2y-1 ):
                if self.level.gridMoveBlocked( _2x+1, _2y ) or self.level.getHeight2( x, y-1 ) > 1:
                    return False
                else:
                    return True
               
        return False


    def use(self, cur_unit ):
        x = int(cur_unit.pos[0])
        y = int(cur_unit.pos[1])
        
        _2x = 2*x
        _2y = 2*y

        if cur_unit.heading == unit.HEADING_N:
            if self.level.gridCanUse( _2x+1, _2y+2 ):
                self.level.gridUse( _2x+1, _2y+2 )
                return True
        elif cur_unit.heading == unit.HEADING_S:
            if self.level.gridCanUse( _2x+1, _2y ):
                self.level.gridUse( _2x+1, _2y )
                return True
        elif cur_unit.heading == unit.HEADING_E:
            if self.level.gridCanUse( _2x+2, _2y+1 ):
                self.level.gridUse( _2x+2, _2y+1 )
                return True
        elif cur_unit.heading == unit.HEADING_W:
            if self.level.gridCanUse( _2x, _2y+1 ):
                self.level.gridUse( _2x, _2y+1 )
                return True
            
        elif cur_unit.heading == unit.HEADING_NW:
            if not self.level.gridMoveBlocked( _2x, _2y+1 ) and self.level.getHeight2( x-1, y ) < 2:
                if self.level.gridCanUse( _2x-1, _2y+2 ):
                    self.level.gridUse( _2x-1, _2y+2 )
                    return True

            if not self.level.gridMoveBlocked( _2x+1, _2y+2 ) and self.level.getHeight2( x, y+1 ) < 2:
                if self.level.gridCanUse( _2x, _2y+3 ):
                    self.level.gridUse( _2x, _2y+3 )
                    return True

        elif cur_unit.heading == unit.HEADING_NE:
            if not self.level.gridMoveBlocked( _2x+2, _2y+1 ) and self.level.getHeight2( x+1, y ) < 2:
                if self.level.gridCanUse( _2x+3, _2y+2 ):
                    self.level.gridUse( _2x+3, _2y+2 )
                    return True

            if not self.level.gridMoveBlocked( _2x+1, _2y+2 ) and self.level.getHeight2( x, y+1 ) < 2:
                if self.level.gridCanUse( _2x+2, _2y+3 ):
                    self.level.gridUse( _2x+2, _2y+3 )
                    return True

               
        elif cur_unit.heading == unit.HEADING_SE:
            if not self.level.gridMoveBlocked( _2x+2, _2y+1 ) and self.level.getHeight2( x+1, y ) < 2:
                if self.level.gridCanUse( _2x+3, _2y ):
                    self.level.gridUse( _2x+3, _2y )
                    return True

            if not self.level.gridMoveBlocked( _2x+1, _2y ) and self.level.getHeight2( x, y-1 ) < 2:
                if self.level.gridCanUse( _2x+2, _2y-1 ):
                    self.level.gridUse( _2x+2, _2y-1 )
                    return True
               
        elif cur_unit.heading == unit.HEADING_SW:
            if not self.level.gridMoveBlocked( _2x, _2y+1 ) and self.level.getHeight2( x-1, y ) < 2:
                if self.level.gridCanUse( _2x-1, _2y ):
                    self.level.gridUse( _2x-1, _2y )
                    return True

            if not self.level.gridMoveBlocked( _2x+1, _2y ) and self.level.getHeight2( x, y-1 ) < 2:
                if self.level.gridCanUse( _2x, _2y-1 ):
                    self.level.gridUse( _2x, _2y-1 )
                    return True
               
        return False



    def pickleSelf(self):

        try:
            #remove and save all transient objects        
            notify = self.notify        
            self.notify = None
            to_network = self.to_network
            self.to_network = None
            from_network = self.from_network
            self.from_network = None
            db_api = self.db_api
            self.db_api = None
    
            #pickle the engine
            pickled_engine = pickle.dumps( self ) 
    
            #restore all transient objects
            self.notify = notify
            self.to_network = to_network
            self.from_network = from_network
            self.db_api = db_api
            
            #update game record in database with pickled state
            self.db_api.setPickledEngine( self.game_id, pickled_engine )
        except:
            print sys.exc_info()
            return 0
        
        return 1

    
    def pong( self, source, t ):
        plyr = self.findPlayer(source)
        self.event_handler.addEvent( (PONG, plyr, t) )
        

    def error(self, msg, source):
        self.event_handler.addEvent( (ERROR, source, msg) )        


#-----------------------------------------------------------------------
def loadFromPickle( pickled_engine, from_network, to_network, notify, db_api ):
    #unpickle the engine state
    eng = pickle.loads(pickled_engine)

    #set transient variables
    eng.from_network = from_network
    eng.to_network = to_network
    eng.notify = notify
    eng.db_api = db_api
    
    print "loaded from pickle"
    
    return eng
    

if __name__ == "__main__":
    EngineThread().start()
