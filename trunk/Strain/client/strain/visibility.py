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



def _LOS2(t1, t2, level, unit_dict, vis_dict ):    
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



def levelVisibilityDict( unit_list, level ):

    if not unit_list:
        return {}

    unit_dict_x = {}
    unit_dict_y = {}
    
    vis_dict = {}
    
    for unit in unit_list:
        unit_dict_x = _visibility3X(unit, level, vis_dict)
        unit_dict_y = _visibility3Y(unit, level, vis_dict)
    
        unit_x = unit['pos'][0]
        unit_y = unit['pos'][1]
    
        for x in xrange( level.maxX ):
            for y in xrange( level.maxY ):
            
                k = (x,y)
                dx = x - unit_x
                dy = y - unit_y
                
        
                if dx == dy or dx == -dy:            
                    if k in unit_dict_x:
                        if k in unit_dict_y:
                            #print "dic_x:", unit_dict_x[k], "dic_y", unit_dict_y[k]
                            unit_dict_x[ k ] += unit_dict_y[ k ]
                            if unit_dict_x[k] > VISIBILITY_MIN:  
                                vis_dict[k] = unit_dict_x[ k ]
                    else:
                        if k in unit_dict_y:
                            #unit_dict_x[ k ] = unit_dict_y[ k ]
                            if unit_dict_y[k] > VISIBILITY_MIN:  
                                vis_dict[k] = unit_dict_y[ k ]
                #else:
                #    unit_dict_x[ k ] = unit_dict_y[ k ]
                #    if unit_dict_x[k] > VISIBILITY_MIN:  
                #        vis_dict[k] = unit_dict_x[ k ]
                

        
    return vis_dict



def _visibility3Y( unit, level, vis_dict ):

    unit_x = unit['pos'][0]
    unit_y = unit['pos'][1]

    unit_dict = {}

    left_45 = level.getMask(0,1)[MASK_MAX]
    right_45 = level.getMask(0,1)[MASK_MIN]
    
    
    #----------------------------Y > 0-------------------------------- 
    if unit_y+1 < level.maxY and not level.opaque( unit_x, unit_y+1, 1 ):
        zero_line = _scanZeroLineY( unit_x, unit_y, level, unit_dict, vis_dict )
        
        left = zero_line[0]
        right = right_45
        x_range_pos = level.maxX - unit_x
           
        #check positive part, x+, y+
        for i in xrange( 1, x_range_pos ):
            if unit_y+i >= level.maxY:
                break
            
            left, right = _scanLineY( unit_x, unit_y, i, i, left, right, level, unit_dict, vis_dict )
            
            if left <= right:
                break
    
        left = left_45
        right = zero_line[1]
        
        #check negative part, x-, y+
        for i in xrange( -1, -unit_x-1, -1 ):
            if unit_y-i >= level.maxY:
                break
            
            left, right = _scanLineY( unit_x, unit_y, i, -i, left, right, level, unit_dict, vis_dict )

            if left <= right:
                break

    #----------------------------Y < 0-------------------------------- 
    if unit_y-1 >= 0 and not level.opaque( unit_x, unit_y-1, 1 ):
        zero_line = _scanZeroLineY( unit_x, unit_y, level, unit_dict, vis_dict, -1 )
        
        left = -right_45
        right = zero_line[1]
        
        x_range_pos = level.maxX - unit_x
           
        #check positive part, x+, y-
        for i in xrange( 1, x_range_pos ):
            if unit_y-i < 0:
                break

            left, right = _scanLineY( unit_x, unit_y, i, -i, left, right, level, unit_dict, vis_dict )
        
            if left <= right:
                break
            
        left = zero_line[0] 
        right = -left_45 
        
        #check negative part, x-, y-
        for i in xrange( -1, -unit_x-1, -1 ):
            if unit_y+i < 0:
                break
            
            left, right = _scanLineY( unit_x, unit_y, i, i, left, right, level, unit_dict, vis_dict )

            if left <= right:
                break

    return unit_dict


