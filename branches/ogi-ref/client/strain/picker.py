#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode, GeomNode
#from pandac.PandaModules import CollisionTraverser, CollisionRay, CollisionHandlerQueue, CollisionNode, GeomNode

# strain related imports
import utils
import client_messaging

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
        
        self.map_pos = None

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
                entry = self.coll_queue.getEntry(0)
                pickedObj = entry.getIntoNodePath()
                pickedPoint = entry.getSurfacePoint(pickedObj)
                return pickedObj, pickedPoint
        return None, None


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
            pickedObj, pickedPoint = self.getMouseHoveredObject()
            if pickedObj:
                node_type = pickedObj.findNetTag("type").getTag("type")
                if node_type == "unit" or node_type == "unit_marker":
                    player_id = pickedObj.findNetTag("player_id").getTag("player_id")
                    # Player can only select his own units
                    if player_id == self.parent.player_id:
                        unit_id = int(pickedObj.findNetTag("id").getTag("id"))
                        self.parent.selectUnit(unit_id)
                else:
                    # Remember picked coordinates so we can send orientation message when mouse is depressed
                    if self.parent.sel_unit_id:
                        unit = self.parent.units[self.parent.sel_unit_id]
                        unit_pos = Point2(unit['pos'][0], unit['pos'][1])
                    else:
                        unit_pos = None
                    if unit_pos != Point2(int(pickedPoint.getX()), int(pickedPoint.getY())):
                        self.map_pos = Point2(int(pickedPoint.getX()), int(pickedPoint.getY()))
                
                            
    def mouseLeftClickUp(self):
        """Handles left mouse click actions when mouse button is depressed.
           Used for unit movement.
        """    
        if self.parent.sel_unit_id and self.map_pos and self.unit_move_orientation != utils.HEADING_NONE:   
            # Send movement message to engine
            x = self.map_pos.getX()
            y = self.map_pos.getY()
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
            ClientMsg.move(self.parent.sel_unit_id, (self.map_pos.x, self.map_pos.y), (o.x, o.y))
        self.map_pos = None
        self.move_timer = 0
        self.parent.sgm.removeTurnArrows()
