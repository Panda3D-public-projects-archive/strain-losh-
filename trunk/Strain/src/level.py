from pandac.PandaModules import Point2#@UnresolvedImport

LEVELS_ROOT = "./data/levels/"

class Level:
        
    def __init__(self, name):        
        self.name = LEVELS_ROOT + name    
        self.maxX = 0
        self.maxY = 0
        self._level_data = []    
        
        self.load(self.name)        

        self.center = Point2( self.maxX / 2, self.maxY / 2 )

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

