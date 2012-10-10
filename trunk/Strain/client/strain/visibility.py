'''
Created on 22 Sep 2012

@author: krav
'''
import math
from profilestats import profile



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
    
    if level.opaque( x1, y1, 1 ) or level.opaque( x2, y2, 1):
        return 0
        
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
    
    max_angles = 0
    for l, r in angles:
        max_angles = max( max_angles, l - r )
          
         
    
    return max_angles / orig_angle



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



def levelVisibilityDictPercent( unit_list, level ):

    if not unit_list:
        return {}

    unit_dict_x = {}
    unit_dict_y = {}
    
    vis_dict = {}
    
    for unit in unit_list:
        unit_dict_x = _visibility3XPercent(unit, level, vis_dict)
        unit_dict_y = _visibility3YPercent(unit, level, vis_dict)
    
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


def levelVisibilityDict( unit_list, level ):

    if not unit_list:
        return {}

    vis_dict = {}
    
    for unit in unit_list:
        _visibility3XPercent(unit, level, vis_dict)
        _visibility3YPercent(unit, level, vis_dict)
    
        
    return vis_dict




def _visibility3YPercent( unit, level, vis_dict ):

    unit_x = unit['pos'][0]
    unit_y = unit['pos'][1]

    unit_dict = {}
    
    left_45 = level.getMask(0,1)[MASK_MAX]
    right_45 = level.getMask(0,1)[MASK_MIN]
    
    #----------------------------Y > 0-------------------------------- 
    if unit_y+1 < level.maxY and not level.opaque( unit_x, unit_y+1, 1 ) and not level.gridVisionBlocked( 2*unit_x+1, 2*unit_y+2):
        zero_line = _scanZeroLineY( unit_x, unit_y, level, unit_dict, vis_dict )
        
        left = zero_line[0]
        right = right_45
        x_range_pos = level.maxX - unit_x
        
        covered_angles = []
        min_y = unit_y
        
        #check positive part, x+, y+
        for i in xrange( 1, x_range_pos ):
            if unit_y+i >= level.maxY:
                break
            
            left, right, min_y = _scanLineYPercent( unit_x, unit_y, i, i, left, right, covered_angles, min_y, level, unit_dict, vis_dict )
            
            if left <= right:
                break
    
        left = left_45
        right = zero_line[1]
        
        covered_angles = []
        min_y = unit_y
                        
        #check negative part, x-, y+
        for i in xrange( -1, -unit_x-1, -1 ):
            if unit_y-i >= level.maxY:
                break
            
            left, right, min_y = _scanLineYPercent( unit_x, unit_y, i, -i, left, right, covered_angles, min_y, level, unit_dict, vis_dict )

            if left <= right:
                break

    #----------------------------Y < 0-------------------------------- 
    if unit_y-1 >= 0 and not level.opaque( unit_x, unit_y-1, 1 ) and not level.gridVisionBlocked( 2*unit_x+1, 2*unit_y):
        zero_line = _scanZeroLineY( unit_x, unit_y, level, unit_dict, vis_dict, -1 )
        
        left = -right_45
        right = zero_line[1]
        
        x_range_pos = level.maxX - unit_x
        
        covered_angles = []
        min_y = unit_y
                           
        #check positive part, x+, y-
        for i in xrange( 1, x_range_pos ):
            if unit_y-i < 0:
                break

            left, right, min_y = _scanLineYPercent( unit_x, unit_y, i, -i, left, right, covered_angles, min_y, level, unit_dict, vis_dict )
        
            if left <= right:
                break
            
        left = zero_line[0] 
        right = -left_45
         
        covered_angles = []
        min_y = unit_y
                        
        #check negative part, x-, y-
        for i in xrange( -1, -unit_x-1, -1 ):
            if unit_y+i < 0:
                break
            
            left, right, min_y = _scanLineYPercent( unit_x, unit_y, i, i, left, right, covered_angles, min_y, level, unit_dict, vis_dict )

            if left <= right:
                break


    return unit_dict


