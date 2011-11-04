from xml.dom import minidom
from weapon import WeaponLoader
import weapon
import engineMath


class unitLoader():
    
    @staticmethod
    def loadUnit( name ):
        xmldoc = minidom.parse('data/base/units.xml')
        
        unit = None
        
        for p in xmldoc.getElementsByTagName( 'unit' ):
                    
            if p.attributes['name'].value != name:
                continue
            
            unit = Unit( p.attributes['name'].value )            
                         
            #add all weapons, and try to set first ranged weapon as active
            wpns = p.attributes['weapons'].value.split(',')
            for wname in wpns:
                wpn = WeaponLoader.loadWeapon(wname)
                unit.weapons.append( wpn )  
                if wpn.type != weapon.TYPE_MELEE:
                    unit.active_weapon = wpn
            if not unit.active_weapon:
                unit.weapons[0]
            
            unit.m = int( p.attributes['m'].value )
            unit.ws = int( p.attributes['ws'].value )
            unit.bs = int( p.attributes['bs'].value )
            unit.s = int( p.attributes['s'].value )
            unit.t = int( p.attributes['t'].value )
            unit.w = int( p.attributes['w'].value )
            unit.i = int( p.attributes['i'].value )
            unit.a = int( p.attributes['a'].value )
            unit.ld = int( p.attributes['ld'].value )

        xmldoc.unlink()
        
        if not unit:
            raise Exception("Unit:%s not found in database." % name)
        return unit
        
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
        self.name = name     
        self.heading = HEADING_N      
        self.losh_dict = {}        
        self.move_dict = {}
        self.resting = False
        self.bs = -1
        self.weapons = []
        self.active_weapon = None
        self.overwatch = True
        self.alive = True
        
        
        self.m = -1
        self.ws = -1
        self.bs = -1
        self.s = -1
        self.t = -1
        self.w = -1
        self.i = -1
        self.ld = -1 
        
    def init(self, in_id, owner, x, y ):
        
        self.id = in_id
        self.owner = owner
        
        self.pos = ( x, y )
           
        if self.name == 'marine_common':
            self.default_AP = 5
            self.default_HP = 5
            self.soundtype = '02'
        elif self.name == 'marine_epic':
            self.default_AP = 6
            self.default_HP = 6
            self.soundtype = '01'
        elif self.name == 'commissar':
            self.default_AP = 5
            self.default_HP = 5
            self.soundtype = '01'                                                   


        self.current_AP = self.default_AP
        self.health = self.default_HP
        
        
        
    def shoot(self, weapon, target):
        #TODO: krav: stavit da se moze gadjat i tile?
        result = weapon.shoot( self, target )        
        return ('shoot', self.id, self.active_weapon.name, result )



    def hit(self, weapon):
        
        #TODO: krav: ovdje ufurat oklope
        self.health -= weapon.str
        if self.health <= 0:
            self.die( weapon )
            return ('kill', self.id, weapon.str )
        return('damage',self.id, weapon.str)


    def die(self, weapon ):
        self.alive = False

       
    #mora vratit rezultat koji ce ic u actions u movementu
    #lista akcija koja se dogodila na overatchu
    def doOverwatch(self, target):
        
        #TODO: krav: check range
        if engineMath.distanceTupple(self.pos, target.pos) > self.active_weapon.range:
            return None
        
        #TODO: krav: check if there is enough ap to fire
        if self.current_AP < 1:
            return None

        self.current_AP -= 1
        return self.shoot(self.active_weapon, target)
        
        
        
        
        
        
