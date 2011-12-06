from xml.dom import minidom
import util
import weapon

    
    
class Armour():

    def __init__(self):
        self.name = None
        self.front = None
        self.head = None
        self.owner = None
        
    
    def save( self, enemy_weapon ):
        
        effective_armour = self.front
        
        #see if i have a storm shield, if so raise my effective armour by 1 if attack is from front
        for wpn in self.owner.weapons:
            if wpn.special == weapon.SPECIAL_STORM_SHIELD:
                if self.owner.inFront( enemy_weapon.owner.pos ):
                    effective_armour += 1
        
        percent_to_save = 100
        
        if enemy_weapon.ap > effective_armour:
            return False
        elif enemy_weapon.ap == effective_armour:
            percent_to_save = 20
        elif enemy_weapon.ap == effective_armour - 1:
            percent_to_save = 50
        elif enemy_weapon.ap == effective_armour - 2:
            percent_to_save = 90

        if util.d100() <= percent_to_save:
            return True
        
        return False


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def loadArmour( name ):     
    xmldoc = minidom.parse('data/base/armour.xml')
    armr = None
            
    for p in xmldoc.getElementsByTagName( 'armour' ):
                
        if p.attributes['name'].value != name:
            continue
        
        armr = Armour()            
        armr.name = p.attributes['name'].value            
        armr.front = int( p.attributes['front'].value )
        armr.head = int( p.attributes['head'].value )
        
    xmldoc.unlink()
    if not armr:
        raise Exception("Armour:%s not found in database." % name)
    return armr



