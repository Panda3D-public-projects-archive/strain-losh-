from panda3d.core import NodePath, Vec4
from direct.directtools.DirectGeometry import LineNodePath

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.zpos = 0.0
        self.visible = False
        self.node = NodePath('gridnode')
        self.border = LineNodePath(self.node, 'border', 4, Vec4(.2, .2, .2, 0))
        self.line = LineNodePath(self.node, 'line', 2, Vec4(.3, .3, .3, 0))

        leftdown = (0, 0, self.zpos)
        leftup = (0, self.height, self.zpos)
        rightdown = (self.width, 0, self.zpos)
        rightup = (self.width, self.height, self.zpos)
        midleft = (0, self.height/2, self.zpos)
        midright = (self.width, self.height/2, self.zpos)
        middown = (self.width/2, 0, self.zpos)
        midup = (self.width/2, self.height, self.zpos)

        self.border.drawLines([[leftdown, rightdown], [leftdown, leftup], [leftup, rightup], [rightdown, rightup], [midleft, midright], [middown, midup]])
        self.border.create()

        for i in range(0, self.width+1):
            for j in range(0, self.height+1):
                top = (i, j, self.zpos)
                bottom = (i, 0, self.zpos)
                left = (0, j, self.zpos)
                right = (i, j, self.zpos)
                self.line.drawLines([[top, bottom], [left, right]])
                self.line.create()

        self.node.flattenStrong()

    def show(self, rootnode):
        self.visible = True
        self.node.reparentTo(rootnode)
    
    def hide(self):
        self.visible = False
        self.node.reparentTo(hidden)