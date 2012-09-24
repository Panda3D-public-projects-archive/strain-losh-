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
     
    d = math.sqrt(  math.pow(dx, 2) + math.pow(dy, 2)  )
    
        
    alfa = math.atan( 0.5 / d )    
    mid = math.atan2( float(dy),dx )
    left = mid + alfa
    right = mid - alfa        
    orig_angle = left - right 
    

    angles = _goThroughTiles2(x1, y1, x2, y2, dx, dy, left, right, mid, level, unit_dict, vis_dict)
    if not angles:
        return 0 
    
    total_angles = 0
    for l, r in angles:
        total_angles += l - r 
         
    
    return total_angles / orig_angle



def levelVisibilityDict( unit_list, level ):
    
    vis_dict = {}
    
    for unit in unit_list:      
        smartSearch(unit, level, vis_dict)      
        
                    
    #fill dict with zeroes
    for x in xrange(level.maxX):
        for y in xrange(level.maxY):
            x_y = (x,y)        
            if x_y not in vis_dict:
                vis_dict[ x_y ] = 0

            
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
            
            if x_y in vis_dict:
                continue
            if x_y in unit_dict:
                continue
            
            if LOS2( unit['pos'], x_y, level, unit_dict, vis_dict ) > VISIBILITY_MIN:
                unit_dict[x_y] = 1
                vis_dict[x_y] = 1




def _goThroughTiles2( x1, y1, x2, y2, dx, dy, left, right, mid, level, unit_dict, vis_dict ):
    
    absX = math.fabs( dx );
    absY = math.fabs( dy );
    
    sgnX = signum( dx )
    sgnY = signum( dy )
    
    x = int( x1 )
    y = int( y1 )

    angles = [[left,right]]
    
    vis = 1
    
    if( absX > absY ):
        y_x = absY/absX            
        D = y_x -0.5

        for i in xrange( int( absX ) ): #@UnusedVariable

            if vis:
                _y_p_1 = y+1 
                if not level.outOfBounds( x, _y_p_1 ):
                    if not _checkAngles(angles, mid, x, _y_p_1, x-x1, _y_p_1-y1, level, dx, dy):
                        vis = 0
                        #return 0
                
                _y_1 = y-1
                if not level.outOfBounds( x, _y_1 ):
                    if not _checkAngles(angles, mid, x, _y_1, x-x1, _y_1-y1, level, dx, dy):
                        vis = 0
                        #return 0
            
            if( D > 0 ):
                y += sgnY
                D -= 1
                
            x += sgnX
            D += y_x

            if vis:
                if not _checkAngles(angles, mid, x, y, x-x1, y-y1, level, dx, dy):
                    vis = 0
                    #return 0
                else:
                    if dy == 0:
                        if i > 1:
                            vis_dict[ (x,y) ] = 1

                    
            if not vis:
                unit_dict[(x,y)] = 0

                

            
    #//(y0 >= x0)            
    else:
        x_y = absX/absY
        D = x_y -0.5;
        
        for i in xrange( int( absY ) ): #@UnusedVariable
            
            if vis:
                _x_p_1 = x+1
                if not level.outOfBounds( _x_p_1, y ):
                    if not _checkAngles(angles, mid, _x_p_1, y, _x_p_1-x1, y-y1, level, dx, dy):
                        vis = 0
                        #return 0
    
                _x_1 = x-1
                if not level.outOfBounds( _x_1, y ):
                    if not _checkAngles(angles, mid, _x_1, y, _x_1-x1, y-y1, level, dx, dy):
                        vis = 0
                        #return 0
                
            
            if( D > 0 ):
                x += sgnX
                D -= 1
            
            y += sgnY
            D += x_y
            
            if vis:
                if not _checkAngles(angles, mid, x, y, x-x1, y-y1, level, dx, dy):
                    vis = 0
                    #return 0
                else:
                    if dx == 0:
                        if i > 0:
                            vis_dict[ (x,y) ] = 1
                    
                    
                    
            if not vis:
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
        


