'''
Created on 22 Sep 2012

@author: krav
'''
import math




#-------MASK-----------------
MASK_UP_LEFT    = 0
MASK_UP_RIGHT   = 1
MASK_DOWN_LEFT  = 2
MASK_DOWN_RIGHT = 3
MASK_MAX        = 4
MASK_MIN        = 5 
MASK_MID        = 6
MASK_LEFT       = 7
MASK_RIGHT      = 8
MASK_ORIG_ANGLE = 9



VISIBILITY_MIN = 0.4


def signum( num ):
    if num < 0: 
        return -1
    else:
        return 1



def LOS(t1, t2, level):    
    x1,y1 = t1
    x2,y2 = t2
        
    dx = x2 - x1
    dy = y2 - y1
     
    if dx == 0 and dy == 0:
        return 1
     
    d = math.sqrt(  math.pow(dx, 2) + math.pow(dy, 2)  )
    
        
    alfa = math.atan( 0.5 / d )    
    mid = math.atan2( float(dy),dx )
    left = mid + alfa
    right = mid - alfa        
    orig_angle = left - right 
    

    angles = _goThroughTiles(x1, y1, x2, y2, dx, dy, left, right, mid, level)
    if not angles:
        return 0 
    
    total_angles = 0
    for l, r in angles:
        total_angles += l - r 
         
    
    return total_angles / orig_angle



def LOS2(t1, t2, level, unit_dict, vis_dict ):    
    x1,y1 = t1
    x2,y2 = t2
        
    dx = x2 - x1
    dy = y2 - y1    
     
    if dx == 0 and dy == 0:
        return 1
     
    mask = level.getMask( dx, dy )     
     
    angles = _goThroughTiles2(x1, y1, x2, y2, dx, dy, mask, level, unit_dict, vis_dict)
    if not angles:
        return 0 
    
    total_angles = 0
    for l, r in angles:
        total_angles += l - r 
         
    return total_angles / mask[MASK_ORIG_ANGLE]



def levelVisibilityDict3( unit_list, level ):

    
    left = level.getMask(1,0)[MASK_MAX]
    right = level.getMask(1,0)[MASK_MIN]
    
    if not unit_list:
        return []
    
    unit = unit_list[0]
    unit_x = unit['pos'][0]
    unit_y = unit['pos'][1]

    unit_dict = {}
    

    y = unit_y

    new_right = scanZeroLineX(unit_x, unit_y, level, unit_dict)    
    
    y_range_pos = level.maxY - unit_y

    
    for i in xrange( 1, y_range_pos ):
            
        if unit_x+i >= level.maxX:
            return unit_dict
        
        if new_right:
            new_right = scanLineX( unit_x, unit_y, i, i, left, new_right, level, unit_dict)
        else:
            new_right = scanLineX( unit_x, unit_y, i, i, left, right, level, unit_dict)
    
    
    return unit_dict



