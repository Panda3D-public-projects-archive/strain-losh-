'''
Created on 19.12.2011.

@author: krav
'''
import math
import time
from xml.dom import minidom


COMMUNICATION_PROTOCOL = 0.1


DYNAMICS_EMPTY = 0
DYNAMICS_UNIT = 1


def levelVisibilityDict( unit_list, level ):
    vis_dict = {}
    for x in xrange(level.maxX):
        for y in xrange(level.maxY):
            vis_dict[(x,y)] = 0

    for unit in unit_list:            
        for x in xrange(level.maxX):
            for y in xrange(level.maxY):
                x_y = (x,y)
                
                if vis_dict[x_y] == 1:
                    continue
                
                if level.getHeight( x_y ):
                    vis_dict[x_y] = 1
                    continue
                     
                tiles = getTiles2D( unit['pos'], x_y, level )
                    
                if tiles:
                    for t in tiles:
                        vis_dict[t] = 1
                    #vis_dict[x_y] = 1
                    continue
          
            
    return vis_dict            


def getMoveDict( unit, level, units, returnOriginTile = False ):    
    """returnOriginTile - if you need to get the tile the unit is standing on, set this to True"""        
    final_dict = {}
    open_list = [(unit['pos'],unit['ap'])]
    
    for tile, actionpoints in open_list:

        for dx in xrange(-1,2):
            for dy in xrange( -1,2 ):            
                
                if( dx == 0 and dy == 0):
                    continue
                
                #we can't check our starting position
                if( tile[0] + dx == unit['pos'][0] and tile[1] + dy == unit['pos'][1] ):
                    continue
                
                x = int( tile[0] + dx )
                y = int( tile[1] + dy )
                
                if( level.outOfBounds(x, y) ):
                    continue
                
                if( canIMoveHere(unit, tile, dx, dy, level, units) == False ):
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
                    
                
    if( returnOriginTile ):
        final_dict[unit['pos']] = unit['ap']
        return final_dict
    
    return final_dict



def canIMoveHere( unit, position, dx, dy, level, units ):
          
    dx = int( dx )
    dy = int( dy )
          
    if( (dx != 1 and dx != 0 and dx != -1) and 
        (dy != 1 and dy != 0 and dy != -1) ):
        #notify.critical( "Exception: %s... %s", sys.exc_info()[1], traceback.extract_stack() )
        raise Exception( "Invalid dx (%d) or dy (%d)" %(dy ,dy) )
    
    ptx = int( position[0] )
    pty = int( position[1] )


    if not tileClearForMoving( unit, ptx + dx, pty + dy, level ):
        return False


    #check grid if unit can move to destination
    if not checkGridMove(ptx, pty, dx, dy, level):
        return False

  
    #check diagonal if it is clear
    if( dx != 0 and dy != 0 ):

        if level.getHeight( (ptx + dx, pty) ) or level.getHeight( (ptx, pty + dy) ):
            return False
            
        #no need to check for 'real variable here, if we are this close to enemy, we MUST know he is there                
        #check if there is a dynamic thing in the way and see if it is a unit, if it is friendly than ok
        stuff = level.getDynamic( ptx + dx, pty ) 
        if stuff and stuff[0] == DYNAMICS_UNIT:
            if( units[ stuff[1] ]['owner_id'] != unit['owner_id'] ):
                return False
                
        stuff = level.getDynamic( ptx, pty + dy ) 
        if stuff and stuff[0] == DYNAMICS_UNIT:
            if( units[ stuff[1] ]['owner_id'] != unit['owner_id'] ):
                return False
                
    return True


