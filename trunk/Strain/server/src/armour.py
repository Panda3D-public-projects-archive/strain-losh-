from xml.dom import minidom
import util



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



    
    
class Armour():

    def __init__(self):
        self.name = None
        self.front = None
        self.head = None
        self.owner = None
        
    
    def save( self, weapon ):
        
        effective_armour = self.front
        
        #see if i have a storm shield, if so raise my effective armour by 1
        for wpn in self.owner.weapons:
            if wpn.special == weapon.SPECIAL_STORM_SHIELD:
                effective_armour += 1
        
        percent = 0
        
        if weapon.ap >= effective_armour:
            return False        
        elif effective_armour == weapon.ap + 1:
            percent = 66
        elif effective_armour == weapon.ap + 2:
            percent = 33
        elif effective_armour == weapon.ap + 3:
            percent = 10
        elif effective_armour == weapon.ap + 4:
            percent = 5
        elif effective_armour == weapon.ap + 4:
            return True
  
        if util.d100() > percent:
            return True
        
        return False
        