def scanLineX( unit_x, unit_y, dx, dy, left, right, level, unit_dict):
    
    #vis can be: 
    #    1 - we see 100% of this, 
    #    -1- we cannot see this tile and no other in this tile till the end of level
    #    0 - we dont know, we have to check 
    vis = 1
    
    right_for_next_line = 0
    
    unit_x_dx = unit_x + dx
    
    #check for end of level
    if unit_x_dx >= level.maxX:
        return right
    
    this_y = unit_y + dy
    
    sigY = signum(dy)
    
    maxi = MASK_MAX
    mini = MASK_MIN
        

    x1 = -1
    
    for x in xrange( unit_x_dx, level.maxX ):
        
        if (x,this_y) in unit_dict:
            continue
        
        if vis == -1:
            unit_dict[ (x,this_y) ] = -1
            continue

        #we hit a wall
        if level.opaque( x, this_y, 1 ):
            
            #if the line below is -1 we cant see anything from this line anymore, put vis = -1
            if unit_dict[ (x, this_y-sigY) ] == -1:
                unit_dict[ (x,this_y) ] = -1
                vis = -1
            #else put vis = 0
            else:
                unit_dict[ (x,this_y) ] = 0
                vis = 0
                
            #we will return this right for next line only if it is the first new right we found
            if not right_for_next_line:
                right_for_next_line = level.getMask(x-unit_x, dy)[maxi]
            else:
                #we know we found a cube already on this line so now we need to check this hole
                #check right angle, if it is already bigger then this, than skip it
                tmp_right = level.getMask(x-unit_x, dy)[maxi] 
                if tmp_right >= right:
                    scanHole(x1, this_y+1, x1-unit_x, dy+1, left, tmp_right, level, unit_dict)
                else:
                    scanHole(x1, this_y+1, x1-unit_x, dy+1, left, right, level, unit_dict)
                
            x1 = x
        
            left = level.getMask(x-unit_x, dy)[mini]
            
            #check line below for -1
            if left <= right:
                if unit_dict[ (x, this_y-sigY) ] == -1:
                    unit_dict[ (x,this_y) ] = -1
                    vis = -1
                else:
                    unit_dict[ (x,this_y) ] = 0
                    vis = 0
                
            continue
            
        
        #if tile down and left are visible, this is also visible if it is empty
        if x != unit_x_dx:
            if unit_dict[ (x-1,this_y) ] == 1 and unit_dict[ (x,this_y-sigY) ] == 1:
                unit_dict[ (x,this_y) ] = 1
                continue
    
        if left <= right:
            unit_dict[ (x,this_y) ] = 0
            continue
    
        #if all else fails do the percent check
        percent = calculatePercent( level.getMask(x-unit_x, dy), left, right )
        if not percent:
            if unit_dict[ (x, this_y-sigY) ] == -1:
                unit_dict[ (x,this_y) ] = -1
                vis = -1
            else:
                vis = 0 
        unit_dict[ (x,this_y) ] = percent
    
    
    
    #check for end of level
    if vis != -1:
        #if there was a hole
        if x1 != -1:
            scanHole(x1, this_y+1, x1-unit_x, dy+1, left, right, level, unit_dict)
    
    
    
    #if we found a new right return that one, if not return the one we got
    if not right_for_next_line:
        return right
    else:
        return right_for_next_line



def scanHole( x1, this_y, dx1, dy1, left, right, level, unit_dict ):
    
    if left <= right:
        return

    min_x = x1+1
    at_least_one_x = False

    old_right = right
        
    for y in xrange( this_y, level.maxY ):
        
        dy = dy1+(y-this_y)
        
        at_least_one_x = False
        
        new_x1 = -1
        new_left = None
        new_dx1 = None
        
        for x in xrange( x1+1, level.maxX ):
            
            if x < min_x:
                continue
            
            dx = dx1+(x-x1)
            
            if level.opaque( x, y, 1 ):
                unit_dict[ (x,y) ] = 0
                
                if new_x1 != -1:
                    scanHole( new_x1, y, new_dx1, dy, new_left, level.getMask( dx, dy )[MASK_MAX], level, unit_dict)
                    
                new_x1 = x
                new_left = level.getMask( dx, dy )[MASK_MIN]
                new_dx1 = dx
                
                right = level.getMask( dx, dy )[MASK_MAX]
                if left <= right:
                    return  
            
                continue
            
            perc = calculatePercent( level.getMask( dx, dy ), left, right )
            
            if perc:
                if not at_least_one_x:
                    min_x = x
                    at_least_one_x = True

                unit_dict[ (x,y) ] = perc
            else:
                if at_least_one_x:
                    if new_x1 != -1:
                        scanHole( new_x1, y, new_dx1, dy, new_left, old_right, level, unit_dict)
                        new_x1 = -1
                    break            
            
        #scan last hole between new_x1 and right
        if new_x1 != -1: 
            scanHole( new_x1, y, new_dx1, dy, new_left, old_right, level, unit_dict)
                
        #if we didnt find any visible tile on this y line, than stop checking
        if not at_least_one_x:
            return
            
            
            


def scanZeroLineX( unit_x, unit_y, level, unit_dict ):
    vis = 1
    
    left = 0
    
    #positive direction
    for x in xrange( unit_x+1, level.maxX ):
        
        if not vis:
            unit_dict[ (x,unit_y) ] = -1
            continue
        
        if level.opaque( x, unit_y, 1 ):
            unit_dict[ (x,unit_y) ] = -1
            vis = 0
            left = level.getMask( x-unit_x, 0 )[MASK_MAX]
        else:
            unit_dict[ (x,unit_y) ] = 1
            
            
    return left
            


