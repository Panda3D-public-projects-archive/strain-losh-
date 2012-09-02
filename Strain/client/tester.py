from panda3d.core import *
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase import DirectObject
from strain.renderer.levelrenderer import LevelRenderer
from strain.renderer.cameramanager import CameraManager
from strain.renderer.unitrenderer import UnitRenderer
from strain.share import Level
import strain.utils as utils
from strain.share import *
import direct.directbase.DirectStart
import random

import os, sys
lib_path = os.path.abspath('server/src')
sys.path.append(lib_path)
from unit import Unit


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
        
        self.unit_renderer.loadForTester(1, 1, 'marine_common', 0, 0, utils.HEADING_N)
        unit_dict = {}
        unit_dict['pos'] = (0,0)
        self.units.append(unit_dict)

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


    def getInvisibleTiles(self):
        t = time.clock()
        l = levelVisibilityDict(self.units, self.level)
        print "tiles timer:::", (time.clock()-t)*1000
        return l
    
    def getInvisibleWalls(self):
        t = time.clock()
        l = visibleWalls(self.units, self.level)
        print "walls timer:::", (time.clock()-t)*1000
        return l
        
    def displayLos(self):
        self.level_renderer.updateLevelLos(self.getInvisibleTiles(), self.getInvisibleWalls())
        #self.level_renderer.switchNodes()
        #self.level_renderer.flattenNodes()

tester = Tester(level_name='../server/data/levels/level2.txt')
run()
