from direct.showbase import DirectObject
from panda3d.core import Plane, Vec3, Vec2, Point3, Point2
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from pandac.PandaModules import GeomNode, CardMaker
import math


class Interface(DirectObject.DirectObject):
    def __init__(self):
        
        base.disableMouse()
        self.mx = 0
        self.my = 0
        self.is_orbiting = False
        self.target = Vec3(0, 0, 0)
        self.cam_dist = 40
        self.pan_rate_div = 20
        self.pan_limits_x = Vec2(-30, 30) 
        self.pan_limits_y = Vec2(-30, 30)
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        base.camera.setPos(10, 10, 20)
        base.camera.lookAt(10, 10, 0)
        self.orbit(0, 0)

        self.accept('w', self.event, ['up', 1])
        self.accept('w-up', self.event, ['up', 0])
        self.accept('s', self.event, ['down', 1])
        self.accept('s-up', self.event, ['down', 0])                   
        self.accept('a', self.event, ['left', 1])
        self.accept('a-up', self.event, ['left', 0])
        self.accept('d', self.event, ['right', 1])
        self.accept('d-up', self.event, ['right', 0])  
        self.accept("mouse3", self.start_orbit)
        self.accept("mouse3-up", self.stop_orbit)
        self.accept("wheel_up", lambda : self.adjust_cam_dist(0.9))
        self.accept("wheel_down", lambda : self.adjust_cam_dist(1.1))
        
        self.keys = {}
        self.keys['up'] = 0
        self.keys['down'] = 0        
        self.keys['left'] = 0
        self.keys['right'] = 0
        self.keys['middle'] = 0
        self.keys['wheel_up'] = 0
        self.keys['wheel_down'] = 0
    
        taskMgr.add(self.update_camera, 'update_camera_task')
        taskMgr.add(self.debug, 'interface_debug_task')
        
    def get_mouse_pos(self):
        if base.mouseWatcherNode.hasMouse(): 
            return base.mouseWatcherNode.getMouse() 
        return None
    
    def get_mouse_grid_coordinates(self):
        mpos = self.get_mouse_pos()
        pos3d = Point3()
        nearPoint = Point3()
        farPoint = Point3()
        base.camLens.extrude(mpos, nearPoint, farPoint)
        if self.plane.intersectsLine(pos3d,
                render.getRelativePoint(camera, nearPoint),
                render.getRelativePoint(camera, farPoint)):
            x = pos3d.getX()
            y = pos3d.getY()
            if x >= 0 and y >= 0:
                return int(x), int(y)
            else:
                return None
        return None
    
    def set_target(self, x, y, z):
        x = self.clamp(x, self.pan_limits_x.getX(), self.pan_limits_x.getY())
        self.target.setX(x)
        y = self.clamp(y, self.pan_limits_y.getX(), self.pan_limits_y.getY())
        self.target.setY(y)
        self.target.setZ(z)
        
    def clamp(self, val, min_val, max_val): 
        return min(max(val, min_val), max_val)

    def adjust_cam_dist(self, factor):
        self.cam_dist = self.cam_dist * factor
        self.orbit(0, 0)
    
    def start_orbit(self): 
        self.is_orbiting = True
        
    def stop_orbit(self):
        self.is_orbiting = False 
    
    def orbit(self, delta_x, delta_y):
        new_cam_hpr = Vec3() 
        new_cam_pos = Vec3()
        cam_hpr = base.camera.getHpr()  
          
        new_cam_hpr.setX(cam_hpr.getX() + delta_x) 
        new_cam_hpr.setY(self.clamp(cam_hpr.getY() - delta_y, -85, -10)) 
        new_cam_hpr.setZ(cam_hpr.getZ())
          
        base.camera.setHpr(new_cam_hpr)  
          
        radian_x = new_cam_hpr.getX() * (math.pi / 180.0) 
        radian_y = new_cam_hpr.getY() * (math.pi / 180.0)  
          
        new_cam_pos.setX(self.cam_dist * math.sin(radian_x) * math.cos(radian_y) + self.target.getX())
        new_cam_pos.setY(-self.cam_dist * math.cos(radian_x) * math.cos(radian_y) + self.target.getY()) 
        new_cam_pos.setZ(-self.cam_dist * math.sin(radian_y) + self.target.getZ()) 
        base.camera.setPos(new_cam_pos.getX(), new_cam_pos.getY(), new_cam_pos.getZ())                     
        base.camera.lookAt(self.target.getX(), self.target.getY(), self.target.getZ()) 
    
    def event(self, button, value):
        self.keys[button] = value
    
    def update_camera(self, task): 
        mpos = self.get_mouse_pos()
        if mpos != None:
            if self.is_orbiting:
                self.orbit((self.mx - mpos.getX()) * 100, (self.my - mpos.getY()) * 100)
            else: 
                move_x = False
                move_y = False
                if self.keys['down']: 
                    rad_x1 = base.camera.getH() * (math.pi / 180.0) 
                    pan_rate1 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_y = True 
                if self.keys['up']: 
                    rad_x1 = base.camera.getH() * (math.pi / 180.0) + math.pi 
                    pan_rate1 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_y = True 
                if self.keys['left']: 
                    rad_x2 = base.camera.getH() * (math.pi / 180.0) + math.pi * 0.5 
                    pan_rate2 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_x = True
                if self.keys['right']: 
                    rad_x2 = base.camera.getH() * (math.pi / 180.0) - math.pi*0.5 
                    pan_rate2 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_x = True 
                
                if move_y: 
                    temp_x = self.target.getX() + math.sin(rad_x1) * pan_rate1 
                    temp_x = self.clamp(temp_x, self.pan_limits_x.getX(), self.pan_limits_x.getY()) 
                    self.target.setX(temp_x) 
                    temp_y = self.target.getY() - math.cos(rad_x1) * pan_rate1 
                    temp_y = self.clamp(temp_y, self.pan_limits_y.getX(), self.pan_limits_y.getY()) 
                    self.target.setY(temp_y) 
                    self.orbit(0, 0) 
                if move_x: 
                    temp_x = self.target.getX() - math.sin(rad_x2) * pan_rate2 
                    temp_x = self.clamp(temp_x, self.pan_limits_x.getX(), self.pan_limits_x.getY()) 
                    self.target.setX(temp_x) 
                    temp_y = self.target.getY() + math.cos(rad_x2) * pan_rate2 
                    temp_y = self.clamp(temp_y, self.pan_limits_y.getX(), self.pan_limits_y.getY()) 
                    self.target.setY(temp_y) 
                    self.orbit(0, 0)
            #print(self.target) 
            self.mx = mpos.getX()
            self.my = mpos.getY()
        return task.cont

    def debug(self, task):
        None
        return task.cont