def _visibility3X( unit, level, vis_dict ):
    
    unit_x = unit['pos'][0]
    unit_y = unit['pos'][1]

    if unit_y == 8:
        pass

    unit_dict = {}
    
    if level.opaque( unit_x, unit_y, 1 ):
        return unit_dict
    else:        
        vis_dict[ unit_x, unit_y ] = 1
        
    #-------------------------- X > 0--------------------------
    #if x+1 is blocked, do not bother with vision checks, everything is blocked
    if unit_x+1 < level.maxX and not level.opaque( unit_x+1, unit_y, 1 ):
        
        left_45 = level.getMask(1,0)[MASK_MAX]
        right_45 = level.getMask(1,0)[MASK_MIN]
        zero_line = _scanZeroLineX( unit_x, unit_y, level, unit_dict, vis_dict )
    
        left = left_45
        right = zero_line
        
        y_range_pos = level.maxY - unit_y
    
        #check positive part, x+, y+
        for i in xrange( 1, y_range_pos ):
            if unit_x+i >= level.maxX:
                break
            
            left, right = _scanLineX( unit_x, unit_y, i, i, left, right, level, unit_dict, vis_dict )
    
            if left <= right:
                break    
    
        left = -zero_line
        right = right_45
        
        #check negative part, x+, y-
        for i in xrange( -1, -unit_y-1, -1 ):
            if unit_x-i >= level.maxX:
                break
            
            left, right = _scanLineX( unit_x, unit_y, -i, i, left, right, level, unit_dict, vis_dict )
            
            if left <= right:
                break
            
    #------------------------ X < 0----------------------------
    if unit_x -1 >= 0 and not level.opaque( unit_x-1, unit_y, 1 ):
        left_45 = level.getMask(-1,0)[MASK_DOWN_RIGHT]
        right_45 = level.getMask(-1,0)[MASK_UP_RIGHT]
    
        zero_line = _scanZeroLineX(unit_x, unit_y, level, unit_dict, vis_dict, -1)
        left = min( zero_line[1], math.pi )
        right = right_45
        
        y_range_pos = level.maxY - unit_y
        
        #check positive part, x-, y+
        for i in xrange( 1, y_range_pos ):
            if unit_x-i < 0:
                break
            
            left, right = _scanLineX( unit_x, unit_y, -i, i, left, right, level, unit_dict, vis_dict )
    
            if left <= right:
                break
                    
        left = left_45
        right = max( zero_line[0], -math.pi )
        
        #check negative part, x-, y-
        for i in xrange( -1, -unit_y-1, -1 ):
            if unit_x+i < 0:
                break
            
            left, right = _scanLineX( unit_x, unit_y, i, i, left, right, level, unit_dict, vis_dict )
    
            if left <= right:
                break
            
            
    return unit_dict



