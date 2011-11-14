#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import Point3, Vec4, VBase3

# strain related imports

#############################################################################
# CLASSES
#############################################################################

#========================================================================
#
class Camera(DirectObject):
    def __init__(self,parent):
        # Disable standard Panda3d mouse
        base.disableMouse()
        self.parent = parent
        self.target = None
        
        # Position the camera
        self.elevation = 0.4
        self.pos = Point3(3, 3, 4) * 1.5
        
        # Rotation and translation
        self.middleMouseIsDown = False
        self.isRotating = False
        self.rotvel = 0.05
        self.rotinter = 0.6
        
        # Zoom
        self.distmax = 64
        self.distmin = 1
        self.zoomvel = 0.75
        self.zoominter = 0.25
        self.dist = 0
        
        # Mouse
        self.mPos = [0,0]
        self.mInc = [0,0]
        
        # Create camera node (target)
        self.node = render.attachNewNode("cameraNode")
        self.node.setPos(0, 0, 0)

        # Locate camera
        base.camera.setPos(self.node.getPos() + self.pos)
        base.camera.lookAt(self.node.getPos())
        
        # Get initial distance (vector)
        self.dist = base.camera.getDistance(self.node)
        
        # Initialize camera controls (mouse)
        self.setupKeys()

    def destroy(self):
        self.node.removeNode()
  
    def update(self, task=None):
        if self.middleMouseIsDown:
            # Update mouse increments depending on the mouse pos
            newPos = [base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]
            self.mInc = [newPos[0] - self.mPos[0], newPos[1] - self.mPos[1]]
        else:
            # Deaccelerate mouse increments
            self.mInc = [self.mInc[0] * 0.4, self.mInc[1] * 0.4]
            
        # Rotation...
        # interpolate mouse last pos to new pos
        self.mPos[0] += self.mInc[0] * self.rotinter
        self.mPos[1] += self.mInc[1] * self.rotinter
        # Get new pos
        camup = VBase3(0, 0, 0)
        camright = base.camera.getNetTransform().getMat().getRow3(0)
        camright.normalize()
        self.pos -= camright * self.mInc[0] * self.rotvel
        camup = base.camera.getNetTransform().getMat().getRow3(2)
        camup.normalize()
        self.pos += camup * self.mInc[1] * self.rotvel
        # Zoom
        camvec = self.node.getPos() - base.camera.getPos()
        camdist = camvec.length()
        camvec.normalize()
        self.pos += camvec * (camdist - self.dist) * self.zoominter

        # Locate camera
        #node follows target
        if self.target != None:
            self.node.setPos(self.target.pos[0], self.target.pos[1], self.elevation)

        # Camera follows node
        base.camera.setPos(self.node.getPos() + self.pos)
        # Camera look at node
        base.camera.lookAt(self.node)

    #-----------------------------------------------------------------
    # Mouse and Key Routines
    #-----------------------------------------------------------------
    #
    def setupKeys(self):
        #setup mouse
        self.mPos = [base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]
        self.accept('mouse2', self.middleMouseDown, [])
        self.accept('mouse2-up', self.middleMouseUp, [])
        self.accept('wheel_down', self.wheelMouseDown, [])
        self.accept('wheel_up', self.wheelMouseUp, [])
        """
        self.accept('w', self.camNDown, [])
        self.accept('w-up', self.camNUp, [])
        self.accept('s', self.camSDown, [])
        self.accept('s-up', self.camSUp, [])
        self.accept('a', self.camWDown, [])
        self.accept('a-up', self.camWUp, [])
        self.accept('d', self.camEDown, [])
        self.accept('d-up', self.camEUp, [])
        """

    def middleMouseDown(self):
        self.middleMouseIsDown = True
        self.mPos = [base.win.getPointer(0).getX(), base.win.getPointer(0).getY()]

    def middleMouseUp(self):
        self.middleMouseIsDown = False

    def wheelMouseDown(self):
        self.dist += self.zoomvel
        if self.dist > self.distmax: 
            self.dist = self.distmax

    def wheelMouseUp(self):
        self.dist -= self.zoomvel
        if self.dist < self.distmin: 
            self.dist = self.distmin
