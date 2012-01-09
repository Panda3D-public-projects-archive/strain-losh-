'''
Created on 19.12.2011.

@author: krav
'''
import math



COMMUNICATION_PROTOCOL = 0.1


LEVELS_ROOT = "./data/levels/"


DYNAMICS_EMPTY = 0
DYNAMICS_UNIT = 1


def levelVisibilityDict( unit_list, level ):
    
    vis_dict = {}
    
    tmp_target = { 'pos':(0,0), 'height':1 }
    
    for x in xrange(level.maxX):
        for y in xrange(level.maxY):
            
            vis_dict[(x,y)] = 0
            
            for unit in unit_list:
                tmp_target['pos'] = (x,y)
                if getLOSOnLevel( unit.__dict__, tmp_target, level):
                    vis_dict[(x,y)] = 1
                    break
            
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

  
    #check diagonal if it is clear
    if( dx != 0 and dy != 0 ):

        if level.getHeight( (ptx + dx, pty) ) or level.getHeight( (ptx, pty + dy) ):
            return False
            
        #no need to check for 'real variable here, if we are this close to enemy, we MUST know he is there                
        #check if there is a dynamic thing in the way and see if it is a unit, if it is friendly than ok
        stuff = level.getDynamic( ptx + dx, pty ) 
        if stuff and stuff[0] == DYNAMICS_UNIT:
            if( units[ stuff[1] ]['owner'] != unit['owner'] ):
                return False
                
        stuff = level.getDynamic( ptx, pty + dy ) 
        if stuff and stuff[0] == DYNAMICS_UNIT:
            if( units[ stuff[1] ]['owner'] != unit['owner'] ):
                return False
                
    return True

#TODO: krav: vidit jel treba bas units slat il semoze prek dynamicsa to pogeldat?
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
    """0-cant see, 1-partial, 2-full"""
    
    if beholder_dict['pos'] == target_dict['pos']:
        return 2
    
    b_pos = beholder_dict['pos'] + ( ( level.getHeight( beholder_dict['pos'] ) + beholder_dict['height'] -1 ) , )
    #print "print "beh:", beholder_dict['pos'], "\ttar:", target_dict['pos'] 
    seen = 0        
    
    #check if we see target_dict's head
    t1 = target_dict['pos'] + ( ( level.getHeight( target_dict['pos'] ) + target_dict['height'] -1 ) , )        
    if _getTiles3D( b_pos, t1, level ):
        seen += 1
    
    #check if we see target_dict's feet
    t2 = target_dict['pos'] + ( level.getHeight( target_dict['pos'] ) , )
    if _getTiles3D( b_pos, t2, level ):
        seen += 1

    return seen


def _getTiles3D( t1, t2, level ):

    #we see ourself
    if( t1 == t2 ):
        return [ t1 ]
    
    x1, y1, z1 = t1
    x2, y2, z2 = t2
    
    #if one of our end points is not empty space, return false
    if level.opaque( x1, y1, z1 ) or level.opaque( x2, y2, z2 ):
        return False
    
    absx0 = math.fabs(x2 - x1);
    absy0 = math.fabs(y2 - y1);
    absz0 = math.fabs(z2 - z1);
    
    dist = int( distance(x1, y1, x2, y2) )

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

    
    sgnz0 = signum(z2 - z1)
    z_d = absz0/dist
    
    if( absx0 > absy0 ):
        sgny0 = signum( y2 - y1 );
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
            if _testTile3D( (x, y, int(z)), (lastx, lasty, int(lastz)), level ):
                list_visible_tiles.append( (x, y, int(z)) )
            else:
                return False
                break
            
    #//(y0 >= x0)            
    else:
        sgnx0 = signum( x2 - x1 );
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
            if _testTile3D( (x, y, int(z)), (lastx, lasty, int(lastz)), level ):
                list_visible_tiles.append( (x, y, int(z)) )
            else:
                return False
                break

    if rev:
        list_visible_tiles.reverse()
    return list_visible_tiles

            