def _scanLineY( unit_x, unit_y, dx, dy, left, right, level, unit_dict, vis_dict ):   
    
    #check if this line is visible at all    
    if left <= right:
        return left, right
        
    unit_y_dy = unit_y + dy
    
    #check for end of level
    if unit_y_dy >= level.maxY or unit_y_dy < 0:
        return left, right
    
    #if vis is = -1 we cannot see this tile and no other tiles in this line till the end of level 
    vis = 1
    
    old_right = right
    old_left = left
    
    right_for_next_line = right
    left_for_next_line = left
        
    sgnX = signum(dx)
    sgnY = signum(dy)
    
    this_x = unit_x + dx
    
    #for remembering y pos of last cube we encountered
    y1 = -1
    
    if dy > 0:
        start = unit_y_dy
        stop = level.maxY
        step = 1
    else:
        start = unit_y_dy
        stop = -1
        step = -1
        
    
    for y in xrange( start, stop, step ):
        
        tile = (this_x, y)
        
        if vis == -1:
            unit_dict[ tile ] = -1
            continue

        if tile in unit_dict and not level.opaque( this_x, y, 1):
            continue
        
        """
        #dok su percentages onda se dijagonale kase medjusobno
        if tile in vis_dict:
            unit_dict[ tile ] = 1
            continue
        """
        
        #we hit a wall
        if level.opaque( this_x, y, 1 ):
            
            #dx > 0 !! if the line left is -1 we cant see anything from this line anymore, put vis = -1
            if unit_dict[ (this_x-sgnX, y) ] == -1:
                unit_dict[ tile ] = -1
                vis = -1
            else:
                unit_dict[ tile ] = 0
                
            tmp_mask = level.getMask( dx, y-unit_y )
            
            
            #dx > 0!! we will return this right for next line only if it is bigger than right_for_next_line
            if dx > 0:
                if dy > 0:
                    left_for_next_line = min( left_for_next_line, tmp_mask[MASK_MIN] )
                    if left < tmp_mask[MASK_MAX] and left >= tmp_mask[MASK_MIN]:
                        left = tmp_mask[MASK_MAX]
                    if right_for_next_line >= tmp_mask[MASK_MIN] and right_for_next_line < tmp_mask[MASK_MAX]:
                        right_for_next_line = tmp_mask[MASK_MAX]
                else:
                    right_for_next_line = max( right_for_next_line, tmp_mask[MASK_MAX] )
                    if right > tmp_mask[MASK_MIN] and right <= tmp_mask[MASK_MAX]:
                        right = tmp_mask[MASK_MIN]                    
                    if left_for_next_line <= tmp_mask[MASK_MAX] and left_for_next_line > tmp_mask[MASK_MIN]:
                        left_for_next_line = tmp_mask[MASK_MIN]
            else:
                if dy > 0:
                    right_for_next_line = max( right_for_next_line, tmp_mask[MASK_MAX] )
                    if right > tmp_mask[MASK_MIN] and right <= tmp_mask[MASK_MAX]:
                        right = tmp_mask[MASK_MIN]
                    if left_for_next_line <= tmp_mask[MASK_MAX] and left_for_next_line > tmp_mask[MASK_MIN]:
                        left_for_next_line = tmp_mask[MASK_MIN]
                else:
                    left_for_next_line = min( left_for_next_line, tmp_mask[MASK_MIN] )
                    if left < tmp_mask[MASK_MAX] and left >= tmp_mask[MASK_MIN]:
                        left = tmp_mask[MASK_MAX]
                    if right_for_next_line >= tmp_mask[MASK_MIN] and right_for_next_line < tmp_mask[MASK_MAX]:
                        right_for_next_line = tmp_mask[MASK_MAX]

                    
            #if we found a cube already on this line we need to check this hole
            if y1 != -1:
                if dx > 0:
                    if dy > 0:
                        tmp_left = min( level.getMask(dx, y-unit_y)[MASK_MIN], left )
                        tmp_right = right
                    else:
                        tmp_left = left 
                        tmp_right = max( level.getMask(dx, y-unit_y)[MASK_MAX], right )
                else:
                    if dy > 0:
                        tmp_left = left 
                        tmp_right = max( level.getMask(dx, y-unit_y)[MASK_MAX], right )
                    else:
                        tmp_left = min( level.getMask(dx, y-unit_y)[MASK_MIN], left )
                        tmp_right = right
                        
                _scanHoleY( this_x+sgnX, y1, dx+sgnX, y1-unit_y, tmp_left, tmp_right, level, unit_dict, vis_dict )
                
                    
                
            #remember this y for next hole checking
            y1 = y
        
            #dx > 0 !! set current angles
            if dx > 0:
                if dy > 0:
                    right = level.getMask(dx, y-unit_y)[MASK_MAX]
                else:
                    left = level.getMask(dx, y-unit_y)[MASK_MIN]
            else:
                if dy > 0:
                    left = level.getMask(dx, y-unit_y)[MASK_MIN]
                else:
                    right = level.getMask(dx, y-unit_y)[MASK_MAX]
                    
            
            #dx > 0 !! check line left for -1
            if left <= right:
                if unit_dict[ (this_x-sgnX, y) ] == -1:
                    unit_dict[ tile ] = -1
                    vis = -1
                else:
                    unit_dict[ tile ] = 0
                
            continue
            
        
        #dx > 0 !! if tile down and left are visible, this is also visible if it is empty (we already checked for that)
        if y != unit_y_dy:
            if unit_dict[ (this_x, y-sgnY) ] == 1:
                if unit_dict[ (this_x-sgnX, y) ] == 1:
                    unit_dict[ tile ] = 1
                    vis_dict[ tile ] = 1
                    continue

    
        #if all else fails do the percent check
        percent = _calculatePercent( level.getMask(dx, y-unit_y), left, right )
        if not percent:
            if unit_dict[ (this_x-sgnX, y) ] == -1:
                unit_dict[ tile ] = -1
                vis = -1
            else:
                unit_dict[ tile ] = 0
        else:
            unit_dict[ tile ] = percent
            
            if percent > VISIBILITY_MIN:
                vis_dict[ tile ] = percent
        
    
        
    #if there was a hole
    if y1 != -1:
        if dx > 0:
            if dy > 0:
                tmp_left = old_left
                tmp_right = right
            else:
                tmp_left = left
                tmp_right = old_right
        else:
            if dy > 0:
                tmp_left = left
                tmp_right = old_right
            else:
                tmp_left = old_left
                tmp_right = right
                
        _scanHoleY( this_x+sgnX, y1, dx+sgnX, y1-unit_y, tmp_left, tmp_right, level, unit_dict, vis_dict )                

    
    return left_for_next_line, right_for_next_line