def _visibility3XPercent( unit, level, vis_dict ):
    
    unit_x = unit['pos'][0]
    unit_y = unit['pos'][1]

    unit_dict = {}
    
    #check tile we are standing on
    if level.opaque( unit_x, unit_y, 1 ):
        return unit_dict
    else:        
        vis_dict[ unit_x, unit_y ] = 1
        
    #-------------------------- X > 0--------------------------
    #if x+1 is blocked, do not bother with vision checks, everything is blocked
    if unit_x+1 < level.maxX and not level.opaque( unit_x+1, unit_y, 1 ) and not level.gridVisionBlocked( 2*unit_x+2, 2*unit_y+1):
        
        left_45 = level.getMask(1,0)[MASK_MAX]
        right_45 = level.getMask(1,0)[MASK_MIN]
        zero_line = _scanZeroLineX( unit_x, unit_y, level, unit_dict, vis_dict )
    
        left = left_45
        right = zero_line
        
        y_range_pos = level.maxY - unit_y
    
        covered_angles = []
        min_x = unit_x
    
        #check positive part, x+, y+
        for i in xrange( 1, y_range_pos ):
            if unit_x+i >= level.maxX:
                break
            
            left, right, min_x = _scanLineXPercent( unit_x, unit_y, i, i, left, right, covered_angles, min_x, level, unit_dict, vis_dict )
    
            if left <= right:
                break    
    
    
        left = -zero_line
        right = right_45
        
        covered_angles = []
        min_x = unit_x
                
        #check negative part, x+, y-
        for i in xrange( -1, -unit_y-1, -1 ):
            if unit_x-i >= level.maxX:
                break
            
            left, right, min_x = _scanLineXPercent( unit_x, unit_y, -i, i, left, right, covered_angles, min_x, level, unit_dict, vis_dict )
            
            if left <= right:
                break
            
    #------------------------ X < 0----------------------------
    if unit_x -1 >= 0 and not level.opaque( unit_x-1, unit_y, 1 ) and not level.gridVisionBlocked( 2*unit_x, 2*unit_y+1):
        left_45 = level.getMask(-1,0)[MASK_DOWN_RIGHT]
        right_45 = level.getMask(-1,0)[MASK_UP_RIGHT]
    
        zero_line = _scanZeroLineX(unit_x, unit_y, level, unit_dict, vis_dict, -1)
        left = min( zero_line[1], math.pi )
        right = right_45
        
        y_range_pos = level.maxY - unit_y
        
        covered_angles = []
        min_x = unit_x
                
        #check positive part, x-, y+
        for i in xrange( 1, y_range_pos ):
            if unit_x-i < 0:
                break
            
            left, right, min_x = _scanLineXPercent( unit_x, unit_y, -i, i, left, right, covered_angles, min_x, level, unit_dict, vis_dict )
    
            if left <= right:
                break
                    
        left = left_45
        right = max( zero_line[0], -math.pi )
        
        covered_angles = []
        min_x = unit_x
                
        #check negative part, x-, y-
        for i in xrange( -1, -unit_y-1, -1 ):
            if unit_x+i < 0:
                break
            
            left, right, min_x = _scanLineXPercent( unit_x, unit_y, i, i, left, right, covered_angles, min_x, level, unit_dict, vis_dict )
    
            if left <= right:
                break

            
    return unit_dict



