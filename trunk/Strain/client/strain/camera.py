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
        
        self.middleMouseIsDown = False
        self.rightMouseIsDown = False
        
        self.mPos=[0,0]
        self.mInc=[0,0]        

        self.node = render.attachNewNode('camera_target_node')
        self.node.setPos(5, 5, 0.3)

        base.camera.reparentTo(self.node)        
        base.camera.setPos(-15, -15, 18)
        base.camera.lookAt(self.node)

        self.setupKeys()
        
        self.camTask = taskMgr.add(self.update, 'camera_update_task') 

    def update(self, task):
        if self.middleMouseIsDown or self.rightMouseIsDown: 
            newPos=[base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]
            self.mInc=[newPos[0] - self.mPos[0], newPos[1] - self.mPos[1]]
        else:
            self.mInc = [self.mInc[0] * 0.4, self.mInc[1] * 0.4]
        
        self.mPos[0] += self.mInc[0] * 0.2
        self.mPos[1] += self.mInc[1] * 0.2
        
        if self.middleMouseIsDown:
            self.node.setH(self.node.getH() - self.mInc[0] * 0.06)
        
        if self.rightMouseIsDown: 
            up_vec = render.getRelativeVector(base.camera, (0, 1, 0))             
            right_vec = render.getRelativeVector(base.camera, (1, 0, 0))
            new_pos_up = Vec3(up_vec.getX() * self.mInc[1]* 0.01, up_vec.getY() * self.mInc[1] * 0.01, 0)
            new_pos_right = Vec3(right_vec.getX() * -self.mInc[0]* 0.01, right_vec.getY() * -self.mInc[0] * 0.01, 0)
            new_pos = Vec3(new_pos_up + new_pos_right)
            new_pos *= 0.7
            self.node.setPos(self.node.getPos() + new_pos)
            #self.node.setPos(self.node.getPos() + Vec3(diffPos.getX() * self.mInc[0]* 0.05, diffPos.getY() * self.mInc[0] * 0.05, 0))
        return task.cont

    #-----------------------------------------------------------------
    # Mouse and Key Routines
    #-----------------------------------------------------------------
    #
    def setKey(self, key, flag):
        self.keys[key] = flag    
    
    def setupKeys(self):
        self.accept('mouse2', self.middleMouseDown, [])
        self.accept('mouse2-up', self.middleMouseUp, [])
        self.accept('wheel_down', self.wheelMouseDown, [])
        self.accept('wheel_up', self.wheelMouseUp, [])
        self.accept('mouse3', self.rightMouseDown, [])
        self.accept('mouse3-up', self.rightMouseUp, [])

    def middleMouseDown(self):
        if not self.rightMouseIsDown:
            self.middleMouseIsDown = True
            self.mPos = [base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]

    def middleMouseUp(self):
        self.middleMouseIsDown = False
        
    def rightMouseDown(self):
        if not self.middleMouseIsDown:
            self.rightMouseIsDown = True
            self.mPos = [base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]

    def rightMouseUp(self):
        self.rightMouseIsDown = False        

    def wheelMouseDown(self):
        None
        """
        self.dist += self.zoomvel
        if self.dist > self.distmax: 
            self.dist = self.distmax
        """
        
    def wheelMouseUp(self):
        None
        """
        self.dist -= self.zoomvel
        if self.dist < self.distmin: 
            self.dist = self.distmin
        """