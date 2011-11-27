from xml.dom import minidom
import unit
from level import Level
import level
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
from util import compileEnemyUnit
import copy

notify = util.Notify()




class Engine( Thread ):
    
        
    __index_uid = 0

    def getUID(self):
        Engine.__index_uid += 1
        return Engine.__index_uid -1
    

        
    #====================================init======================================0
    def __init__(self):
        Thread.__init__(self)
        notify.info("------------------------Engine Starting------------------------")

        self.stop = False
        self.level = None         
        self.players = []
        self.units = {}
        
        self.turn = 0
        self.active_player = None
                
        self.name = "EngineThread"


    def run(self):
        engine._instance = self
        print "Engine started"
        EngMsg.startServer( notify )
        
        lvl = "level2.txt"
        self.level = Level( lvl )
        notify.info("Loaded level:%s", lvl )
      
        self.loadArmyList()
      
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


    def testLevelLOS(self):
        dic = {}
        
        print self.getLOS( self.units[0], self.units[1] )
        return
        
        
        print "poceo test"
        for x1 in xrange(self.level.maxX):
            for y1 in xrange( self.level.maxY ):
                for x2 in xrange(self.level.maxX):
                    for y2 in xrange( self.level.maxY ):
                        t1 = (x1,y1)
                        t2 = (x2,y2)
                        dic[ (t1,t2) ] = self.getTiles2D( t1 , t2 )
                        try:dic[ (t1,t2) ].pop()
                        except:pass
        
        print "zavrsio filanje"
        
        total = 0
        drukcijih = 0
        for t1, t2 in dic:
            lista = []
            listb = []
            
            for a,b in dic[ (t1,t2)]: #@UnusedVariable
                lista.append(a)
            for a,b in dic[ (t2,t1)]: #@UnusedVariable
                listb.append(a)
            
            #listb.reverse()
            
            for idx,a in enumerate(lista):
                if a != listb[idx]:
                    if drukcijih < 7:
                        print "--------nije jednako:", lista, listb 
                    drukcijih += 1
                    break
            total += 1
            
                
        print "zavrsio test, total:",total,"\tdrukcijih:", drukcijih
        pass
        


    def handleMsg(self, msg, source):
        """This method is the main method for handling incoming messages to the Engine"""     
        
        #TODO: krav: ovdje na pocetak stavit validate player
        
        if( msg[0] == ENGINE_SHUTDOWN ):
            EngMsg.sendErrorMsg("Server is shutting down")
            self.stop = True
            
        elif( msg[0] == MOVE ):            
            self.moveUnit( msg[1]['unit_id'], msg[1]['new_position'], msg[1]['orientation'], source )
            
        elif( msg[0] == LEVEL ):                
            EngMsg.sendLevel( util.compileLevel( self.level ) )
                        
        elif( msg[0] == ENGINE_STATE ):                
            EngMsg.sendState( util.compileState( self, self.findPlayer( source ) ), source )
            
        elif( msg[0] == END_TURN ):
            self.endTurn()
                        
        elif( msg[0] == CHAT ):
            self.chat( msg[1], source, msg[2] )
                        
        elif( msg[0] == OVERWATCH ):
            self.chat( msg[1], source, msg[2] )
                        
        elif( msg[0] == SHOOT ):
            self.shoot( msg[1]['shooter_id'], msg[1]['target_id'], source )
                        
        else:
            notify.error( "Unknown message Type: %s", msg )
        
        
    def chat(self, msg, source, to_allies):
        sender = self.findPlayer( source )
        
        for p in self.players:
            if not p.connection or p == sender:
                continue
            if to_allies:
                if p.team == sender.team:
                    EngMsg.chat( msg, sender.name, p.connection )
            else:                    
                EngMsg.chat( msg, sender.name, p.connection )
            
                
    def loadArmyList(self):
        
        notify.debug( "Army lists loading" )
        
        xmldoc = minidom.parse('data/base/armylist.xml')
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
                if( self.level.outOfBounds(x, y) ):
                    print "This unit is out of level bounds", unittype, x, y
                    continue
                
                
                tmpUnit = unit.loadUnit(unittype)
                tmpUnit.init( self.getUID(), player, x, y )                
                tmpUnit.heading = util.getHeading(tmpUnit.pos, self.level.center)

                
                if not self.level.putUnit( tmpUnit ):
                    continue                            
                
                player.units.append( tmpUnit )                
                self.units[tmpUnit.id] = tmpUnit
                
                
            self.players.append( player )
    
        xmldoc.unlink()   

        notify.info( "Army lists loaded OK" )


    def endTurn(self):
        
        if self.active_player == self.players[-1]:
            self.active_player = None          
        
        self.beginTurn()
        
        pass


    def beginTurn(self):

        if not self.active_player:
            self.active_player = self.players[0]
            self.turn += 1
        else:
            i = self.players.index(self.active_player)
            self.active_player = self.players[i+1]

        print "turn:", self.turn, "\tplayer:", self.active_player.name

        #go through all units of active player and reset them
        for unit in self.units.itervalues():   
            if unit.owner == self.active_player:            
                unit.newTurn( self.turn )
          
        #check visibility
        self.checkVisibility()

        #send all stuff to all players that are logged in        
        for p in self.players:
            if p.connection:
                EngMsg.sendNewTurn( self.turn, self.active_player.name, util.compileNewTurn(self, p), p.connection )
        
        
    def checkVisibility(self):

        for player in self.players:
            player.visible_enemies = []
            for myunit in player.units:
                for enemy in self.units.itervalues():
                    if enemy.owner == player or enemy.owner.team == player.team:
                        continue
                    if self.getLOS( myunit, enemy ):
                        if enemy not in player.visible_enemies: 
                            player.visible_enemies.append( enemy )
                            
        


    def getLOS(self, beholder, target ):
        """0-cant see, 1-partial, 2-full"""
        b_pos = beholder.pos + ( ( self.level.tuppleGet( beholder.pos ) + beholder.height -1 ) , )
        #print "print "beh:", beholder.pos, "\ttar:", target.pos 
        seen = 0        
        seen_back = 0        
        #check if we see target's head
        t1 = target.pos + ( ( self.level.tuppleGet( target.pos ) + target.height -1 ) , )        
        if self.getTiles3D( b_pos, t1 ):
            seen += 1
            seen_back += 1
        
        #check if we see target's feet
        t2 = target.pos + ( self.level.tuppleGet( target.pos ) , )
        if self.getTiles3D( b_pos, t2 ):
            seen += 1

        #TODO: krav: ovo stavit da vraca za oboje
        #check if target sees beholders feet
        #b2 = beholder.pos + ( ( self.level.tuppleGet( beholder.pos ) ) , )        
        #if self.getTiles3D( t1, b2 ):
        #    seen_back += 1
        #return ( seen, seen_back )
    
        return seen
    
    
    def getTiles3D(self, t1, t2 ):

        #we can't look at ourselves
        if( t1 == t2 ):
            return []
        
        x1, y1, z1 = t1
        x2, y2, z2 = t2
        
        #if one of our end points is not empty space, return false
        if self.level.test3D( x1, y1, z1 ) or self.level.test3D( x2, y2, z2 ):
            return False
        
        absx0 = math.fabs(x2 - x1);
        absy0 = math.fabs(y2 - y1);
        absz0 = math.fabs(z2 - z1);
        
        dist = int( util.distance(x1, y1, x2, y2) )

        list_visible_tiles = [ t1 ]
        rev = False
        
        if( absx0 > absy0 ):
            if x2 < x1:
                x1, y1, z1 = t2
                x2, y2, z2 = t1
                list_visible_tiles[0] = t2
                rev = True
        else:
            if y2 < y1:
                x1, y1, z1 = t2
                x2, y2, z2 = t1
                list_visible_tiles[0] = t2
                rev = True
        
        
        x = int( x1 );
        y = int( y1 );
        z = int( z1 )

        
        sgnz0 = util.signum(z2 - z1)
        z_d = absz0/dist
        
        if( absx0 > absy0 ):
            sgny0 = util.signum( y2 - y1 );
            y_x = absy0/absx0            
            D = y_x -0.5

            if dist > absz0:
                Dz = z_d - 0.5
            
            for i in xrange( int( absx0 ) ): #@UnusedVariable
                lastx, lasty, lastz = x, y, z
                
                if( D > 0 ):
                    y += sgny0
                    D -= 1

                if dist > absz0:
                    if Dz > 0:
                        z += sgnz0
                        Dz -= 1
                    Dz += z_d
                else: 
                    z = z + z_d * sgnz0

                x += 1
                D += y_x
                
                #=========================TEST==========================================
                if self.testTile3D( (x, y, int(z)), (lastx, lasty, int(lastz)) ):
                    list_visible_tiles.append( (x, y, int(z)) )
                else:
                    return False
                    break
                
        #//(y0 >= x0)            
        else:
            sgnx0 = util.signum( x2 - x1 );
            x_y = absx0/absy0
            D = x_y -0.5;
            
            if( dist > absz0 ):
                Dz = z_d - 0.5

            for i in xrange( int( absy0 ) ): #@UnusedVariable
                lastx, lasty, lastz = x, y, z
        
                if( D > 0 ):
                    x += sgnx0
                    D -= 1.0

                if dist > absz0:
                    if Dz > 0:
                        z += sgnz0
                        Dz -= 1
                    Dz += z_d 
                else:
                    z = z + z_d * sgnz0
                    
                y += 1
                D += x_y
                
                #=========================TEST==========================================
                if self.testTile3D( (x, y, int(z)), (lastx, lasty, int(lastz)) ):
                    list_visible_tiles.append( (x, y, int(z)) )
                else:
                    return False
                    break

        if rev:
            list_visible_tiles.reverse()
        return list_visible_tiles

                
    def getTiles2D(self, t1, t2 ):
        """this method returns list of tuples( (x,y, visibility ); visibility = {0:clear, 1:partial, 2:not visible}"""    
        #we can't look at ourselves
        if( t1 == t2 ):
            return []
        
        x1, y1 = t1
        x2, y2 = t2
        
        absx0 = math.fabs(x2 - x1);
        absy0 = math.fabs(y2 - y1);
        
        if( absx0 > absy0 ):
            if x2 < x1:
                x1, y1 = t2
                x2, y2 = t1
        else:
            if y2 < y1:
                x1, y1 = t2
                x2, y2 = t1
        
        
        x = int( x1 );
        y = int( y1 );

        #distance, in tiles, between t1 and currently tested tile
        distance = 1

        #this is the list we are going to return at the end
        list_visible_tiles = []
        
        #we add tiles to list with this visibility, if we encounter a partial obstacle, we change this to 1
        #so that all the next tiles we add are partial as well
        visibility = 0
        
        if( absx0 > absy0 ):
            sgny0 = util.signum( y2 - y1 );
            y_x = absy0/absx0
            D = y_x -0.5;

            for i in xrange( int( absx0 ) ): #@UnusedVariable
                lastx, lasty = x, y
                
                if( D > 0 ):
                    y += sgny0
                    D -= 1

                x += 1
                D += y_x
                
                #=========================TEST==========================================
                list_visible_tiles, visibility = self.testTile( x, y, distance, list_visible_tiles, visibility, lastx, lasty )
                
                distance += 1
            
        #//(y0 >= x0)            
        else:
            sgnx0 = util.signum( x2 - x1 );
            x_y = absx0/absy0
            D = x_y -0.5;

            for i in xrange( int( absy0 ) ): #@UnusedVariable
                lastx, lasty = x, y
        
                if( D > 0 ):
                    x += sgnx0
                    D -= 1.0
            
                y += 1
                D += x_y
                
                #=========================TEST==========================================
                list_visible_tiles, visibility = self.testTile( x, y, distance, list_visible_tiles, visibility, lastx, lasty )
                
                distance += 1
                
                
        return list_visible_tiles
                

    #tests the tile for visibility
    def testTile3D(self, pos, lastpos ):
        
        #level bounds
        if( self.level.outOfBounds( pos[0], pos[1] ) ):
            return False
        if( self.level.outOfBounds( lastpos[0], lastpos[1] ) ):
            return False
        
        #if we can't see here
        if self.level.test3D( pos[0], pos[1], pos[2] ):
            return False
        
        #moved along x
        if pos[0] != lastpos[0]:
            #moved along y
            if pos[1] != lastpos[1]:
                
                #moved along z - diagonal x-y-z
                if pos[2] != lastpos[2]:
                        if( self.level.test3D( lastpos[0], lastpos[1], pos[2] ) and
                            self.level.test3D( lastpos[0], pos[1], lastpos[2] ) and
                            self.level.test3D( pos[0], lastpos[1], lastpos[2] ) ):                             
                                return False
                         
                        if ( self.level.test3D( lastpos[0], pos[1], lastpos[2] ) and
                              self.level.test3D( lastpos[0], pos[1], pos[2] ) and
                              self.level.test3D( pos[0], lastpos[1], lastpos[2] ) and
                              self.level.test3D( pos[0], lastpos[1], pos[2] ) ): 
                            return False
                
                        return True
                #diagonal x-y
                if ( self.level.test3D( pos[0], lastpos[1], pos[2] ) and
                     self.level.test3D( lastpos[0], pos[1], pos[2] ) ):  
                            return False
                else:
                    return True

            #moved along z - diagonal x-z
            if pos[2] != lastpos[2]:
                if ( self.level.test3D( pos[0], pos[1], lastpos[2] ) and
                     self.level.test3D( lastpos[0], pos[1], pos[2] ) ):  
                            return False
                else:
                    return True
                    
        #moved along y 
        if pos[1] != lastpos[1]:
            #moved along z - diagonal y-z
            if pos[2] != lastpos[2]:
                if ( self.level.test3D( pos[0], pos[1], lastpos[2] ) and
                     self.level.test3D( pos[0], lastpos[1], pos[2] ) ):  
                            return False
                else:
                    return True

            
                
        return True
        

    #tests the tile for visibility
    def testTile(self, x, y, distance, list_visible_tiles, visibility, lastx, lasty ):
        
        #level bounds
        if( self.level.outOfBounds(x, y) ):
            return( list_visible_tiles, visibility )
        
        #if we can't see here, set visibility to 2, and return
        if( self.level._level_data[x][y] > 1 ):
            visibility = 2
            list_visible_tiles.append( ( (x,y), visibility) )                    
            return( list_visible_tiles, visibility )
        
        #partial view, increase visibility by one 
        if( self.level._level_data[x][y] == 1 ):
            #if this is a tile next the origin, than ignore the partial
            if distance > 1 and visibility < 2:
                    visibility += 1
    
        #diagonal
        if lastx != x and lasty != y:
            
            #if both side tiles are totally blocked, just set visibility to 2 and return
            if self.level._level_data[x][lasty] > 1 and self.level._level_data[lastx][y] > 1:
                visibility = 2
                
            #if both side tiles are partially blocked, set partial visibility
            elif self.level._level_data[x][lasty] == 1 and self.level._level_data[lastx][y] == 1:
                if distance > 1 and visibility < 2:                    
                        visibility += 1
                
            #if one side tile is completely blocked
            elif self.level._level_data[x][lasty] >= 2:
                
                #if other side tile is empty, or partial, treat it as partial cover
                if self.level._level_data[lastx][y] <= 1:
                    if distance > 1 and visibility < 2:                    
                            visibility += 1
                
            #if one side tile is completely blocked
            elif self.level._level_data[lastx][y] >= 2:
                
                #if other side tile is empty, or partial, treat it as partial cover
                if self.level._level_data[x][lasty] <= 1:
                    if distance > 1 and visibility < 2:                    
                            visibility += 1
                
        
        
        list_visible_tiles.append( ( (x,y), visibility) )                    
        return( list_visible_tiles, visibility )




    def getMoveDict(self, unit, returnOrigin = False ):    
                
        final_dict = {}

        open_list = [(unit.pos,unit.ap)]
        
        for tile, actionpoints in open_list:

            for dx in xrange(-1,2):
                for dy in xrange( -1,2 ):            
                    
                    if( dx == 0 and dy == 0):
                        continue
                    
                    
                    #we can't check our starting position
                    if( tile[0] + dx == unit.pos[0] and tile[1] + dy == unit.pos[1] ):
                        continue
                    
                    
                    x = int( tile[0] + dx )
                    y = int( tile[1] + dy )
                    
                    
                    if( self.level.outOfBounds(x, y) ):
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
                    
                    pt = (x,y) 
                    
                    if pt in final_dict:
                        if( final_dict[pt] < ap ):
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
                    else: 
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
                        
                    
        if( returnOrigin ):
            final_dict[unit.pos] = unit.ap
            return final_dict
        
        return final_dict
  
 


    def canIMoveHere(self, unit, position, dx, dy ):
              
        dx = int( dx )
        dy = int( dy )
              
        if( (dx != 1 and dx != 0 and dx != -1) and 
            (dy != 1 and dy != 0 and dy != -1) ):
            notify.critical( "Exception: %s... %s", sys.exc_info()[1], traceback.extract_stack() )
            raise Exception( "Invalid dx (%d) or dy (%d)" %(dy ,dy) )
        
        ptx = int( position[0] )
        pty = int( position[1] )


        if not self.level.tileClearForMoving( unit, ptx + dx, pty + dy ):
            return False

      
        #check diagonal if it is clear
        if( dx != 0 and dy != 0 ):

            if self.level.tuppleGet( (ptx + dx, pty) ) or self.level.tuppleGet( (ptx, pty + dy) ):
                return False
                
            #check if there is a dynamic thing in the way 
            if( self.level._dynamics[ ptx + dx ][ pty ][0] != level.DYNAMICS_EMPTY ):
                #see if it is a unit
                if( self.level._dynamics[ ptx + dx ][ pty ][0] == level.DYNAMICS_UNIT ):
                    #so its a unit, see if it is friendly
                    unit_id = self.level._dynamics[ ptx + dx ][ pty ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
                        return False
                    

            if( self.level._dynamics[ ptx ][ pty + dy ][0] != level.DYNAMICS_EMPTY ):
                if( self.level._dynamics[ ptx ][ pty + dy ][0] == level.DYNAMICS_UNIT ):
                    unit_id = self.level._dynamics[ ptx ][ pty + dy ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
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
            
        
        
        x = target_tile[0]
        y = target_tile[1]
        
        
        path_list = [ (target_tile, moveDict[target_tile]) ]
        
        
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
                    if( self.canIMoveHere( unit, (x,y), dx, dy) == False ):
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
            notify.critical( "Got wrong unit id:%s", unit_id )
            EngMsg.sendErrorMsg( "Wrong unit id.", source )
            return None

        unit = self.units[unit_id]

        #check to see if this is the owner
        if unit.owner.connection != source:
            notify.critical( "Client:%s\ttried to do an action with unit that he does not own" % source.getAddress() )
            EngMsg.sendErrorMsg( "You cannot do this to a unit you do not own." )
            return None

        return unit
        
        
    def validatePlayer(self, source):
        if self.active_player.connection == source:
            return True
        
        EngMsg.sendErrorMsg( 'It is not your turn.', source )
        return False
        
        
    def moveUnit(self, unit_id, new_position, new_heading, source ):

        if not self.validatePlayer( source ):
            return

        unit = self.findAndValidateUnit( unit_id, source )
        if not unit:
            return
                
        my_actions = []
        
        actions_for_others = {}
        #fill it up with empty lists
        for p in self.players:
            if p.connection == source:
                continue
            actions_for_others[p] = []                                    
                                    
        #special case if we just need to rotate the unit
        if unit.pos == new_position:
            
            #see if we actually need to rotate the unit
            if unit.rotate( new_heading ):
                my_actions.append( ('rotate', new_heading) )
                for p in self.players:
                    if unit in p.visible_enemies:
                        actions_for_others[p].append( ('rotate', new_heading) )
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
                
                self.level.removeUnit( unit )
                unit.rotate( tile )                
                unit.move( tile, ap_remaining )
                self.level.putUnit( unit )            
                                    
                my_actions.append( ('move', tile ) )              
                                 
                for p in self.players:
                    if unit in p.visible_enemies: 
                        actions_for_others[p].append( ('move', tile ) )
                 
                overwatch = self.checkEnemyVision( unit, actions_for_others )
                 
                res = self.checkMovementInterrupt( unit, overwatch )
                if res:
                    my_actions.extend( res )
                    break
                

                
                #if this is the last tile than apply last orientation change
                if( tile == path[-1][0] ):
                    if unit.rotate( new_heading ):
                        my_actions.append( ('rotate', new_heading) )
                    
                    for p in self.players:
                        if unit in p.visible_enemies: 
                            actions_for_others[p].append( ('rotate', new_heading) )
                    
                    
            
        EngMsg.move( unit.id, my_actions, source )
        for plyr in actions_for_others:
            if actions_for_others[plyr] and plyr.connection:
                EngMsg.move( unit.id, actions_for_others[plyr], plyr.connection )
            
            
        EngMsg.sendUnit( util.compileUnit(unit), source )
            

    def checkEnemyVision(self, unit, actions_for_others ):
        
        overwatch = []
        
        #go through all enemy players, if we see this unit we need to register its movement
        for p in self.players:
            if p == unit.owner:
                continue
            
            seen = 0
            
            for enemy in p.units:
                if self.getLOS( enemy, unit ):
                    seen = 1
                    if enemy.overwatch:
                        overwatch.append( enemy )
            
            if seen:
                if unit not in p.visible_enemies:
                    p.visible_enemies.append( unit )
                    actions_for_others[ p ].append( ('spot', compileEnemyUnit(unit) ) )
            else:
                if unit in p.visible_enemies:
                    p.visible_enemies.remove( unit )
                    actions_for_others[ p ].append( ('vanish', unit.id ) )
                
        return overwatch
    
    
    def checkMovementInterrupt(self, unit, overwatch ):
        spotted = self.checkMyVision( unit )        
        ret_actions = []        
        
        if spotted:
            for enemy in spotted:
                unit.owner.visible_enemies.append( enemy )
                ret_actions.append( ('spot', util.compileUnit(enemy)) )
                
        if overwatch:
            for enemy in overwatch:
                res = enemy.doOverwatch( unit )
                if res:
                    ret_actions.append( ('overwatch', res ) )
                if not unit.alive:
                    break
                        
            self.checkForDeadUnits()
                        
        return ret_actions
    
    
    def checkMyVision(self, unit):
        
        #we moved this unit, so we need visibilit to every enemy unit, and stop movement if this unit
        #sees anything or if an enemy unit on overwatch sees this unit
        spotted = []

        for player in self.players:
            if player == unit.owner or player.team == unit.owner.team:
                continue        
        
            for enemy in player.units:
                if self.getLOS( unit, enemy ) and enemy not in unit.owner.visible_enemies:
                    spotted.append( enemy )
                            
        return spotted
            

    def shoot(self, shooter_id, target_id, source ):
        
        if not self.validatePlayer( source ):
            return
        
        shooter = self.findAndValidateUnit( shooter_id, source )
        
        if not shooter:
            return
        
        if( target_id in self.units ) == False:
            notify.critical( "Got wrong unit id:%s", target_id )
            EngMsg.sendErrorMsg( "Wrong unit id.", source )
            return None

        target = self.units[target_id]

        #check to see if the owner is trying to shoot his own units
        if target.owner.connection == source:
            notify.critical( "Client:%s\ttried to shoot his own unit." % source.getAddress() )
            EngMsg.sendErrorMsg( "You cannot shoot you own units." )
            return None

         
        shoot_msg = shooter.shoot( target )
               
        #if nothing happened
        if not shoot_msg:
            return
                
        #check visibility for each player
        for p in self.players:
            print p.name
            #if this player is the one doing the shooting send him everything
            if shooter.owner == p:
                if p.connection:
                    EngMsg.shoot( shoot_msg, p.connection )
                
            else:
                #example message = [('rotate', 0, 3), ('shoot', 0, (4, 7), u'Bolt Pistol', [('bounce', 6)])]
                tmp_shoot_msg = copy.deepcopy(shoot_msg)
                for m in tmp_shoot_msg[:]:

                    if m[0] == 'rotate':
                        unit_id = m[1]
                        #if we dont see the shooter, remove the rotate msg                    
                        if self.units[unit_id].owner != p and self.units[unit_id] not in p.visible_enemies:
                            tmp_shoot_msg.remove( m )

                    elif m[0] == 'shoot':
                        sht, unit_id, pos, wpn, lst = m

                        #if we dont see the shooter, remove him and his position
                        if self.units[unit_id] not in p.visible_enemies:
                            unit_id = -1
                            pos = None
                        #go through list of targets and if we dont see the target, remove it from the list
                        for effect in lst[:]:
                            tmp_target_id = effect[1]
                            if self.units[tmp_target_id].owner != p and self.units[tmp_target_id] not in p.visible_enemies:
                                lst.remove( effect )
                                
                        i = tmp_shoot_msg.index(m)
                        tmp_shoot_msg.pop( i )
                        new = (sht, unit_id, pos, wpn, lst)
                        tmp_shoot_msg.insert( i, new )
                        
                        if p.connection:
                            EngMsg.shoot( tmp_shoot_msg, p.connection )

        
        self.checkForDeadUnits()
        
        
        #update units for players and their allies
        for p in self.players:
            if p == shooter.owner or p.team == shooter.owner.team:
                if p.connection:
                    EngMsg.sendUnit( util.compileUnit(shooter), p.connection )
            if p == target.owner or p.team == target.owner.team:
                if p.connection: 
                    EngMsg.sendUnit( util.compileUnit(target), p.connection ) 
        
        
        #TODO: krav: ovo provjerit sa 3 igraca, sa 2 nece bas radit
        self.updateVisibilityAndSendVanishMessages()
        
        
        
    def updateVisibilityAndSendVanishMessages(self):
        
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
                    if p.connection:
                        EngMsg.sendMsg( ('vanish', enemy.id) , p.connection )
                    p.visible_enemies.remove( enemy )
                        
        
        
    def checkForDeadUnits(self):
        
        for unit in self.units.values():
            if unit.alive:
                continue
                
            notify.info("Unit:%s died", unit.id )
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


    def findPlayer( self, source ):
        for p in self.players:
            if p.connection == source:
                return p


if __name__ == "__main__":
    Engine().start()
