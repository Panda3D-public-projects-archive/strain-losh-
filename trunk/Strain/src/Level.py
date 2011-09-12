class Level:
    def __init__(self, name):
        self.maxX = self.maxY = 0
        self._level_data = []
        
        self.load(name)

    def load(self, name):
        line_count = 0
        file = open('levels/'+name, "r")
        for line in file:
            line_count = line_count + 1
            if line_count == 1:
                s = line.split()
                self.maxX = int(s[0]); self.maxY = int(s[1])
            else:
                s = line.split(";")
                s = s[0:self.maxX]
                self._level_data.append(s)
           
        file.close()
        self._level_data.reverse()
        
        #convert entries in _level_data from string to integer AND change x-y order
        tmp = [[None] * self.maxY for i in xrange(self.maxX)]
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._level_data[j][i] = int( self._level_data[j][i] )
                tmp[i][j] = self._level_data[j][i]
        self._level_data = tmp 

