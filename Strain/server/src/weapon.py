'''
Created on 1.11.2011.

@author: krav
'''
from xml.dom import minidom
import math



TYPE_RIFLE = 'rifle'
TYPE_PISTOL = 'pistol'
TYPE_ASSAULT = 'assault'
TYPE_HEAVY = 'heavy'
TYPE_MELEE = 'melee'

SPECIAL_FLAMER = 'flamer'

class WeaponLoader():

    @staticmethod
    def loadWeapon( name ):     
        if __debug__:
            xmldoc = minidom.parse('../../Strain/data/base/weapons.xml')
        else:
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
            try:wpn.shots = int(p.attributes['shots'].value)
            except:pass
            try:wpn.special = p.attributes['special'].value
            except:pass
            try:wpn.blast = int(p.attributes['blast'].value)
            except:pass
            

        xmldoc.unlink()

        return wpn



    
    
class Weapon():



    def __init__(self):
        self.name = None
        self.range = None
        self.str = None
        self.ap = None
        self.type = None
        self.shots = None
        self.special = None
        self.blast = None
        
    
    def givePercent( self, distance, bs ):
        
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
        return res
        
        
        
        