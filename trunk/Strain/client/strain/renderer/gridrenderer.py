from panda3d.core import *

class GridRenderer():    
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.display = False
        self.node = None
        
    def redraw(self, x, y, tile_size, zpos, thickness=1.0, color=Vec4(0.96,0.64,0.37,1)):
        if self.node != None:
            self.node.removeNode()
        self.node = self.parent_node.attachNewNode('GridRendererNode')
        
        segs = LineSegs()
        segs.setThickness(thickness)
        segs.setColor(color)
        for i in xrange(x):
            segs.moveTo(i*tile_size, 0, zpos+0.05)
            segs.drawTo(i*tile_size, y*tile_size, zpos+0.05)
        for j in xrange(y):
            segs.moveTo(0, j*tile_size, zpos+0.05)
            segs.drawTo(x*tile_size, j*tile_size, zpos+0.05)
        self.node = NodePath(segs.create())
        #self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.node.setLightOff()
     
    def toggle(self):
        if not self.display:
            self.node.reparentTo(self.parent_node)
            self.display = True
        else:
            self.node.detachNode()
            self.display = False
            
    def cleanup(self):
        self.node.removeNode()