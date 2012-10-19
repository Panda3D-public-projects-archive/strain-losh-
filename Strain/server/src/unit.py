from xml.dom import minidom
import weapon
import util
import armour
import math
import engine
from server_messaging import *
from share import *
#from util import *
from buffs import *

#TODO: ovo je kopirano u interface.py
HEADING_NONE      = 0
HEADING_NW        = 1
HEADING_N         = 2
HEADING_NE        = 3
HEADING_W         = 4
HEADING_E         = 5
HEADING_SW        = 6
HEADING_S         = 7
HEADING_SE        = 8



class Unit():
    
    
    def __init__( self, name, engine ):        
        self.id = -1
        self.db_id = None
        self.owner = None
        self.owner_id = None
        self.engine = engine
        self.pos = ( -1, -1 )
        self.name = name     
        self.heading = HEADING_N      
        self.resting = False
        self.ranged_weapon = weapon.loadWeapon("Harsh Language", self)
        self.melee_weapon = weapon.loadWeapon("Karate", self)
        self.overwatch = False
        self.alive = True
        self.last_action = 'spawn'
        #self.set_up = False #for heavy weapons this is only initialized if a owner has a heavy weapon
        self.height = 2
        
        self.ap, self.default_ap = 0, 0
        self.hp, self.default_hp = 0, 0
                
        self.can_use = False
                
        self.ws = -1
        
        self.ability_list = []

        self.buffs = []
        
        
    def init(self, in_id, owner, x, y ):
        self.id = in_id
        self.owner = owner
        self.owner_id = owner.id
        
        self.pos = ( x, y )
           
        self.ap = self.default_ap
        self.hp = self.default_hp


    def doIKnowAboutThisUnit(self, tmp_unit ):
        if tmp_unit.owner == self.owner or tmp_unit.owner.team == self.owner.team or tmp_unit in self.owner.visible_enemies:
                return True
        return False
        

    def melee(self, target, to_hit, overwatch = False):
        
        #set up heavy weapons cannot do melee
        if self.hasHeavyWeapon() and self.set_up:
                return False 
            
        if self.ap < self.melee_weapon.ap_cost:
            return False
        
        #TODO: krav: melee bi trebao obojici trosit ap, i da bude contest of skill - dakle bilo ko moze dobit
        self.ap -= self.melee_weapon.ap_cost
        
        """
        to_hit = 90
        #charge
        if self.last_action == 'move':
            to_hit += 10
        #if enemy has a better weapon skill
        to_hit += (self.ws - target.ws) * 10
        """
                
        #face opponent 
        if self.rotate( target.pos ):
            self.engine.event_handler.addEvent( (ROTATE, self, getHeadingTile(self.heading, self.pos) ) )
            
        #rotate opponent to us
        if target.rotate( self.pos ):
            self.engine.event_handler.addEvent( (ROTATE, target, getHeadingTile(target.heading, self.pos) ) )
         
        self.last_action = 'melee'
            
        #get action from weapon
        tmp_event = self.melee_weapon.fire(target, to_hit)
        if overwatch:
            tmp_event = (OVERWATCH,) + tmp_event
            
        #send action to handler
        self.engine.event_handler.addEvent( tmp_event )

        return True


        
    def shoot(self, target, to_hit, overwatch = False):
        #if we cant hit the target abort
        if not to_hit:
            return False
        
        distance = distanceTupple(self.pos, target.pos)
        
        #if in melee range, do melee
        if distance < 2:
            return self.melee( target, to_hit, overwatch )
        
        #check if we have a heavy weapon and we are not set up, return
        if self.hasHeavyWeapon() and not self.set_up:
            return False
            
        #check if there is enough ap to fire
        if self.ap < self.ranged_weapon.ap_cost:
            return False
        self.ap -= self.ranged_weapon.ap_cost
                        
        #check to see if we need to rotate owner before shooting, but if we are on overwatch, we cant rotate
        #we already checked if target is in front, if this is overwatch
        if not overwatch:
            if self.rotate( target.pos ):
                self.engine.event_handler.addEvent( (ROTATE, self, getHeadingTile(self.heading, self.pos) ) )

        #ok everything checks out, we can do the actual shooting                        
        self.last_action = 'shoot'
        
        

        modifier = self.buffCheck( ACTION_SHOOT_BEGIN )
        
        
        #get action from weapon
        tmp_event = self.ranged_weapon.fire( target, to_hit * modifier )
        if overwatch:
            tmp_event = (OVERWATCH,) + tmp_event
            
        #add action to handler
        self.engine.event_handler.addEvent( tmp_event )
        
        self.buffCheck( ACTION_SHOOT_OVER )
        
        
        return True


    def buffCheck(self, action):
        
        ret_value = None
        
        events = []
        
        if action == ACTION_SHOOT_BEGIN:
            modifiers = [1]
            for buff in self.buffs[:]:
                buff.action( ACTION_SHOOT_BEGIN, modifiers, events, self.buffs )
            ret_value = modifiers[0]
            
        #generic event
        else:
            for buff in self.buffs[:]:
                buff.action( action, None, events, self.buffs )
            
        
        for action in events:
            self.engine.event_handler.addEvent( action )

        
        return ret_value


    def toggleOverwatch(self):
        #check if there are enough AP
        if self.ap >= 2:
            self.overwatch = True
            self.ap -= 2
        else:
            return "Not enough AP for overwatch."
        

    def toggleSetup(self):
        if not self.hasHeavyWeapon():
            return "The owner does not have any heavy weapons."

        if self.set_up:
            msg = self.tearDown()
            if msg:
                return msg
        else:
            msg = self.setUp()
            if msg:
                return msg

    def tryToUse(self):
        if not self.can_use:
            return "Unit cannot use anything."
                
        if self.ap < 1:
            return "Not enough AP for using."
                
        #try to use something
        if self.engine.use( self ):
            self.ap -= 1
            self.last_action = 'use'
            self.engine.event_handler.addEvent( (USE, self) )
        else:
            return "There is nothing to use in front."


    def iAmHit(self, weapon):
        
        dmg_saved = self.armour.reduceDmg( weapon )
        dmg_received = weapon.str - dmg_saved
        
        if dmg_received < 0:
            dmg_received = 0
        
        if dmg_received:
            self.hp -= dmg_received
        else:
            return (BOUNCE, self.id)
                
        if self.hp <= 0:
            self.die( weapon )
            return (KILL, self.id, dmg_received )
        return (DAMAGE, self.id, dmg_received)


    def die(self, weapon ):
        self.alive = False

       
    def setUp(self):
        if self.set_up:
            return "This owner already set-up."
        else:
            if self.ap < 2:
                return "Not enough AP to set up."
            
            self.ap -= 2
            self.set_up = True
            self.last_action = 'setup'
            return None
        
        
    def tearDown(self):
        if self.set_up:
            if self.ap < 2:
                return "Not enough AP to tearDown."
            
            self.ap -= 2
            self.set_up = False
            self.last_action = 'tearDown'
            return None
        else:
            return "This owner is not set-up."
       
       
    def doOverwatch(self, target, to_hit ):
        return self.shoot( target, to_hit, True )
        
        
    def move(self, new_position, ap_remaining ):
        self.last_action = 'move'
        self.overwatch = False
        self.pos = new_position
        self.ap = ap_remaining
        
        
    def rotate(self, look_at_tile ):
        tmp_heading = util.getHeading(self.pos, look_at_tile)
        
        if self.heading == tmp_heading:
            return False
        
        #self.last_action = 'rotate'
        self.heading = tmp_heading        
        return True

        
    def newTurn(self, turn_num):
        #replenish AP
        self.ap = self.default_ap
        
        #if owner rested last turn
        if self.resting:
            self.ap += 1
            self.resting = False

        self.buffCheck( ACTION_NEW_TURN )
        
        
    def endTurn(self):
        self.buffCheck( ACTION_TURN_END )
        

    def hasHeavyWeapon(self):
        if self.ranged_weapon.special == weapon.SPECIAL_SET_UP:
            return True
        return False
    

    def inFront(self, tile):
        angle1 = math.atan2( tile[1] - self.pos[1] , tile[0] - self.pos[0] )
        angle2 = util.headingToAngle(self.heading)

        d = math.fabs( angle1-angle2 ) 

        if d <= util._PI_4:
            return True
        elif d >= util._7_PI_4:
            return True
        
        return False
        

    def amIStuck(self):
        if self.hasHeavyWeapon() and self.set_up:
            return "Need to teardown heavy weapon first."
        
        return False

    
    
    def taunt(self):
        if self.ap < 1:
            return "Not enough AP for taunting."
        
        self.ap -= 1
        self.last_action = 'taunt'
        
        self.engine.taunt( self )
        
        
        

