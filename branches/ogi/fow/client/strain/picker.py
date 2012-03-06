#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from direct.showbase import DirectObject
from panda3d.core import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode#@UnresolvedImport
from panda3d.core import BitMask32, Plane, Vec3, Point3#@UnresolvedImport
from panda3d.core import TransparencyAttrib, CardMaker#@UnresolvedImport
from panda3d.core import *

# strain related imports
import strain.utils as utils
from share import *


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
        self.hovered_tile = None
        self.hovered_point = Point3()
        
        self.mouse_node = aspect2d.attachNewNode('mouse_node')
        self.move_node = aspect2d.attachNewNode('move_node')
        self.move_np_list = []
    
        #taskMgr.add(self.rayupdate, 'rayupdate_task')
        taskMgr.add(self.pickerTask, 'picker_task')
        taskMgr.add(self.positionTask, 'position_task')
    
    def calcUnitAvailMove(self, unit_id):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        self.deleteUnitAvailMove()
        unit = self.parent.units[unit_id]
        if self.parent.turn_player != self.parent.player:
            return
        if unit:
            unit['move_dict'] = getMoveDict(unit, self.parent.level, self.parent.units)
            self.parent.units[unit_id]['move_dict'] = unit['move_dict']
            move_dict = unit['move_dict']
            for tile in move_dict:
                text = TextNode('node name')
                text.setText( "%s" % move_dict[tile])
                text.setAlign(TextNode.ACenter)
                textNodePath = self.move_node.attachNewNode(text)
                textNodePath.setColor(1, 1, 1)
                textNodePath.setScale(0.05)    
                textNodePath.setPythonTag('pos', tile)            
                self.move_np_list.append(textNodePath)
        self.move_node.reparentTo(aspect2d)
        self.hovered_tile = None
                
    def deleteUnitAvailMove(self):
        self.move_node.detachNode() 
        for c in self.move_np_list:
            c.removeNode()
        self.move_np_list = []
        
    def positionTask(self, task):
        for unit_id in self.parent.sgm.unit_np_dict:
            u = self.parent.sgm.unit_np_dict[unit_id]
            p = utils.nodeCoordIn2d(u.model)
            u.node_2d.setPos(p)
        for tile in self.move_np_list:
            pos = Point3(tile.getPythonTag('pos')[0]+0.5, tile.getPythonTag('pos')[1]+0.5, utils.GROUND_LEVEL)
            pos2d = utils.pointCoordIn2d(pos)
            tile.setPos(pos2d)
        return task.cont
    
    def pickerTask(self, task):
        # Get mouse position
        min_distance = 0.5
        min_unit_id = None
        min_tile= None
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            r2d = Point3(mpos.getX(), 0, mpos.getY())
            a2d = aspect2d.getRelativePoint(render2d, r2d)
            self.mouse_node.setPos(a2d)
            
            # Get 2d coordinates of all units
            for unit_id in self.parent.sgm.unit_np_dict:
                if self.parent.isThisMyUnit(unit_id):
                    u = self.parent.sgm.unit_np_dict[unit_id]
                    # Calculate distance between every friendly unit and mouse cursor and remember closest unit
                    d = self.mouse_node.getDistance(u.node_2d)
                    if d < min_distance:
                        min_distance = d
                        min_unit_id = unit_id
                elif self.parent.isThisEnemyUnit(unit_id):
                    u = self.parent.sgm.unit_np_dict[unit_id]
                    # Calculate distance between every enemy unit and mouse cursor and remember closest unit
                    d = self.mouse_node.getDistance(u.node_2d)
                    # To target enemy unit, distance has to be even smaller than needed for regular selection/movement
                    if d < min_distance and d < 0.1:
                        min_distance = d
                        min_unit_id = unit_id
            
            # Get 2d coordinates for every movement node of the selected unit
            for tile in self.move_np_list:
                # We cannot do nodepath.getDistance() because tiles are reparented to self.move_node and are in different coord space than mouse node
                # So we do simple vector math to get distance
                d = Vec3(self.mouse_node.getPos() - tile.getPos()).length()
                if d < min_distance:
                    min_distance = d
                    min_unit_id = None
                    min_tile = tile
            
            # At the end of all this we have:
            # - min_distance to a unit or a movement node, IF this distance is lower than 0.5 which is set at the beginning
            # - min_unit_id - ID of unit which is closest to the mouse, or None if there is a movement tile closer, or if everything is further than 0.5
            # - min_tile - nodepath of the movement tile closest to the mouse, or None if there is a unit closer, or if evertythin is further than 0.5
            
        # If a unit is the closest to the mouse:
        # - hide movement nodes (Incubation style!)
        # - unmark last hovered unit
        # - unmark last hovered tile
        # - mark new hovered unit
        # TODO: ogs: potencijalna optimizacija da se provjeri da li je self.hovered_unit_id = min_unit_id, tada ne treba unmark+mark
        if min_unit_id != None:
            self.move_node.detachNode() 
            if self.hovered_unit_id != None:
                self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
                self.hovered_tile = None
            self.parent.sgm.unit_np_dict[int(min_unit_id)].markHovered()
            self.hovered_unit_id = min_unit_id
        # If a movement tile is closest to the mouse:
        # - show movement nodes (Incubation style!)
        # - unmark last hovered unit
        # - unmark last marked tile
        # - mark new hovered tile
        elif min_tile != None:
            self.move_node.reparentTo(aspect2d)
            if self.hovered_unit_id != None:
                self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered() 
                self.hovered_unit_id = None           
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
            min_tile.setColor(1, 0, 0)
            self.hovered_tile = min_tile
        # If neither any of the units nor any of the movement tiles is closer than 0.5:
        # - unmark last hovered unit
        # - unmark last hovered tile
        else:
            if self.hovered_unit_id != None:
                self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                self.hovered_unit_id = None
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
                self.hovered_tile = None
        return task.cont
    
    """
    def rayupdate(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            
            if self.parent.sgm.comp_inited['level'] == False:
                return task.cont
            
            if self.parent._anim_in_process:
                return task.cont
            
            pos3d = Point3()
            nearPoint = Point3()
            farPoint = Point3()
            base.camLens.extrude(mpos, nearPoint, farPoint)
            if self.plane.intersectsLine(pos3d, render.getRelativePoint(camera, nearPoint), render.getRelativePoint(camera, farPoint)) and self.hovered_unit_id == None:    
                self.hovered_point = pos3d
                
            self.pickerRay.setFromLens(base.camNode, mpos.getX(),mpos.getY())
            if self.collisionHandler.getNumEntries() > 0:
                self.collisionHandler.sortEntries()
                mouse_hovered_object = self.collisionHandler.getEntry(0).getIntoNodePath()
                new_hovered_unit_id = mouse_hovered_object.findNetTag('id').getNetTag('id')
                if self.hovered_unit_id != None:
                    if self.hovered_unit_id != new_hovered_unit_id:
                        if self.parent.sgm.unit_np_dict.has_key(int(self.hovered_unit_id)):
                            self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                        self.hovered_unit_id = new_hovered_unit_id
                        self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].markHovered()
                        self.hovered_point = None
                else:
                    self.hovered_unit_id = new_hovered_unit_id
                    self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].markHovered()
                    self.hovered_point = None
            else:
                if self.hovered_unit_id != None:
                    try:
                        self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                        self.hovered_unit_id = None
                    except KeyError:
                        self.hovered_unit_id = None
        return task.cont
    """
