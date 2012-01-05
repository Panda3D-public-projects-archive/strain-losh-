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
        self.shots = None
    
    
    
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
        
        
    def fire(self, target, visibility ):

        ret_list = []

        for i in xrange(self.shots):
            #when we are here, we are certain that the target is in los        
            to_hit = self.givePercent( target, visibility )       
                    
            if util.d100() <= to_hit: 
                ret_list.append( self.hitTarget( target ) )
            else: 
                ret_list.append( ('miss', target.id) )
    
        return ret_list
    
    
    def hitTarget(self, target):
        return target.iAmHit( self, target.armour.reduceDmg( self ) )

        

        
def loadWeapon( name ):     
    xmldoc = minidom.parse('data/base/weapons.xml')
    
    wpn = None
    
    for p in xmldoc.getElementsByTagName( 'weapon' ):
                
        if p.attributes['name'].value != name:
            continue
        
        wpn = Weapon()            
        wpn.name = p.attributes['name'].value
        wpn.type = p.attributes['type'].value 
        wpn.str = int(p.attributes['Str'].value)
        try:wpn.range = int(p.attributes['range'].value)
        except: pass
        wpn.ap_cost = float(p.attributes['ap_cost'].value)
        
        try:wpn.power = int(p.attributes['power'].value)
        except:pass
        try:wpn.special = p.attributes['special'].value
        except:pass
        try:wpn.shots = int(p.attributes['shots'].value)
        except:pass
        try:wpn.blast = int(p.attributes['blast'].value)
        except:pass


    xmldoc.unlink()
    if not wpn:
        raise Exception("Weapon:%s not found in database." % name)
    return wpn