def _testTile3D( pos, lastpos, level ):
    
    #level bounds
    if( level.outOfBounds( pos[0], pos[1] ) ):
        return False
    if( level.outOfBounds( lastpos[0], lastpos[1] ) ):
        return False
    
    #if we can't see here
    if level.opaque( pos[0], pos[1], pos[2] ):
        return False
    
    #moved along x
    if pos[0] != lastpos[0]:
        #moved along y
        if pos[1] != lastpos[1]:
            
            #moved along z - diagonal x-y-z
            if pos[2] != lastpos[2]:
                    if( level.opaque( lastpos[0], lastpos[1], pos[2] ) and
                        level.opaque( lastpos[0], pos[1], lastpos[2] ) and
                        level.opaque( pos[0], lastpos[1], lastpos[2] ) ):                             
                            return False
                     
                    if ( level.opaque( lastpos[0], pos[1], lastpos[2] ) and
                          level.opaque( lastpos[0], pos[1], pos[2] ) and
                          level.opaque( pos[0], lastpos[1], lastpos[2] ) and
                          level.opaque( pos[0], lastpos[1], pos[2] ) ): 
                        return False
            
                    return True
            #diagonal x-y
            if ( level.opaque( pos[0], lastpos[1], pos[2] ) and
                 level.opaque( lastpos[0], pos[1], pos[2] ) ):  
                        return False
            else:
                return True

        #moved along z - diagonal x-z
        if pos[2] != lastpos[2]:
            if ( level.opaque( pos[0], pos[1], lastpos[2] ) and
                 level.opaque( lastpos[0], pos[1], pos[2] ) ):  
                        return False
            else:
                return True
                
    #moved along y 
    if pos[1] != lastpos[1]:
        #moved along z - diagonal y-z
        if pos[2] != lastpos[2]:
            if ( level.opaque( pos[0], pos[1], lastpos[2] ) and
                 level.opaque( pos[0], lastpos[1], pos[2] ) ):  
                        return False
            else:
                return True
    
    return True




def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1


def distance( x1, y1, x2, y2 ):    
    return math.sqrt( math.pow( (x2-x1) , 2) +  math.pow( (y2-y1) , 2) )
    





class Level:
        
    def __init__(self, name):        
        self.name = LEVELS_ROOT + name    
        self.maxX = 0
        self.maxY = 0
        self._level_data = []    
        self._dynamics = []
        
        self.load(self.name)        

        self.center = ( self.maxX / 2, self.maxY / 2 )


    def load(self, name):
        line_count = 0
        lvl_file = open( name, "r")
        for line in lvl_file:
            line_count = line_count + 1
            if line_count == 1:
                s = line.split()
                self.maxX = int(s[0]); self.maxY = int(s[1])
            else:
                s = line.split(";")
                s = s[0:self.maxX]
                self._level_data.append(s)
           
        lvl_file.close()
        self._level_data.reverse()
        
        #convert entries in _level_data from string to integer AND change x-y order
        tmp = [[None] * self.maxY for i in xrange(self.maxX)]
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._level_data[j][i] = int( self._level_data[j][i] )
                tmp[i][j] = self._level_data[j][i]
        self._level_data = tmp 

        #we make this so its size is the same as level 
        self._dynamics = [[ None ] * self.maxY for i in xrange(self.maxX)] #@UnusedVariable


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
        
                
    def getDynamic(self, x, y):
        return self._dynamics[int(x)][int(y)]


    def clearDynamics(self):
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._dynamics[i][j] = None

    
    def getHeight(self, pos ):
        return self._level_data[ int(pos[0]) ][ int(pos[1]) ]


    def opaque(self, x, y, z):
        if self._level_data[ int(x) ][ int(y) ] <= z: 
            return False
        return True
    
    
    