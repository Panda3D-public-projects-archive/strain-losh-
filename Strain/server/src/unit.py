from xml.dom import minidom
import weapon
import util
import armour
import math
import engine
from server_messaging import *

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
    
    
    def __init__( self, name ):        
        self.id = -1
        self.owner = None
        self.pos = ( -1, -1 )
        self.name = name     
        self.heading = HEADING_N      
        self.resting = False
        self.bs = -1
        self.weapons = []
        self.active_weapon = None
        self.overwatch = False
        self.alive = True
        self.last_action = 'spawn'
        #self.set_up = False #for heavy weapons this is only initilaized if a unit has a heavy weapon
        self.height = 2
        
        self.ap, self.default_ap = 0, 0
        self.hp, self.default_hp = 0, 0
        
        #self.m = -1
        self.ws = -1
        #self.bs = -1
        self.s = -1
        #self.t = -1
        #self.w = -1
        #self.i = -1
        #self.ld = -1 
        
    def init(self, in_id, owner, x, y ):
        
        self.id = in_id
        self.owner = owner
        
        self.pos = ( x, y )
           
        if self.name == 'marine_common':
            self.soundtype = '02'
        elif self.name == 'marine_epic':
            self.soundtype = '01'
        elif self.name == 'commissar':
            self.soundtype = '01'                                                   


        self.ap = self.default_ap
        self.hp = self.default_hp
        

    def setActiveWeapon(self, weapon):
        self.active_weapon = weapon
        
        
    def melee(self, target):
        
        ret_lst = []
        
        if self.ap < 1:
            return None
        
        #set up heavy weapons cannot do melee
        if self.hasHeavyWeapon() and self.set_up:
                return None 
        
        #TODO: krav: melee bi trebao obojici trosit ap, i da bude contest of skill - dakle bilo ko moze dobit
        self.ap -= 1
        
        base = 90
        
        #charge
        if self.last_action == 'move':
            base += 10        
        
        #face opponent 
        if self.rotate( target.pos ):
            ret_lst.append( ( ROTATE, self.id, self.heading) )
            
        #rotate opponent to us, if he has any ap left
        if target.ap > 0:
            if target.rotate( self.pos ):
                ret_lst.append( ( ROTATE, target.id, target.heading) )
         
        
        base -= 10 * target.numberOfMeleeWeapons() 
        base += 10 * (self.numberOfMeleeWeapons() - 1)        
        base += (self.ws - target.ws) * 10
        
        wpn = self.chooseMeleeWeapon(target)
        
        self.last_action = 'melee'
        
        #roll to hit
        if util.d100() > base:
            ret_lst.append( ('melee', self.id, target.pos, wpn.name, [('miss', target.id)] ) )
            return ret_lst        
            
        ret_lst.append(  ('melee', self.id, target.pos, wpn.name, wpn.hitInMelee( self, target ) ) )
        return ret_lst

        
    def chooseMeleeWeapon(self, target):
        dmg = 0

        w = None
        for wpn in self.weapons:
            if wpn.type != weapon.TYPE_MELEE:
                continue
            
            if wpn.str > dmg:
                dmg = wpn.str
                w = wpn
    
        if not w:
            w = weapon.loadWeapon("Karate")
            w.owner = self
            w.str = self.s
                
        return w

        
        
    def numberOfMeleeWeapons(self):
        res = 0
        for wpn in self.weapons:
            if self.hasHeavyWeapon():
                res -= 1
            if wpn.type == weapon.TYPE_MELEE or wpn.type == weapon.TYPE_PISTOL:
                res += 1        
            if wpn.parry:
                res += 1
        return res
        

                
    def shoot(self, target, visibility, overwatch = False):
        #TODO: krav: stavit da se moze gadjat i tile?
                
        if not visibility:
            return None
        
        distance = util.distanceTupple(self.pos, target.pos)
        
        #check range
        if distance > self.active_weapon.range:
            return None
        
        #check melee
        if distance < 2:
            return self.melee( target )
        
        #check if we have a heavy weapon and if we are set up
        if self.hasHeavyWeapon():
            if not self.set_up:
                return None
            
        #check if there is enough ap to fire
        if self.active_weapon.sustained and self.last_action == 'shoot':
            if self.ap >= self.active_weapon.sustained:
                self.ap -= self.active_weapon.sustained
            else:
                return None
        else:
            if self.ap < 1:
                return None
            self.ap -= 1
                        
        #check to see if we need to rotate unit before shooting, but if we are on overwatch, we cant rotate
        rot = [] 
        if not overwatch:
            if self.rotate( target.pos ):
                rot.append( ( ROTATE, self.id, self.heading) ) 
                        
        self.last_action = 'shoot'
        
        rot.append( (SHOOT, self.id, target.pos, self.active_weapon.name, self.active_weapon.shoot( self, target, visibility ) ) )
        return rot


    def _shoot(self, target):
        pass


    def setOverwatch(self):
        #check if there are enough AP
        if self.ap >= 2:
            self.overwatch = True
            return True
        
        return False


    def hit(self, weapon, dmg_saved):
        
        dmg_received = weapon.str - dmg_saved
        
        if dmg_received:
            self.hp -= dmg_received
        else:
            return [('bounce', self.id)]
                
        if self.hp <= 0:
            self.die( weapon )
            return [('kill', self.id, dmg_received )]
        return [('damage',self.id, dmg_received)]


    def save(self, enemy_weapon):
        return self.armour.save( enemy_weapon )


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
       
       
    def doOverwatch(self, target, visibility ):
        return self.shoot( target, visibility, True )
        
        
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
        for w in self.weapons:
            if w.type == weapon.TYPE_HEAVY and self.armour != 'Terminator':
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

#-----------------------------------------------------------------------
def loadUnit( name ):
    xmldoc = minidom.parse('data/base/units.xml')
    
    unit = None
    
    for p in xmldoc.getElementsByTagName( 'unit' ):
                
        if p.attributes['name'].value != name:
            continue
        
        unit = Unit( p.attributes['name'].value )            

        #load armour                     
        unit.armour =  armour.loadArmour( p.attributes['armour'].value )
        unit.armour.owner = unit
        unit.default_ap = unit.armour.ap
        
        #add all weapons, and try to set first ranged weapon as active
        wpns = p.attributes['weapons'].value.split(',')
        for wname in wpns:
            wpn = weapon.loadWeapon( wname )
            wpn.owner = unit
            unit.weapons.append( wpn )  
            if wpn.type != weapon.TYPE_MELEE:
                unit.active_weapon = wpn
        if not unit.active_weapon:
            unit.weapons[0]

        #initialize set_up if needed
        if unit.hasHeavyWeapon():
            unit.set_up = False

        unit.default_hp = int( p.attributes['hp'].value )
        
        #unit.m = int( p.attributes['m'].value )
        unit.ws = int( p.attributes['ws'].value )
        #unit.bs = int( p.attributes['bs'].value )
        unit.s = int( p.attributes['s'].value )
        #unit.t = int( p.attributes['t'].value )
        #unit.w = int( p.attributes['w'].value )
        #unit.i = int( p.attributes['i'].value )
        #unit.a = int( p.attributes['a'].value )
        #unit.ld = int( p.attributes['ld'].value )

    xmldoc.unlink()
    
    if not unit:
        raise Exception("Unit:%s not found in database." % name)
    return unit
    

