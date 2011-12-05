from xml.dom import minidom
import math
import util




TYPE_RIFLE = 'rifle'
TYPE_PISTOL = 'pistol'
TYPE_ASSAULT = 'assault'
TYPE_HEAVY = 'heavy'
TYPE_MELEE = 'melee'

SPECIAL_FLAMER = 'flamer'
SPECIAL_STORM_SHIELD = 'storm_shield'



    
    
class Weapon():



    def __init__(self):
        self.owner = None
        self.name = None
        self.range = None
        self.str = None
        self.ap = None
        self.type = None
        self.sustained = None
        self.special = None
        self.blast = None
        self.parry = None
    
    def givePercent( self, distance, bs, visibility ):
        
        #TODO: krav: razlika izmedju ws-ova oba lika da se gleda
        if self.type == TYPE_MELEE:
            if distance > 1:
                return 0
            else:
                return 100
        
        if self.special == SPECIAL_FLAMER:
            if distance <= self.range:
                return 100
            else:
                return 0
        
        factor = bs * 7
        
        #trivial check if we are out of range
        if distance > self.range:
            return 0
    
        #TODO: krav: ufurat bs kod hevij wepona
        if self.type == TYPE_HEAVY:
            x = distance * 95 / self.range
            return -x + 69 + factor
    
        point_blank = (bs-1)
        if distance <= point_blank:
            return 100
        
        t = math.pi / (self.range-point_blank) 
        x = (distance-point_blank) * t - math.pi / 2
        sin = math.sin(-x)    
    
        if sin > 0:
            res = sin * (70 - factor) 
        else:
            res = sin * (25 + factor ) 
        
        res += 30 + factor    
        
        if visibility == 1:
            res *= 0.5
        
        return res
        
        
    def shoot(self, shooter, target, visibility ):

        #when we are here, we are certain that the target is in los
        #check range
        distance = util.distanceTupple(shooter.pos, target.pos)
        
        to_hit = self.givePercent(distance, shooter.bs, visibility)       
                
        if util.d100() <= to_hit:
            return self.hit( target )
        else:
            return [('miss', target.id)]
    
    
    def hit(self, target):
        if target.save( self ):
            return [('bounce', target.id)]
        return target.hit( self )

        
    def hitInMelee(self, attacker, target):
        if target.save( self ):
            return [('bounce', target.id)]
        
        res = None
        
        if attacker.s > self.str:
            orig_str = self.str
            self.str = attacker.s
            res = target.hit( self )
            self.str = orig_str
        else:
            res = target.hit( self )
            
        return res

        
def loadWeapon( name ):     
    xmldoc = minidom.parse('data/base/weapons.xml')
    
    wpn = None
    
    for p in xmldoc.getElementsByTagName( 'weapon' ):
                
        if p.attributes['name'].value != name:
            continue
        
        wpn = Weapon()            
        wpn.name = p.attributes['name'].value
        
        try:wpn.type = p.attributes['type'].value 
        except:pass
        try:wpn.str = int(p.attributes['Str'].value)
        except:pass
        try:wpn.ap = int(p.attributes['AP'].value)
        except:pass
        try:wpn.range = int(p.attributes['range'].value)
        except:pass
        try:wpn.sustained = int(p.attributes['sustained'].value)
        except:pass
        try:wpn.special = p.attributes['special'].value
        except:pass
        try:wpn.blast = int(p.attributes['blast'].value)
        except:pass
        

    xmldoc.unlink()
    if not wpn:
        raise Exception("Weapon:%s not found in database." % name)
    return wpn


