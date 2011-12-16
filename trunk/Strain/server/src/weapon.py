from xml.dom import minidom
import math
import util




TYPE_RIFLE = 'rifle'
TYPE_PISTOL = 'pistol'
TYPE_ASSAULT = 'assault'
TYPE_HEAVY = 'heavy'
TYPE_MELEE = 'melee'

SPECIAL_FLAMER = 'flamer'




    
    
class Weapon():

    def __init__(self):
        self.owner = None
        self.name = None
        self.range = None
        self.str = None
        self.ap_cost = None
        self.type = None
        self.special = None
        self.blast = None
        self.parry = None
        self.power = None
    
    def givePercent( self, target, visibility ):
        
        distance = util.distanceTupple( self.owner.pos, target.pos)

        if self.type == TYPE_MELEE:
            if distance >= 2:
                return 0
            else:
                return 100
        
        if self.special == SPECIAL_FLAMER:
            if distance <= self.range:
                return 100
            else:
                return 0
        
        #trivial check if we are out of range
        if distance > self.range:
            return 0
    
        #for every tile of distance, accuracy drops for this factor
        factor = 5
        
        #TODO: krav: a mozda da svako oruzje ima svoj accuracy
        if self.type == TYPE_RIFLE:
            factor = 5
        elif self.type == TYPE_ASSAULT:
            factor = 6
        elif self.type == TYPE_HEAVY:
            factor = 5
        elif self.type == TYPE_PISTOL:
            factor = 7
            
        res = 100 - (distance * factor)  

        if visibility == 1:
            res *= 0.6
        
        return int(res)
        
        
    def shoot(self, target, visibility ):

        #when we are here, we are certain that the target is in los        
        to_hit = self.givePercent( target, visibility)       
                
        if util.d100() <= to_hit:
            return self.hit( target )
        else:
            return [('miss', target.id)]
    
    
    def hit(self, target):
        return target.hit( self, target.save( self ) )

        
    def hitInMelee(self, attacker, target):
        return target.hit( self, target.save( self ) )

        
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
        try:wpn.range = int(p.attributes['range'].value)
        except:pass
        try:wpn.ap_cost = int(p.attributes['ap_cost'].value)
        except:pass
        try:wpn.power = int(p.attributes['power'].value)
        except:pass
        try:wpn.special = p.attributes['special'].value
        except:pass
        try:wpn.blast = int(p.attributes['blast'].value)
        except:pass


    xmldoc.unlink()
    if not wpn:
        raise Exception("Weapon:%s not found in database." % name)
    return wpn