def calculatePercent( mask, left, right ):

    if left <= mask[MASK_RIGHT] or right >= mask[MASK_LEFT]:
        return 0
    
    tmp_left = left
    tmp_right = right
    
    if left >= mask[MASK_LEFT]:
        if right <= mask[MASK_RIGHT]:
            return 1
        
        tmp_left = mask[MASK_LEFT]
        
    if right <= mask[MASK_RIGHT]:
        tmp_right = mask[MASK_RIGHT]
        
    return (tmp_left-tmp_right)/mask[MASK_ORIG_ANGLE]




def levelVisibilityDict( unit_list, level ):

    vis_dict = {}
    
    for unit in unit_list:      
        smartSearch(unit, level, vis_dict)      
        
    """
    #fill dict with zeroes
    for x in xrange(level.maxX):
        for y in xrange(level.maxY):
            x_y = (x,y)        
            if x_y not in vis_dict:
                vis_dict[ x_y ] = 0
    """
         
    return vis_dict            


def smartSearch( unit, level, vis_dict ):
    
    unit_dict = {}
    min_x = 0
    max_x = level.maxX
    step_x = 1
    
    min_y = 0
    max_y = level.maxY
    step_y = 1
    
    if unit['pos'][0] <= level.center[0]:
            min_x, max_x, step_x = max_x-1, min_x-1, -1 
    if unit['pos'][1] <= level.center[1]:
            min_y, max_y, step_y = max_y-1, min_y-1, -1
            

    for x in xrange(min_x, max_x, step_x):
        for y in xrange(min_y, max_y, step_y):
            
            x_y = (x,y)
            
            if x_y in unit_dict:
                continue
            if x_y in vis_dict:
                continue
            
            if LOS2( unit['pos'], x_y, level, unit_dict, vis_dict ) > VISIBILITY_MIN:
                unit_dict[x_y] = 1
                vis_dict[x_y] = 1




def _goThroughTiles2( x1, y1, x2, y2, dx, dy, mask, level, unit_dict, vis_dict ):
    
    absX = math.fabs( dx );
    absY = math.fabs( dy );
    
    sgnX = signum( dx )
    sgnY = signum( dy )
    
    x = int( x1 )
    y = int( y1 )

    angles = [ [mask[MASK_LEFT], mask[MASK_RIGHT]] ]
    
    mid = mask[MASK_MID]
    
    vis = 1
    
    if( absX > absY ):
        y_x = absY/absX            
        D = y_x -0.5

        _x_x1 = x - x1
        
        for i in xrange( int( absX ) ): #@UnusedVariable

            if vis:
                _y_p_1 = y+1 
                if not level.outOfBounds( x, _y_p_1 ):
                    if not _checkAngles(angles, mid, x, _y_p_1, _x_x1, _y_p_1-y1, level, dx, dy):
                        vis = 0
                        #return 0
                
                _y_1 = y-1
                if not level.outOfBounds( x, _y_1 ):
                    if not _checkAngles(angles, mid, x, _y_1, _x_x1, _y_1-y1, level, dx, dy):
                        vis = 0
                        #return 0
            
            if( D > 0 ):
                y += sgnY
                D -= 1
                
            x += sgnX
            D += y_x

            _x_x1 = x - x1
            
            if vis:
                if not _checkAngles(angles, mid, x, y, _x_x1, y-y1, level, dx, dy):
                    vis = 0
                    #return 0
                else:
                    if dy == 0:
                        if i > 1:
                            vis_dict[ (x,y) ] = 1

            if not vis:           
                if math.fabs( _x_x1 ) != math.fabs( y - y1 ):
                    unit_dict[(x,y)] = 0

            
    #//(y0 >= x0)            
    else:
        x_y = absX/absY
        D = x_y -0.5;
        
        _y_y1 = y - y1
        
        for i in xrange( int( absY ) ): #@UnusedVariable
            
            if vis:
                _x_p_1 = x+1
                if not level.outOfBounds( _x_p_1, y ):
                    if not _checkAngles(angles, mid, _x_p_1, y, _x_p_1-x1, _y_y1, level, dx, dy):
                        vis = 0
                        #return 0
    
                _x_1 = x-1
                if not level.outOfBounds( _x_1, y ):
                    if not _checkAngles(angles, mid, _x_1, y, _x_1-x1, _y_y1, level, dx, dy):
                        vis = 0
                        #return 0
                
            
            if( D > 0 ):
                x += sgnX
                D -= 1
            
            y += sgnY
            D += x_y
            
            _y_y1 = y - y1              
            
            if vis:
                if not _checkAngles(angles, mid, x, y, x-x1, _y_y1, level, dx, dy):
                    vis = 0
                    #return 0
                else:
                    if dx == 0:
                        if i > 0:
                            vis_dict[ (x,y) ] = 1
                    
            if not vis:
                if absX != absY: 
                    if math.fabs( x - x1 ) != math.fabs( _y_y1 ):
                        unit_dict[(x,y)] = 0
                else:
                    unit_dict[(x,y)] = 0

    #special case for last square
    if vis:
        if absX > absY:
            if absY != 0:
                _y_sgn = y-sgnY
                if not _checkAngles(angles, mid, x, _y_sgn, x-x1, _y_sgn-y1, level, dx, dy):
                    vis = 0
                    #return 0
        else:
            if absX != 0:
                _x_sgn = x-sgnX
                if not _checkAngles(angles, mid, _x_sgn, y, _x_sgn-x1, y-y1, level, dx, dy):
                    vis = 0
                    #return 0
                    
                    
    if not vis:
        unit_dict[ (x,y) ] = 0        
        
        
    return angles

    

