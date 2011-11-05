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
        
    
    def save( self, weapon ):
        
        percent = 0
        if weapon.ap >= self.front:
            return False        
        elif self.front == weapon.ap + 1:
            percent = 66
        elif self.front == weapon.ap + 2:
            percent = 33
        elif self.front == weapon.ap + 3:
            percent = 10
        elif self.front == weapon.ap + 4:
            percent = 5
        elif self.front == weapon.ap + 4:
            return True
  
        if util.d100() > percent:
            return True
        
        return False
        


