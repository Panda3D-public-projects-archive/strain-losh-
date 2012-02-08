import random
import math
import unit
import logging.handlers
import cPickle as pickle
import datetime
import os


OBSERVER_ID = -666

random.random()

_PI = math.pi
_PI_2 = _PI / 2
_3_PI_2 = 3 * _PI / 2
_PI_4 = _PI / 4
_3_PI_4 = 3 * _PI / 4 
_5_PI_4 = 5 * _PI / 4
_7_PI_4 = 7 * _PI / 4
_2_PI = 2 * _PI
_PI_8 = _PI / 8
_3_PI_8 = 3 * _PI / 8
_5_PI_8 = 5 * _PI / 8
_7_PI_8 = 7 * _PI / 8



class Notify():
    
    def __init__(self):
        self.logger = logging.getLogger('EngineLog')
        self.hdlr = logging.handlers.RotatingFileHandler('Engine.log', maxBytes = 1024*1024*3 )
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdlr.setFormatter(self.formatter)
        if len( self.logger.handlers ) < 1:
            self.logger.addHandler( self.hdlr )
        self.logger.setLevel(logging.DEBUG)

    def critical(self,msg, *args):
        self.error(msg, *args)
                
    def debug(self, msg,*args ):
        self.error(msg,*args)
        
    def info(self, msg,*args ):
        self.error(msg,*args)
            
    def error(self, msg,*args ):
        self.logger.critical(msg, *args)
        #print msg%args
    


def compileNewTurn(engine, player):
    dic = compileState(engine, player)
    del dic['level']
    return dic


def compileState(engine, player):        
    dic = {}
    units = {}

    #compile all my units
    for unt in player.units:
        units[unt.id] = compileUnit(unt)

    for unt in player.visible_enemies:
        units[unt.id] = compileEnemyUnit(unt)
    for unt in player.detected_enemies:
        units[unt.id] = compileDetectedEnemyUnit(unt)
    
        
    dic[ 'units' ] = pickle.dumps( units )    
    dic[ 'level' ] = pickle.dumps( compileLevel( engine.level ) )        
    dic[ 'turn' ] = engine.turn
    dic[ 'active_player_id' ] = engine.active_player.id
    dic[ 'players' ] = pickle.dumps( compilePlayers( engine.players, player ) )     
    
    return dic


def compilePlayers(players, active_player):
    ret = []
    
    for p in players:
        
        #observer
        if p.id == OBSERVER_ID:
            continue
        
        if p == active_player:
            plyr = compileTarget(p, ['units', 'connection', 'msg_lst'] )
            plyr['units'] = compileAllUnits( p.units )
            plyr['visible_enemies'] = compileAllEnemyUnits( p.visible_enemies ) 
            plyr['detected_enemies'] = compileAllDetectedUnits( p.detected_enemies ) 
            ret.append( plyr )
            
        else:
            plyr = compileTarget(p, ['units', 'connection', 'visible_enemies', 'detected_enemies', 'msg_lst']) 
            ret.append( plyr )
    
    return ret

    
def compileAllUnits(units):
    dct = {}
    for u in units:
        dct[u.id] = compileUnit(u)
    return dct


def compileAllEnemyUnits(units):
    dct = {}
    for u in units:
        dct[u.id] = compileEnemyUnit(u)
    return dct


def compileAllDetectedUnits(units):
    dct = {}
    for u in units:
        dct[u.id] = compileDetectedEnemyUnit(u)
    return dct


def compileLevel(level):
    return compileTarget( level,['_dynamics'] )


def compileUnit(unit):
    ret = compileTarget( unit, ['owner', 'weapons', 'active_weapon', 'armour'] )
     
    ret['owner_id'] = unit.owner.id             
    ret['weapons'] = compileWeaponList( unit.weapons )
    ret['armour'] = compileArmour( unit.armour )
    ret['active_weapon'] = compileWeapon( unit.active_weapon )
    return ret


def compileEnemyUnit(unit):
    ret = compileUnit(unit)
     
    del ret['resting']
    del ret['last_action']
    del ret['hp']
    del ret['ap']
    
    return ret


def compileDetectedEnemyUnit(unit):
    return { 'pos': unit.pos }


def compileArmour(armr):
    ret = compileTarget( armr, ['owner'] )
    return ret


def compileWeapon( wpn ):
    return compileTarget( wpn, ['owner'] )

    
def compileWeaponList( weapons ):
    wpn_list = []
    for weapon in weapons:
        wpn_list.append( compileWeapon( weapon ) )
    return wpn_list


def compileTarget( target, banned_list = [] ):
    attr_dict ={}
    for attr in target.__dict__:
        if attr in banned_list:
            continue
        attr_dict[attr] = target.__dict__[attr]
    return attr_dict
    



def getHeading( myPosition, lookAtPoint ):
    
    #trivial check if this is the same position, if it is, return none
    if myPosition == lookAtPoint:
        return unit.HEADING_NONE
    
    angle = math.atan2( lookAtPoint[1] - myPosition[1] , lookAtPoint[0] - myPosition[0] )

    return angleToHeading(angle)
    
    
def angleToHeading( angle ):
    if angle < -_7_PI_8:
        return unit.HEADING_W
    elif angle < -_5_PI_8:
        return unit.HEADING_SW
    elif angle < -_3_PI_8:
        return unit.HEADING_S
    elif angle < -_PI_8:
        return unit.HEADING_SE
    elif angle < _PI_8:
        return unit.HEADING_E
    elif angle < _3_PI_8:
        return unit.HEADING_NE
    elif angle < _5_PI_8:
        return unit.HEADING_N
    elif angle < _7_PI_8:
        return unit.HEADING_NW
    
    return unit.HEADING_W
    
    
def headingToAngle( heading ):
    
    if heading == unit.HEADING_W:
        return -_PI
    if heading == unit.HEADING_S:
        return -_PI_2
    if heading == unit.HEADING_E:
        return 0
    if heading == unit.HEADING_N:
        return _PI_2    
    if heading == unit.HEADING_SW:
        return -_3_PI_4
    if heading == unit.HEADING_SE:
        return -_PI_4
    if heading == unit.HEADING_NE:
        return _PI_4
    if heading == unit.HEADING_NW:
        return _3_PI_4

    

def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1



def d( num, dice ):
    ret = 0
    for a in xrange( num ):
        ret += random.randint( 1, dice )
    return ret


def d100():
    return random.randint( 1, 100 )


def distanceTupple( t1, t2  ):
    return distance( t1[0], t1[1], t2[0], t2[1] )


def distance( x1, y1, x2, y2 ):    
    return math.sqrt( math.pow( (x2-x1) , 2) +  math.pow( (y2-y1) , 2) )
    
    
def getReplayName():
    today = datetime.date.today()    
    i = 1
    
    while True:
        fname = "replay_%s_%d.rpl" %(today,i)
        if not os.path.exists(fname):
            break
        i+=1
    
    return fname