def _scanLineYPercent( unit_x, unit_y, dx, dy, left, right, covered_angles, min_y, level, unit_dict, vis_dict ):   
    
    #check if this line is visible at all    
    if left <= right:
        return left, right, min_y
        
    unit_y_dy = unit_y + dy
    
    #check for end of level
    if unit_y_dy >= level.maxY or unit_y_dy < 0:
        return left, right, min_y
    
    #if vis is = -1 we cannot see this tile and no other tiles in this line till the end of level 
    vis = 1
    
    sgnX = signum(dx)
    sgnY = signum(dy)
    
    this_x = unit_x + dx
    
    if dy > 0:
        start = unit_y_dy
        stop = level.maxY
        step = 1
    else:
        start = unit_y_dy
        stop = -1
        step = -1
        
    at_least_one = False
    
    for y in xrange( start, stop, step ):
        
        tile = (this_x, y)
        
        if dy > 0:
            if y < min_y:
                unit_dict[ tile ] = 0
                continue
        else:
            if y > min_y:
                unit_dict[ tile ] = 0
                continue
        
        if vis == -1:
            unit_dict[ tile ] = -1
            continue

        blocked = 0
        """
        #dok su percentages onda se dijagonale kase medjusobno
        if tile in vis_dict:
            unit_dict[ tile ] = 1
            continue
        """
        tmp_mask = level.getMask( dx, y-unit_y )
        
        #------------------cube-------------------
        if level.opaque( this_x, y, 1 ):
            
            maxi = tmp_mask[MASK_MAX]
            mini = tmp_mask[MASK_MIN]
            
            blocked = 2
            
        #----------------perpen wall----------------------
        elif level.gridVisionBlocked( 2*this_x+1, 2*y+1-sgnY ):
            
            if sgnY == sgnX:
                mini = tmp_mask[MASK_MIN]
            else:
                maxi = tmp_mask[MASK_MAX]
                
            #--------both walls--------------------            
            if level.gridVisionBlocked( 2*this_x+1-sgnX, 2*y+1 ):
                if sgnY == sgnX:
                    maxi = tmp_mask[MASK_MAX]
                else:
                    mini = tmp_mask[MASK_MIN]
                blocked = 2
            #-------just perpen-----------------
            else:
                if sgnY == sgnX:
                    if sgnY > 0:
                        maxi = tmp_mask[MASK_DOWN_LEFT]
                    else:
                        maxi = tmp_mask[MASK_UP_RIGHT]
                else:
                    if sgnY > 0:
                        mini = tmp_mask[MASK_DOWN_RIGHT]
                    else:
                        mini = tmp_mask[MASK_UP_LEFT]
                blocked = 1
            
        #---------parallel wall----------------------------
        elif level.gridVisionBlocked( 2*this_x+1-sgnX, 2*y+1 ):
            
            if sgnY == sgnX:
                maxi = tmp_mask[MASK_MAX]
                if sgnY > 0:
                    mini = tmp_mask[MASK_DOWN_LEFT]
                else:
                    mini = tmp_mask[MASK_UP_RIGHT]
            else:
                mini = tmp_mask[MASK_MIN]
                if sgnY > 0:
                    maxi = tmp_mask[MASK_DOWN_RIGHT]
                else:
                    maxi = tmp_mask[MASK_UP_LEFT]
                    
            blocked = 1
            
        #----------------------blocked-------------------
        if blocked:    
                
            left, right = _processNewAngle(maxi, mini, left, right, covered_angles)
            
            #dx > 0 !! check line left for -1
            if left <= right:
                return left, right, min_y
            
            if blocked == 2:
                #dx > 0 !! if the line left is -1 we cant see anything from this line anymore, put vis = -1
                if unit_dict[ (this_x-sgnX, y) ] == -1:
                    unit_dict[ tile ] = -1
                    vis = -1
                else:
                    unit_dict[ tile ] = 0
                
                continue
        
        #-----------not blocked-------------------
        else:
            #do not check this is there was a block of any sorts
            #dx > 0 !! if tile down and left are visible, this is also visible if it is empty (we already checked for that)
            if y != unit_y_dy:
                if unit_dict[ (this_x, y-sgnY) ] == 1:
                    if unit_dict[ (this_x-sgnX, y) ] == 1:
                        unit_dict[ tile ] = 1
                        vis_dict[ tile ] = 1
                        continue

    
        #if all else fails do the percent check
        percent = _calculatePercent( tmp_mask, left, right, covered_angles )

        if not percent:
            if unit_dict[ (this_x-sgnX, y) ] == -1:
                unit_dict[ tile ] = -1
                vis = -1
            else:
                unit_dict[ tile ] = 0
        else:
            #lines must put something regardles of visibility
            if not at_least_one:
                min_y = y
                at_least_one = True
            unit_dict[ tile ] = percent
            if percent > VISIBILITY_MIN:
                vis_dict[ tile ] = percent
        
        
    if not at_least_one:
        return left, left, 0

     
    return left, right, min_y



