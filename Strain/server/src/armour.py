from xml.dom import minidom
import util
import weapon

    
    
class Armour():

    def __init__(self):
        self.name = None
        self.front = None
        self.side = None
        self.owner = None
        self.ap = None
        
    
    def save( self, enemy_weapon ):

        if enemy_weapon.power:
            return 0

        if self.owner.inFront( enemy_weapon.owner.pos ):
            return self.front

        return self.side
 


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
        armr.side = int( p.attributes['sides_back'].value )
        armr.ap = int( p.attributes['action_points'].value )
        
    xmldoc.unlink()
    if not armr:
        raise Exception("Armour:%s not found in database." % name)
    return armr



