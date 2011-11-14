#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode, GeomNode

# strain related imports
import utils

class Picker(DirectObject):
    def __init__(self,parent):
        self.parent = parent
        
        self.coll_trav = CollisionTraverser()
        self.coll_queue = CollisionHandlerQueue()
        self.coll_node = CollisionNode("mouse_ray")
        self.coll_nodepath = base.camera.attachNewNode(self.coll_node)
        self.coll_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.coll_ray = CollisionRay()
        self.coll_node.addSolid(self.coll_ray)
        self.coll_trav.addCollider(self.coll_nodepath, self.coll_queue)

        # Mouse handler
        self.accept('mouse1', self.mouseLeftClick)
        self.accept("mouse1-up", self.mouseLeftClickUp)

    def getMousePos(self):
        """Returns mouse coordinates if mouse pointer is inside Panda window."""
        if base.mouseWatcherNode.hasMouse(): 
            return base.mouseWatcherNode.getMouse() 
        return None
    
    def getMouseHoveredObject(self):
        """Returns the closest object in the scene graph over which we hover mouse pointer.
           Returns None if no objects found.
        """
        pos = self.getMousePos()
        if pos:
            self.coll_ray.setFromLens(base.camNode, pos.getX(), pos.getY())
            self.coll_trav.traverse(render)
            if self.coll_queue.getNumEntries() > 0:
                self.coll_queue.sortEntries()
                np = self.coll_queue.getEntry(0).getIntoNodePath()
                return np
        return None

    def mouseLeftClick(self):
        """Handles left mouse click actions.
           Procedure first checks for gui clicks, if there are none then it checks 3d collision.
        """
        if self.parent.interface.hovered_gui == self.parent.interface.deselect_button:
            self.parent.deselectUnit()
            self.parent.interface.console.unfocus()
        elif self.parent.interface.hovered_gui == self.parent.interface.punit_button:
            self.parent.selectPrevUnit()
            self.parent.interface.console.unfocus()
        elif self.parent.interface.hovered_gui == self.parent.interface.nunit_button:
            self.parent.selectNextUnit()
            self.parent.interface.console.unfocus() 
        elif self.parent.interface.hovered_gui == self.parent.interface.endturn_button:
            self.parent.endTurn()
            self.parent.interface.console.unfocus()
        elif self.parent.interface.hovered_gui == self.parent.interface.console:
            self.parent.interface.console.focus()
        else:
            self.parent.interface.console.unfocus()  
            print self.getMouseHoveredObject()
            #print pickedObj, pickedPoint
            return
            if pickedObj:
                node_type = selected.findNetTag("type").getTag("type")
                if node_type == "unit" or node_type == "unit_marker":
                    unit_id = int(pickedObj.findNetTag("id").getTag("id"))
                    unit = self.ge.unit_np_dict[unit_id] 
                    if self.selected_unit != unit:
                        self.selectUnit(unit)
                    else:
                        # Remember movement tile so we can send orientation message when mouse is depressed
                        self.unit_move_destination = Point2(int(unit.node.getX()), int(unit.node.getY()))
                
                            
    def mouseLeftClickUp(self):
        """Handles left mouse click actions when mouse button is depressed.
           Used for unit movement.
        """  
        return      
        if self.selected_unit and self.unit_move_destination and self.unit_move_orientation != utils.HEADING_NONE:   
            # Send movement message to engine
            x = self.unit_move_destination.getX()
            y = self.unit_move_destination.getY()
            if self.unit_move_orientation == utils.HEADING_NW:
                o = Point2(x-1, y+1)
            elif self.unit_move_orientation == utils.HEADING_N:
                o = Point2(x, y+1)
            elif self.unit_move_orientation == utils.HEADING_NE:
                o = Point2(x+1, y+1)
            elif self.unit_move_orientation == utils.HEADING_W:
                o = Point2(x-1, y)
            elif self.unit_move_orientation == utils.HEADING_E:
                o = Point2(x+1, y)
            elif self.unit_move_orientation == utils.HEADING_SW:
                o = Point2(x-1, y-1)
            elif self.unit_move_orientation == utils.HEADING_S:
                o = Point2(x, y-1)
            elif self.unit_move_orientation == utils.HEADING_SE:
                o = Point2(x+1, y-1)
            self.ge.createMoveMsg(self.selected_unit, (self.unit_move_destination.x, self.unit_move_destination.y), 
                                                            (o.x, o.y))
        self.unit_move_destination = None
        self.move_timer = 0
        self.removeTurnArrows()
