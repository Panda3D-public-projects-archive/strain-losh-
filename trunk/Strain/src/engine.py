from xml.dom import minidom
from unit import Unit
from level import Level
from pandac.PandaModules import Point2#@UnresolvedImport
import math
from messaging import EngMsg, Msg
from threading import Thread
import time
import logging
import sys, traceback
import cPickle as pickle


class Notify():
    
    def __init__(self):
        #=============================SET UP LOGGING===================================
        self.logger = logging.getLogger('EngineLog')
        self.hdlr = logging.FileHandler('Engine.log')
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdlr.setFormatter(self.formatter)
        self.logger.addHandler(self.hdlr) 
        self.logger.setLevel(logging.DEBUG)
        

    def critical(self,msg, *args):
        self.error(msg, *args)        
    def debug(self, msg,*args ):
        self.error(msg,*args)
        
    def info(self, msg,*args ):
        self.error(msg,*args)
            
    def error(self, msg,*args ):
        self.logger.critical(msg, *args)
        print msg%args
    

notify = Notify()

def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1

_PI = math.pi
_PI_2 = _PI / 2
_3_PI_2 = 3 * _PI / 2
_PI_4 = _PI / 4
_3_PI_4 = 3 * _PI / 4 
_5_PI_4 = 5 * _PI / 4
_2_PI = 2 * _PI
_PI_8 = _PI / 8
_3_PI_8 = 3 * _PI / 8
_5_PI_8 = 5 * _PI / 8
_7_PI_8 = 7 * _PI / 8


def getHeading( myPosition, lookAtPoint ):
    
    #trivial check if this is the same position, if it is, return none
    if myPosition == lookAtPoint:
        return Unit.HEADING_NONE
    
    angle = math.atan2( lookAtPoint.y - myPosition.y , lookAtPoint.x - myPosition.x )

    if angle < -_7_PI_8:
        return Unit.HEADING_W
    elif angle < -_5_PI_8:
        return Unit.HEADING_SW
    elif angle < -_3_PI_8:
        return Unit.HEADING_S
    elif angle < -_PI_8:
        return Unit.HEADING_SE
    elif angle < _PI_8:
        return Unit.HEADING_E
    elif angle < _3_PI_8:
        return Unit.HEADING_NE
    elif angle < _5_PI_8:
        return Unit.HEADING_N
    elif angle < _7_PI_8:
        return Unit.HEADING_NW
    
    return Unit.HEADING_W
    


class Player:
    
    def __init__(self, in_id, name, team):
        self.id = in_id
        self.name = name 
        self.team = team
        self.unitlist = []
        self.list_visible_enemies = []
        self.connection = None
        pass






