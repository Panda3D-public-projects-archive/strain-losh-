from xml.dom import minidom
from Unit import Unit
from Level import Level

class Engine:

    players = []
    units = {}
        
        
    _index_uid = 0

        
    def __init__(self):
        
        self.loadArmyList()
        self.level = Level("level3.txt")
        
    def getUID(self):
        self._index_uid += 1
        return self._index_uid -1
    
        
    def loadArmyList(self):
        xmldoc = minidom.parse('etc/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( self.getUID(), p.attributes['name'].value )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                tmpUnit = Unit( self.getUID(),
                                player, 
                                u.attributes['type'].value, 
                                u.attributes['x'].value,
                                u.attributes['y'].value )
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.id] = tmpUnit
                
            self.players.append( player )
    
        xmldoc.unlink()   
        
    
class Player:
    
    def __init__(self, id, name):
        self.id = id
        self.name = name 
        self.unitlist = []
        pass