from panda3d.core import *
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

class Tester(DirectObject.DirectObject):
    def __init__(self, level_name):
        self.node = render.attachNewNode('RootNode')
        self.level = Level(level_name)
        self.level_renderer = LevelRenderer(self, self.node)
        self.level_renderer.create(self.level, self.level.maxX, self.level.maxY, tile_size, ground_level)
        self.camera = CameraManager(self)
        self.units = []
        self.unit_renderers = {}
        self.id_counter = 1
        
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, ground_level))
        base.accept('mouse2', self.toggleUnit)
        base.accept('o', render.analyze)
        base.accept('i', render.ls)
        base.accept('x', self.level_renderer.switchNodes)
        base.accept('c', self.displayLos)

    def toggleUnit(self):
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
                        u.cleanup()
                        u.node.removeNode()
                        break
                if id:
                    self.unit_renderers.pop(id)
                    unit_dict = {}
                    unit_dict['pos'] = (int(pos3d.x), int(pos3d.y))
                    self.units.remove(unit_dict)
                else:
                    id = self.id_counter                
                    self.unit_renderers[self.id_counter] = UnitRenderer(self, self.node)
                    self.unit_renderers[self.id_counter].loadForTester(self.id_counter, 1, 'marine_common', int(pos3d.x), int(pos3d.y), utils.HEADING_N)
                    self.id_counter += 1
                    unit_dict = {}
                    unit_dict['pos'] = (int(pos3d.x), int(pos3d.y))
                    self.units.append(unit_dict)
        print self.units

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
        self.level_renderer.switchNodes()
        self.level_renderer.updateLevelLos(self.getInvisibleTiles(), self.getInvisibleWalls())
        self.level_renderer.flattenNodes()

tester = Tester(level_name='../server/data/levels/base2.txt')
run()