def _scanHoleY( this_x, y1, dx1, dy1, left, right, level, unit_dict, vis_dict ):
    
    if left <= right:
        return

    if dy1 > 0:
        min_y = y1+1
    else: 
        min_y = y1-1
        
    at_least_one_y = False

    old_right = right
    old_left = left
        
    if dx1 > 0:
        start = this_x
        stop = level.maxX
        step = 1
    else:
        start = this_x
        stop = -1
        step = -1
        
        
    for x in xrange( start, stop, step ):
        
        dx = dx1+(x-this_x)
        
        at_least_one_y = False
        
        new_y1 = -1
        new_left = None
        new_right = None
        new_dy1 = None
        
        
        if dy1 > 0:
            start1 = min_y
            stop1 = level.maxY
            step1 = 1
        else:
            start1 = min_y
            stop1 = -1
            step1 = -1
        
        for y in xrange( start1, stop1, step1 ):
            
            tile = (x, y)
            
            if at_least_one_y and tile in vis_dict:
                continue
            
            dy = dy1+(y-y1)
            
            if level.opaque( x, y, 1 ):
                unit_dict[ tile ] = 0
                
                if new_y1 != -1:
                    if dx1 > 0:
                        if dy1 > 0:
                            tmp_left = level.getMask( dx, dy )[MASK_MIN]
                            tmp_right = new_right
                        else:
                            tmp_left = new_left
                            tmp_right = level.getMask( dx, dy )[MASK_MAX]
                    else:
                        if dy1 > 0:
                            tmp_left = new_left
                            tmp_right = level.getMask( dx, dy )[MASK_MAX]
                        else:
                            tmp_left = level.getMask( dx, dy )[MASK_MIN]
                            tmp_right = new_right
                            
                    _scanHoleY( x, new_y1, dx, new_dy1, tmp_left, tmp_right, level, unit_dict, vis_dict )
                        
                        
                #save values for next hole
                new_y1 = y
                new_dy1 = dy
                if dx1 > 0:
                    if dy1 > 0:
                        left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        new_right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                    else:
                        new_left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        right = max( right, level.getMask( dx, dy )[MASK_MAX] )                        
                else:
                    if dy1 > 0:
                        new_left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                    else:
                        left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        new_right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                    
                if left <= right:
                    break  
            
                continue
            
            perc = _calculatePercent( level.getMask( dx, dy ), left, right )
            
            if perc:
                if not at_least_one_y:
                    min_y = y
                    at_least_one_y = True

                unit_dict[ tile ] = perc
                
                if perc > VISIBILITY_MIN:
                    vis_dict[ tile ] = perc
                
            else:
                if at_least_one_y:
                    break            
            
        #scan last hole between new_x1 and right
        if new_y1 != -1: 
            if dx1 > 0:
                if dy1 > 0:
                    tmp_left = old_left
                    tmp_right = new_right
                else:
                    tmp_left = new_left
                    tmp_right = old_right                    
            else:
                if dy1 > 0:
                    tmp_left = new_left
                    tmp_right = old_right
                else:
                    tmp_left = old_left
                    tmp_right = new_right
                    
            _scanHoleY( x, new_y1, dx, new_dy1, tmp_left, tmp_right, level, unit_dict, vis_dict )
            old_left = left
            old_right = right
                
                
        #if we didnt find any visible tile on this y line, than stop checking
        if not at_least_one_y:
            return
            
            

