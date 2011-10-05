from xml.dom import minidom
from Unit import Unit
from Level import Level
from pandac.PandaModules import Point2, Point3, NodePath, Vec3
import math
from Messaging import Message, Messaging





def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1




class Player:
    
    def __init__(self, id, name, team):
        self.id = id
        self.name = name 
        self.team = team
        self.unitlist = []
        self.list_visible_enemies = []
        pass






class Engine:
    
    __shared_state = {}

    players = []
    units = {}
        
        
    __index_uid = 0


    dynamics = { 'empty' : 0,
                 'unit' : 1 }

        
        
    #====================================init======================================0
    def __init__(self):
        self.__dict__ = self.__shared_state


        self.level = Level("level2.txt")

        #we make this so its size is the same as level 
        self.dynamic_obstacles = [[(0,0)] * self.level.maxY for i in xrange(self.level.maxX)]

        self.turn = 0


        self.loadArmyList()

        self.moveUnit( self.units[self.units.keys()[0]], Point2( 0, 0 )  )
        

        
        
    def getUID(self):
        self.__index_uid += 1
        return self.__index_uid -1
    
        
    def loadArmyList(self):
        xmldoc = minidom.parse('etc/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( self.getUID(), p.attributes['name'].value, p.attributes['team'].value )                        
            
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
                                player, 
                                unittype, 
                                x,
                                y )
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.id] = tmpUnit
                
                self.dynamic_obstacles[x][y] = ( Engine.dynamics['unit'], tmpUnit.id )
                
            self.players.append( player )
    
        xmldoc.unlink()   




    def beginTurn(self):
        
        #increment turn by one
        self.turn += 1

        
        list_visible_units = []
        
        for player in self.players:
            player.list_visible_enemies = []
        
        
        #TODO: krav: napravit da ne dupla provjere
        
        #go through all units
        for unit in self.units:
            
            #reset AP to default
            unit.current_AP = unit.default_AP
            
            #check visibility to other units
            losh_dict = self.getLOSHList( unit.pos, True )            
            for unit2 in self.units:
                if( losh_dict.has_key( unit2.pos ) ):
                    
                    list_visible_units.append( unit2 )
                    
                    if( unit2.owner != unit ):
                        unit.owner.list_visible_enemies.append( unit2 )
            
        
        
        
        
        
        
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

    
                
        if( absx0 > absy0 ):
            y_x = absy0/absx0;
            D = y_x -0.5;

            for i in xrange( int( absx0 ) ):
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
                        
                        if( losh_dict.has_key(a[0]) ):
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
                    
                    
                    if( final_dict.has_key( pt ) ):
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
                    if( self.units[unit_id].owner != unit.owner ):
                        return False
                    

            if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] != Engine.dynamics['empty'] ):
                if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] == Engine.dynamics['unit'] ):
                    unit_id = self.dynamic_obstacles[ ptx ][ pty + dy ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
                        return False

            
        return True
        


    
    def getPath(self, unit, target_tile ):
        
        moveDict = self.getMoveDict(unit, True)

        
        #if target_tile tile is not in the move list, then raise alarm
        if( moveDict.has_key( target_tile ) == False ):
            print "getPath() got an invalid target_tile"
            raise Exception( "getPath() got an invalid target_tile" )
            
        
        
        x = target_tile.x
        y = target_tile.y
        
        path_list = [ target_tile ]
        
        
        while( 1 ):
        
            biggest_ap = ( 0, 0 )
            
            #find a tile with biggest remaining AP next to this one
            for dx in xrange(-1,2):
                for dy in xrange(-1,2):
                    
                    if( dx == 0 and dy == 0 ):
                        continue
                    
                    pt = Point2( x+dx, y+dy )
                    
                    #check if the point is even in the list
                    if( moveDict.has_key( pt ) == False ):
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
                    
            
            path_list.append( biggest_ap[0] )
            x = biggest_ap[0].x
            y = biggest_ap[0].y
        
      
        raise Exception( "hahahah how did you get to this part of code?" )
        
        
        
    """This method will change the position of the unit without any checks, so call it AFTER you have checked that 
     this move is legal. Does everything needed when moving an unit, moving it in dynamic_obstalces, and posting a message 
     about it."""    
    def _moveUnit(self, unit, new_position ):
        
        #delete from dynamic_obstacles
        self.dynamic_obstacles[ int( unit.pos.x ) ][ int( unit.pos.y ) ] = ( Engine.dynamics['empty'], 0 )
        
        #remember old position and set new position
        old_pos = unit.pos
        unit.pos = new_position
        
        #set new dynamic_obstacles
        self.dynamic_obstacles[ int( unit.pos.x ) ][ int( unit.pos.y ) ] = ( Engine.dynamics['unit'], unit.id )
        
        #add this action in message queue
        #Messaging.queue_list.append( Message( Message.types['move'], ( unit.id, old_pos, unit.pos )  ) )
        Messaging.move( unit.id, old_pos, unit.pos )
        
        
        
        
    def moveUnit(self, unit, new_position ):
        
        try:
            path = self.getPath( unit, new_position )
        except:
            raise Exception("Not a valid destination.")
    
        
        for tile in path:
            self._moveUnit( unit, tile )

        
        
        pass
    
    
    #we calculate visibility when (unit) has moved
    def calculateVisibility(self, unit ):
        
        losh_dict = self.getLOSHDict( unit.pos )
        
        
        for enemy in self.units.keys():
            pass
        
        
        pass
    



    