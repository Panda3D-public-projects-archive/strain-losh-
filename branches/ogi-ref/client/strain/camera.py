from direct.showbase import DirectObject
from panda3d.core import Point2, Vec3#@UnresolvedImport
import math

#===============================================================================
# CLASS Camera --- DEFINITION
#===============================================================================
class Camera(DirectObject.DirectObject):    
    
    def __init__(self, camera, mwn, maxX, maxY, taskMgr):
        self.camera = camera
        self.mwn = mwn
        
        self.mx = 0
        self.my = 0
        self.is_orbiting = False
        self.target = Vec3(0, 0, 0)
        self.cam_dist = 40
        self.pan_rate_div = 20
        self.pan_limits_x = Point2(-5, maxX + 5) 
        self.pan_limits_y = Point2(-5, maxY + 5)
        self.camera.setPos(10, 10, 20)
        self.camera.lookAt(10, 10, 0)
        self.orbit(0, 0)
    
        self.accept('w', self.setKey, ['up', 1])
        self.accept('w-up', self.setKey, ['up', 0])
        self.accept('s', self.setKey, ['down', 1])
        self.accept('s-up', self.setKey, ['down', 0])                   
        self.accept('a', self.setKey, ['left', 1])
        self.accept('a-up', self.setKey, ['left', 0])
        self.accept('d', self.setKey, ['right', 1])
        self.accept('d-up', self.setKey, ['right', 0])
        self.accept("mouse3", self.startOrbit)
        self.accept("mouse3-up", self.stopOrbit)
        self.accept("wheel_up", lambda : self.adjustCamDist(0.9))
        self.accept("wheel_down", lambda : self.adjustCamDist(1.1))
        
        self.keys = {}
        self.keys['up'] = 0
        self.keys['down'] = 0        
        self.keys['left'] = 0
        self.keys['right'] = 0
        self.keys['middle'] = 0
        self.keys['wheel_up'] = 0
        self.keys['wheel_down'] = 0
        
        taskMgr.add(self.updateCamera, 'updateCamera_task')

    def setKey(self, button, value):
        """Sets the state of keyboard.
           1 = pressed
           0 = depressed
        """
        self.keys[button] = value
    
    def setTarget(self, x, y, z):
        """Sets the target point which will be the center of camera view.""" 
        x = self.clamp(x, self.pan_limits_x.getX(), self.pan_limits_x.getY())
        self.target.setX(x)
        y = self.clamp(y, self.pan_limits_y.getX(), self.pan_limits_y.getY())
        self.target.setY(y)
        self.target.setZ(z)
        
    def clamp(self, val, min_val, max_val):
        """If val > min_val and val < max_val returns val
           If val <= min_val returns min_val
           If val >= max_val returns max_val
        """
        return min(max(val, min_val), max_val)

    def adjustCamDist(self, factor):
        """Adjusts distance from the camera to the level. Used for zooming of the camera."""
        self.cam_dist = self.cam_dist * factor
        self.orbit(0, 0)
    
    def startOrbit(self): 
        """Sets camera is orbiting flag.
           Fires when right mouse button is pressed.
        """
        self.is_orbiting = True
            
    def stopOrbit(self):
        """Clears camera is orbiting flag.
           Fires when right mouse button is depressed.
        """
        self.is_orbiting = False 
    
    def orbit(self, delta_x, delta_y):
        """Handles camera orbiting (turning around camera target)."""
        new_cam_hpr = Vec3() 
        new_cam_pos = Vec3()
        cam_hpr = self.camera.getHpr()  
          
        new_cam_hpr.setX(cam_hpr.getX() + delta_x) 
        new_cam_hpr.setY(self.clamp(cam_hpr.getY() - delta_y, -85, -10)) 
        new_cam_hpr.setZ(cam_hpr.getZ())
          
        self.camera.setHpr(new_cam_hpr)  
          
        radian_x = new_cam_hpr.getX() * (math.pi / 180.0) 
        radian_y = new_cam_hpr.getY() * (math.pi / 180.0)  
          
        new_cam_pos.setX(self.cam_dist * math.sin(radian_x) * math.cos(radian_y) + self.target.getX())
        new_cam_pos.setY(-self.cam_dist * math.cos(radian_x) * math.cos(radian_y) + self.target.getY()) 
        new_cam_pos.setZ(-self.cam_dist * math.sin(radian_y) + self.target.getZ()) 
        self.camera.setPos(new_cam_pos.getX(), new_cam_pos.getY(), new_cam_pos.getZ())                     
        self.camera.lookAt(self.target.getX(), self.target.getY(), self.target.getZ()) 
        
    def updateCamera(self, task):
        """Task to update position of camera.""" 
        if self.mwn.hasMouse(): 
            mpos = self.mwn.getMouse()
            if self.is_orbiting:
                self.orbit((self.mx - mpos.getX()) * 100, (self.my - mpos.getY()) * 100)

            move_x = False
            move_y = False
            if self.keys['down']: 
                rad_x1 = self.camera.getH() * (math.pi / 180.0) 
                pan_rate1 = 0.2 * self.cam_dist / self.pan_rate_div 
                move_y = True 
            if self.keys['up']: 
                rad_x1 = self.camera.getH() * (math.pi / 180.0) + math.pi 
                pan_rate1 = 0.2 * self.cam_dist / self.pan_rate_div 
                move_y = True 
            if self.keys['left']: 
                rad_x2 = self.camera.getH() * (math.pi / 180.0) + math.pi * 0.5 
                pan_rate2 = 0.2 * self.cam_dist / self.pan_rate_div 
                move_x = True
            if self.keys['right']: 
                rad_x2 = self.camera.getH() * (math.pi / 180.0) - math.pi*0.5 
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

        