def checkGridMove( x, y, dx, dy, level ):
    
    _2x = x*2
    _2y = y*2
  
    if dx == 1:
        if dy == 1:      
            if level.gridMoveBlocked( _2x+2, _2y+1 ) or level.gridMoveBlocked( _2x+1, _2y+2 ) or \
                level.gridMoveBlocked( _2x+3, _2y+2 ) or level.gridMoveBlocked( _2x+2, _2y+3 ):
                    return False
            
                        
        if dy == -1:
            if level.gridMoveBlocked( _2x+2, _2y+1 ) or level.gridMoveBlocked( _2x+1, _2y ) or \
                level.gridMoveBlocked( _2x+3, _2y ) or level.gridMoveBlocked( _2x+2, _2y-1 ):
                    return False
                        
        if level.gridMoveBlocked( _2x+2, _2y+1 ):
            return False
        
        
    if dx == -1:
        if dy == 1:
            if level.gridMoveBlocked( _2x, _2y+1 ) or level.gridMoveBlocked( _2x+1, _2y+2 ) or \
                level.gridMoveBlocked( _2x-1, _2y+2 ) or level.gridMoveBlocked( _2x, _2y+3 ):
                    return False
                        
        if dy == -1:
            if level.gridMoveBlocked( _2x, _2y+1 ) or level.gridMoveBlocked( _2x+1, _2y ) or \
                level.gridMoveBlocked( _2x-1, _2y ) or level.gridMoveBlocked( _2x, _2y-1 ):
                    return False
             
             
        if level.gridMoveBlocked( _2x, _2y+1 ):
            return False
        
        
    if dy == 1:
        if level.gridMoveBlocked( _2x+1, _2y+2 ):
            return False

    if dy == -1:
        if level.gridMoveBlocked( _2x+1, _2y ):
            return False
    

    return True


def tileClearForMoving(unit, x, y, level):
    #check if the level is clear at that tile
    if level.getHeight( (x, y) ):
        return False
    
    ret = level.getDynamic( x, y ) 
    if ret:
        if ret[0] == DYNAMICS_UNIT:
            if ret[1] != unit['id']:
                return False
    
    return True


def getLOSOnLevel( beholder_dict, target_dict, level ):    
    return getTiles2D( beholder_dict['pos'], target_dict['pos'], level )

            