class clPickerTool(DirectObject.DirectObject):
    def __init__(self): 
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        traverser = CollisionTraverser()
        self.tr = traverser
        collisionhandler = CollisionHandlerQueue()
        self.cHandQ = collisionhandler
        pickerNode = CollisionNode('mouseRay')
        pickerNP = base.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        pickerRay = CollisionRay()
        self.pr = pickerRay
        pickerNode.addSolid(pickerRay)
        self.tr.addCollider(pickerNP, self.cHandQ)
      
        cm = CardMaker('tile') 
        cm.setFrame(0, base.tile_size, 0, base.tile_size) 
        self.select_tile = render.attachNewNode(cm.generate())
        self.select_tile.setPos(0, 0, 0)
        self.select_tile.setColor(1, 0, 0)
        self.select_tile.lookAt(0, 0, -1)
        
        cmMT = CardMaker('movetile')
        cmMT.setFrame(0, base.tile_size, 0, base.tile_size) 
        self.move_tile = render.attachNewNode(cmMT.generate())
        self.move_tile.setPos(0, 0, 0)
        self.move_tile.lookAt(0, 0, -1)        
        self.move_tile.hide()
        
        self.mouse_tile = Point3()
        self.last_mouse_tile = None
      
        self.accept('mouse1', self.PickObject)
        taskMgr.add(self.GetMousePos,'GetMousePosTask')    
    
    def hide_move_tile(self):
        self.move_tile.setPos(0, 0, -50)
        self.move_tile.hide()
    
    def GetMousePos(self, task): 
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse() 
            pos3d = Point3() 
            nearPoint = Point3() 
            farPoint = Point3() 
            base.camLens.extrude(mpos, nearPoint, farPoint) 
            if self.plane.intersectsLine(pos3d, render.getRelativePoint(camera, nearPoint), render.getRelativePoint(camera, farPoint)): 
                x = pos3d.getX()
                y = pos3d.getY()
                if x >= 0 and x < base.level.x and y >= 0 and y < base.level.y:
                    self.mouse_tile = Point3(int(x), int(y), 0)
                else:
                    self.mouse_tile = None
            if base.game_state['movement'] == 1 and base.picked_unit != None and self.mouse_tile != None:
                if self.mouse_tile != self.last_mouse_tile:
                    self.last_mouse_tile = self.mouse_tile
                    for i in base.picked_unit.closed_tile_list:
                        if self.mouse_tile.x == i[0].x and self.mouse_tile.y == i[0].y:
                            if base.picked_unit.current_AP - i[2] >= 2:
                                self.move_tile.setColor(0, 1, 0)
                            else:
                                self.move_tile.setColor(0, 0, 1)
                            self.move_tile.setPos(self.mouse_tile)
                            self.move_tile.show()
                            break
                        else:
                            self.move_tile.hide()
            #print base.gameState['movement'], base.pickedUnit
        return task.again 
      
    def PickObject(self):
        if base.mouseWatcherNode.hasMouse():
            if base.game_state['movement'] == 0:
                old_picked_unit = base.picked_unit
                pickedObj = None
                base.picked_unit = None
                mpos = base.mouseWatcherNode.getMouse()
                self.pr.setFromLens(base.camNode, mpos.getX(), mpos.getY())
                self.tr.traverse(render)
                if self.cHandQ.getNumEntries() > 0:
                    # This is so we get the closest object.
                    self.cHandQ.sortEntries()
                    pickedObj = self.cHandQ.getEntry(0).getIntoNodePath()
                    if pickedObj.findNetTag('Unit').getTag('Unit') == 'true' and base.game_state['movement'] == 0:
                        base.picked_unit = base.units[pickedObj.findNetTag('Name').getTag('Name')]
                        pos = base.calc_world_pos(base.picked_unit.model.getPos())
                        self.select_tile.setPos(pos)
                
                if pickedObj == None and self.mouse_tile != None:
                    x = floor(self.mouse_tile.x)
                    y = floor(self.mouse_tile.y)
                    if x >= base.level.x * -base.tile_size and x < base.level.x * base.tile_size and y >= base.level.y * -base.tile_size and y < base.level.y * base.tile_size:
                        self.select_tile.setPos(floor(self.mouse_tile.x), floor(self.mouse_tile.y), 0)
                        for u in base.units.itervalues():
                            base.picked_unit = None
                            if base.calc_world_pos(u.model.getPos()) == self.select_tile.getPos():
                                base.picked_unit = u
                                break 
                
                if base.picked_unit != None and base.picked_unit != old_picked_unit:
                    base.picked_unit.model.play('selected')
                    base.picked_unit.talk('select')
            else:
                dest = Point2(self.mouse_tile.x, self.mouse_tile.y)
                base.picked_unit.move(dest)
                base.toggle_state('movement')
                
