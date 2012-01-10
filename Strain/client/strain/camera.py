#############################################################################
# IMPORTS
#############################################################################

# python imports
import math

# panda3D imports
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import *
from direct.task import Task

# strain related imports
import utils as utils

#############################################################################
# CLASSES
#############################################################################

#========================================================================
#
class Camera(DirectObject):
    def __init__(self,parent,x,y):
        # Disable standard Panda3d mouse
        base.disableMouse()
        self.parent = parent
        self.target = None
        
        self.rightMouseIsDown = False
        
        self.mPos=[0,0]
        self.mInc=[0,0]   

        # self.node is used to manipulate position and heading
        self.node = render.attachNewNode('cam_target_node')
        self.node.setPos(5, 5, 0.3)
        self.node.setH(-45)
        
        # self.pitch_node is used to manipulate pitch
        self.pitch_node = self.node.attachNewNode('cam_pitch_node')
        self.pitch_node.setP(-45)

        base.camera.reparentTo(self.pitch_node)        
        base.camera.setPos(0, -24, 0)
        base.camera.lookAt(self.node)

        self.zoom_velocity = 0.75
        self.pan_velocity = 10  
        self.anim_velocity = 15
        self.dist = base.camera.getDistance(self.node)
        self.distmax = 30
        self.distmin = 5

        self.setupKeys()
        self.isFollowing = False   
        
        self.camTask = taskMgr.add(self.update, 'camera_update_task') 

    def clamp(self, val, min_val, max_val):
        """If val > min_val and val < max_val returns val
           If val <= min_val returns min_val
           If val >= max_val returns max_val
        """
        return min(max(val, min_val), max_val)
    
    def setKey(self, button, value):
        """Sets the state of keyboard.
           1 = pressed
           0 = depressed
        """
        if self.parent.interface.console.consoleEntry['focus'] == 1:
            self.keys['up'] = 0
            self.keys['down'] = 0
            self.keys['left'] = 0
            self.keys['right'] = 0
        else:
            self.keys[button] = value    
    
    def update(self, task):
        
        # If our camera is following a unit and user presses move keys, change to free camera style
        if self.keys['up'] == 1 or self.keys['down'] == 1 or self.keys['left'] == 1 or self.keys['right'] == 1:
            if self.isFollowing:
                self.toggleFollow()
                
        cam_pos = Vec3(0,0,0)
        dx = 0
        dy = 0
        
        if self.rightMouseIsDown: 
            newPos=[base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]
            self.mInc=[newPos[0] - self.mPos[0], newPos[1] - self.mPos[1]]
        else:
            self.mInc = [self.mInc[0] * 0.4, self.mInc[1] * 0.4]
        
        self.mPos[0] += self.mInc[0] * 0.2
        self.mPos[1] += self.mInc[1] * 0.2
        
        if self.rightMouseIsDown:
            self.node.setH(self.node.getH() - self.mInc[0] * 0.06)
            self.pitch_node.setP(self.clamp(self.pitch_node.getP() - self.mInc[1] * 0.06, -85, -10)) 
        
        if self.keys['up'] == 1:
            dy = globalClock.getDt() * self.pan_velocity
        if self.keys['down'] == 1:
            dy = -globalClock.getDt() * self.pan_velocity
        if self.keys['left'] == 1:
            dx = -globalClock.getDt() * self.pan_velocity
        if self.keys['right'] == 1:
            dx = globalClock.getDt() * self.pan_velocity
        
        self.node.setPos(self.node, dx, dy, 0)

        # zoom
        up_vec = render.getRelativeVector(base.camera, (0, 1, 0))
        dist = base.camera.getDistance(self.node) 
        cam_pos += up_vec * (dist - self.dist) * 0.25
        
        base.camera.setPos(render, base.camera.getPos(render) + cam_pos)
        
        
        return task.cont

    def toggleFollow(self):
        if self.isFollowing:
            self.setUnfollow()
        else:
            if self.parent.sel_unit_id != None:
                self.setFollow(self.parent.sgm.unit_np_dict[self.parent.sel_unit_id].node)


    def setFollow(self, node):
        self.node.reparentTo(node)
        self.node.setPos(0, 0, 0)
        self.node.setH(0)
        cam_pos = base.camera.getPos()
        base.camera.setPos(0, cam_pos.getY(), cam_pos.getZ())
        base.camera.lookAt(self.node)
        self.dist = base.camera.getDistance(self.node)
        self.parent.interface.console.consoleOutput('Camera type = FOLLOW', utils.CONSOLE_SYSTEM_MESSAGE)
        self.parent.interface.console.show()
        self.isFollowing = True        
        
    def setUnfollow(self):
        pos = self.node.getPos(render)
        h = self.node.getH(render)
        self.node.reparentTo(render)
        self.node.setPos(pos) 
        self.node.setH(h)
        self.parent.interface.console.consoleOutput('Camera type = FREE', utils.CONSOLE_SYSTEM_MESSAGE)
        self.parent.interface.console.show()
        self.isFollowing = False        

    def animate(self):
        if self.parent.sel_unit_id != None:
            node = self.parent.sgm.unit_np_dict[self.parent.sel_unit_id].node
            dist = self.node.getDistance(node)
            duration = self.clamp(dist/self.anim_velocity, 0.2, 2)
            i = self.node.posInterval(duration = duration, pos = node.getPos(), blendType = 'easeInOut')
            i.start()
    
    def setKey(self, key, flag):
        self.keys[key] = flag    
    
    def setupKeys(self):
        self.accept('w', self.setKey, ['up', 1])
        self.accept('w-up', self.setKey, ['up', 0])
        self.accept('s', self.setKey, ['down', 1])
        self.accept('s-up', self.setKey, ['down', 0])                   
        self.accept('a', self.setKey, ['left', 1])
        self.accept('a-up', self.setKey, ['left', 0])
        self.accept('d', self.setKey, ['right', 1])
        self.accept('d-up', self.setKey, ['right', 0])
        self.accept('wheel_down', self.wheelMouseDown, [])
        self.accept('wheel_up', self.wheelMouseUp, [])
        self.accept('mouse3', self.rightMouseDown, [])
        self.accept('mouse3-up', self.rightMouseUp, [])
        self.accept('space', self.animate, [])
        self.accept('f5', self.toggleFollow)

        self.keys = {}
        self.keys['up'] = 0
        self.keys['down'] = 0        
        self.keys['left'] = 0
        self.keys['right'] = 0  
        
    def rightMouseDown(self):
        self.rightMouseIsDown = True
        self.mPos = [base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]

    def rightMouseUp(self):
        self.rightMouseIsDown = False        

    def wheelMouseDown(self):
        self.dist += self.zoom_velocity
        if self.dist > self.distmax: 
            self.dist = self.distmax
        
    def wheelMouseUp(self):
        self.dist -= self.zoom_velocity
        if self.dist < self.distmin: 
            self.dist = self.distmin
        