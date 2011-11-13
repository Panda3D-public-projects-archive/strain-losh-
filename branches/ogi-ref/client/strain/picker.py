#############################################################################
# IMPORTS
#############################################################################

# python imports
import math

# panda3D imports
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import CollisionTraverser,CollisionRay,CollisionHandlerQueue,CollisionNode,GeomNode
from pandac.PandaModules import RenderModeAttrib

# strain related imports

class Picker(DirectObject):
    def __init__(self,parent):
        #record vars
        self.parent=parent
        self.lastPicked=[]
        ## left mouse handler
        self.accept('mouse1-up', self.mousePick, [1])
        ## right mouse handler
        self.accept('mouse3', self.mousePick, [3])
        #camera handler -> called each frame from cam.update()
        pass


    def makePickable(self,obj,model,tag='true'):
        #sets nodepath pickable state (unpickable is ...)
        model.setTag('pickable',tag)
        #register the model class in a python tag
        model.setPythonTag('class',obj)

    def mousePick(self, but):
        #get mode from but
        mode="mouse"+str(but)
        #if no object under mouse exit
        if base.mouseWatcherNode.hasMouse()==False: return
        #get mouse coords
        mpos=base.mouseWatcherNode.getMouse()
        #check if we are clicking on the inventory
        click=self.parent.grid.av.bag.mouseClick(mpos)
        if click: return
        #check collisions from camera to mpos
        ray,rayNP=self.initRay(base.camera,0,0,-1)
        ray.setFromLens(base.camNode, mpos.getX(),mpos.getY())
        pickedObj,pickedPoint=self.initTraverser(ray,rayNP,mode)
        #call mouse function (left or right)
        if pickedPoint:
            if but==1: self.mouseLeft(pickedObj,pickedPoint)
            if but==3: self.mouseRight(pickedObj,pickedPoint)

    def initRay(self,node,dx=0,dy=0,dz=-1):
        rayNP=node.attachNewNode(CollisionNode("rayBullet"))
        ray=CollisionRay(0,0,0,dx,dy,dz)
        rayNP.node().addSolid(ray)
        rayNP.node().setFromCollideMask(GeomNode.getDefaultCollideMask())
        #rayNP.show()
        return ray,rayNP

    def initTraverser(self,ray,rayNP,mode="mouse1"):
        #the collision traverser. we need this to perform collide in the end
        cTrav = CollisionTraverser()
        #to visualize the collisions
        #base.cTrav=cTrav
        #cTrav.hideCollisions()
        #cTrav.showCollisions(render)
        #setting up a collision handler queue which will collect the collisions in a list
        queue = CollisionHandlerQueue()
        #add the from object to the queue so its collisions will get listed in it.
        cTrav.addCollider(rayNP, queue)
        #finally.. we perform the collisiontest using the .traversre call
        cTrav.traverse(render)
        #get collisions
        pickedObj,pickedPoint=self.getCollisions(queue,mode)
        #remove the collider
        cTrav.removeCollider(rayNP)
        cTrav.clearColliders()
        rayNP.removeNode()
        #print cTrav.getNumColliders()
        #return the collision data
        return pickedObj,pickedPoint

    def getCollisions(self,queue,mode="mouse1"):
        pickedObj=None
        pickedPoint=None
        #check for first collision
        if queue.getNumEntries() > 0:
            queue.sortEntries()
            for i in range(queue.getNumEntries()):
                entry = queue.getEntry(i)
                pickedObj=entry.getIntoNodePath()
                #iterate up in model hierarchy to found a pickable tag
                parent=pickedObj.getParent()
                for n in range(4):
                    if parent.getTag('pickable')!="" or parent==render: break
                    parent=parent.getParent()
                #return appropiate picked object
                ok=False
                if mode=="mouse1" or mode=="mouse3": ok=self.mouseCollisions(entry,parent)
                if mode=="shoot": ok=self.shootCollisions(entry,parent)
                if mode=="camera": ok=self.cameraCollisions(entry,parent)
                if ok==True:
                    pickedObj=parent
                    pickedPoint = entry.getSurfacePoint(pickedObj)
                    break
        return pickedObj,pickedPoint

    def mouseCollisions(self,entry,parent):
        #if pickable terrain, chest or avatar
        tag=parent.getTag('pickable')
        if tag=="terrain" or tag=="chest" or tag=="avatar":
            return True
        return False

    def shootCollisions(self,entry,parent):
        #if pickable but not an item
        tag=parent.getTag('pickable')
        if tag!="" and tag!="item":
            return True
        return False

    def cameraCollisions(self,entry,parent):
        #if pickable but not an item
        tag=parent.getTag('pickable')
        if tag!="":
            if parent==self.parent.cam.target.node: return True
            if parent==self.parent.cam.cube: return True
            if parent.isHidden()==False:
                parent.setRenderMode(RenderModeAttrib.MWireframe,1.0)
                self.lastPicked.append(parent)
        return False

    def resetCameraCollisions(self):
        for n in self.lastPicked:
            if n.isHidden()==False: n.clearRenderMode()
    #-----------------------------------------------------------------
    # Mouse Handlers
    #-----------------------------------------------------------------
    #
    def mouseLeft(self,pickedObj,pickedPoint):
        grid=self.parent.grid
        if pickedObj==None: return
        # get object, node and position
        start=utils.getCell(grid.av.node.getPos())
        p=utils.getCell(grid.node.getRelativePoint(pickedObj,pickedPoint))
        node=pickedObj
        tag=pickedObj.getTag('pickable')
        target=pickedObj.getPythonTag('class')
        #set cell as camera target [+shift]
        if self.parent.keyMap['shift']==1:
            self.parent.cam.target=target
            return
        #if a path already exists, stop following it
        if grid.av.mov.path:
            grid.av.mov.isMoving=False
            return
        #click over terrain
        if tag=='terrain':
            grid.av.mov.getPath(start,p,None) # path to p without target
            return
        #click over avatar
        if tag=='avatar' or tag=='chest':
            grid.av.mov.getPath(start,p,target,but=1) # path to p with selected target
            return

    def mouseRight(self,pickedObj,pickedPoint):
        grid=self.parent.grid
        if pickedObj==None: return
        # get object, node and position
        start=utils.getCell(grid.av.node.getPos())
        p=utils.getCell(grid.node.getRelativePoint(pickedObj,pickedPoint))
        node=pickedObj
        tag=pickedObj.getTag('pickable')
        target=pickedObj.getPythonTag('class')
        #click over chest
        if tag=='chest':
            grid.av.mov.getPath(start,p,target,but=3) # path to p with selected target
            eturn
        #click over avatar target
        if tag=="avatar":
            grid.av.combat.initRangedCombat(target)
        #turn avatar towards cell pos
        utils.playSound(grid.sound_step, start="random", duration=.5, volume=.2, loop=False)
        grid.av.mov.angle=utils.turnAt(grid.av.node, p, .2)
        self.infoCell(p)

