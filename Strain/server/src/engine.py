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


LEVELS_ROOT = "./data/levels/"

engine_state_filename = "engine_state.txt"


######################################################################################################
######################################################################################################
class EngineThread( Thread ):
    
    
    def __init__( self, game_id, from_network, to_network, notify, default = True, level = None, budget = None, players = None ):
        Thread.__init__(self)
        
        self.name = ("EngineThread-" + str(game_id))
            
        self.setDaemon(True)
        self.stop = False

        self.game_id = game_id

        self.notify = notify
            
        #to check if we need to load Engine from file/db..
        saved_engine = None 
        try:
            saved_engine = open( engine_state_filename, "r" )
        except:
            pass
        
        if saved_engine:
            self.engine = loadFromPickle( saved_engine, from_network, to_network, notify ) 
        else:
            self.engine = Engine( game_id, from_network, to_network, notify )
            if default:
                self.engine.InitDefault()
            else:
                self.engine.Init( level, budget, players )


        
    def run(self):

        while True:
            self.engine.runOneTick()
            if self.stop:
                break
            
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
    def __init__(self, game_id, from_network, to_network, notify):
        self.notify = notify
        self.notify.info("------------------------Engine Starting game_id:%d------------------------" %game_id)

        self.game_id = game_id
        self.from_network = from_network
        self.to_network = to_network

        self.stop = False
        self.level = None         
        self.players = []
        self.units = {}
        self.dead_units = {}
        
        #K-player.id V-grid that player with that id saw last
        self._grid_player = {}
        
        
        self.turn = 0
        self.active_player = None

        self.army_size = 1000

        self.observer = Player( OBSERVER_ID, 'observer', None, self )
        self.observer.defeated = True
        
        print "Engine started"


        

    def InitDefault(self):
        level_filename = "LevelBlockout.txt"
        self.level = Level( LEVELS_ROOT + level_filename )
        self.notify.info("Loaded level:%s", level_filename )

        self.loadArmyList()
        

    def Init(self, level, budget, players):
        level_filename = level + ".txt"
        self.level = Level( LEVELS_ROOT + level_filename )
        self.notify.info("Loaded level:%s", level_filename )

        self.loadArmyList()
        

    def runOneTick(self):
        
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        while not self.stop:

            time.sleep( 0.1 )
    
            #get a message if there is one
            msg = self.from_network.getMyMsgs( self.game_id )
            if msg:
                print "-----", msg
                self.handleMsg( msg[0][1:], msg[0][0] )

        
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
              
        return 0


    def handleMsg(self, msg, source):
        """This method is the main method for handling incoming messages to the Engine"""     
 
        if( msg[0] == ENGINE_SHUTDOWN ):
            self.error("Engine is shutting down")
            self.stop = True
            
        elif( msg[0] == MOVE ):            
            self.moveUnit( msg[1]['unit_id'], msg[1]['new_position'], msg[1]['orientation'], source )
            
        elif( msg[0] == LEVEL ):                
            self.sendLevel( util.compileLevel( self.level ), source )
                        
        elif( msg[0] == ENGINE_STATE ):                
            self.sendState( util.compileState( self, self.findPlayer( source ) ), source )
            
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
            self.pong( source )            
                        
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

            #a = pickle.dumps(self)
            dump_file = open( engine_state_filename, "w" )
            self.pickleSelf()
            pickle.dump(self, dump_file )
            print "pickled engine to:", engine_state_filename
            exit()

            
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
                player.addUseMsg( unit.id )
                self.observer.addUseMsg( unit.id )
            else:
                return
                    
        elif param == TAUNT:
            if unit.ap < 1:
                self.error( "Not enough AP for taunting.", source )
                return
                    
            unit.taunt()            
            self.taunt( unit )

                    
        player.addUnitMsg( compileUnit(unit) )
        self.observer.addUnitMsg( compileUnit(unit) )
        
        self.checkAndSendLevelMsgs()
        self.updateVisibilityAndSendVanishAndSpotMessages()
        
        
    def taunt(self, unit):
        
        res_overwatch = self.checkForAndDoOverwatch( unit )
        
        unit_ids_involved = { unit.id:0 }
        
        if res_overwatch:
           
            #check visibility for each player                              
            for p in self.players:  
                if p == unit.owner:
                    unit.owner.addTauntMsg( unit.id, res_overwatch )
                    self.observer.addTauntMsg( unit.id, res_overwatch )
                    continue
                       
                tmp_shoot_msg = self.parseShootMsgForPlayer( res_overwatch, p )
                p.addTauntMsg( unit.id, (tmp_shoot_msg) )         

            unit_ids_involved.update( self.findUnitsInvolved( res_overwatch ) )
                        
        #there was no overwatch
        else:
            
            for p in self.players:
                if p == unit.owner:            
                    unit.owner.addTauntMsg( unit.id,  None )
                    self.observer.addTauntMsg( unit.id, None )
                    continue
                
                if unit in p.visible_enemies:
                    p.addTauntMsg( unit.id, None )
        
        
        self.sendUNITMsgsAndRemoveDeadUnits( unit_ids_involved )
        
        
        
    def chat(self, msg, source, to_allies):
        sender = self.findPlayer( source )
        
        for p in self.players:
            if p == sender:
                continue
            if to_allies:
                if p.team == sender.team:
                    p.addChatMsg( msg, sender.name )
            else:                    
                p.addChatMsg( msg, sender.name )
            
        if not to_allies:
            self.observer.addChatMsg( msg, sender.name )
                
                
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
        
        self.notify.info( "Army lists loaded OK" )


    def endTurn(self, source):
        
