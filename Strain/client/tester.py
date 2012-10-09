from strain.visibility import *
import math
from panda3d.core import *
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase import DirectObject
from strain.renderer.levelrenderer import LevelRenderer
from strain.renderer.cameramanager import CameraManager
from strain.renderer.unitrenderer import UnitRenderer
from strain.renderer.coordrenderer import CoordRenderer
from strain.share import *
import strain.utils as utils
import direct.directbase.DirectStart
import random
from profilestats import profile
import zipfile
import cPickle as pickle
from strain.visibility import *


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
        self.mode = 1
        
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, ground_level))
        base.accept('mouse1', self.addUnit)
        #base.accept('mouse2', self.addUnit)
        
        base.accept('o', render.analyze)
        base.accept('i', render.ls)
        base.accept('c', self.displayLos)
        base.accept('1', self.setMode1)
        base.accept('2', self.setMode2)

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

    def setMode1(self):
        self.mode = 1
        self.displayLos()

    def setMode2(self):
        self.mode = 2
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


    def testDiff(self):

        diff_dic = {}
        
        ok = True
                
                
        for unit_x in xrange( self.level.maxX ):
            for unit_y in xrange( self.level.maxY ):
                
                if self.level.opaque( unit_x, unit_y, 1 ):
                    continue

                test_dic = {}
                #make test_dic
                for x in xrange( self.level.maxX ):
                    for y in xrange( self.level.maxY ):
                        perc = LOS( (unit_x, unit_y), (x,y), self.level )
                        if perc > VISIBILITY_MIN:
                            test_dic[ (x,y) ] = perc
                
                print "\n\nview from:", ( unit_x, unit_y )
                self.units = []
                unit_dict = {}
                unit_dict['pos'] = ( unit_x, unit_y )
                self.units.append( unit_dict )
                
                t = time.clock()        
                dic3 = levelVisibilityDictPercent(self.units, self.level)
                t2 = time.clock()
                print "dic3 timer:::", (t2-t)*1000, "ms"
                #print "dic3:", dic3

                """
                #ispis test_dicta
                test2_dic = {}                
                for tile in test_dic.keys():
                    #test_dic[tile] = float( test_dic[tile] )
                    test2_dic[tile] = '{0:2.0%}'.format(test_dic[tile])
                self.writeNumbers(test2_dic)
                """
                
                for x in xrange( self.level.maxX ):
                    #for y in xrange( x ):
                    for y in xrange( self.level.maxY ):
                        
                        t = (x,y)
                        
                        if t in test_dic:
                            if t not in dic3:
                                print "fali u dic3:", t, "LOS:", LOS((unit_x,unit_y), t, self.level)
                                ok = False
                                #return
                            else:     
                                if test_dic[t] != dic3[t]:
                                    diff = test_dic[t]-dic3[t]
                                    if diff > 0.0001:                                            
                                        diff_dic[t] = (test_dic[t], dic3[t])
                                        print "diff: ", t, " test_dict:",test_dic[t], "  dic3:", dic3[t], "   d:",diff
                                        #ok = False
                                        #return                                    
                            
                        if t in dic3:
                            if not t in test_dic:
                                print "viska u dic3:", t, "dic3:", dic3[t], "LOS:", LOS((unit_x,unit_y), t, self.level)
                                ok = False
                                #return                                 
                        
            
                #break
                if not ok:
                    return
    
        if ok:
            print "sve ok"
        else:
            print "NIJE OKKK!!!!"

    def cilin(self):


        #p = LOS( (0,20), (12,21), self.level )
        #print p
        #return

        self.testDiff()
        
        t = time.clock()        
        dic3 = levelVisibilityDictPercent(self.units, self.level)
        t2 = time.clock()        

            
        if dic3:
            vis_list = []
            invis_list = []
            for tile in dic3.keys():
                if dic3[tile]> VISIBILITY_MIN:
                    vis_list.append(tile)
                    #dic3[tile] = 1
                    #diff_dic[tile] = '{0:2.0%}'.format(diff_dic[tile])
                    dic3[tile] = '{0:2.0%}'.format(dic3[tile])
                    #del( diff_dic[tile] )
                else:
                    invis_list.append(tile)
                    #diff_dic[tile] = '{0:2.0%}'.format(diff_dic[tile])
                    #del( dic3[tile] )

                    
            #print "-------visible:", vis_list
            #print "invis:", invis_list
        if self.mode == 1:
            self.writeNumbers(dic3)


                
        """
        t = time.clock()
        dic3 = levelVisibilityDict(self.units, self.level)
        t2 = time.clock()
        print "levelvis timer:::", (t2-t)*1000, "ms"
        
        self.writeNumbers(dic3)        
        return 
        """
        


#tester = Tester(level_name='../server/data/levels/l1.txt')
tester = Tester(level_name='../server/data/levels/assassins.txt')
#tester = Tester(level_name='../server/data/levels/assassins2.txt')
#tester = Tester(level_name='../server/data/levels/level2.txt')
run()
