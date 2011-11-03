from xml.dom import minidom
from weapon import WeaponLoader
import weapon


class unitLoader():
    
    @staticmethod
    def loadUnit( name ):
        xmldoc = minidom.parse('data/base/units.xml')
        
        unit = None
        
        for p in xmldoc.getElementsByTagName( 'unit' ):
                    
            if p.attributes['name'].value != name:
                continue
            
            unit = Unit( p.attributes['name'].value )            
                         
            wpns = p.attributes['weapons'].value.split(',')
            for wname in wpns:
                wpn = WeaponLoader.loadWeapon(wname)
                unit.weapons.append( wpn )  
                if wpn.type != weapon.TYPE_MELEE:
                    unit.active_weapon = wpn
            if not unit.active_weapon:
                unit.weapons[0]
            
            unit.m = p.attributes['m'].value
            unit.ws = p.attributes['ws'].value
            unit.bs = p.attributes['bs'].value
            unit.s = p.attributes['s'].value
            unit.t = p.attributes['t'].value
            unit.w = p.attributes['w'].value
            unit.i = p.attributes['i'].value
            unit.a = p.attributes['a'].value
            unit.ld = p.attributes['ld'].value

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
        self.owner_id = -1
        self.name = name     
        self.heading = HEADING_N      
        self.losh_dict = {}        
        self.move_dict = {}
        self.resting = False
        self.bs = -1
        self.weapons = []
        self.active_weapon = None
        
        self.m = -1
        self.ws = -1
        self.bs = -1
        self.s = -1
        self.t = -1
        self.w = -1
        self.i = -1
        self.ld = -1 
        
    def init(self, in_id, owner_id, x, y ):
        
        self.id = in_id
        self.owner_id = owner_id
        
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
        