#        player = self.findPlayer( source )       
#        if player != self.active_player:
#            self.error( "It's not your turn.", source)
#            return
        
        if self.checkVictoryConditions():
            self.error( "Game over, engine stopping" )
            self.observer.saveMsgs()
            time.sleep(3)
            self.stop = True
            return

        self.beginTurn()
                
        
    def checkAndSendLevelMsgs(self):
        #TODO: krav: ovo popravit
        vis_walls = {}
        changes = {}
        
        for p in self.players:
            vis_walls[p.id] = visibleWalls( compileAllUnits( p.units ).values() , self.level)
            print "player:", p.name, "walls:", vis_walls[p.id]
            
            
        for x in xrange( self.level.maxgridX ):
            for y in xrange( self.level.maxgridY ):
                if not self.level._grid[x][y]:
                    continue

                for p in self.players:
                    #TODO: krav: brijem da ova provjera ne radi bas tocno, treba provjerit
                    if (x,y) in vis_walls[p.id]:
                        if self.level._grid[x][y] != self._grid_player[p.id][x][y]:
                            self._grid_player[p.id][x][y] = self.level._grid[x][y]
                            changes[p.id] = p
                            
                            
        for p in changes.values():
            p.addLevelMsg( util.compileLevelWithDifferentGrid(self.level, self._grid_player[p.id]))
        
        
        
        
    def checkVictoryConditions(self):
        
        #mark all defeated players
        for p in self.players:
            if p.defeated:
                continue
            if not p.units:
                p.addErrorMsg( 'U have no more units... hahahhhah' )
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
                p.addErrorMsg( 'a draw.... pathetic...' )
                return True
                if p == self.players[-1]:
                    self.observer.addErrorMsg( 'a draw.... pathetic...' )

        #send derogatory messages to losers
        for p in self.players:
            
            #a team won
            if winning_team:            
                if p.team == winning_team:
                    p.addErrorMsg( 'YOU WIN!!!' )
                else:
                    p.addErrorMsg( 'team ' + winning_team + ' WINS! ...and you lose!' )
            #just one player won
            else:
                if p == winner:
                    p.addErrorMsg( 'YOU WIN!!!' )
                else:
                    p.addErrorMsg( 'player ' + winner.name + ' WINS! ...and you lose!' )

        if winning_team:
            print "winning team:", winning_team
            self.observer.addErrorMsg( "winning team:" + str(winning_team) )
        else:
            print "winner:", winner.name
            self.observer.addErrorMsg( "winner:" + winner.name )
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
                
        for p in self.players:
            #delete all previous msgs (like vanish and spot)
            p.msg_lst = []
            p.addEngineStateMsg( util.compileState(self, p) )
            p.addNewTurnMsg( util.compileNewTurn(self, p) )        
                                     
        #check visibility
        self.updateVisibilityAndSendVanishAndSpotMessages()
                                     
        #ok so we have all units for this game initialized, add them all to observer's list
        #so obs can see them all when adding engine_state and new_turn messages
        for u in self.units.values():
            self.observer.units.append( u )
                                     
                                     
        self.observer.addEngineStateMsg( util.compileState(self, self.observer) )
        self.observer.addNewTurnMsg( util.compileNewTurn(self, self.observer) )        

        self.checkAndSendLevelMsgs()
        

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
        self.updateVisibilityAndSendVanishAndSpotMessages()
        
        #go through all units of active player and reset them
        for unit in self.active_player.units:               
            unit.newTurn( self.turn )

        #send new turn messages       
        for p in self.players:
            p.addNewTurnMsg( util.compileNewTurn(self, p) )
        
        self.observer.addNewTurnMsg( util.compileNewTurn(self, p) )
        

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
        
        #list that we will send to owning player        
        my_actions = []
        
        #this is for parsing overwatch msgs
        res_overwatch = None
        
        #dict where we will fill out actions for other players that they see
        actions_for_others = {}
        #fill it up with empty lists
        for p in self.players:
            if p == owner:
                continue
            actions_for_others[p] = []                                    
                                    
        #special case if we just need to rotate the unit
        if unit.pos == new_position:
            
            #see if we actually need to rotate the unit
            if unit.rotate( new_heading ):
                my_actions.append( (ROTATE, new_heading) )
                for p in self.players:
                    if unit in p.visible_enemies:
                        actions_for_others[p].append( (ROTATE, new_heading) )
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
                
                self.level.removeUnit( unit )
                unit.rotate( tile )                
                unit.move( tile, ap_remaining )
                self.level.putUnit( unit )            
                                    
                my_actions.append( (MOVE, tile ) )              
                                
                #check vision for enemy 
                for p in self.players:
                    if unit in p.visible_enemies: 
                        actions_for_others[p].append( (MOVE, tile ) )
                 
                self.checkEnemyVision( unit, actions_for_others )
                
                res_spot = self.didISpotAnyone( unit )
                res_overwatch = self.checkForAndDoOverwatch( unit ) 
                if res_spot or res_overwatch:
                    if res_spot:
                        my_actions.extend( res_spot )
                    if res_overwatch:
                        my_actions.extend( res_overwatch )
                    break

                
                #if this is the last tile than apply last orientation change
                if( tile == path[-1][0] ):
                    if unit.rotate( new_heading ):
                        my_actions.append( ( ROTATE, new_heading) )
                    
                    for p in self.players:
                        if unit in p.visible_enemies: 
                            actions_for_others[p].append( (ROTATE, new_heading) )


        #so we know which units to update with UNIT msgs            
        unit_ids_involved = { unit.id:0 }


        #check visibility for each player                    
        if res_overwatch:          
            for p in self.players:  
                if p == owner:
                    continue
                
                for ov_msg in res_overwatch:       
                    tmp_shoot_msg = self.parseShootMsgForPlayer( ov_msg[1], p )         
                    actions_for_others[p].append( ('overwatch', tmp_shoot_msg) )
                            
                                        
            unit_ids_involved.update( self.findUnitsInvolved( res_overwatch ) )
            
            
        #send everything to owner of moving unit
        owner.addMoveMsg( unit.id, my_actions )
        self.observer.addMoveMsg( unit.id, my_actions )
        
        #send stuff that other players need to see
        for plyr in actions_for_others:
            if actions_for_others[plyr]:
                plyr.addMoveMsg( unit.id, actions_for_others[plyr] )

        #check to see if unit can use at this new location
        self.checkUnitCanUse( unit )

        self.sendUNITMsgsAndRemoveDeadUnits( unit_ids_involved )
        self.checkAndSendLevelMsgs()
            
        
        
    def sendUNITMsgsAndRemoveDeadUnits(self, unit_ids_involved ):
        #send UNIT msgs
        for tmp_unit_id in unit_ids_involved:
            tmp_unit = self.units[tmp_unit_id] 
            for p in self.players:
                if tmp_unit.owner == p or tmp_unit.owner.team == p.team:
                    p.addUnitMsg( util.compileUnit(tmp_unit) )                                        
                else:
                    if tmp_unit in p.visible_enemies:
                        p.addUnitMsg( util.compileEnemyUnit(tmp_unit) )
                        
            self.observer.addUnitMsg( util.compileUnit(tmp_unit) )                     
        
        self.removeDeadUnits()

            
    def checkForAndDoOverwatch(self, unit):
        ret_actions = []
        
        for p in self.players:
            if p == unit.owner:
                continue
            
            for enemy in p.units:  
                to_hit, msg = toHit( util.compileUnit(enemy), util.compileUnit(unit), self.level) #@UnusedVariable
                if to_hit:
                    if enemy.overwatch and enemy.inFront( unit.pos ) and enemy.alive:
                        res = enemy.doOverwatch( unit, to_hit )
                        if res:
                            ret_actions.append( ('overwatch', res ) )
                        if not unit.alive:
                            break
        
        
        return ret_actions
    
    
    def parseShootMsgForPlayer(self, shoot_msg, player): 
        #example message = [(ROTATE, 0, 3), (SHOOT, 0, (4, 7), u'Bolt Pistol', [('bounce', 6)])]
        tmp_shoot_msg = copy.deepcopy(shoot_msg)
        for m in tmp_shoot_msg[:]:
            if m[0] == ROTATE:
                tmp_unit_id = m[1]
                tmp_unit = self.units[tmp_unit_id]
                #if we dont see this unit, remove the rotate msg                    
                if tmp_unit.owner != player and tmp_unit not in player.visible_enemies:
                    tmp_shoot_msg.remove( m )

            elif m[0] == SHOOT or m[0] == 'melee':
                sht, tmp_unit_id, pos, wpn, lst = m
                tmp_unit = self.units[tmp_unit_id] 
                #if we dont see the shooter, remove him and his position
                if player != tmp_unit.owner and tmp_unit not in player.visible_enemies:
                    tmp_unit_id = -1
                    pos = None
                #go through list of targets and if we dont see the target, remove it from the list
                for effect in lst[:]:
                    tmp_target_id = effect[1]
                    trgt = self.units[tmp_target_id]
                    if trgt.owner != player and trgt not in player.visible_enemies:
                        lst.remove( effect )
                        
                i = tmp_shoot_msg.index(m)
                tmp_shoot_msg.pop( i )
                new = (sht, tmp_unit_id, pos, wpn, lst)
                tmp_shoot_msg.insert( i, new )
                
                #p.addShootMsg( tmp_shoot_msg )
                #actions_for_others[p].append( ('overwatch', tmp_shoot_msg) )
    
        return tmp_shoot_msg
    
    
    
    def checkEnemyVision(self, unit, actions_for_others ):
            
        #go through all enemy players, if we see this unit we need to spot or vanish someone
        for p in self.players:
            if p == unit.owner:
                continue
            
            seen = 0
            
            for enemy in p.units:
                if self.getLOS( enemy, unit ):
                    seen = 1
                    break
            
            if seen:
                if unit not in p.visible_enemies:
                    p.visible_enemies.append( unit )
                    actions_for_others[ p ].append( ( SPOT, compileEnemyUnit(unit) ) )
            else:
                if unit in p.visible_enemies:
                    p.visible_enemies.remove( unit )
                    actions_for_others[ p ].append( ( VANISH, unit.id ) )
                
    
    
    def didISpotAnyone(self, unit ):
        spotted = self.checkMyVision( unit )        
        ret_actions = []        
        
        if spotted:
            for enemy in spotted:
                unit.owner.visible_enemies.append( enemy )
                ret_actions.append( ( SPOT, util.compileEnemyUnit(enemy)) )
                        
        return ret_actions
    
    
    def checkMyVision(self, unit):
        
        #we moved this unit, so we need visibility to every enemy unit, and stop movement if this unit
        #sees anything or if an enemy unit on overwatch sees this unit
        spotted = []

        for player in self.players:
            if player == unit.owner or player.team == unit.owner.team:
                continue        
        
            for enemy in player.units:
                if enemy not in unit.owner.visible_enemies and self.getLOS( unit, enemy ):
                    spotted.append( enemy )
                            
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

        #check to see if the owner is trying to shoot his own units
        if target.owner == owner:
            self.notify.critical( "Client:%s\ttried to shoot his own unit." % source.getAddress() )
            self.error( "You cannot shoot you own units.", source )
            return
        
         
        to_hit, msg = toHit( util.compileUnit(shooter), util.compileUnit(target), self.level)
        if not to_hit:
            self.error( msg, source)
            return
                 
        
        if shooter.hasHeavyWeapon() and not shooter.set_up:
            if distanceTupple(shooter.pos, target.pos) > 2:
                self.error( "Need to set up heavy weapon before shooting.", source )
                return
        
        #---------------- main shoot event ------------------------
        shoot_msg = shooter.shoot( target, to_hit )
         
        #if nothing happened, just return
        if not shoot_msg:
            return
                
                
        res = self.checkForAndDoOverwatch( shooter )
        if res:
            shoot_msg.extend( res )
                
                            
                
        #check visibility for each player
        for p in self.players:

            #if this player is the one doing the shooting send him everything
            if shooter.owner == p:
                p.addShootMsg( shoot_msg )
                self.observer.addShootMsg( shoot_msg )
                continue
                
            tmp_shoot_msg = self.parseShootMsgForPlayer( shoot_msg, p )
            p.addShootMsg( tmp_shoot_msg )

        #find all units involved in shooting: shooter and (multiple) targets, and update them
        unit_ids_involved = { shooter.id:0, target.id:0 } 
        unit_ids_involved.update( self.findUnitsInvolved( shoot_msg ) )                  
        self.sendUNITMsgsAndRemoveDeadUnits( unit_ids_involved )        
                
        self.updateVisibilityAndSendVanishAndSpotMessages()
        self.checkAndSendLevelMsgs()
            
            
    def findUnitsInvolved(self, shoot_msg ):
        unit_ids_involved = {}
        
        for cmd in shoot_msg:
            if cmd[0] == SHOOT: 
                unit_ids_involved[ cmd[1] ] = 0
                for trgt in cmd[4]:
                    unit_ids_involved[ trgt[1] ] = 0
            elif cmd[0] == ROTATE:
                unit_ids_involved[ cmd[1] ] = 0
            elif cmd[0] == 'overwatch': 
                for cmd2 in cmd[1]:
                    if cmd2[0] == ROTATE:
                        unit_ids_involved[ cmd2[1] ] = 0
                    elif cmd2[0] == SHOOT:
                        unit_ids_involved[ cmd2[1] ] = 0
                        for trgt in cmd2[4]:
                            unit_ids_involved[ trgt[1] ] = 0
            
        return unit_ids_involved
        
        
        
    def updateVisibilityAndSendVanishAndSpotMessages(self):
        
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
                    p.addMsg( (VANISH, enemy.id) )
                    p.visible_enemies.remove( enemy )
                    
        
        #add new enemies
        for p in self.players:
            for enemy in self.units.itervalues():
                if enemy.owner == p or enemy.owner.team == p.team:
                    continue
                
                for myunit in p.units:
                    if enemy not in p.visible_enemies and self.getLOS( myunit, enemy ):
                        p.visible_enemies.append( enemy )
                        p.addMsg( ( SPOT, util.compileEnemyUnit(enemy)) )
        
        
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
        self.notify = None


    def sendDeploymentMsg( self, level, army_size, source ):
        deploy_dict = {}
        
        deploy_dict['level'] = util.compileLevel( level )
        deploy_dict['army_size'] = army_size
        
        self.to_network.putMsg( source, ( DEPLOYMENT, deploy_dict ) )
        
    
    
    def pong( self, source ):
        self.to_network.putMsg( source, (PONG, time.time()) )
        

    def error(self, msg, source = None):
        if not source:
            for p in self.players:
                p.addErrorMsg( msg )
            return
        
        self.to_network.putMsg( source, (ERROR, msg) )


#-----------------------------------------------------------------------
def loadFromPickle( pickled_engine, from_network, to_network, notify ):
    
    #eng = pickle.loads(pickled_engine)
    eng = pickle.load(pickled_engine)


    #now cleanup all things that are session related
    #set the msg queues
    eng.from_network = from_network
    eng.to_network = to_network
    
    #set logging
    eng.notify = notify
    
    print "loaded from pickle"
    
    return eng
    

if __name__ == "__main__":
    EngineThread().start()
