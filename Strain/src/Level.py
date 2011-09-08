from panda3d.core import NodePath, CardMaker, Vec4
from pandac.PandaModules import Texture, TextureStage, TextureAttrib
from pandac.PandaModules import Geom, GeomNode, GeomVertexData, GeomTriangles, GeomVertexWriter, GeomVertexFormat

class Level:
    def __init__(self):
        self.maxX = self.maxY = 0
        self.node = NodePath('levelnode')
        self.wall_width = 1
        self.tex_count = 3
        self._level_data = []
        self.node_data = []
        self.game_data = []

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
        tmp = [[None] * self.maxX for i in xrange(self.maxY)]
        for i in range( 0, self.maxX ):
            for j in range( 0, self.maxY ):
                self._level_data[j][i] = int( self._level_data[j][i] )
                tmp[i][j] = self._level_data[j][i]
        self._level_data = tmp 
        
        
        self.game_data = [[None] * self.maxX for i in xrange(self.maxY)]

    def create(self):
        for x in xrange(0, self.maxX): 
            list = []
            for y in xrange(0, self.maxY): 
                tag = self._level_data[x][y]
                c = loader.loadModel("tile")
                c.setPos(x, y, 0)
                c.setTag("pos", "%(maxX)s-%(maxY)s" % {"maxX":x, "maxY":y})
                list.append(c) 
                if tag != 0:
                    c.setScale(1, 1, tag)
                    coef = 1 + 0.05*tag
                    c.setColorScale(coef, coef, coef, 1)
                c.reparentTo(render)
            self.node_data.append(list)
                    
    def show(self, rootnode):
        self.node.reparentTo(rootnode)
    
    def hide(self):
        self.node.reparentTo(hidden)
