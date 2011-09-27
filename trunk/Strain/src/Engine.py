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
    
    def __init__(self, id, name):
        self.id = id
        self.name = name 
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

        self.loadArmyList()
        self.level = Level("level3.txt")
        
        
        
        
    def getUID(self):
        self._index_uid += 1
        return self._index_uid -1
    
        
    def loadArmyList(self):
        xmldoc = minidom.parse('etc/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( self.getUID(), p.attributes['name'].value )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                tmpUnit = Unit( self.getUID(),
                                player, 
                                u.attributes['type'].value, 
                                u.attributes['x'].value,
                                u.attributes['y'].value )
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.id] = tmpUnit
                
            self.players.append( player )
    
        xmldoc.unlink()   
        
    
    #this method returns list of tuples( Point2D, visibility ); visibility = {0:clear, 1:partial, 2:not visible}
    def getLOS(self, origin, target ):
        
        x1 = origin.x
        y1 = origin.y
        
        x2 = target.x
        y2 = target.y
        
        
        absx0 = int( math.fabs(x2 - x1) );
        absy0 = int( math.fabs(y2 - y1) );
        

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

            for i in xrange( absx0 ):
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

            for i in xrange( absy0 ):
        
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
        if( x > self.level.maxX-1 or x < 0 or y > self.level.maxY-1 or y < 0 ):
            return( list_visible_tiles, visibility )
        
        #if we can't see here, set visibility to 2
        if( self.level._level_data[x][y] > 1 ):
            visibility = 2
        
        #partial view, set to 1 if not already 2... if this is a tile next the origin, than ignore the partial
        elif( self.level._level_data[x][y] == 1 ):
            if( distance > 1 and visibility < 1 ):
                visibility = 1
    
             
        list_visible_tiles.append( (Point2(x,y), visibility) )

                    
        return( list_visible_tiles, visibility )



    
    def getLOSList(self, position ):
        pass        
    
    