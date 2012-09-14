import math
from share import MASK_UP_RIGHT

def linija_od_nulexy( x1, y1 ):
    lista_tocaka = []
    y_x =float(y1) / x1
    D = y_x - 0.5
    x = 0
    y = 0
    lista_tocaka.append( (0, 0) )
    print (x,y),",",D 
    for x in xrange( 1, x1+1 ):
        if D>0:
            y += 1
            D -= 1
        D += y_x
        lista_tocaka.append( (x,y) )
        print (x,y),",",D 
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

def signum( num ):
    if( num < 0 ): 
        return -1
    elif( num >= 0 ):
        return 1
    
def orig_linija( t1, t2, level ):
    x1, y1 = t1
    x2, y2 = t2
    
    if x1 == x2 and y1 == y2:
        return [t1]
    
    absx0 = int(math.fabs(x2-x1))
    absy0 = int(math.fabs(y2-y1))
    
    sgnx0 = signum(x2-x1)
    sgny0 = signum(y2-y1)
    
    x = x1
    y = y1
    
    li = [(x,y)]
    
    if absx0 > absy0:
        y_x = float(absy0)/absx0
        D = y_x - 0.5
        #print "y_x =", y_x, "    y_x_2=", y_x/2
        for i in xrange( absx0 ):
            lastx = x
            lasty = y
            #print "D:",D
            if D>0:
                y += sgny0
                D -= 1
            x += sgnx0
            D += y_x
            if level.opaque(x,y,1) or not checkGridVisibility((x,y), (lastx,lasty), level):
                return []
            li.append((x,y))
        
    else:
        x_y = float(absx0)/absy0
        D = x_y - 0.5
        for i in xrange( absy0 ):
            lastx = x
            lasty = y
            if D>0:
                x+=sgnx0
                D-=1
            y+=sgny0
            D+=x_y
            if level.opaque(x,y,1) or not checkGridVisibility((x,y), (lastx,lasty), level):
                return []
            
            li.append((x,y))
            
    return li


def getTiles2DCilindar( t1, t2, level ):
    x1, y1 = t1
    x2, y2 = t2
    
    #we see ourself
    if( t1 == t2 ):
        return [ (x1,y1) ]
    
    absx0 = math.fabs(x2 - x1);
    absy0 = math.fabs(y2 - y1);
    
    list_visible_tiles = [ (x1,y1) ]
    
    x = int( x1 )
    y = int( y1 )

    
    if( absx0 > absy0 ):
        sgny0 = signum( y2 - y1 )
        sgnx0 = signum( x2 - x1 )
        y_x = absy0/absx0            
        D = y_x -0.5

        for i in xrange( int( absx0 ) ): #@UnusedVariable
            
            _y_p_1 = y+1 
            if not level.outOfBounds( x, _y_p_1 ):
                list_visible_tiles.append( (x, _y_p_1) )
            
            _y_1 = y-1
            if not level.outOfBounds( x, _y_1 ):
                list_visible_tiles.append( (x, _y_1) )
            
            if( D > 0 ):
                y += sgny0
                D -= 1
                
            x += sgnx0
            D += y_x

            #its visible add it to list            
            list_visible_tiles.append( (x, y) )
            
    #//(y0 >= x0)            
    else:
        sgnx0 = signum( x2 - x1 )
        sgny0 = signum( y2 - y1 )
        x_y = absx0/absy0
        D = x_y -0.5;
        
        for i in xrange( int( absy0 ) ): #@UnusedVariable
            
            _x_p_1 = x+1
            if not level.outOfBounds( _x_p_1, y ):
                list_visible_tiles.append( (_x_p_1, y) )

            _x_1 = x-1
            if not level.outOfBounds( _x_1, y ):
                list_visible_tiles.append( (_x_1, y) )
            
            if( D > 0 ):
                x += sgnx0
                D -= 1
            
            y += sgny0
            D += x_y
            
            #its clear, add it to visible list
            list_visible_tiles.append( (x, y) )


    #special case for last square
    if absx0 > absy0:
        if absy0 != 0:
            list_visible_tiles.append( (x, y-sgny0) )
    else:
        if absx0 != 0:
            list_visible_tiles.append( (x-sgnx0, y) )

    return list_visible_tiles