def _scanLineXPercent( unit_x, unit_y, dx, dy, left, right, covered_angles, min_x, level, unit_dict, vis_dict ):
    
    if left <= right:
        return left, right, min_x
    
    unit_x_dx = unit_x + dx
    
    """
    #check for end of level
    if unit_x_dx >= level.maxX or unit_x_dx < 0:
        return left, right, min_x
    """
    
    #if vis is = -1 we cannot see this tile and no other tiles in this line till the end of level 
    vis = 1
    
    sgnY = signum(dy)
    sgnX = signum(dx)
    
    this_y = unit_y + dy
    
    if dx > 0:
        start = unit_x_dx
        stop = level.maxX
        step = 1
    else:
        start = unit_x_dx
        stop = -1
        step = -1
    
    at_least_one = False
    
    for x in xrange( start, stop, step ):
                
        tile = (x, this_y)
        
        if dx > 0:
            if x < min_x:
                unit_dict[ tile ] = 0
                continue
        else:
            if x > min_x:
                unit_dict[ tile ] = 0
                continue
            
        
        if vis == -1:
            unit_dict[ tile ] = -1
            continue

        blocked = 0
        """
        #dok su percentages onda se dijagonale kase medjusobno
        if tile in vis_dict:
            unit_dict[ tile ] = 1
            continue
        """
        tmp_mask = level.getMask(x-unit_x, dy)
        
        #---------------cube-------------------
        if level.opaque( x, this_y, 1 ):
            
            maxi = tmp_mask[MASK_MAX]
            mini = tmp_mask[MASK_MIN]

            blocked = 2

        #------------perpen wall-----------------
        elif level.gridVisionBlocked( 2*x+1-sgnX, 2*this_y+1 ):
                        
            if sgnY == sgnX:
                maxi = tmp_mask[MASK_MAX]
            else:
                mini = tmp_mask[MASK_MIN]

            #----------both walls---------------                
            if level.gridVisionBlocked( 2*x+1, 2*this_y+1-sgnY ):
                if sgnY == sgnX:
                    mini = tmp_mask[MASK_MIN]
                else:
                    maxi = tmp_mask[MASK_MAX]
                blocked = 2
            #-------just perpend-----------
            else:
                if sgnY == sgnX:
                    if sgnX > 0:
                        mini = tmp_mask[MASK_DOWN_LEFT]
                    else:
                        mini = tmp_mask[MASK_UP_RIGHT]
                else:
                    if sgnX > 0:
                        maxi = tmp_mask[MASK_UP_LEFT]
                    else:
                        maxi = tmp_mask[MASK_DOWN_RIGHT]
                blocked = 1


        #------------parallel wall-----------------------
        elif level.gridVisionBlocked( 2*x+1, 2*this_y+1-sgnY ):
                        
            if sgnY == sgnX:
                mini = tmp_mask[MASK_MIN]
                if sgnX > 0:
                    maxi = tmp_mask[MASK_DOWN_LEFT]
                else:
                    maxi = tmp_mask[MASK_UP_RIGHT]
            else:
                maxi = tmp_mask[MASK_MAX]
                if sgnX > 0:
                    mini = tmp_mask[MASK_UP_LEFT]
                else:
                    mini = tmp_mask[MASK_DOWN_RIGHT]

            blocked = 1

        #-----------------------blocked---------------------
        if blocked:

            left, right = _processNewAngle(maxi, mini, left, right, covered_angles)
                    
            if left <= right:
                return left, right, min_x

            if blocked == 2:
                #dy > 0 !! if the line below is -1 we cant see anything from this line anymore, put vis = -1
                if unit_dict[ (x, this_y-sgnY) ] == -1:
                    unit_dict[ tile ] = -1
                    vis = -1
                else:
                    unit_dict[ tile ] = 0

                continue
        #---------------------not blocked------------------
        else:
            #dy > 0 !! if tile down and left are visible, this is also visible if it is empty (we already checked for that)
            if x != unit_x_dx:
                if unit_dict[ (x-sgnX,this_y) ] == 1:
                    if unit_dict[ (x,this_y-sgnY) ] == 1:
                        unit_dict[ tile ] = 1
                        vis_dict[ tile ] = 1
                        continue

    
        #if all else fails do the percent check
        percent = _calculatePercent( tmp_mask, left, right, covered_angles )

        if not percent:
            if unit_dict[ (x, this_y-sgnY) ] == -1:
                unit_dict[ tile ] = -1
                vis = -1
            else:
                unit_dict[ tile ] = 0
        else:
            #must put something regardless of visibility
            if not at_least_one:
                min_x = x
                at_least_one = True
            unit_dict[ tile ] = percent
            if percent > VISIBILITY_MIN:
                vis_dict[ tile ] = percent
    
        
    if not at_least_one:
        return left, left, 0
        
    return left, right, min_x