def getTiles2D( t1, t2, level ):
    x1, y1 = t1
    x2, y2 = t2
    
    #we see ourself
    if( t1 == t2 ):
        return [ (x1,y1) ]
    
    #if one of our end points is not empty space, return false
    if level.opaque( x1, y1, 2 ) or level.opaque( x2, y2, 2 ):
        return False
    
    absx0 = math.fabs(x2 - x1);
    absy0 = math.fabs(y2 - y1);
    
    list_visible_tiles = [ (x1,y1) ]
    rev = False
    
    if( absx0 > absy0 ):
        if x2 < x1:
            x1, y1 = t2
            x2, y2 = t1
            list_visible_tiles = []
            rev = True
    else:
        if y2 < y1:
            x1, y1 = t2
            x2, y2 = t1
            list_visible_tiles = []
            rev = True
    
    
    x = int( x1 )
    y = int( y1 )

    
    if( absx0 > absy0 ):
        sgny0 = signum( y2 - y1 );
        y_x = absy0/absx0      
        y_x_2 = y_x/2      
        D = y_x -0.5

        for i in xrange( int( absx0 ) ): #@UnusedVariable
            _2x = x*2
            _2y = y*2
            
            if( D > 0 ):
                if D < y_x_2:
                    if( level.outOfBounds( x+1, y ) ):
                        return False
                    if level.opaque( x+1, y, 2 ) or level.gridVisionBlocked( _2x+2, _2y+1 ):
                        return False
                    if sgny0 > 0 and level.gridVisionBlocked( _2x+3, _2y+2 ):
                        return False
                    if sgny0 < 0 and level.gridVisionBlocked( _2x+3, _2y ):
                        return False
                    
                    list_visible_tiles.append( (x+1, y) )
                    
                else:
                    if sgny0 > 0:
                        if( level.outOfBounds( x, y+1 ) ):
                            return False
                        if level.opaque( x, y+1, 2 ) or level.gridVisionBlocked( _2x+1, _2y+2 ) or level.gridVisionBlocked( _2x+2, _2y+3 ):
                            return False
                        list_visible_tiles.append( (x, y+1) )
                    else:
                        if( level.outOfBounds( x, y-1 ) ):
                            return False
                        if level.opaque( x, y-1, 2 ) or level.gridVisionBlocked( _2x+1, _2y ) or level.gridVisionBlocked( _2x+2, _2y-1 ):
                            return False
                        list_visible_tiles.append( (x, y-1) )

                    
                y += sgny0
                D -= 1

            else:
                
                #so now we know we are going only +1 on x 
                if level.gridVisionBlocked( 2*x+2, 2*y+1 ):
                    return False

                if level.opaque( x+1, y, 2):
                    return False

            x += 1
            D += y_x

            #its visible add it to list            
            list_visible_tiles.append( (x, y) )
            
    #//(y0 >= x0)            
    else:
        sgnx0 = signum( x2 - x1 );
        x_y = absx0/absy0
        x_y_2 = x_y/2
        D = x_y -0.5;
        left_blocked = False
        right_blocked = False
        
        for i in xrange( int( absy0 ) ): #@UnusedVariable
            _2x = x*2
            _2y = y*2
            
            if( D > 0 ):
                
                #if this is straight 45 degree diagonal
                if x_y == 1:

                    if sgnx0 > 0:
                        if( level.outOfBounds( x+1, y+1 ) ):
                            return False
                        
                        if level.gridVisionBlocked( _2x+2, _2y+1 ) or level.gridVisionBlocked( _2x+3, _2y+2 ) or level.opaque( x+1, y, 2 ):
                            right_blocked = True
                            
                        if level.gridVisionBlocked( _2x+1, _2y+2 ) or level.gridVisionBlocked( _2x+2, _2y+3 ) or level.opaque( x, y+1, 2):
                            left_blocked = True

                        if right_blocked and left_blocked:
                            return False
                    
                    if sgnx0 < 0:
                        if( level.outOfBounds( x-1, y+1 ) ):
                            return False
                    
                        if level.gridVisionBlocked( _2x, _2y+1 ) or level.gridVisionBlocked( _2x-1, _2y+2 ) or level.opaque( x-1, y, 2 ):
                            left_blocked = True
                            
                        if level.gridVisionBlocked( _2x+1, _2y+2 ) or level.gridVisionBlocked( _2x, _2y+3 ) or level.opaque( x, y+1, 2 ):
                            right_blocked = True

                        if left_blocked and right_blocked:                            
                                return False

                #not a 45 diagonal                    
                else:
                               
                    if D < x_y_2:
                        if( level.outOfBounds( x, y+1 ) ):
                            return False
                        if level.opaque( x, y+1, 2 ) or level.gridVisionBlocked( _2x+1, _2y+2 ):
                            return False
                        if sgnx0 > 0 and level.gridVisionBlocked( _2x+2, _2y+3 ):
                            return False
                        if sgnx0 < 0 and level.gridVisionBlocked( _2x, _2y+3 ):
                            return False
                        list_visible_tiles.append( (x, y+1) )
                            
                    else:
                        
                        if sgnx0 > 0:
                            if( level.outOfBounds( x+1, y ) ):
                                return False
                            if level.opaque( x+1, y, 2 ) or level.gridVisionBlocked( _2x+3, _2y+2 ) or level.gridVisionBlocked( _2x+2, _2y+1 ):
                                return False
                            list_visible_tiles.append( (x+1, y) )
                        else:
                            if( level.outOfBounds( x-1, y ) ):
                                return False
                            if level.opaque( x-1, y, 2 ) or level.gridVisionBlocked( _2x-1, _2y+2 ) or level.gridVisionBlocked( _2x, _2y+1 ):
                                return False
                            list_visible_tiles.append( (x-1, y) )
                
                x += sgnx0
                D -= 1.0

            else:
                #so now we know we are going only +1 on y 
                if level.gridVisionBlocked( 2*x+1, 2*y+2 ):
                    return False

                if level.opaque( x, y+1, 2):
                    return False

            y += 1
            D += x_y
            
            #its clear, add it to visible list
            list_visible_tiles.append( (x, y) )


    if rev:
        list_visible_tiles.reverse()
        list_visible_tiles.append( t2 )
        
    return list_visible_tiles



