import math
from strain.visibility import LOS
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
from profilestats import profile
import zipfile
import cPickle as pickle


import os, sys
from zipfile import ZipFile
lib_path = os.path.abspath('server/src')
sys.path.append(lib_path)



loadPrcFile("./config/config.prc")
ground_level = 0
tile_size = 1.
base.setFrameRateMeter(True)

    
class Tester(DirectObject.DirectObject):
    def __init__(self, level_name):
        self.node = render.attachNewNode('RootNode')
        self.writenode = self.node.attachNewNode('')
        self.level = Level(level_name)
        self.level_renderer = LevelRenderer(self, self.node)
        self.level_renderer.create(self.level, self.level.maxX, self.level.maxY, tile_size, ground_level)
        #self.level_renderer.redrawLights()
        self.camera = CameraManager(self)
        self.units = []
        self.unit_renderer = UnitRenderer(self, self.node)
        self.unit_renderers = {}
        self.id_counter = 1
        
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, ground_level))
        base.accept('mouse1', self.addUnit)
        #base.accept('mouse2', self.addUnit)
        
        base.accept('o', render.analyze)
        base.accept('i', render.ls)
        base.accept('c', self.displayLos)

        """
        self.unit_renderer.loadForTester(1, 1, 'marine_common', 0, 0, utils.HEADING_N)
        unit_dict = {}
        unit_dict['pos'] = (0,0)
        self.units.append(unit_dict)
        """
        self.cr = CoordRenderer(self, self.node)
        self.cr.redraw(self.level.maxX, self.level.maxY, tile_size, ground_level)
        
        self.node_3d = self.node.attachNewNode('3dnode')

        b=OnscreenImage(parent=render2dp, image="galaxy1.jpg") #@UndefinedVariable
        #base.cam.node().getDisplayRegion(0).setSort(20)
        base.cam2dp.node().getDisplayRegion(0).setSort(-20)#@UndefinedVariable
        
        self.displayLos()

    def writeNumbers(self, d):
        for c in self.writenode.getChildren():
            c.removeNode()
        for i in d:
            t = TextNode('node name')
            t.setText( "%s" % d[i]) 
            tnp = self.writenode.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.3)
            tnp.setPos(i[0]+0.4, i[1]+0.4, 0.1)
            tnp.setBillboardPointEye()
            tnp.setLightOff()  


    def addUnit(self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            pos3d = Point3()
            nearPoint = Point3()
            farPoint = Point3()
            base.camLens.extrude(mpos, nearPoint, farPoint)
            if self.plane.intersectsLine(pos3d,render.getRelativePoint(camera, nearPoint),render.getRelativePoint(camera, farPoint)):
                
                
                id = None
                for u in self.unit_renderers.itervalues():
                    if int(u.node.getX()) == int(pos3d.x) and int(u.node.getY()) == int(pos3d.y):
                        id = int(u.id)
                        #u.cleanup()
                        u.node.removeNode()
                        break
                if id:
                    self.unit_renderers.pop(id)
                    unit_dict = {}
                    unit_dict['pos'] = (int(pos3d.x), int(pos3d.y))
                    self.units.remove(unit_dict)
                else:
                    if pos3d.x >= self.level.maxX or pos3d.y >= self.level.maxY or pos3d.x < 0 or pos3d.y < 0:
                        return
                    id = self.id_counter                
                    self.unit_renderers[self.id_counter] = UnitRenderer(self, self.node)
                    self.unit_renderers[self.id_counter].loadForTester(self.id_counter, 1, 'marine_common', int(pos3d.x), int(pos3d.y), utils.HEADING_N)
                    self.id_counter += 1
                    unit_dict = {}
                    unit_dict['pos'] = (int(pos3d.x), int(pos3d.y))
                    self.units.append(unit_dict)
                
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

                self.displayLos()


    def displayLos(self):
        self.cilin()

    @profile
    def cilin(self):
        
        pm = pickle.dumps(self.level.mask)
        
        print "mask size:", len( pm )
        
        import zlib
        zpm = zlib.compress( pm, 6 )
        print "ziped mask", len( zpm )
        
        pmz = zlib.decompress(zpm)
        print "compare", cmp( pm, pmz )
        
        return 0
        dic = {}

        t = time.clock()

        
        for unit in self.units:        
            for x in xrange( self.level.maxX ):
                for y in xrange( self.level.maxY ):
                    value = LOS( unit['pos'], (x,y), self.level)
                    if value == 0:
                        dic[(x,y)] = "" 
                    else:
                        dic[(x,y)] = '{:.0%}'.format(value) 
        """
        x = 3
        y = 5
        #dic[(x,y)] = '{:.2%}'.format(LOS((2,4), (x,y), self.level))
        """
        """
        for unit in self.units:
            #for y in xrange(8):
                dic[(x,y)] = '{:.2%}'.format(LOS( unit['pos'], (x,y), self.level))
        """
        t2 = time.clock()
        print "cilin timer:::", (t2-t)*1000, "ms"
        
        
        self.writeNumbers(dic)
        
        


tester = Tester(level_name='../server/data/levels/assassins2.txt')
run()