def _processNewAngle( maxi, mini, left, right, covered_angles ):
    
    ret = False
    
    #check if we need to modify left/right
    if left <= maxi and left > mini:
        left = mini
        ret = True
    if right >= mini and right < maxi:
        right = maxi
        ret = True

    if ret:
        return left, right
    
    #if this angle is out of our visible angle
    if mini >= left or maxi <= right:
        return left, right
    
    #here we remember angle we modified so we can check all others only against that one
    current = [maxi, mini]
    
    while( True ):

        new_current = False
    
        #check if this angle is already covered by some other angle   
        for angles in covered_angles:
            
            if angles[0] >= current[0]:
                
                #completely covered by another angle, just return
                if angles[1] <= current[1]:
                    return left, right
    
                #this is angle between 0-1, need to expand it to right 
                elif angles[1] <= current[0]:
                    angles[1] = current[1]
                    current = angles
                    new_current = True
                    break
                
            elif angles[1] <= current[1]:
                #0 is < maxi, we chaecked that
                #so this means this angle is between 0-1, we need to expand left
                if angles[0] >= current[1]:
                    angles[0] = current[0]
                    current = angles
                    new_current = True
                    break
    
        if new_current:
            covered_angles.remove( current )
        else:
            covered_angles.append( current )
            break
            
            
    
    return left, right


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

        if level.opaque( x, unit_y, 1 ) or level.gridVisionBlocked( 2*x-sgn+1, 2*unit_y+1):
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
        
        if level.opaque( unit_x, y, 1 ) or level.gridVisionBlocked( 2*unit_x+1, 2*y+1-sgn):
            unit_dict[ tile ] = -1
            vis = 0

            maxi = level.getMask( 0, y-unit_y )[MASK_MAX]
            mini = level.getMask( 0, y-unit_y )[MASK_MIN]
                
                
        else:
            unit_dict[ tile ] = 1
            vis_dict[ tile ] = 1
            
            
    return mini, maxi
            


