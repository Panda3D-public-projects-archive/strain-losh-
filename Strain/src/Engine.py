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
        
        player_nodes = xmldoc.getElementsByTagName( 'player' )
        
        for p in player_nodes:
            player = Player( p.attributes['name'].value )                        
            
            for units in p.getElementsByTagName( 'unit' ):
                u = Unit( player, 
                          units.attributes['name'].value, 
                          units.attributes['type'].value, 
                          units.attributes['x'].value,
                          units.attributes['y'].value )
                
                player.unitlist.append( u )
    
            self.players.append( player )
    
        xmldoc.unlink()   
        
    
        
    
class Player:
    
    def __init__(self, name):
        self.name = name 
        self.unitlist = []
        pass