def toHit( shooter, target, level ):
    
    tiles = getTiles2D( shooter['pos'], target['pos'], level)
    if not tiles:
        return ( 0, "No line of sight.")
        
    if len( tiles ) == 1:
        return ( 100, "You shooting yourself?")
        
    vision = _getVision(tiles, level)
    
    if not vision:
        return ( 0, "No line of sight." )
    
    distance = int( distanceTupple( shooter['pos'], target['pos'] ) )
    #check if this is melee
    if distance < 2:
        print "--------MELEEEEEEEEEEEEEE!!!!!!!!!!!!------------"
        return ( 90, "Melee." )
    
    wpn = shooter['ranged_weapon']
    if distance > wpn['range']:
        return ( 0, "Out of range! " + wpn['name'] + " max range:" + str(wpn['range']) + ". Target is @" + str(distance) )

    percent = 90 - distance * 5
    
    if vision == 2:
        return ( percent, wpn['name'] + "@" + str(distance)  )
    elif vision == 1:
        return ( int(percent * 0.66), "Partial cover (x0.66)," + wpn['name'] + "@" + str(distance) )


def _getVision( tiles, level):
    
    #------check if tiles are diagonal-------
    x1,y1 = tiles[0]
    x2,y2 = tiles[1]
    
    #yes diagonal! set up 2 'normal' tiles list and send them again to this method
    if x2 - x1 != 0 and y2 - y1 != 0:
        tilesx = []
        tilesy = []
        
        for i in xrange( len(tiles) -1):
            tilesx.append( tiles[i] )
            tilesy.append( tiles[i] )
        
            tilesx.append( (tiles[i+1][0], tiles[i][1]) )
            tilesy.append( (tiles[i][0], tiles[i+1][1]) )
        
        #append last tile
        tilesx.append( tiles[-1] )
        tilesy.append( tiles[-1] )
        
        visx = _getVision( tilesx, level )
        visy = _getVision( tilesy, level )
        
        res = visx + visy
        if res >= 3:
            return 2
        elif res < 3 and res > 0: 
            return 1
        elif res == 0:
            return 0
        
    #-----normal calculations----------
    vision = 2
    
    for i in xrange( len(tiles) -1):
        dx = tiles[i+1][0] - tiles[i][0]
        dy = tiles[i+1][1] - tiles[i][1]
        x,y = tiles[i]

        x1 = 2*x+2
        y1 = 2*y+1
        
        if dx > 0:
            #x1 = 2*x+2
            #y1 = 2*y+1
            pass
        elif dx < 0:
            x1 = 2*x
            y1 = 2*y+1
        elif dy > 0:
            x1 = 2*x+1
            y1 = 2*y+2
        elif dy < 0:
            x1 = 2*x+1
            y1 = 2*y
            
        #check if this is a half cover
        if level.gridVision( x1, y1 ) == 1:
            #we see over first half cover
            if i > 0:
                vision = 1
            continue
        
        #or maybe a half cube
        elif level.getHeight( (x, y) ) == 1:
            #we see over first half cube
            if i > 1:
                vision = 1
            continue
            
        #if it is not a half cover, than see if we can shoot through it
        elif level.gridBulletBlocked( x1, y1 ):
            #return ( 0, "Cannot shoot through " + level._grid[x1][y1].name + "." )
            return 0
    
    return vision
    