def _scanLineX( unit_x, unit_y, dx, dy, left, right, level, unit_dict, vis_dict ):
    """
        if y > 0, max right angle is being carried over, and left is saved in the beggining and later used for hole
        angles.
        
        if y < 0, min left angle is being carried over, and right is saved and used for hole angles. 
    """
    
    if left <= right:
        return left, right
    
    unit_x_dx = unit_x + dx
    
    #check for end of level
    if unit_x_dx >= level.maxX or unit_x_dx < 0:
        return left, right
    
    #if vis is = -1 we cannot see this tile and no other tiles in this line till the end of level 
    vis = 1
    
    old_right = right
    old_left = left
    
    right_for_next_line = right
    left_for_next_line = left
        
    sgnY = signum(dy)
    sgnX = signum(dx)
    
    this_y = unit_y + dy
    
    #for remembering x pos of last cube we encountered
    x1 = -1

    if dx > 0:
        start = unit_x_dx
        stop = level.maxX
        step = 1
    else:
        start = unit_x_dx
        stop = -1
        step = -1

    
    for x in xrange( start, stop, step ):
        
        tile = (x, this_y)
        
        if vis == -1:
            unit_dict[ tile ] = -1
            continue

        if tile in unit_dict and not level.opaque( x, this_y, 1):
            continue
        
        """
        #dok su percentages onda se dijagonale kase medjusobno
        if tile in vis_dict:
            unit_dict[ tile ] = 1
            continue
        """
        
        #we hit a wall
        if level.opaque( x, this_y, 1 ):
            
            #dy > 0 !! if the line below is -1 we cant see anything from this line anymore, put vis = -1
            if unit_dict[ (x, this_y-sgnY) ] == -1:
                unit_dict[ tile ] = -1
                vis = -1
            else:
                unit_dict[ tile ] = 0
                
            tmp_mask = level.getMask(x-unit_x, dy)
            
            #dy > 0!! we will return this right for next line only if it is bigger than right_for_next_line
            if dy > 0:
                if dx > 0:
                    right_for_next_line = max( right_for_next_line, tmp_mask[MASK_MAX] )
                    if right >= tmp_mask[MASK_MIN] and right < tmp_mask[MASK_MAX]:
                        right = tmp_mask[MASK_MAX]
                    if left_for_next_line <= tmp_mask[MASK_MAX] and left_for_next_line > tmp_mask[MASK_MIN]:
                        left_for_next_line = tmp_mask[MASK_MIN]
                else:
                    left_for_next_line = min( left_for_next_line, tmp_mask[MASK_MIN] )
                    if left <= tmp_mask[MASK_MAX] and left > tmp_mask[MASK_MIN]:
                        left = tmp_mask[MASK_MIN]
                    if right_for_next_line >= tmp_mask[MASK_MIN] and right_for_next_line < tmp_mask[MASK_MAX]:
                        right_for_next_line = tmp_mask[MASK_MAX]
            else:
                if dx > 0:
                    left_for_next_line = min( left_for_next_line, tmp_mask[MASK_MIN] )
                    if left <= tmp_mask[MASK_MAX] and left > tmp_mask[MASK_MIN]:
                        left = tmp_mask[MASK_MIN]
                    if right_for_next_line >= tmp_mask[MASK_MIN] and right_for_next_line < tmp_mask[MASK_MAX]:
                        right_for_next_line = tmp_mask[MASK_MAX]
                else:
                    right_for_next_line = max( right_for_next_line, tmp_mask[MASK_MAX] )
                    if right >= tmp_mask[MASK_MIN] and right < tmp_mask[MASK_MAX]:
                        right = tmp_mask[MASK_MAX]
                    if left_for_next_line <= tmp_mask[MASK_MAX] and left_for_next_line > tmp_mask[MASK_MIN]:
                        left_for_next_line = tmp_mask[MASK_MIN]


                
            #if we found a cube already on this line we need to check this hole
            if x1 != -1:
                if dy > 0:
                    if dx > 0:
                        tmp_left = left
                        tmp_right = max( level.getMask(x-unit_x, dy)[MASK_MAX], right )
                    else:
                        tmp_left = min( level.getMask(x-unit_x, dy)[MASK_MIN], left )
                        tmp_right = right 
                else:
                    if dx > 0:
                        tmp_left = min( level.getMask(x-unit_x, dy)[MASK_MIN], left )
                        tmp_right = right
                    else:
                        tmp_left = left
                        tmp_right = max( level.getMask(x-unit_x, dy)[MASK_MAX], right )
                         
                _scanHoleX(x1, this_y+sgnY, x1-unit_x, dy+sgnY, tmp_left, tmp_right, level, unit_dict, vis_dict)
                    
                
            #remember this x for next hole checking
            x1 = x
        
            #dy > 0 !! set left to MIN
            if dy > 0:
                if dx > 0:
                    left = level.getMask(x-unit_x, dy)[MASK_MIN]
                else:
                    right = level.getMask(x-unit_x, dy)[MASK_MAX]
            else:
                if dx > 0:
                    right = level.getMask(x-unit_x, dy)[MASK_MAX]
                else:
                    left = level.getMask(x-unit_x, dy)[MASK_MIN]

            
            #dy > 0 !! check line below for -1
            if left <= right:
                if unit_dict[ (x, this_y-sgnY) ] == -1:
                    unit_dict[ tile ] = -1
                    vis = -1
                else:
                    unit_dict[ tile ] = 0
                
            continue
            
        
        #dy > 0 !! if tile down and left are visible, this is also visible if it is empty (we already checked for that)
        if x != unit_x_dx:
            if unit_dict[ (x-sgnX,this_y) ] == 1 and unit_dict[ (x,this_y-sgnY) ] == 1:
                unit_dict[ tile ] = 1
                vis_dict[ tile ] = 1
                continue

    
        #if all else fails do the percent check
        percent = _calculatePercent( level.getMask(x-unit_x, dy), left, right )
        if not percent:
            if unit_dict[ (x, this_y-sgnY) ] == -1:
                unit_dict[ tile ] = -1
                vis = -1
            else:
                unit_dict[ tile ] = 0
        else:
            unit_dict[ tile ] = percent
        
            if percent > VISIBILITY_MIN:
                vis_dict[ tile ] = percent
        
    
        
    #if there was a hole
    if x1 != -1:
        if dy > 0:
            if dx > 0:
                tmp_left = left
                tmp_right = old_right
            else:
                tmp_left = old_left
                tmp_right = right
        else:
            if dx > 0:
                tmp_left = old_left
                tmp_right = right
            else:
                tmp_left = left
                tmp_right = old_right
                
        _scanHoleX(x1, this_y+sgnY, x1-unit_x, dy+sgnY, tmp_left, tmp_right, level, unit_dict, vis_dict)                

    
    return left_for_next_line, right_for_next_line



