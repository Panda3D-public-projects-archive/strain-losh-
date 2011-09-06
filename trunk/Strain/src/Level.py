from panda3d.core import NodePath, CardMaker, Vec4
from pandac.PandaModules import Texture, TextureStage, TextureAttrib
from pandac.PandaModules import Geom, GeomNode, GeomVertexData, GeomTriangles, GeomVertexWriter, GeomVertexFormat

class Level:
    def __init__(self):
        self.x = self.y = 0
        self.node = NodePath('levelnode')
        self.wall_width = 1
        self.tex_count = 3
        self.row_data = []
        self.node_data = []

    def load(self, name):
        line_count = 0
        file = open('levels/'+name, "r")
        for line in file:
            line_count = line_count + 1
            if line_count == 1:
                s = line.split()
                self.x = int(s[0]); self.y = int(s[1])
            else:
                s = line.split(";")
                s = s[0:int(self.x)]
                self.row_data.append(s)
        file.close()
        self.row_data.reverse()

    def create(self):
        for x in xrange(0, self.x): 
            list = []
            for y in xrange(0, self.y): 
                tag = int(self.row_data[y][x])
                c = loader.loadModel("tile")
                c.setPos(x, y, 0)
                c.setTag("pos", "%(x)s-%(y)s" % {"x":x, "y":y})
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