def checkGridVisibility( pos, lastpos, level):
    
    dx = pos[0] - lastpos[0]
    dy = pos[1] - lastpos[1]
    
    x = lastpos[0]
    y = lastpos[1]

    _2x = x*2
    _2y = y*2
  
  
    if dx == 1:
        if dy == 1:
            if level.gridVisionBlocked( _2x+2, _2y+1 ):
                if level.gridVisionBlocked( _2x+2, _2y+3 ):
                    return False
                if level.getHeight( (x, y+1) ) > 1:
                    return False
                
                
            if level.gridVisionBlocked( _2x+2, _2y+3 ):
                if level.getHeight( (x+1, y) ) > 1:
                    return False
                if level.gridVisionBlocked( _2x+3, _2y+2 ):
                    return False
            
            
            if level.gridVisionBlocked( _2x+1, _2y+2 ):
                if level.gridVisionBlocked( _2x+3, _2y+2 ):
                    return False
                if level.getHeight( (x+1, y) ) > 1:
                    return False
            
            if level.gridVisionBlocked( _2x+3, _2y+2 ) and level.getHeight( (x, y+1) ) > 1:
                    return False
                
                
        if dy == -1:
            if level.gridVisionBlocked( _2x+2, _2y+1 ):
                if level.gridVisionBlocked( _2x+2, _2y-1 ):
                    return False
                if level.getHeight( (x, y-1) ) > 1:
                    return False

                
            if level.gridVisionBlocked( _2x+2, _2y-1 ):
                if level.getHeight( (x+1, y) ) > 1:
                    return False
                if level.gridVisionBlocked( _2x+3, _2y ):
                    return False
                
                
            if level.gridVisionBlocked( _2x+1, _2y ):
                if level.gridVisionBlocked( _2x+3, _2y ):
                    return False
                if level.getHeight( (x+1, y) ) > 1:
                    return False

            if level.gridVisionBlocked( _2x+3, _2y ) and level.getHeight( (x, y-1) ) > 1:
                    return False


        if level.gridVisionBlocked( _2x+2, _2y+1 ):
            return False

        
    if dx == -1:
        if dy == 1:
            if level.gridVisionBlocked( _2x, _2y+1 ):
                if level.gridVisionBlocked( _2x, _2y+3 ):
                    return False
                if level.getHeight( (x, y+1) ) > 1:
                    return False
                
            if level.gridVisionBlocked( _2x, _2y+3 ):
                if level.getHeight( (x-1, y) ) > 1:
                    return False
                if level.gridVisionBlocked( _2x-1, _2y+2 ):
                    return False
                
                
            if level.gridVisionBlocked( _2x+1, _2y+2 ):
                if level.gridVisionBlocked( _2x-1, _2y+2 ):
                    return False
                if level.getHeight( (x-1, y) ) > 1:
                    return False

            if level.gridVisionBlocked( _2x-1, _2y+2 ) and level.getHeight( (x, y+1) ) > 1:
                return False



        if dy == -1:
            if level.gridVisionBlocked( _2x, _2y+1 ):
                if level.gridVisionBlocked( _2x, _2y-1 ):
                    return False
                if level.getHeight( (x, y-1) ) > 1:
                    return False

            
            if level.gridVisionBlocked( _2x, _2y-1 ):
                if level.getHeight( (x-1, y) ) > 1:
                    return False
                if level.gridVisionBlocked( _2x-1, _2y ):
                    return False
            
            
            if level.gridVisionBlocked( _2x+1, _2y ):
                if level.gridVisionBlocked( _2x-1, _2y ):
                    return False
                if level.getHeight( (x-1, y) ) > 1:
                    return False
             
            if level.gridVisionBlocked( _2x-1, _2y ) and level.getHeight( (x, y-1) ) > 1:
                return False 
             
             
        if level.gridVisionBlocked( _2x, _2y+1 ):
            return False

        
    if dy == 1:
        if level.gridVisionBlocked( _2x+1, _2y+2 ):
            return False

    if dy == -1:
        if level.gridVisionBlocked( _2x+1, _2y ):
            return False
    
    
    return True    
    

def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1


def distance( x1, y1, x2, y2 ):    
    return math.sqrt( math.pow( (x2-x1) , 2) +  math.pow( (y2-y1) , 2) )
    

def distanceTupple( t1, t2 ):    
    return math.sqrt( math.pow( (t2[0]-t1[0]) , 2) +  math.pow( (t2[1]-t1[1]) , 2) )
    