def _goThroughTiles( x1, y1, x2, y2, dx, dy, left, right, mid, level ):
    
    absX = math.fabs( dx );
    absY = math.fabs( dy );
    
    sgnX = signum( dx )
    sgnY = signum( dy )
    
    x = int( x1 )
    y = int( y1 )

    angles = [[left,right]]
    
    if( absX > absY ):
        y_x = absY/absX            
        D = y_x -0.5

        for i in xrange( int( absX ) ): #@UnusedVariable

            _y_p_1 = y+1 
            if not level.outOfBounds( x, _y_p_1 ):
                if not _checkAngles(angles, mid, x, _y_p_1, x-x1, _y_p_1-y1, level, dx, dy):
                    return 0
            
            _y_1 = y-1
            if not level.outOfBounds( x, _y_1 ):
                if not _checkAngles(angles, mid, x, _y_1, x-x1, _y_1-y1, level, dx, dy):
                    return 0
            
            if( D > 0 ):
                y += sgnY
                D -= 1
                
            x += sgnX
            D += y_x

            if not _checkAngles(angles, mid, x, y, x-x1, y-y1, level, dx, dy):
                return 0

            
    #//(y0 >= x0)            
    else:
        x_y = absX/absY
        D = x_y -0.5;
        
        for i in xrange( int( absY ) ): #@UnusedVariable
            
            _x_p_1 = x+1
            if not level.outOfBounds( _x_p_1, y ):
                if not _checkAngles(angles, mid, _x_p_1, y, _x_p_1-x1, y-y1, level, dx, dy):
                    return 0

            _x_1 = x-1
            if not level.outOfBounds( _x_1, y ):
                if not _checkAngles(angles, mid, _x_1, y, _x_1-x1, y-y1, level, dx, dy):
                    return 0
                
            
            if( D > 0 ):
                x += sgnX
                D -= 1
            
            y += sgnY
            D += x_y
            
            if not _checkAngles(angles, mid, x, y, x-x1, y-y1, level, dx, dy):
                return 0
            

    #special case for last square
    if absX > absY:
        if absY != 0:
            _y_sgn = y-sgnY
            if not _checkAngles(angles, mid, x, _y_sgn, x-x1, _y_sgn-y1, level, dx, dy):
                return 0
    else:
        if absX != 0:
            _x_sgn = x-sgnX
            if not _checkAngles(angles, mid, _x_sgn, y, _x_sgn-x1, y-y1, level, dx, dy):
                return 0

    return angles

    

