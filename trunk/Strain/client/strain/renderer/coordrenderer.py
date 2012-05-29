from panda3d.core import *

class CoordRenderer():    
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.display = False
        self.node = None
       
    def redraw(self, x, y, tile_size, zpos):
        if self.node != None:
            self.node.removeNode()
        self.node = self.parent_node.attachNewNode('CoordRendererNode')
        offset = tile_size/2
        for i in xrange(0, x):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i*tile_size+offset, -offset, zpos)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i*tile_size+offset, y*tile_size+offset, zpos)
            tnp.setBillboardPointEye()
            tnp.setLightOff()            
        for i in xrange(0, y):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(-offset, i*tile_size+offset, zpos)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(x*tile_size+offset, i*tile_size+offset, zpos)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
            
    def toggle(self):
        if not self.display:
            self.node.reparentTo(self.parent_node)
            self.display = True
    
        else:
            self.node.detachNode()
            self.display = False   
            
    def cleanup(self):
        self.node.removeNode()         
    