def _calculatePercent( mask, left, right, covered_angles ):

    if left <= mask[MASK_RIGHT] or right >= mask[MASK_LEFT]:
        return 0
    
    
    vis_left = min( mask[MASK_LEFT], left )
    vis_right = max( mask[MASK_RIGHT], right )


    for angles in covered_angles:
        #left is bigger
        if angles[0] >= vis_left:
            
            #both angles covered, this is completely blocked, we can stop search
            if angles[1] <= vis_right:
                vis_left = vis_right
                break
            
            #both are bigger, no angle covered, this doesnt cover anything maybe some other will block it, continue
            if angles[1] >= vis_left:
                continue
            
            #some covered, set visible angle and max_vs
            vis_left = angles[1]
            
        
        #right is smaller
        elif angles[1] <= vis_right:
            #we know already left is not bigger
            
            #if both are smaller this doesnt block, just continue
            if angles[0] <= vis_right:
                continue
    
            #some cover, set visible_left and calculate max
            vis_right = angles[0]
    
        #-----split------
        else: 
        
            a = vis_left - angles[0]
            b = angles[1] - vis_right
        
        
            if a > b:
                vis_right = angles[0]
            else:
                vis_left = angles[1]
                    
        
    return (vis_left - vis_right)/mask[MASK_ORIG_ANGLE]




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
    
    visibility_blocked = 0
    orig_len = len( angles )
    
    for lr in angles[:]:
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
                if vis_angles_return == 0:
                    visibility_blocked += 1
                elif vis_angles_return == -1:
                    return _checkWallAngles(angles, mid, x, y, _x, _y, level, dx, dy)
                    

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
                if vis_angles_return == 0:
                    visibility_blocked += 1
                elif vis_angles_return == -1:
                    return _checkWallAngles(angles, mid, x, y, _x, _y, level, dx, dy)

        if dy > 0:
            #down wall
            if level.gridVisionBlocked( _2x+1, _2y ):
                
                mini = mask[MASK_DOWN_RIGHT]
                maxi = mask[MASK_DOWN_LEFT]
                            
                vis_angles_return = _modifyVisibleAngle(lr, mini, maxi, angles) 
                if vis_angles_return == 0:
                    visibility_blocked += 1
                elif vis_angles_return == -1:
                    return _checkWallAngles(angles, mid, x, y, _x, _y, level, dx, dy)

        elif dy < 0:
            #up wall
            if level.gridVisionBlocked( _2x+1, _2y+2 ):
                
                mini = mask[MASK_UP_LEFT]
                maxi = mask[MASK_UP_RIGHT]
                            
                vis_angles_return = _modifyVisibleAngle(lr, mini, maxi, angles) 
                if vis_angles_return == 0:
                    visibility_blocked += 1
                elif vis_angles_return == -1:
                    return _checkWallAngles(angles, mid, x, y, _x, _y, level, dx, dy)

    for lr in angles[:]:
        if lr[0] <= lr[1]:
            angles.remove( lr )


    if visibility_blocked < orig_len:
        return 1
    else:
        return 0


def _checkAngles( angles, mid, x, y, _x, _y, level, dx, dy ):
    """
    Return 0 if there is no visibility.
    """
    
    mask = level.getMask( _x, _y )
    visibility_blocked = 0
    orig_len = len( angles )
    
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

            ret = _modifyVisibleAngle(lr, mini, maxi, angles)
            if ret == 0:
                visibility_blocked += 1
            elif ret == -1:
                return _checkAngles(angles, mid, x, y, _x, _y, level, dx, dy)                

        #check walls    
        walls_result = _checkWallAngles(angles, mid, x, y, _x, _y, level, dx, dy)     
        if walls_result == -1:
            return _checkAngles(angles, mid, x, y, _x, _y, level, dx, dy)  
        elif walls_result == 0:
            visibility_blocked += 1 
   
    for lr in angles[:]:
        if lr[0] <= lr[1]:
            angles.remove( lr )
   
    if visibility_blocked < orig_len:
        return 1
    else:
        return 0
        
        
def _modifyVisibleAngle( lr, mini, maxi, angles ):
    """
    Returns 0 if vision is blocked.
    1 if vision is not blocked.
    -1 if there was a split in angles. 
    """
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
            #this is for mathematical los, if u see 25% on both sides, u see 50% of the tile
            old_right = lr[1]
            lr[1] = maxi
            angles.append( [mini, old_right] )
            return -1
            
        
    if lr[0] <= lr[1]:
        return 0    
        
    return 1
        


