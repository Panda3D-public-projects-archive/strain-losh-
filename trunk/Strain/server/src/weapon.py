from xml.dom import minidom
import math
import util
from strain.share import *



SPECIAL_SET_UP = "set_up"
SPECIAL_SILENCED = "silenced"
    
class Weapon():

    def __init__(self):
        self.owner = None
        self.id = None
        self.name = None
        self.range = None
        self.str = None
        self.ap_cost = None
        self.special = None
        self.blast = None
        self.parry = None
        self.power = None
        self.shots = None
    
    
    def fire(self, target, to_hit):
        
        #ranged weapon
        if self.range:
            tmp_event = (SHOOT, self.owner, target.pos, self)
        #melee weapon
        else:
            tmp_event = (MELEE, self.owner, target.pos, self)


        res_list = []
        for i in xrange(self.shots): #@UnusedVariable                            
            if util.d100() <= to_hit:
                res_list.append( self.hitTarget( target ) ) 
            else: 
                res_list.append( (MISS, target.id) ) 
    
        tmp_event += (res_list,)
        return tmp_event
    
    
    def hitTarget(self, target):
        return target.iAmHit( self )

        

        
def loadWeapon( name, owner = None ):     
    xmldoc = minidom.parse('data/base/weapons.xml')
    
    wpn = None
    
    for p in xmldoc.getElementsByTagName( 'weapon' ):
                
        if p.attributes['name'].value != name:
            continue
        
        wpn = Weapon()            
        if owner:
            wpn.owner = owner
        wpn.id = p.attributes['id'].value 
        wpn.name = p.attributes['name'].value 
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



