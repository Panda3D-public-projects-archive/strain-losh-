#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import Point3,Vec4,VBase3

# strain related imports

#############################################################################
# CLASSES
#############################################################################

#========================================================================
#
class Camera(DirectObject):
    def __init__(self,parent):
        #disable mouse
        base.disableMouse()
        #init vars
        self.parent=parent
        self.collisionMode=False
        self.target=None
        #positioning
        self.elevation=.4
        self.pos=Point3(3,3,4)*1.5
        #rotation and translation
        self.middleMouseIsDown=False
        self.isRotating=False
        self.rotvel=.05
        self.rotinter=.6
        #zoom
        self.distmax=64
        self.distmin=1
        self.zoomvel=0.75
        self.zoominter=.25
        self.dist=0
        #mouse
        self.mPos=[0,0]
        self.mInc=[0,0]
        #create camera node (target)
        self.node = render.attachNewNode("cameraNode")
        self.node.setPos(0,0,0)
        #self.node=utils.loadNode(render,"cameraNode",(0,0,0))
        #self.cube = utils.loadModel(self.node,"cameraCube","cube/cube",(0,0,-.1))
        #self.parent.picker.makePickable(self,self.cube,'camera')
        #self.cube.hide()
        #init camera lens
        #lens = OrthographicLens()
        #lens.setFilmSize(20*.5, 15*.5) # or whatever is appropriate for your scene
        #base.cam.node().setLens(lens)
        #base.cam.node().getLens().setNear(0.1)
        #base.cam.node().getLens().setFar(32*1.5)
        #base.camLens.setFov(50)
        #locate camera
        base.camera.setPos(self.node.getPos()+self.pos)
        base.camera.lookAt(self.node.getPos())
        #get initial dist (vector?)
        self.dist=base.camera.getDistance(self.node)
        #initialize camera controls (mouse)
        self.setupKeys()

    def destroy(self):
        self.node.removeNode()
  
    def update(self,task=None):
    #-----------------
    # Mouse increments
    #-----------------
        if self.middleMouseIsDown:
            #update mouse increments depending on the mouse pos
            newPos=[base.win.getPointer(0).getX(),base.win.getPointer(0).getY()]
            self.mInc=[newPos[0]-self.mPos[0],newPos[1]-self.mPos[1]]
        else:
            #deaccelerate mouse increments
            self.mInc=[self.mInc[0]*.4,self.mInc[1]*.4]
        #-----------------
        # Rotation
        #-----------------
        #interpolate mouse last pos to new pos
        self.mPos[0]+=self.mInc[0]*self.rotinter
        self.mPos[1]+=self.mInc[1]*self.rotinter
        #get new pos
        camup=VBase3(0,0,0)
        camright = base.camera.getNetTransform().getMat().getRow3(0)
        camright.normalize()
        self.pos -= camright*self.mInc[0]*self.rotvel
        camup = base.camera.getNetTransform().getMat().getRow3(2)
        camup.normalize()
        self.pos += camup*self.mInc[1]*self.rotvel*1
        #-----------------
        # Zoom
        #-----------------
        camvec = self.node.getPos() - base.camera.getPos()
        camdist = camvec.length()
        camvec.normalize()
        self.pos+=camvec*(camdist-self.dist)*self.zoominter
        #-------------------
        # Locate Camera
        #-------------------
        #node follows target
        if self.target!=None:
            if self.target.type=="@":
                self.node.setPos(self.target.node.getPos()+(0,0,self.elevation))
            else:
                self.node.setPos(self.target.pos[0],self.target.pos[1],self.elevation)
        else:
            None
        #    self.node.setPos(self.parent.grid.mapper.xsize/2,self.parent.grid.mapper.ysize/2,self.elevation)
        #camera follows node
        base.camera.setPos(self.node.getPos()+self.pos)
        #camera look at node
        base.camera.lookAt(self.node)
        #-------------------
        # Collisions
        #-------------------
        if self.collisionMode==True:
            #check collisions from camera in forward direction
            self.parent.picker.resetCameraCollisions()
            ray,rayNP=self.parent.picker.initRay(base.camera,0,1,0)
            pickedObj,pickedPoint=self.parent.picker.initTraverser(ray,rayNP,"camera")

    #-----------------------------------------------------------------
    # Mouse and Key Routines
    #-----------------------------------------------------------------
    #
    def setupKeys(self):
        #setup keys
        self.accept('v', self.toggleCollisionMode, [])
        #setup mouse
        self.mPos=[base.win.getPointer(0).getX(),base.win.getPointer(0).getY()]
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
    def toggleCollisionMode(self):
        if self.collisionMode==False:
            self.collisionMode=True
            self.parent.gui.consoleMsg("Camera collisions are now ON.")
        else:
            self.collisionMode=False
            self.parent.picker.resetCameraCollisions()
            self.parent.gui.consoleMsg("Camera collisions are now OFF.")


    def middleMouseDown(self):
        self.middleMouseIsDown=True
        self.mPos=[base.win.getPointer(0).getX(),base.win.getPointer(0).getY()]

    def middleMouseUp(self):
        self.middleMouseIsDown=False

    def wheelMouseDown(self):
        self.dist+=self.zoomvel
        if self.dist>self.distmax: self.dist=self.distmax

    def wheelMouseUp(self):
        self.dist-=self.zoomvel
        if self.dist<self.distmin: self.dist=self.distmin