def cilindar(t1, t2, level):    
    x1,y1 = t1
    x2,y2 = t2
        
    dx = x2 - x1
    dy = y2 - y1
     
    d = math.sqrt(  math.pow(dx, 2) + math.pow(dy, 2)  )
    
    if d == 0:
        return 1
    
    alfa = math.degrees( math.atan( 0.5 / d ) )    


    mid = math.degrees( math.atan2( float(dy),dx ) )

    left = mid + alfa
    right = mid - alfa        
    orig_angle = left - right 
    

    for x,y in getTiles2DCilindar(t1, t2, level): 
        if level.opaque( x,y, 1):
            _x = x-x1
            _y = y-y1
            _xy = level.getMask( _x, _y )
            
            if _x < 0 and _y == 0:
                if mid > 0:
                    mini = _xy[MASK_UP_RIGHT]                    
                    maxi = _xy[MASK_DOWN_RIGHT]+360
                else:
                    mini = _xy[MASK_UP_RIGHT]-360
                    maxi = _xy[MASK_DOWN_RIGHT]
            else:
                mini = _xy[MASK_MIN]
                maxi = _xy[MASK_MAX]
                
            if left > mini and left < maxi:
                left = mini
            if right > mini and right < maxi:
                right = maxi
                
            if left <= right:
                return 0
    
    visible_angle = left - right
    return visible_angle/orig_angle
    

#cilindar( (0,0), (4,3) )
#print getTiles2DCilindar( (2,2), (5,2)  )
#linija_od_nulexy( 7,5 )
#print linija_od_nule( 4,8 )

#print linija( (0,0), (8,1) )
#li = linija( (8,4), (0,0) )
#li.reverse()
#print li

#exit(0)




#level = Level('../server/data/levels/l1.txt')
#print getTiles2DCilindar( (2, 0), (3, 7), level)
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
        base.accept('y', self.getInvisible3d)
        
        base.accept('1', self.setMode1)
        base.accept('2', self.setMode2)
        base.accept('3', self.setMode3)
        
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
        
        self.getInvisible3d()
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
    
    def setMode1(self):
        self.mode = 1
        self.getInvisible3d()
        self.displayLos()

    def setMode2(self):
        self.mode = 2
        self.getInvisible3d()
        self.displayLos()

    def setMode3(self):
        self.mode = 3
        self.getInvisible3d()
        self.displayLos()
        self.writeNumbers({(0,0):2,(0,1):2.3})

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
                
                
                
                """
                self.unit_renderer.node.setPos(int(pos3d.x)+0.5, int(pos3d.y)+0.5, 0)
                unit_dict = {}
                unit_dict['pos'] = (int(pos3d.x), int(pos3d.y))
                self.units.append( unit_dict )
                """
                
                self.getInvisible3d()
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

                self.getInvisible3d()
                self.displayLos()


    def getInvisible3d(self):
        #getTiles3D( (0,0,0), (2,0,1), self.level)
        d = levelInvisibility3d3d(self.units, self.level)
        t = loader.loadTexture('testercube.png')
        if self.node_3d != None:
            self.node_3d.removeNode()
            self.node_3d = self.node.attachNewNode('3dnode')
        if self.mode != 3:
            return
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
        #self.level_renderer.updateLevelLos({}, {})
        if self.mode == 1:
            self.cilin()    
        else:
            self.level_renderer.updateLevelLos(self.getInvisibleTiles(), self.getInvisibleWalls())
            
        #self.level_renderer.switchNodes()
        #self.level_renderer.flattenNodes()


    def orig(self):
        dic = {}
        
        for u in self.units:
            for x in xrange( self.level.maxX ):
                for y in xrange( self.level.maxY ):
                    for t in orig_linija(u['pos'], (x,y), self.level):
                        dic[t] = 1
        
        self.level_renderer.updateLevelLos(dic, {})
        

    def cilin(self):
        dic = {}

                                
        for unit in self.units:        
            for x in xrange( self.level.maxX ):
                for y in xrange( self.level.maxY ):
                    dic[(x,y)] = '{:.0%}'.format(cilindar( unit['pos'], (x,y), self.level)) 
        """
        x = 0
        y = 1
        dic[(x,y)] = '{:.2%}'.format(cilindar((2,4), (x,y), self.level))
        """
        """
        for unit in self.units:
            for y in xrange(8):
                dic[(x,y)] = '{:.2%}'.format(cilindar( unit['pos'], (x,y), self.level))
        """
        
        
        self.writeNumbers(dic)
        
        


tester = Tester(level_name='../server/data/levels/halls0.txt')
run()
