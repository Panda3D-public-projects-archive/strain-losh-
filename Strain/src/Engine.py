from xml.dom import minidom
from Unit import Unit

class Engine:

    players = []
    units = {}
        
    def __init__(self):
        
        self.loadArmyList()
        
        
    def loadArmyList(self):
        xmldoc = minidom.parse('etc/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        players = []
        units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( p.attributes['name'].value )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                tmpUnit = Unit( player, 
                          u.attributes['name'].value, 
                          u.attributes['type'].value, 
                          u.attributes['x'].value,
                          u.attributes['y'].value )
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.name] = tmpUnit
                
            self.players.append( player )
    
        xmldoc.unlink()   
        
    
        
    
class Player:
    
    def __init__(self, name):
        self.name = name 
        self.unitlist = []
        pass