def _scanHoleX( x1, this_y, dx1, dy1, left, right, level, unit_dict, vis_dict ):
    
    if left <= right:
        return

    if dx1 > 0:
        min_x = x1+1
    else:
        min_x = x1-1
        
    at_least_one_x = False

    old_right = right
    old_left = left
        
    if dy1 > 0:
        start = this_y
        stop = level.maxY
        step = 1
    else:
        start = this_y
        stop = -1
        step = -1
        
        
    for y in xrange( start, stop, step ):
        
        dy = dy1+(y-this_y)
        
        at_least_one_x = False
        
        new_x1 = -1
        new_left = None
        new_right = None
        new_dx1 = None
        
        if dx1 > 0:
            start1 = min_x
            stop1 = level.maxX
            step1 = 1
        else:
            start1 = min_x
            stop1 = -1
            step1 = -1
        
        
        for x in xrange( start1, stop1, step1 ):
            
            tile = (x,y)
            
            if at_least_one_x and tile in vis_dict:
                continue
            
            dx = dx1+(x-x1)
            
            if level.opaque( x, y, 1 ):
                unit_dict[ tile ] = 0
                
                if new_x1 != -1:
                    if dy1 > 0:
                        if dx1 > 0:
                            tmp_left = new_left
                            tmp_right = level.getMask( dx, dy )[MASK_MAX]
                        else:
                            tmp_left = level.getMask( dx, dy )[MASK_MIN]
                            tmp_right = new_right
                    else:
                        if dx1 > 0:
                            tmp_left = level.getMask( dx, dy )[MASK_MIN]
                            tmp_right = new_right
                        else:
                            tmp_left = new_left
                            tmp_right = level.getMask( dx, dy )[MASK_MAX]
                            
                    _scanHoleX( new_x1, y, new_dx1, dy, tmp_left, tmp_right, level, unit_dict, vis_dict )
                        
                        
                #save values for next hole                     
                new_x1 = x
                new_dx1 = dx
                if dy1 > 0:
                    if dx1 > 0:
                        new_left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                    else:
                        left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        new_right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                else:
                    if dx1 > 0:
                        left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        new_right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                    else:
                        new_left = min( left, level.getMask( dx, dy )[MASK_MIN] )
                        right = max( right, level.getMask( dx, dy )[MASK_MAX] )
                        

                if left <= right:
                    break  
            
                continue
            
            perc = _calculatePercent( level.getMask( dx, dy ), left, right )
            
            if perc:
                if not at_least_one_x:
                    min_x = x
                    at_least_one_x = True

                unit_dict[ tile ] = perc
                if perc > VISIBILITY_MIN:
                    vis_dict[ tile ] = perc
            else:
                if at_least_one_x:
                    break            
            
        #scan last hole between new_x1 and right
        if new_x1 != -1: 
            if dy1 > 0:
                if dx1 > 0:
                    tmp_left = new_left
                    tmp_right = old_right
                else:
                    tmp_left = old_left
                    tmp_right = new_right
            else:
                if dx1 > 0:
                    tmp_left = old_left
                    tmp_right = new_right
                else:
                    tmp_left = new_left
                    tmp_right = old_right
                    
                    
            _scanHoleX( new_x1, y, new_dx1, dy, tmp_left, tmp_right, level, unit_dict, vis_dict )
            old_left = left
            old_right = right
                
                
        #if we didnt find any visible tile on this y line, than stop checking
        if not at_least_one_x:
            return
            
            
            


