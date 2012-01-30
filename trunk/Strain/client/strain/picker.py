#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from direct.showbase import DirectObject
from panda3d.core import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode#@UnresolvedImport
from panda3d.core import BitMask32, Plane, Vec3, Point3#@UnresolvedImport

# strain related imports
import strain.utils as utils


class Picker(DirectObject.DirectObject):      
    def __init__(self, parent):
        self.parent = parent
        # define collision traverser and set it to base.cTrav
        # it will traverse render each frame
        base.cTrav = CollisionTraverser()
        # set up collision handler
        self.collisionHandler = CollisionHandlerQueue()
        
        pickerNode = CollisionNode('mouseraycnode')
        pickerNP = base.camera.attachNewNode(pickerNode)
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        pickerNode.setTag('rays','ray1')   
        pickerNode.setFromCollideMask(BitMask32.bit(1))     
        base.cTrav.addCollider(pickerNP, self.collisionHandler) 
        # debug
        #base.cTrav.showCollisions(render) 
        
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, utils.GROUND_LEVEL))  
        
        self.hovered_unit_id = None
        self.hovered_point = Point3()
        
        taskMgr.add(self.rayupdate, 'rayupdate_task')   
        
    def rayupdate(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            
            pos3d = Point3()
            nearPoint = Point3()
            farPoint = Point3()
            base.camLens.extrude(mpos, nearPoint, farPoint)
            if self.plane.intersectsLine(pos3d, render.getRelativePoint(camera, nearPoint), render.getRelativePoint(camera, farPoint)):
                self.hovered_point = pos3d
            
            self.pickerRay.setFromLens(base.camNode, mpos.getX(),mpos.getY())
            if self.collisionHandler.getNumEntries() > 0:
                self.collisionHandler.sortEntries()
                mouse_hovered_object = self.collisionHandler.getEntry(0).getIntoNodePath()
                new_hovered_unit_id = mouse_hovered_object.findNetTag('id').getNetTag('id')
                if self.hovered_unit_id != None:
                    if self.hovered_unit_id != new_hovered_unit_id:
                        self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                        self.hovered_unit_id = new_hovered_unit_id
                        self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].markHovered()
                else:
                    self.hovered_unit_id = new_hovered_unit_id
                    self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].markHovered()
            else:
                if self.hovered_unit_id != None:
                    self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                self.hovered_unit_id = None
        return task.cont
