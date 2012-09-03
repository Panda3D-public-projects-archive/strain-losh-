import math

def linija_od_nulexy( x1, y1 ):
    lista_tocaka = []
    y_x =float(y1) / x1
    D = y_x - 0.5
    y = 0
    for x in xrange( x1 ):
        if D>0:
            y += 1
            D -= 1
        D += y_x
        lista_tocaka.append( (x,y) )
    lista_tocaka.append( (x1, y1) )
    return lista_tocaka
    

def linija_od_nule( x1, y1 ):
    lista_tocaka = []
    if x1 >= y1:
        y_x =float(y1) / x1
        D = y_x - 0.5
        y = 0
        for x in xrange( x1 ):
            if D>0:
                y += 1
                D -= 1
            D += y_x
            lista_tocaka.append( (x,y) )
        lista_tocaka.append( (x1, y1) )
    else:
        x_y =float(x1) / y1
        D = x_y - 0.5
        x = 0
        for y in xrange( y1 ):
            if D>0:
                x += 1
                D -= 1
            D += x_y
            lista_tocaka.append( (x,y) )
        lista_tocaka.append( (x1, y1) )
    return lista_tocaka

def sig( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1
    
def linija( t1, t2 ):
    x1, y1 = t1
    x2, y2 = t2
    absx0 = int(math.fabs(x2-x1))
    absy0 = int(math.fabs(y2-y1))
    
    sgnx0 = sig(x2-x1)
    sgny0 = sig(y2-y1)
    
    x = x1
    y = y1
    
    li = [(x,y)]
    
    if absx0 > absy0:
        y_x = float(absy0)/absx0
        D = y_x - 0.5
        print "y_x =", y_x, "    y_x_2=", y_x/2
        for i in xrange( absx0 ):
            print "D:",D
            if D>0:
                y += sgny0
                D -= 1
            x += sgnx0
            D += y_x
            li.append((x,y))
        
    else:
        x_y = float(absx0)/absy0
        D = x_y - 0.5
        for i in xrange( absy0 ):
            if D>0:
                x+=sgnx0
                D-=1
            y+=sgny0
            D+=x_y
            li.append((x,y))
            
    return li
    
#print linija_od_nulexy( 8,4 )
#print linija_od_nule( 4,8 )

#print linija( (0,0), (8,1) )
#li = linija( (8,4), (0,0) )
#li.reverse()
#print li

#exit(0)









from panda3d.core import *
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase import DirectObject
from strain.renderer.levelrenderer import LevelRenderer
from strain.renderer.cameramanager import CameraManager
from strain.renderer.unitrenderer import UnitRenderer
from strain.renderer.coordrenderer import CoordRenderer
from strain.share import Level
import strain.utils as utils
from strain.share import *
import direct.directbase.DirectStart
import random

import os, sys
lib_path = os.path.abspath('server/src')
sys.path.append(lib_path)


loadPrcFile("./config/config.prc")
ground_level = 0
tile_size = 1.
base.setFrameRateMeter(True)

    
    



class Tester(DirectObject.DirectObject):
    def __init__(self, level_name):
        self.node = render.attachNewNode('RootNode')
        self.level = Level(level_name)
        self.level_renderer = LevelRenderer(self, self.node)
        self.level_renderer.create(self.level, self.level.maxX, self.level.maxY, tile_size, ground_level)
        #self.level_renderer.redrawLights()
        self.camera = CameraManager(self)
        self.units = []
        self.unit_renderer = UnitRenderer(self, self.node)
        
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, ground_level))
        base.accept('mouse1', self.toggleUnit)
        base.accept('o', render.analyze)
        base.accept('i', render.ls)
        base.accept('c', self.displayLos)
        base.accept('y', self.getInvisible3d)
        
        self.unit_renderer.loadForTester(1, 1, 'marine_common', 0, 0, utils.HEADING_N)
        unit_dict = {}
        unit_dict['pos'] = (0,0)
        self.units.append(unit_dict)
        self.cr = CoordRenderer(self, self.node)
        self.cr.redraw(self.level.maxX, self.level.maxY, tile_size, ground_level)
        
        self.node_3d = self.node.attachNewNode('3dnode')

        b=OnscreenImage(parent=render2dp, image="galaxy1.jpg") #@UndefinedVariable
        #base.cam.node().getDisplayRegion(0).setSort(20)
        base.cam2dp.node().getDisplayRegion(0).setSort(-20)#@UndefinedVariable
        
        self.displayLos()

    def toggleUnit(self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            pos3d = Point3()
            nearPoint = Point3()
            farPoint = Point3()
            base.camLens.extrude(mpos, nearPoint, farPoint)
            if self.plane.intersectsLine(pos3d,render.getRelativePoint(camera, nearPoint),render.getRelativePoint(camera, farPoint)):
                self.unit_renderer.node.setPos(int(pos3d.x)+0.5, int(pos3d.y)+0.5, 0)
                unit_dict = {}
                unit_dict['pos'] = (int(pos3d.x), int(pos3d.y))
                self.units[0] = unit_dict


    def getInvisible3d(self):
        #getTiles3D( (0,0,0), (2,0,1), self.level)
        d = levelInvisibility3d3d(self.units, self.level)
        t = loader.loadTexture('testercube.png')
        if self.node_3d != None:
            self.node_3d.removeNode()
            self.node_3d = self.node.attachNewNode('3dnode')
        for i in d.iterkeys():
            m = loader.loadModel('cube')
            m.setScale(1,1,0.7)
            m.setTexture(t)
            m.setTransparency(TransparencyAttrib.MAlpha)
            m.setPos(i[0], i[1], i[2]*0.7)
            m.reparentTo(self.node_3d)
        
       

    def getInvisibleTiles(self):
        t = time.clock()

        l = levelVisibilityDict(self.units, self.level)
        t2 = time.clock()
        #print "tiles timer:::", (t2-t)*10, "ms"
        """
        t = time.clock()
        for i in xrange( 100 ):
            l = levelVisibilityDict(self.units, self.level)
        t2 = time.clock()
        print "tiles 100 call - timer:::", (t2-t)*10, "ms"
        """
        return l
    
    def getInvisibleWalls(self):
        t = time.clock()
        l = visibleWalls(self.units, self.level)
        #print "walls timer:::", (time.clock()-t)*1000
        return l
        
    def displayLos(self):
        self.level_renderer.updateLevelLos(self.getInvisibleTiles(), self.getInvisibleWalls())
        #self.level_renderer.switchNodes()
        #self.level_renderer.flattenNodes()

tester = Tester(level_name='../server/data/levels/level3.txt')
run()