def _scanZeroLineX( unit_x, unit_y, level, unit_dict, vis_dict, sgn = 1 ):
    vis = 1
    
    #default values if we dont find a blocking cube
    if sgn > 0:
        maxi = 0
    else: 
        maxi = -math.pi, math.pi
        
    if sgn > 0:
        start = unit_x+1
        stop = level.maxX
        step = 1
    else:
        start = unit_x-1
        stop = -1
        step = -1
        
    for x in xrange( start, stop, step ):
        
        tile = (x, unit_y)
        
        if not vis:
            unit_dict[ tile ] = -1
            continue
        
        if level.opaque( x, unit_y, 1 ):
            unit_dict[ tile ] = -1
            vis = 0
            if sgn > 0:
                maxi = level.getMask( x-unit_x, 0 )[MASK_MAX]
            else:
                maxi = level.getMask( x-unit_x, 0 )[MASK_DOWN_RIGHT], level.getMask( x-unit_x, 0 )[MASK_UP_RIGHT] 
        else:
            unit_dict[ tile ] = 1
            vis_dict[ tile ] = 1
            
            
    return maxi
            


def _scanZeroLineY( unit_x, unit_y, level, unit_dict, vis_dict, sgn = 1 ):
    vis = 1
    
    if sgn > 0:
        mini, maxi = math.pi/2, math.pi/2
    else:
        mini, maxi = -math.pi/2, -math.pi/2
        
    if sgn > 0:
        start = unit_y+1
        stop = level.maxY
        step = 1
    else:
        start = unit_y-1
        stop = -1
        step = -1
        
    for y in xrange( start, stop, step ):

        tile = (unit_x, y)

        if not vis:
            unit_dict[ tile ] = -1
            continue
        
        if level.opaque( unit_x, y, 1 ):
            unit_dict[ tile ] = -1
            vis = 0

            maxi = level.getMask( 0, y-unit_y )[MASK_MAX]
            mini = level.getMask( 0, y-unit_y )[MASK_MIN]
                
                
        else:
            unit_dict[ tile ] = 1
            vis_dict[ tile ] = 1
            
            
    return mini, maxi
            


def _calculatePercent( mask, left, right ):

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




def levelVisibilityDict4( unit_list, level ):

    vis_dict = {}
    
    for unit in unit_list:      
        _smartSearch(unit, level, vis_dict)      
        
    """
    #fill dict with zeroes
    for x in xrange(level.maxX):
        for y in xrange(level.maxY):
            x_y = (x,y)        
            if x_y not in vis_dict:
                vis_dict[ x_y ] = 0
    """
         
    return vis_dict            


def _smartSearch( unit, level, vis_dict ):
    
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
            
            percent = _LOS2( unit['pos'], x_y, level, unit_dict, vis_dict )
            if percent > VISIBILITY_MIN:
                unit_dict[x_y] = percent
                vis_dict[x_y] = percent




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
    tiles = (x,y)
    if tiles:
        pass
    for lr in angles[:]:
        if x == 2 or x == 6:
            pass
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
        


