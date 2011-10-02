from xml.dom import minidom
from Unit import Unit
from Level import Level
from pandac.PandaModules import Point2, Point3, NodePath, Vec3
import math




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
        pass






class Engine:
    
    __shared_state = {}

    players = []
    units = {}
        
        
    _index_uid = 0

        
        
    #====================================init======================================0
    def __init__(self):
        self.__dict__ = self.__shared_state


        self.level = Level("level2.txt")

        #we make this so its size is the same as level 
        self.dynamic_obstacles = [[(0,0)] * self.level.maxY for i in xrange(self.level.maxX)]

        self.loadArmyList()

        
       
        
        
    def getUID(self):
        self._index_uid += 1
        return self._index_uid -1
    
        
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
                if( self.dynamic_obstacles[x][y][0] != 0 ):
                    print "This tile already occupied, unit cannot deploy here", x, y, unittype
                    continue
                 
                
                tmpUnit = Unit( self.getUID(),
                                player, 
                                unittype, 
                                x,
                                y )
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.id] = tmpUnit
                
                self.dynamic_obstacles[x][y] = ( 1, tmpUnit.id )
                
            self.players.append( player )
    
        xmldoc.unlink()   
        

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



    
    def getLOSHList(self, position ):
        
        dict1 = {}
        
        for i in xrange( self.level.maxX ):
            for j in xrange( self.level.maxY ):
                for a in self.getLOS(position, Point2(i,j)):
                    if( a[1] != 2 ):
                        
                        try:
                            if( dict1[a[0]] > a[1] ):
                                dict1[a[0]] = a[1]
                        except:
                            dict1[a[0]] = a[1]
                        
        
        unique_losh_list = []        
        
        #transform dict1 to list
        for k in dict1.keys():
            unique_losh_list.append( ( k, dict1[k])  )        
                
        return unique_losh_list
                
                
                
    def getMoveList(self, unit ):    
        
        #this holds the same data as tmp_level, which we will convert to a list and than return
        final_dict = {}

        
        open_list = [(unit.pos,unit.current_AP)]


        
        for tile, actionpoints in open_list:

            for i in xrange(-1,2):
                for j in xrange( -1,2 ):            
                    
                    if( i == 0 and j == 0):
                        continue
                    
                    x = int( tile.x-i )
                    y = int( tile.y-j )
                    
                    
                    if( self.outOfLevelBounds(x, y) ):
                        continue
                    
                    
                    #if we are checking diagonally
                    if( i == j or i == -j ):
                        
                        #we cant move diagonally around a corner
                        if( self.level._level_data[x][ int( tile.y) ] != 0 or self.level._level_data[ int( tile.x ) ][y] != 0 ):
                            continue
                        
                        ap = actionpoints - 1.5
                            
                    else:
                        ap = actionpoints - 1
                    
                    
                    
                    if( ap < 0 ):
                        continue
                    
                    
                    
                    if( self.level._level_data[x][y] == 0 and self.dynamic_obstacles[x][y][0] == 0 ):
                        
                        pt = Point2(x,y) 
                        
                        try:
                            if( final_dict[pt] < ap ):
                                final_dict[pt] = ap
                                open_list.append( ( pt, ap ) ) 
                        except:
                                final_dict[pt] = ap
                                open_list.append( ( pt, ap ) ) 

                
  
    
        final_list = []
        
        #transform dict to list
        for k in final_dict.keys():
            final_list.append( ( k, final_dict[k])  )
        
        
        return final_list
        

    
    
    
    
    