class Level:
        
    def __init__(self, name = None):        
        self.maxX = 0
        self.maxY = 0
        self.maxgridX = 0
        self.maxgridY = 0        
        self._level_data = []    
        self._dynamics = []
        self._grid = []
        self._walls = {}
        
        if name:
            self.load( name )        

        self.center = ( self.maxX / 2, self.maxY / 2 )


    def load(self, name):
        self.name = name
        self._level_data = []    
        line_count = 0
        lvl_file = open( name, "r")

        s = lvl_file.readline().split()
        self.maxX = int(s[0]) 
        self.maxY = int(s[1])

        #----------------------------------load cubes----------------------------------
        for line in lvl_file:
            s = line.split(";")
            s = s[0:self.maxX]
            self._level_data.append(s)
            if line_count == self.maxY-1:
                break
            line_count = line_count + 1
        
        
        #initialize grid
        self.maxgridX = 2 * self.maxX + 2
        self.maxgridY = 2 * self.maxY + 2
        
        self._grid = [[ None ] * (2*self.maxY+1) for i in xrange(2*self.maxX+1)] #@UnusedVariable
        
        
        #---------------------------------load walls----------------------------------
        self._walls = loadWalls()
        
        #---------------------------------load grid stuff------------------------------
        in_grid = False
        for line in lvl_file:
            line = line.strip()
            if not in_grid and line != 'GRID':
                continue         
            in_grid = True
            
            if line == 'GRID':
                continue
            if line == '/GRID':
                break
            
            s = line.split(',')        
            x = int(s[0])
            y = int(s[1])
            wall_type = self._walls[ s[2] ]
            
            #put wall in grid
            self._grid[ x ][ y ] = wall_type

            
            #TODO: krav: ovo maknut:put flag in all nodes touching this wall
            if x % 2 == 0:
                self._grid[ x ][ y + 1 ] = wall_type
                self._grid[ x ][ y - 1 ] = wall_type
            else:
                self._grid[ x + 1][ y ] = wall_type
                self._grid[ x - 1][ y ] = wall_type
                
                
        lvl_file.close()
        self._level_data.reverse()
        #self._grid.reverse()
        
        #convert entries in _level_data from string to integer AND change x-y order
        tmp = [[None] * self.maxY for i in xrange(self.maxX)]
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._level_data[j][i] = int( self._level_data[j][i] )
                tmp[i][j] = self._level_data[j][i]
        self._level_data = tmp 

        #we make this so its size is the same as level 
        self._dynamics = [[ None ] * self.maxY for i in xrange(self.maxX)] #@UnusedVariable

    def changeRowNumber(self, a):
        pass
    
    def changeColumnNumber(self, a):
        pass

    def increaseElement(self, x, y ):
        self._level_data[x][y] = self._level_data[x][y] + 1
        if self._level_data[x][y] > 5:
            self._level_data[x][y] = 5
                
    def decreaseElement(self, x, y ):
        self._level_data[x][y] = self._level_data[x][y] - 1
        if self._level_data[x][y] < 0:
            self._level_data[x][y] = 0

    def saveLevel(self):
        
        fajl = open( self.name, "w" )
        
        fajl.write( str(self.maxX) + " " + str(self.maxY) + "\n"  )
        
        import copy
        data = copy.deepcopy( self._level_data )
        
        for l in data:
            l.reverse()
        
        for y in xrange( self.maxY ):
            for x in xrange( self.maxX ):   
                fajl.write( str(data[x][y]) + ";" )
            fajl.write( "\n" )
            
        fajl.write("\n\n\nGRID\n")
        
        for x in xrange( self.maxX*2+1):
            for y in xrange( self.maxY*2+1):
                if x % 2 == 0 and y % 2 == 0:
                    continue
                if not self._grid[x][y]:
                    continue
        
                fajl.write( str(x) + ',' + str(y) + ',' + self._grid[x][y].name + '\n' )
        
        fajl.write("/GRID\n")
        
        
        
        fajl.close()
        
        print "saved OK"
        
        
        pass


    def outOfBounds( self, x, y ):
        if( x < 0 or y < 0 or x >= self.maxX or y >= self.maxY ):
            return True
        else: 
            return False


    def canUnitFitHere(self, unit):

        x, y = int(unit.pos[0]), int(unit.pos[1])

        #check to see if there is something in the way on level
        if self._level_data[x][y] != 0:
            print "This unit cannot be placed on non empty level tile", unit.name, x, y
            return False
        
        #check to see if the tile is already occupied
        if self._dynamics[x][y]:
            print "This tile already occupied, unit cannot deploy here", x, y, unit.type
            return False
            
        return True
    
        
    def putUnit(self, unit ):
        if self.canUnitFitHere(unit):
            self._dynamics[ int(unit.pos[0]) ][ int(unit.pos[1]) ] = ( DYNAMICS_UNIT, unit.id )
            return True
        
        return False
        
        
    def removeUnit(self, unit ):
        self._dynamics[ int(unit.pos[0]) ][ int(unit.pos[1]) ] = None

        
    def putUnitDict(self, unit ):
        self._dynamics[ int(unit['pos'][0]) ][ int(unit['pos'][1]) ] = ( DYNAMICS_UNIT, unit['id'] )
        
        
    def removeUnitDict(self, unit ):
        self._dynamics[ int(unit['pos'][0]) ][ int(unit['pos'][1]) ] = None
        
    
    def removeUnitId(self, unit_id):
        for i in xrange(0, self.maxX):
            for j in xrange(0, self.maxY):
                if self._dynamics[i][j] == ( DYNAMICS_UNIT, unit_id ):
                    self._dynamics[i][j] = None
                    return
                
    def getDynamic(self, x, y):
        return self._dynamics[int(x)][int(y)]


    def clearDynamics(self):
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._dynamics[i][j] = None

    
    def getHeight(self, pos ):
        return self._level_data[ int(pos[0]) ][ int(pos[1]) ]


    def getHeight2(self, x, y ):
        if x < 0 or y < 0 or x >= self.maxX or y >= self.maxY:
            return 0
        return self._level_data[ x ][ y ]


    def opaque(self, x, y, z):
        if self._level_data[ int(x) ][ int(y) ] <= z: 
            return False
        return True
    
    
    def gridMoveBlocked(self, x, y ):
        if self._grid[x][y]:
            return self._grid[x][y].blockMove

        return False
    
    
    def gridVisionBlocked(self, x, y ):
        if self._grid[x][y]:
            if self._grid[x][y].blockVision > 1:
                return True

        return False
    
    
    def gridVision(self, x, y ):
        if self._grid[x][y]:
            return self._grid[x][y].blockVision               

        return False
    
    
    def gridBulletBlocked(self, x, y ):
        if self._grid[x][y]:
            return self._grid[x][y].blockBullets

        return False
    
    
    def gridCanUse(self, x, y):
        if x < 0 or y < 0 or x > self.maxgridX or y > self.maxgridY:
            return False
        if self._grid[x][y] and self._grid[x][y].usesTo:
                return True
        return False
    
    
    def gridUse(self, x, y):
        if not self._grid[x][y] and not self._grid[x][y].usesTo:
            return False
        
        self._grid[x][y] = self._walls[ self._grid[x][y].usesTo ]

    
    