def _checkWallAngles( angles, mid, x, y, _x, _y, level, dx, dy ):
    _2x = x * 2
    _2y = y * 2
    mask = level.getMask( _x, _y )
    
    for lr in angles:
        #lr[0] = left
        #lr[1] = right        
        
        if dx > 0:
            #left wall
            if level.gridVisionBlocked( _2x, _2y+1 ):
                
                if _x > 0:
                    mini = mask[MASK_DOWN_LEFT]
                    maxi = mask[MASK_UP_LEFT]
                else:
                    mini = mask[MASK_UP_LEFT]
                    maxi = mask[MASK_DOWN_LEFT]
                    if _y == 0:
                        if mid > 0:
                            maxi = mask[MASK_DOWN_LEFT]+360
                        else:
                            mini = mask[MASK_UP_LEFT]-360
                            
                vis_angles_return = _modifyVisibleAngle(lr, mini, maxi, angles) 
                if not vis_angles_return:
                    return 0
                elif vis_angles_return == -1:
                    return -1
                    

        elif dx < 0:
            #right wall
            if level.gridVisionBlocked( _2x+2, _2y+1 ):
                
                if _x > 0:
                    mini = mask[MASK_DOWN_RIGHT]
                    maxi = mask[MASK_UP_RIGHT]
                else:
                    mini = mask[MASK_UP_RIGHT]
                    maxi = mask[MASK_DOWN_RIGHT]
                    if _y == 0:
                        if mid > 0:
                            maxi = mask[MASK_DOWN_RIGHT]+360
                        else:
                            mini = mask[MASK_UP_RIGHT]-360
                            
                vis_angles_return = _modifyVisibleAngle(lr, mini, maxi, angles) 
                if not vis_angles_return:
                    return 0
                elif vis_angles_return == -1:
                    return -1

        if dy > 0:
            #down wall
            if level.gridVisionBlocked( _2x+1, _2y ):
                
                mini = mask[MASK_DOWN_RIGHT]
                maxi = mask[MASK_DOWN_LEFT]
                            
                vis_angles_return = _modifyVisibleAngle(lr, mini, maxi, angles) 
                if not vis_angles_return:
                    return 0
                elif vis_angles_return == -1:
                    return -1

        elif dy < 0:
            #up wall
            if level.gridVisionBlocked( _2x+1, _2y+2 ):
                
                mini = mask[MASK_UP_LEFT]
                maxi = mask[MASK_UP_RIGHT]
                            
                vis_angles_return = _modifyVisibleAngle(lr, mini, maxi, angles) 
                if not vis_angles_return:
                    return 0
                elif vis_angles_return == -1:
                    return -1

    return 1


def _checkAngles( angles, mid, x, y, _x, _y, level, dx, dy ):
    
    mask = level.getMask( _x, _y )
    
    for lr in angles[:]:
        
        #if this square is not empty check angles for it
        if level.opaque( x, y, 1):
            
            if _x < 0 and _y == 0:
                if mid > 0:
                    mini = mask[MASK_UP_RIGHT]                    
                    maxi = mask[MASK_DOWN_RIGHT]+360
                else:
                    mini = mask[MASK_UP_RIGHT]-360
                    maxi = mask[MASK_DOWN_RIGHT]
            else:
                mini = mask[MASK_MIN]
                maxi = mask[MASK_MAX]

            if not _modifyVisibleAngle(lr, mini, maxi, angles):
                return 0                

        #check walls    
        walls_result = _checkWallAngles(angles, mid, x, y, _x, _y, level, dx, dy)     
        if walls_result == 0:
            return 0
        elif walls_result == -1:
            return _checkAngles(angles, mid, x, y, _x, _y, level, dx, dy)
   
                
    return 1
        
        
def _modifyVisibleAngle( lr, mini, maxi, angles ):
    
    left_bigger = False
    
    if lr[0] > mini: 
        if lr[0] <= maxi:
            lr[0] = mini
        else:
            left_bigger = True
            
    if lr[1] >= mini:
        if lr[1] < maxi:
            lr[1] = maxi
    else:
        if left_bigger:
            #----------------SPLIT-------------------
            old_right = lr[1]
            lr[1] = maxi
            angles.append( [mini, old_right] )
            return -1
            
        
    if lr[0] <= lr[1]:
        return 0    
        
    return 1
        


