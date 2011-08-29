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

    def create2(self):
        for x in xrange(0, self.x): 
            for y in xrange(0, self.y): 
                tag = int(self.row_data[y][x])
                c = loader.loadModel("cube")
                c.setPos(x, self.y - y - 1, 0)
                if tag == 0:
                    ltag = 0.01
                else:
                    ltag = tag
                c.setScale(1, 1, ltag*0.2)
                #tex = loader.loadTexture('%i.png' % (tag+1))
                #c.setTexture(tex, 1) 
                c.setColor(0.2, 1-(tag*0.1), 0.2, 1)
                c.reparentTo(render)

    def create(self):
        tile_node = GeomNode("tilenode")
        geoms = []
        
        for i in xrange(self.tex_count): 
            gvd = GeomVertexData('name', GeomVertexFormat.getV3t2(), Geom.UHStatic) 
            geom = Geom(gvd) 
            prim = GeomTriangles(Geom.UHStatic) 
            vertex = GeomVertexWriter(gvd, 'vertex') 
            texcoord = GeomVertexWriter(gvd, 'texcoord') 
            tex = loader.loadTexture('%i.png' % (i+1)) 
            tex.setMagfilter(Texture.FTLinearMipmapLinear) 
            tex.setMinfilter(Texture.FTLinearMipmapLinear) 
            geoms.append({'geom':geom, 
                          'prim':prim, 
                          'vertex':vertex, 
                          'texcoord':texcoord, 
                          'index':0, 
                          'gvd':gvd, 
                          'texture':tex})

        for x in xrange(0, self.x): 
            for y in xrange(0, self.y): 
                t_img = int(self.row_data[y][x]) 
                i = geoms[t_img]['index'] 
                geoms[t_img]['vertex'].addData3f(x, y, 0) 
                geoms[t_img]['texcoord'].addData2f(0, 0) 
                geoms[t_img]['vertex'].addData3f(x, y+1, 0) 
                geoms[t_img]['texcoord'].addData2f(0, 1) 
                geoms[t_img]['vertex'].addData3f(x+1, y+1, 0) 
                geoms[t_img]['texcoord'].addData2f(1, 1) 
                geoms[t_img]['vertex'].addData3f(x+1, y, 0) 
                geoms[t_img]['texcoord'].addData2f(1, 0)
                # d: index displace, becouse we use one vertex pool for the all geoms 
                d = i * (self.tex_count + 1) 
                geoms[t_img]['prim'].addVertices(d, d + 2, d + 1) 
                geoms[t_img]['prim'].addVertices(d, d + 3, d + 2) 
                geoms[t_img]['index'] += 1 

        for i in xrange(2): 
            geoms[i]['prim'].closePrimitive() 
            geoms[i]['geom'].addPrimitive(geoms[i]['prim']) 
            tile_node.addGeom(geoms[i]['geom']) 
            tile_node.setGeomState(i, tile_node.getGeomState(i).addAttrib(TextureAttrib.make(geoms[i]['texture']))) 
        
        
        self.node.attachNewNode(tile_node)
                    
    def show(self, rootnode):
        self.node.reparentTo(rootnode)
    
    def hide(self):
        self.node.reparentTo(hidden)