#-----------------------------------------------------------------------
def loadUnit( name, engine ):
    xmldoc = minidom.parse('data/base/units.xml')
    
    unit = None
    
    for p in xmldoc.getElementsByTagName( 'owner' ):
                
        if p.attributes['name'].value != name:
            continue
        
        unit = Unit( p.attributes['name'].value, engine )            
        unit.db_id = int( p.attributes['id'].value )
        unit.default_hp = int( p.attributes['hp'].value )
        unit.ws = int( p.attributes['ws'].value )
        
        try:
            unit.ranged_weapon = weapon.loadWeapon( p.attributes['ranged_weapon'].value, unit )
        except:
            pass
        
        try: 
            unit.melee_weapon = weapon.loadWeapon( p.attributes['melee_weapon'].value, unit )
        except:
            pass
        
        #initialize set_up if needed
        if unit.hasHeavyWeapon():
            unit.set_up = False
            
        #load armour                     
        unit.armour =  armour.loadArmour( p.attributes['armour'].value )
        owner.armour.owner = unit
        unit.default_ap = owner.armour.ap
        
        for ability in p.getElementsByTagName('ability'):
            owner.ability_list.append(ability.attributes['name'].value)
        
    xmldoc.unlink()
    
    if not unit:
        raise Exception("Unit:%s not found in database." % name)
    return unit
    


def getHeadingTile(h, dest):
    int_h = int(h)
    if int_h == HEADING_N:
        offset = (0, 1)
    elif int_h == HEADING_NW:
        offset = (-1, 1)
    elif int_h == HEADING_W:
        offset = (-1, 0)
    elif int_h == HEADING_SW:
        offset = (-1, -1)
    elif int_h == HEADING_S:
        offset = (0, -1)
    elif int_h == HEADING_SE:
        offset = (1, -1)
    elif int_h == HEADING_E:
        offset = (1, 0)
    elif int_h == HEADING_NE:
        offset = (1, 1)
    else:
        offset = (0, 0)
    return tuple([item1 + item2 for item1, item2 in zip(dest, offset)])
