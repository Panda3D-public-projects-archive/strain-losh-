import random
import math
from unit import *



_PI = math.pi
_PI_2 = _PI / 2
_3_PI_2 = 3 * _PI / 2
_PI_4 = _PI / 4
_3_PI_4 = 3 * _PI / 4 
_5_PI_4 = 5 * _PI / 4
_2_PI = 2 * _PI
_PI_8 = _PI / 8
_3_PI_8 = 3 * _PI / 8
_5_PI_8 = 5 * _PI / 8
_7_PI_8 = 7 * _PI / 8



def getHeading( myPosition, lookAtPoint ):
    
    #trivial check if this is the same position, if it is, return none
    if myPosition == lookAtPoint:
        return HEADING_NONE
    
    angle = math.atan2( lookAtPoint[1] - myPosition[1] , lookAtPoint[0] - myPosition[0] )

    if angle < -_7_PI_8:
        return HEADING_W
    elif angle < -_5_PI_8:
        return HEADING_SW
    elif angle < -_3_PI_8:
        return HEADING_S
    elif angle < -_PI_8:
        return HEADING_SE
    elif angle < _PI_8:
        return HEADING_E
    elif angle < _3_PI_8:
        return HEADING_NE
    elif angle < _5_PI_8:
        return HEADING_N
    elif angle < _7_PI_8:
        return HEADING_NW
    
    return HEADING_W
    



class Weapon():
    
    def __init__(self):
    
        self.range = 24
        self.type = TYPE_RIFLE
    


TYPE_RIFLE = 1
RANGE = 24
BS = 4

def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1




def givePercent( weapon, distance, bs ):
    
    point_blank = (bs-1)
    if distance <= point_blank:
        return 100
    
    t = math.pi / (weapon.range-point_blank) 
    x = (distance-point_blank) * t - math.pi / 2

    sin = math.sin(-x)
    factor = bs * 7

    if sin > 0:
        res = math.sin(-x) * (70 - factor) 
    else:
        res = math.sin(-x) * (25 + factor ) 
    
    res = res + 30 + factor
    
    return res


def d( num, dice ):
    ret = 0
    for a in xrange( num ):
        ret += random.randint( 1, dice )
    return ret


def d100():
    return d(1,100)

random.random()


def percentList( bs, weapon = None ):
    a = []
    if not weapon: 
        wpn = Weapon()
    else:
        wpn = weapon
        
    for i in xrange( 1,25 ):
        a.append( (i, givePercent( wpn, i, bs ) ) )
        #print a[-1]
    
    return a

def distance( x1, y1, x2, y2 ):    
    return math.sqrt( math.pow( (x2-x1) , 2) +  math.pow( (y2-y1) , 2) )
    
    
