from xml.dom import minidom
import weapon
import util
import armour
import math
import engine
from server_messaging import *
from strain.share import *

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
        #self.set_up = False #for heavy weapons this is only initialized if a unit has a heavy weapon
        self.height = 2
        
        self.ap, self.default_ap = 0, 0
        self.hp, self.default_hp = 0, 0
                
        self.can_use = False
                
        self.move_dict = []
        self.shoot_dict = []
                
        self.ws = -1
        
        
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
            self.engine.event_handler.addEvent( (ROTATE, self, self.heading) )
            
        #rotate opponent to us
        if target.rotate( self.pos ):
            self.engine.event_handler.addEvent( (ROTATE, target, target.heading) )
         
        self.last_action = 'melee'
            
        #get event from weapon
        tmp_event = self.melee_weapon.fire(target, to_hit)
        if overwatch:
            tmp_event = (OVERWATCH,) + tmp_event
            
        #send event to handler
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
                        
        #check to see if we need to rotate unit before shooting, but if we are on overwatch, we cant rotate
        #we already checked if target is in front, if this is overwatch
        if not overwatch:
            if self.rotate( target.pos ):
                self.engine.event_handler.addEvent( (ROTATE, self, self.heading) )

        #ok everything checks out, we can do the actual shooting                        
        self.last_action = 'shoot'
        
        #get event from weapon
        tmp_event = self.ranged_weapon.fire( target, to_hit )
        if overwatch:
            tmp_event = (OVERWATCH,) + tmp_event
            
        #add event to handler
        self.engine.event_handler.addEvent( tmp_event )
        
        return True


    def setOverwatch(self):
        #check if there are enough AP
        if self.ap >= 2:
            self.overwatch = True
            return True
        
        return False


    def iAmHit(self, weapon):
        
        dmg_saved = self.armour.reduceDmg( weapon )
        dmg_received = weapon.str - dmg_saved
        
        if dmg_received < 0:
            dmg_received = 0
        
        if dmg_received:
            self.hp -= dmg_received
        else:
            return ('bounce', self)
                
        if self.hp <= 0:
            self.die( weapon )
            return ('kill', self, dmg_received )
        return ('damage', self, dmg_received)


    def die(self, weapon ):
        self.alive = False

       
    def setUp(self):
        if self.set_up:
            return "This unit already set-up."
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
            return "This unit is not set-up."
       
       
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
        
        #if unit rested last turn
        if self.resting:
            self.ap += 1
            self.resting = False

        

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

    
    def use(self):
        self.ap -= 1
        self.last_action = 'use'

    
    def taunt(self):
        self.ap -= 1
        self.last_action = 'taunt'
        
        

#-----------------------------------------------------------------------
def loadUnit( name, engine ):
    xmldoc = minidom.parse('data/base/units.xml')
    
    unit = None
    
    for p in xmldoc.getElementsByTagName( 'unit' ):
                
        if p.attributes['name'].value != name:
            continue
        
        unit = Unit( p.attributes['name'].value, engine )            
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
        unit.armour.owner = unit
        unit.default_ap = unit.armour.ap
        
    xmldoc.unlink()
    
    if not unit:
        raise Exception("Unit:%s not found in database." % name)
    return unit
    

