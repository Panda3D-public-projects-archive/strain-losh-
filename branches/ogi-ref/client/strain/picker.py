#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode, GeomNode

# strain related imports

class Picker(DirectObject):
    def __init__(self,parent):
        self.parent = parent
        self.lastPicked = []
        # Mouse handler
        self.accept('mouse1-up', self.mousePick, [1])

    def makePickable(self, model, tag='true'):
        # Sets nodepath pickable state
        model.setTag('pickable', tag)

    def mousePick(self, but):
        mode = "mouse" + str(but)
        if not base.mouseWatcherNode.hasMouse(): 
            return
        mpos = base.mouseWatcherNode.getMouse()
        # Check collisions from camera to mpos
        ray, rayNP = self.initRay(base.camera, 0, 0, -1)
        ray.setFromLens(base.camNode, mpos.getX(), mpos.getY())
        pickedObj, pickedPoint = self.initTraverser(ray, rayNP, mode)
        # Call mouse function (left or right)
        if pickedPoint:
            if but == 1: 
                self.mouseLeft(pickedObj, pickedPoint)

    def initRay(self, node, dx=0, dy=0, dz=-1):
        rayNP = node.attachNewNode(CollisionNode("ray"))
        ray = CollisionRay(0, 0, 0, dx, dy, dz)
        rayNP.node().addSolid(ray)
        rayNP.node().setFromCollideMask(GeomNode.getDefaultCollideMask())
        #rayNP.show()
        return ray, rayNP

    def initTraverser(self, ray, rayNP, mode):
        cTrav = CollisionTraverser()
        #setting up a collision handler queue which will collect the collisions in a list
        queue = CollisionHandlerQueue()
        #add the from object to the queue so its collisions will get listed in it.
        cTrav.addCollider(rayNP, queue)
        #finally.. we perform the collisiontest using the .traversre call
        cTrav.traverse(render)
        #get collisions
        pickedObj, pickedPoint = self.getCollisions(queue, mode)
        #remove the collider
        cTrav.removeCollider(rayNP)
        cTrav.clearColliders()
        rayNP.removeNode()
        #print cTrav.getNumColliders()
        #return the collision data
        return pickedObj, pickedPoint

    def getCollisions(self, queue, mode):
        pickedObj = None
        pickedPoint = None
        #check for first collision
        if queue.getNumEntries() > 0:
            queue.sortEntries()
            for i in range(queue.getNumEntries()):
                entry = queue.getEntry(i)
                pickedObj = entry.getIntoNodePath()
                parent = pickedObj.getParent()
                for n in range(4):
                    if parent.getTag('pickable') != "" or parent == render: 
                        break
                    parent = parent.getParent()
                #return appropiate picked object
                ok = False
                if mode == "mouse1" or mode == "mouse3": 
                    ok = self.mouseCollisions(entry, parent)
                if mode == "shoot": 
                    ok = self.shootCollisions(entry, parent)
                if ok == True:
                    pickedObj = parent
                    pickedPoint = entry.getSurfacePoint(pickedObj)
                    break
        return pickedObj, pickedPoint

    def mouseCollisions(self, entry, parent):
        #if pickable terrain, chest or avatar
        tag = parent.getTag('pickable')
        if tag == "unit":
            return True
        return False

    def shootCollisions(self, entry, parent):
        tag = parent.getTag('pickable')
        if tag == "utem":
            return True
        return False

    def mouseLeft(self, pickedObj, pickedPoint):
        if not pickedObj: 
            return
