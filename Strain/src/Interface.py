from direct.showbase import DirectObject
from panda3d.core import Plane, Vec4, Vec3, Vec2, Point3, Point2
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from pandac.PandaModules import GeomNode, CardMaker 
from pandac.PandaModules import Texture, TextureStage, RenderAttrib, DepthOffsetAttrib, TransparencyAttrib
from ResourceManager import UnitLoader
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
        self.pan_limits_x = Vec2(-5, 15) 
        self.pan_limits_y = Vec2(-5, 15)
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        base.camera.setPos(10, 10, 20)
        base.camera.lookAt(10, 10, 0)
        self.orbit(0, 0)
        
        self.hovered_tile = None
        self.selected_unit = None
        self.selected_unitmodel = None
        self.off_model = None
        self.selected_unit_tex = loader.loadTexture('sel.png')
        self.selected_unit_tile = None
        self.ts = TextureStage('ts')
        self.ts.setMode(TextureStage.MBlend)

        self.init_collision()

        self.accept('w', self.event, ['up', 1])
        self.accept('w-up', self.event, ['up', 0])
        self.accept('s', self.event, ['down', 1])
        self.accept('s-up', self.event, ['down', 0])                   
        self.accept('a', self.event, ['left', 1])
        self.accept('a-up', self.event, ['left', 0])
        self.accept('d', self.event, ['right', 1])
        self.accept('d-up', self.event, ['right', 0])
        self.accept("mouse1-up", self.mouse_left_click)
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
        
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
    
        taskMgr.add(self.update_camera, 'update_camera_task')
        taskMgr.add(self.hover, 'hover_task')

    def init_collision(self):
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        self.coll_trav = CollisionTraverser()
        self.coll_queue = CollisionHandlerQueue()
        self.coll_node = CollisionNode('mouse_ray')
        self.coll_nodepath = base.camera.attachNewNode(self.coll_node)
        self.coll_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.coll_ray = CollisionRay()
        self.coll_node.addSolid(self.coll_ray)
        self.coll_trav.addCollider(self.coll_nodepath, self.coll_queue)
    
    def find_object(self):
        pos = self.get_mouse_pos()
        if pos:
            self.coll_ray.setFromLens(base.camNode, pos.getX(), pos.getY())
            self.coll_trav.traverse(render)
            if self.coll_queue.getNumEntries() > 0:
                self.coll_queue.sortEntries()
                np = self.coll_queue.getEntry(0).getIntoNodePath()
                return np
        return None
     
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
            self.mx = mpos.getX()
            self.my = mpos.getY()
        return task.cont

    def mark_available_move_tile(self, nodepath):
        nodepath.setColorScale(2, 2, 2, 1)

    def mark_hovered_tile(self, nodepath, flag):
        if flag:
            nodepath.setColorScale(2, 2, 2, 1)
        else:
            nodepath.setColorScale(1, 1, 1, 1)

    def mark_selected_tile(self, nodepath, tex, color):
        self.ts.setColor(color)
        nodepath.setTexture(self.ts, tex)
        self.selected_unit_tile = nodepath
        
    def clear_selected_tile(self, nodepath):
        if nodepath:
            nodepath.setTextureOff(self.ts)
 
    def hover(self, task):
        np = self.find_object()
        if np:
            if self.hovered_tile != np:
                if self.hovered_tile:
                    self.mark_hovered_tile(self.hovered_tile, 0)
                self.mark_hovered_tile(np, 1)
                self.hovered_tile = np
        return task.cont 

    def select_unit(self, unit):
        self.deselect_unit()
        self.selected_unit = unit
        self.selected_unitmodel = base.graphics_engine.unit_models[unit.id]
        pos = self.selected_unitmodel.get_unit_grid_pos()
        if self.selected_unit.owner.name == 'ultramarinac':
            col = Vec4(1, 0, 0, 1)
        else:
            col = Vec4(0, 0, 1, 1)
        self.mark_selected_tile(base.graphics_engine.node_data[int(pos.x)][int(pos.y)], self.selected_unit_tex, col)
        ul = UnitLoader()
        self.off_model = ul.load(self.selected_unit.type, "off")
        self.off_model.reparentTo(base.graphics_engine.alt_render)
        self.off_model.setPos(0,-8,-1.7)
        self.off_model.play('idle02')
        #self.selected_unit.find_path()

    def deselect_unit(self):
        if self.selected_unit:
            self.clear_selected_tile(self.selected_unit_tile)
            if self.off_model:
                self.off_model.cleanup()
                self.off_model.remove()
            self.selected_unit = None
            self.selected_unitmodel = None
    
    def mouse_left_click(self):
        selected = self.find_object()
        if selected:
            node_type = selected.findNetTag("type").getTag("type")
            if node_type == "unit":
                unit_id = int(selected.findNetTag("id").getTag("id"))
                unit = base.engine.units[unit_id] 
                if self.selected_unit != unit:
                    self.select_unit(unit)
            elif node_type == "tile":
                p = selected.getParent().getPos()
                u = base.graphics_engine.unit_data[int(p.x)][int(p.y)]
                if u:
                    unit = base.engine.units[int(u.id)]
                else:
                    unit = None
                if unit:
                    if self.selected_unit != unit:
                        self.select_unit(unit)
                else:
                    pos = Point2(int(p.x), int(p.y))
                    #self.selected_unit.move(pos)

