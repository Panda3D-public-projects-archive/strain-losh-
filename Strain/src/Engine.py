from xml.dom import minidom
from Unit import Unit

class Engine:

    players = []
    units = {}
        
        
    _index_for_players = 0
    _index_for_units = 0
        
    def __init__(self):
        
        self.loadArmyList()
        
    def getUnitIndex(self):
        self._index_for_units += 1
        return self._index_for_units -1
    
    def getPlayerIndex(self):
        self._index_for_players += 1
        return self._index_for_players -1
    
        
    def loadArmyList(self):
        xmldoc = minidom.parse('etc/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( self.getPlayerIndex(), p.attributes['name'].value )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                tmpUnit = Unit( self.getUnitIndex(),
                                player, 
                                u.attributes['name'].value, 
                                u.attributes['type'].value, 
                                u.attributes['x'].value,
                                u.attributes['y'].value )
                
                player.unitlist.append( tmpUnit )
                self.units[tmpUnit.name] = tmpUnit
                
            self.players.append( player )
    
        xmldoc.unlink()   
        
    
        
    
class Player:
    
    def __init__(self, id, name):
        self.id = id
        self.name = name 
        self.unitlist = []
        pass