class Wall:
    
    def __init__(self):
        self.name = None
        self.blockMove = False
        self.blockVision = False
        self.blockBullets = False
        self.destroysTo = None  
        self.usesTo = None
    
    
#-------WALL LOADING---------

def loadWalls():
    #TODO: krav: a jebiga kako drugacije sad?
    try:
        xmldoc = minidom.parse('data/base/walls.xml')
    except:
        try:
            xmldoc = minidom.parse('./../server/data/base/walls.xml')
        except:
            raise Exception( "Wrong 'walls.xml' directory")
        
    
    walls = {}
    
    for p in xmldoc.getElementsByTagName( 'wall' ):                
        wpn = Wall()            
        wpn.name = p.attributes['name'].value
        wpn.blockMove = int( p.attributes['blockMove'].value )
        wpn.blockVision = int( p.attributes['blockVision'].value ) 
        wpn.blockBullets = int( p.attributes['blockBullets'].value ) 
        try:wpn.destroysTo = p.attributes['destroysTo'].value
        except:pass
        try:wpn.usesTo = p.attributes['usesTo'].value
        except: pass

        walls[wpn.name] = wpn

    xmldoc.unlink()
    
    
    #------------check usesTo and destroysTo from every wall-------
    for el in walls.itervalues():
        if el.usesTo:
            try:
                walls[el.usesTo]
            except:
                raise Exception( "Wrong usesTo in: ", el.name, " it is:", el.usesTo," but there is no such wall.")
    
        if el.destroysTo:
            try:
                walls[el.destroysTo]
            except:
                raise Exception( "Wrong destroysTo in: ", el.name, " it is:", el.destroysTo," but there is no such wall.")
    
    
    return walls


    