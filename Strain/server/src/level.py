

LEVELS_ROOT = "./data/levels/"


DYNAMICS_EMPTY = 0
DYNAMICS_UNIT = 1


class Level:
        
    def __init__(self, name):        
        self.name = LEVELS_ROOT + name    
        self.maxX = 0
        self.maxY = 0
        self._level_data = []    
        self._dynamics = []
        
        self.load(self.name)        

        self.center = ( self.maxX / 2, self.maxY / 2 )


    def load(self, name):
        line_count = 0
        lvl_file = open( name, "r")
        for line in lvl_file:
            line_count = line_count + 1
            if line_count == 1:
                s = line.split()
                self.maxX = int(s[0]); self.maxY = int(s[1])
            else:
                s = line.split(";")
                s = s[0:self.maxX]
                self._level_data.append(s)
           
        lvl_file.close()
        self._level_data.reverse()
        
        #convert entries in _level_data from string to integer AND change x-y order
        tmp = [[None] * self.maxY for i in xrange(self.maxX)]
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._level_data[j][i] = int( self._level_data[j][i] )
                tmp[i][j] = self._level_data[j][i]
        self._level_data = tmp 

        #we make this so its size is the same as level 
        self._dynamics = [[ None ] * self.maxY for i in xrange(self.maxX)] #@UnusedVariable


    def outOfBounds( self, x, y ):
        if( x < 0 or y < 0 or x >= self.maxX or y >= self.maxY ):
            return True
        else: 
            return False


    #TODO: krav: spojit ovo i opaque()
    def canUnitFitHere(self, unit):

        x, y = int(unit.pos[0]), int(unit.pos[1])

        #check to see if there is something in the way on level
        if self._level_data[x][y] != 0:
            print "This unit cannot be placed on non empty level tile", unit.name, x, y
            return False
        
        #check to see if the tile is already occupied
        if self._dynamics[x][y]:
            print "This tile already occupied, unit cannot deploy here", x, y, unit.type
            return False
            
        
    def putUnit(self, unit ):
        if not self.canUnitFitHere(unit):
            self._dynamics[ int(unit.pos[0]) ][ int(unit.pos[1]) ] = ( DYNAMICS_UNIT, unit.id )
            return True
        
        return False
        
    def removeUnit(self, unit ):
        self._dynamics[ int(unit.pos[0]) ][ int(unit.pos[1]) ] = None
        
        
    def getDynamic(self, x, y):
        return self._dynamics[int(x)][int(y)]

    
    def getHeight(self, pos ):
        return self._level_data[ int(pos[0]) ][ int(pos[1]) ]


    def opaque(self, x, y, z):
        if self._level_data[ int(x) ][ int(y) ] <= z: 
            return False
        return True
    
    
    