class Engine( Thread ):
    
    players = []
    units = {}
        
    __shared_state = {}
    __instance = None
          
    __index_uid = 0

    #TODO: krav: maknut ovo i stavit konstante
    dynamics = { 'empty' : 0,
                 'unit' : 1 }

    @staticmethod
    def getInstance():
        """Singleton implementation"""
        if not Engine.__instance:
            Engine.__instance = Engine()
        return Engine.__instance
        
        
    #====================================init======================================0
    def __init__(self):
        notify.info("------------------------Engine Starting------------------------")
        self.__dict__ = self.__shared_state
        Engine.__instance = self

        Thread.__init__(self)
        

        self.stop = False
        self.level = None 
        self.dynamic_obstacles = []
        self.turn = 0        
        
        self.name = "EngineThread"


    def run(self):
        print "Engine started"
        EngMsg.startServer()
        
        self.level = Level( "level2.txt" )

        #we make this so its size is the same as level 
        self.dynamic_obstacles = [[(0,0)] * self.level.maxY for i in xrange(self.level.maxX)]
        
        self.loadArmyList()

        
        self.turn = 0        
        self.beginTurn()

        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        while( self.stop == False ):

            time.sleep( 0.1 )

            #see if there is a new client connected
            EngMsg.handleConnections()

            #get a message if there is one
            msg = EngMsg.readMsg()
            if msg:
                self.handleMsg( msg[0], msg[1] )
        
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        
        #we are shutting down everything   
        EngMsg.stopServer()       
        
        notify.info( "++++++++++++++++++++++++Engine stopped!++++++++++++++++++++++++" ) 

        return 0


    def handleMsg(self, msg, source):
        """This method is the main method for handling incoming messages to the Engine"""     
        
        if( msg.type == Msg.ENGINE_SHUTDOWN ):
            EngMsg.sendErrorMsg("Server is shutting down")
            self.stop = True
            
        elif( msg.type == Msg.MOVE ):            
            self.moveUnit( msg.values['unit_id'], msg.values['new_position'], msg.values['orientation'], source )
            
        elif( msg.type == Msg.LEVEL ):                
            EngMsg.sendLevel( pickle.dumps(self.level) )
                        
        elif( msg.type == Msg.ENGINE_STATE ):                
            EngMsg.sendState( self.compileState(), source )
            
        elif( msg.type == Msg.END_TURN ):
            self.endTurn()
                        
        else:
            notify.error( "Unknown message Type: %s", msg )
        
        
        
        pass

        
    def compileState(self):
        #TODO: krav: treba u paramtear ove funkcije primit za kojeg plejera se zove fja i prema tome ispunit cijeli state
        
        dic = {}

        dic[ 'pickled_units' ] = pickle.dumps( self.units )    
        dic[ 'pickled_level' ] = pickle.dumps( self.level )        
        dic[ 'turn' ] = self.turn     
        #TODO: krav: vidit kaj cemo s ovim   
        #dic[ 'pickled_players' ] = pickle.dumps( self.players )
        
        return dic
    
        
        
    def getUID(self):
        self.__index_uid += 1
        return self.__index_uid -1
    
        
    def loadArmyList(self):
        
        notify.debug( "Army lists loading" )
        
        xmldoc = minidom.parse('etc/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( p.attributes['id'].value, p.attributes['name'].value, p.attributes['team'].value )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                
                x = int( u.attributes['x'].value )
                y = int( u.attributes['y'].value )
                
                unittype = u.attributes['type'].value
                
                
                #check to see level boundaries
                if( self.outOfLevelBounds(x, y) ):
                    print "This unit is out of level bounds", unittype, x, y
                    continue
                
                #check to see if the tile is already occupied
                if( self.dynamic_obstacles[x][y][0] != Engine.dynamics['empty'] ):
                    print "This tile already occupied, unit cannot deploy here", x, y, unittype
                    continue
                 
                
                tmpUnit = Unit( self.getUID(),
                                player.id, 
                                unittype, 
                                x,
                                y )
                
                tmpUnit.heading = getHeading(tmpUnit.pos, self.level.center)
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.id] = tmpUnit
                
                self.dynamic_obstacles[x][y] = ( Engine.dynamics['unit'], tmpUnit.id )
                
            self.players.append( player )
    
        xmldoc.unlink()   

        notify.info( "Army lists loaded OK" )


    def endTurn(self):
        
        #TODO: krav: end turn here
        self.beginTurn()
        
        pass


    #TODO: krav: ovo treba parametar koji plejer je trnutno aktivan da mu ne posaljem krive unite
    def beginTurn(self):
        
        
        #increment turn by one
        self.turn += 1

        #TODO: krav: visible units here:
        #list_visible_units = []
        
        #for player in self.players:
        #    player.list_visible_enemies = []
        
        
        EngMsg.sendNewTurn( self.turn )
        
        
        #TODO: krav: napravit da ne dupla provjere
        
        #go through all units
        for unit_id in self.units:
            
            unit = self.units[unit_id]
            
            #replenish AP
            unit.current_AP = unit.default_AP
            
            if unit.resting:
                unit.current_AP += 1
                unit.resting = False
                
            
            
            
            #get new move_dict
            unit.move_dict = self.getMoveDict(unit)
            unit.losh_dict = self.getLOSHDict(unit.pos)
            
            #check visibility to other units
            #for unit2 in self.units:
            #    if unit2.pos in losh_dict:
                    
            #        list_visible_units.append( unit2 )
                    
            #        if( unit2.owner != unit_id ):
            #            unit_id.owner.list_visible_enemies.append( unit2 )
            
            #after updating everything send unit_id data to client        
            EngMsg.sendUnit( pickle.dumps(unit) )
        
        
        
        
        
        pass

        

    def outOfLevelBounds( self, x, y ):
        if( x < 0 or y < 0 or x >= self.level.maxX or y >= self.level.maxY ):
            return True
        else: 
            return False
        
    
    #this method returns list of tuples( Point2D, visibility ); visibility = {0:clear, 1:partial, 2:not visible}
    def getLOS(self, origin, target ):
        
        x1 = origin.x
        y1 = origin.y
        
        x2 = target.x
        y2 = target.y
        
        
        #we can't look at ourselves
        if( x1 == x2 and y1 == y2 ):
            return []
        
        
        absx0 = math.fabs(x2 - x1);
        absy0 = math.fabs(y2 - y1);
        

        sgnx0 = signum( x2 - x1 );
        sgny0 = signum( y2 - y1 );

        
        x = int( x1 );
        y = int( y1 );


        #distance, in tiles, between origin and currently tested tile
        distance = 1

        #this is the list we are going to return at the end
        list_visible_tiles = []
        
        #we add tiles to list with this visibility, if we encounter a partial obstacle, we change this to 1
        #so that all the next tiles we add are partial as well
        visibility = 0

    
        #TODO: krav: napravit da nemres vidit kroz dijagonale            
        if( absx0 > absy0 ):
            y_x = absy0/absx0;
            D = y_x -0.5;

            for i in xrange( int( absx0 ) ):
                
                #diagonal step
                if( D > 0 ):
                    if( sgny0 == -1 ): y -= 1
                    else: y += 1
                    D -= 1
            

                if( sgnx0 == 1 ): x += 1
                else: x -= 1

                D += y_x
                
                
                #=========================TEST==========================================
                list_visible_tiles, visibility = self.testTile(x, y, distance, list_visible_tiles, visibility)
                

                distance += 1
                pass
            
        #//(y0 >= x0)            
        else:
            x_y = absx0/absy0;
            D = x_y -0.5;

            for i in xrange( int( absy0 ) ):
        
                if( D > 0 ):
                    if( sgnx0 == -1 ): x -= 1
                    else: x += 1
                    D -= 1.0
            
    
                if( sgny0 == 1 ): y += 1
                else: y -= 1
    
                D += x_y
    
                
                #=========================TEST==========================================
                list_visible_tiles, visibility = self.testTile( x, y, distance, list_visible_tiles, visibility )
                

                distance += 1
                pass
                
                
        return list_visible_tiles
                

    #tests the tile for visibility
    def testTile(self, x, y, distance, list_visible_tiles, visibility ):
        
        #level bounds
        if( self.outOfLevelBounds(x, y) ):
            return( list_visible_tiles, visibility )
        
        #if we can't see here, set visibility to 2
        if( self.level._level_data[x][y] > 1 ):
            visibility = 2
        
        #partial view, increase visibility by one, if not already 2... 
        #if this is a tile next the origin, than ignore the partial
        #if we have already partial cover, and we come up on other, we cant see any further
        elif( self.level._level_data[x][y] == 1 ):
            if( distance > 1 and visibility < 2 ):
                visibility += 1
    
             
        list_visible_tiles.append( (Point2(x,y), visibility) )

                    
        return( list_visible_tiles, visibility )



    
    def getLOSHDict(self, position ):
        
        losh_dict = {}
        
        for i in xrange( self.level.maxX ):
            for j in xrange( self.level.maxY ):
                for a in self.getLOS(position, Point2(i,j)):
                    if( a[1] != 2 ):
                        
                        if a[0] in losh_dict:
                            if( losh_dict[a[0]] > a[1]):
                                losh_dict[a[0]] = a[1]
                        else:
                            losh_dict[a[0]] = a[1]
                            
        
        return losh_dict
        
               
                

    def getMoveDict(self, unit, returnOrigin = False ):    
                
        final_dict = {}

        open_list = [(unit.pos,unit.current_AP)]

        
        for tile, actionpoints in open_list:

            for dx in xrange(-1,2):
                for dy in xrange( -1,2 ):            
                    
                    if( dx == 0 and dy == 0):
                        continue
                    
                    
                    #we can't check our starting position
                    if( tile.x + dx == unit.pos.x and tile.y + dy == unit.pos.y ):
                        continue
                    
                    
                    x = int( tile.x + dx )
                    y = int( tile.y + dy )
                    
                    
                    if( self.outOfLevelBounds(x, y) ):
                        continue
                    
                    
                    if( self.canIMoveHere(unit, tile, dx, dy) == False ):
                        continue                   
                    
                    
                    #if we are checking diagonally
                    if( dx == dy or dx == -dy ):
                        ap = actionpoints - 1.5
                    else:
                        ap = actionpoints - 1
                    
                    if( ap < 0 ):
                        continue
                    
                    
                    pt = Point2(x,y) 
                    
                    
                    if pt in final_dict:
                        if( final_dict[pt] < ap ):
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
                    else: 
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
                        
                    
        if( returnOrigin ):
            final_dict[unit.pos] = unit.current_AP
            return final_dict
        
        return final_dict
  
 


    def canIMoveHere(self, unit, position, dx, dy ):
              
        dx = int( dx )
        dy = int( dy )
              
        if( (dx != 1 and dx != 0 and dx != -1) and 
            (dy != 1 and dy != 0 and dy != -1) ):
            notify.critical( "Exception: %s... %s", sys.exc_info()[1], traceback.extract_stack() )
            raise Exception( "Invalid dx (%d) or dy (%d)" %(dy ,dy) )
        
        ptx = int( position.x )
        pty = int( position.y )


        #check if the level is clear at that tile
        if( self.level._level_data[ ptx + dx ][ pty + dy ] != 0 ):
            return False
        
        #check if there is a dynamic obstacle in the way
        if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][0] != Engine.dynamics['empty'] ):
            #ok if it a unit, it may be the current unit so we need to check that
            if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][0] == Engine.dynamics['unit'] ):
                if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][1] != unit.id ):
                    return False

        
        #check diagonal if it is clear
        if( dx != 0 and dy != 0 ):
            
            #if there is something in level in the way
            if( self.level._level_data[ ptx + dx ][ pty ] != 0 or 
                self.level._level_data[ ptx ][ pty + dy ] != 0 ):
                return False
        
            #check if there is a dynamic thing in the way 
            if( self.dynamic_obstacles[ ptx + dx ][ pty ][0] != Engine.dynamics['empty'] ):
                #see if it is a unit
                if( self.dynamic_obstacles[ ptx + dx ][ pty ][0] == Engine.dynamics['unit'] ):
                    #so its a unit, see if it is friendly
                    unit_id = self.dynamic_obstacles[ ptx + dx ][ pty ][1] 
                    if( self.units[unit_id].owner_id != unit.owner_id ):
                        return False
                    

            if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] != Engine.dynamics['empty'] ):
                if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] == Engine.dynamics['unit'] ):
                    unit_id = self.dynamic_obstacles[ ptx ][ pty + dy ][1] 
                    if( self.units[unit_id].owner_id != unit.owner_id ):
                        return False

            
        return True
        


    
    def getPath(self, unit, target_tile ):
        
        #if we are trying to find a path to the tile we are on
        if( target_tile == unit.pos ):
            return[]
            
        
        moveDict = self.getMoveDict(unit, True)

        
        #if target_tile tile is not in the move list, then raise alarm
        if (target_tile in moveDict) == False:
            print "getPath() got an invalid target_tile"
            notify.critical("getPath() got an invalid target tile:%s", target_tile )
            raise Exception( "Trying to move to an invalid target_tile:%s", target_tile )
            
        
        
        x = target_tile.x
        y = target_tile.y
        
        
        path_list = [ (target_tile, moveDict[target_tile]) ]
        
        
        while( 1 ):
        
            biggest_ap = ( 0, 0 )
            
            #find a tile with biggest remaining AP next to this one
            for dx in xrange(-1,2):
                for dy in xrange(-1,2):
                    
                    if( dx == 0 and dy == 0 ):
                        continue
                    
                    pt = Point2( x+dx, y+dy )
                    
                    #check if the point is even in the list
                    if (pt in moveDict) == False:
                        continue
                    
                    
                    #if we can't move here just skip
                    if( self.canIMoveHere( unit, Point2(x,y), dx, dy) == False ):
                        continue
                    
                    #if we are looking at the origin, and we can move there, we just checked that, stop
                    if( x + dx == unit.pos.x and y + dy == unit.pos.y ):
                        path_list.reverse()
                        return path_list
                    
                    #finally we can check the tile 
                    if( moveDict[pt] > biggest_ap[1] ):
                        biggest_ap =  (pt, moveDict[pt])
                    
            
            path_list.append( biggest_ap )
            x = biggest_ap[0].x
            y = biggest_ap[0].y
        
      
        raise Exception( "hahahah how did you get to this part of code?" )
        
        
        
    def _moveUnit(self, unit, new_position, ap_remaining ):
        """This method will change the position of the unit without any checks, so call it AFTER you have checked that 
         this move is legal. Does everything needed when moving an unit, moving it in dynamic_obstalces, and posting a message 
         about it."""    
        
        #delete from dynamic_obstacles
        self.dynamic_obstacles[ int( unit.pos.x ) ][ int( unit.pos.y ) ] = ( Engine.dynamics['empty'], 0 )
        
        #set new position
        unit.pos = new_position
        
        #set new dynamic_obstacles
        self.dynamic_obstacles[ int( unit.pos.x ) ][ int( unit.pos.y ) ] = ( Engine.dynamics['unit'], unit.id )
        
        #reduce amount of AP for unit
        unit.current_AP = ap_remaining


    
    def _rotateUnit(self, unit, look_at_tile ):
        tmp_heading = getHeading(unit.pos, look_at_tile)
        if unit.heading != tmp_heading:
            unit.heading = tmp_heading
            return True
        return False
        
        
    def moveUnit(self, unit_id, new_position, new_heading, source ):
        
        if( unit_id in self.units ) == False:
            notify.critical( "Got wrong unit id:%s", unit_id )
            EngMsg.sendErrorMsg( "Wrong unit id.", source )
            return

        #TODO: krav: provjerit dal ovaj plejer koji je poslao move eksli smije micat ovaj unit

        unit = self.units[unit_id]

        move_actions = []
        
        #special case if we just need to rotate the unit
        if unit.pos == new_position:
            
            #see if we actually need to rotate the unit
            if self._rotateUnit( unit, new_heading ):
                move_actions.append( ('rotate', new_heading) )
            #if not, than do nothing
            else:
                return
            
        #otherwise do the whole moving thing
        else:
            try:
                path = self.getPath( unit, new_position )
            except Exception:
                notify.critical( "Exception:%s", sys.exc_info()[1] )
                EngMsg.sendErrorMsg( sys.exc_info()[1], source )
                return   
            
            #everything checks out, do the actual moving
            for tile, ap_remaining in path:
                self._rotateUnit( unit, tile )
                self._moveUnit( unit, tile, ap_remaining )
                move_actions.append( ('move', tile ) )

                #TODO: krav: movement interrupt                
                if self.isMovementInterrupted( unit ):
                    break
                
                #if this is the last tile than apply last orientation change
                if( tile == path[-1][0] ):
                    if self._rotateUnit(unit, new_heading):
                        move_actions.append( ('rotate', new_heading) )
                    
                    
        #we moved a unit so update its move_dict and losh_dict
        unit.move_dict = self.getMoveDict(unit)
        unit.losh_dict = self.getLOSHDict(unit.pos)
                    
            
        EngMsg.move( unit.id, move_actions )
        EngMsg.sendUnit( pickle.dumps(unit) )
            
            
        pass
    
    
    def isMovementInterrupted(self, unit):
        """Returns True if movement needs to stop"""
        #TODO: krav: check overwatch
        
        return False
        pass
    
    
    #we calculate visibility when (unit) has moved
    def calculateVisibility(self, unit ):
        
        losh_dict = self.getLOSHDict( unit.pos )
        
        
        for enemy in self.units:
            pass
        
        
        pass
    



    