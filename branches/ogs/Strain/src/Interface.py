from direct.showbase import DirectObject
from panda3d.core import Plane, Vec4, Vec3, Vec2, Point3, Point2
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from pandac.PandaModules import GeomNode, CardMaker 
from pandac.PandaModules import Texture, TextureStage, RenderAttrib, DepthOffsetAttrib, TransparencyAttrib
from ResourceManager import UnitLoader
import math

#===============================================================================
# GLOBAL DEFINITIONS
#===============================================================================

_TILE_AVAILABLE_MOVE    = "_tile_available_move"
_TILE_HOVERED           = "_tile_hovered"
_TILE_FULL_LOS          = "_tile_full_los"
_TILE_PARTIAL_LOS       = "_tile_partial_los"
_TILE_UNIT_POS          = "_tile_unit_pos"
_TILE_RESET             = "_tile_reset"

#===============================================================================
# CLASS Interface --- DEFINITION
#===============================================================================

class Interface(DirectObject.DirectObject):
    def __init__(self):
        
        base.disableMouse()
        self.mx = 0
        self.my = 0
        self.is_orbiting = False
        self.target = Vec3(0, 0, 0)
        self.cam_dist = 40
        self.pan_rate_div = 20
        self.pan_limits_x = Vec2(-5, 15) 
        self.pan_limits_y = Vec2(-5, 15)
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        base.camera.setPos(10, 10, 20)
        base.camera.lookAt(10, 10, 0)
        self.orbit(0, 0)
        
        self.los_visible = False
        self.unit_los_visible = False
        
        self.hovered_tile = None
        self.selected_unit = None
        self.selected_unitmodel = None
        self.off_model = None
        self.selected_unit_tex = loader.loadTexture("sel.png")
        self.selected_unit_tile = None

        self.initCollision()

        self.accept('w', self.setKey, ['up', 1])
        self.accept('w-up', self.setKey, ['up', 0])
        self.accept('s', self.setKey, ['down', 1])
        self.accept('s-up', self.setKey, ['down', 0])                   
        self.accept('a', self.setKey, ['left', 1])
        self.accept('a-up', self.setKey, ['left', 0])
        self.accept('d', self.setKey, ['right', 1])
        self.accept('d-up', self.setKey, ['right', 0])
        self.accept('l-up', self.switchLos)
        self.accept('o-up', self.switchUnitLos)
        self.accept("mouse1-up", self.mouseLeftClick)
        self.accept("mouse3", self.startOrbit)
        self.accept("mouse3-up", self.stopOrbit)
        self.accept("wheel_up", lambda : self.adjustCamDist(0.9))
        self.accept("wheel_down", lambda : self.adjustCamDist(1.1))
        
        self.keys = {}
        self.keys['up'] = 0
        self.keys['down'] = 0        
        self.keys['left'] = 0
        self.keys['right'] = 0
        self.keys['middle'] = 0
        self.keys['wheel_up'] = 0
        self.keys['wheel_down'] = 0
    
        taskMgr.add(self.updateCamera, 'updateCamera_task')
        taskMgr.add(self.hover, 'hover_task')

    def initCollision(self):
        """Initializes objects needed to perform panda collisions."""
        self.coll_trav = CollisionTraverser()
        self.coll_queue = CollisionHandlerQueue()
        self.coll_node = CollisionNode("mouse_ray")
        self.coll_nodepath = base.camera.attachNewNode(self.coll_node)
        self.coll_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.coll_ray = CollisionRay()
        self.coll_node.addSolid(self.coll_ray)
        self.coll_trav.addCollider(self.coll_nodepath, self.coll_queue)
    
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
     
    def getMousePos(self):
        """Returns mouse coordinates if mouse pointer is inside Panda window."""
        if base.mouseWatcherNode.hasMouse(): 
            return base.mouseWatcherNode.getMouse() 
        return None
    
    def setTarget(self, x, y, z):
        """Sets the target point which will be the center of camera view.""" 
        x = self.clamp(x, self.pan_limits_x.getX(), self.pan_limits_x.getY())
        self.target.setX(x)
        y = self.clamp(y, self.pan_limits_y.getX(), self.pan_limits_y.getY())
        self.target.setY(y)
        self.target.setZ(z)
        
    def clamp(self, val, min_val, max_val):
        """If val > min_val and val < max_val returns val
           If val <= min_val returns min_val
           If val >= max_val returns max_val
        """
        return min(max(val, min_val), max_val)

    def adjustCamDist(self, factor):
        """Adjusts distance from the camera to the level. Used for zooming of the camera."""
        self.cam_dist = self.cam_dist * factor
        self.orbit(0, 0)
    
    def startOrbit(self): 
        """Sets camera is orbiting flag.
           Fires when right mouse button is pressed.
        """
        self.is_orbiting = True
            
    def stopOrbit(self):
        """Clears camera is orbiting flag.
           Fires when right mouse button is depressed.
        """
        self.is_orbiting = False 
    
    def orbit(self, delta_x, delta_y):
        """Handles camera orbiting (turning around camera target)."""
        new_cam_hpr = Vec3() 
        new_cam_pos = Vec3()
        cam_hpr = base.camera.getHpr()  
          
        new_cam_hpr.setX(cam_hpr.getX() + delta_x) 
        new_cam_hpr.setY(self.clamp(cam_hpr.getY() - delta_y, -85, -10)) 
        new_cam_hpr.setZ(cam_hpr.getZ())
          
        base.camera.setHpr(new_cam_hpr)  
          
        radian_x = new_cam_hpr.getX() * (math.pi / 180.0) 
        radian_y = new_cam_hpr.getY() * (math.pi / 180.0)  
          
        new_cam_pos.setX(self.cam_dist * math.sin(radian_x) * math.cos(radian_y) + self.target.getX())
        new_cam_pos.setY(-self.cam_dist * math.cos(radian_x) * math.cos(radian_y) + self.target.getY()) 
        new_cam_pos.setZ(-self.cam_dist * math.sin(radian_y) + self.target.getZ()) 
        base.camera.setPos(new_cam_pos.getX(), new_cam_pos.getY(), new_cam_pos.getZ())                     
        base.camera.lookAt(self.target.getX(), self.target.getY(), self.target.getZ()) 
    
   
    def setKey(self, button, value):
        """Sets the state of keyboard.
           1 = pressed
           0 = depressed
        """
        self.keys[button] = value    

    def setTileColorScale(self, tile, r, g, b, alpha):
        """Sets color scale of tile nodepath.
           r, g, b, a = 1, 1, 1, 1 resets the color scale
        """
        tile.setColorScale(r, g, b, alpha)

    def changeTileColor(self, tile, event, rgba=None):
        """Changes color of the tile nodepath according to event and flag.
           Event defines the reason for color change.
           Flag defines the scale of the color change.
        """
        if   event == _TILE_AVAILABLE_MOVE:
            self.setTileColorScale(tile, 2, 2, 2, 1)
        elif event == _TILE_HOVERED:
            self.setTileColorScale(tile, 2, 2, 2, 1)
        elif event == _TILE_FULL_LOS:
            self.setTileColorScale(tile, 2, 0.6, 0.6, 1)
        elif event == _TILE_PARTIAL_LOS:
            self.setTileColorScale(tile, 1, 0.6, 0.6, 1)
        elif event == _TILE_UNIT_POS:
            r = rgba.getX()
            g = rgba.getY()
            b = rgba.getZ()
            a = rgba.getW()
            self.setTileColorScale(tile, r, g, b, a)
        elif event == _TILE_RESET:
            self.setTileColorScale(tile, 1, 1, 1, 1)
        else:
            self.setTileColorScale(tile, 1, 1, 1, 1)

    def resetAllTileColor(self):
        """Resets the color of all tiles in the level."""
        for tile_list in base.graphics_engine.node_data:
            for tile in tile_list:
                self.changeTileColor(tile, _TILE_RESET)   

    def setTileBlendTexture(self, tile, texture, color):
        """Sets texture and its color to be blended with the original tile texture."""
        ts = TextureStage("ts")
        ts.setMode(TextureStage.MBlend)
        ts.setColor(color)
        tile.setTexture(ts, texture)
        
    def clearTileBlendTexture(self, tile):
        """Clears all blended textures from a tile."""
        tile.setTextureOff()
    
    def markSelectedTile(self, tile):
        """Marks the tile of the selected unit with circular pointer in color of the unit's team."""
        if self.selected_unit.owner.name == "ultramarinac":
            color = Vec4(1, 0, 0, 1)
        else:
            color = Vec4(0, 0, 1, 1)
        self.setTileBlendTexture(tile, self.selected_unit_tex, color)
        self.selected_unit_tile = tile
        
    def clearSelectedTile(self, tile):
        """Clear the mark from the tile of the selected unit."""
        self.clearTileBlendTexture(tile)

    def selectUnit(self, unit):
        """Performs actions for unit selection.
           Clears previous selection, sets global Interface.selected_unit variable, marks selected unit tile,
           loads and renders selected unit model in an off screen buffer for portrait display.
        """
        self.deselectUnit()
        self.selected_unit = unit
        self.selected_unitmodel = base.graphics_engine.unit_models[unit.id]
        pos = self.selected_unitmodel.get_unit_grid_pos()
        self.markSelectedTile(base.graphics_engine.node_data[int(pos.x)][int(pos.y)])
        ul = UnitLoader()
        self.off_model = ul.load(self.selected_unit.type, "off")
        self.off_model.reparentTo(base.graphics_engine.alt_render)
        self.off_model.setPos(0,-8,-1.7)
        self.off_model.play("idle02")

    def deselectUnit(self):
        """Performs actions for unit deselection.
           Clears unit tile, cleans up off screen models, 
           clears Interface.selected_unit and Interface.selected_unitmodel variables.
        """
        if self.selected_unit:
            self.clearSelectedTile(self.selected_unit_tile)
            if self.off_model:
                self.off_model.cleanup()
                self.off_model.remove()
            self.selected_unit = None
            self.selected_unitmodel = None
        
    def selectPrevUnit(self):
        """Selects previous unit in the same team with unspent action points."""
        None
        
    def selectNextUnit(self):
        """Selects next unit in the same team with unspent action points."""
        None     

    def displayLos(self):
        """Displays visual indicator of tiles which are in line of sight of the selected unit.
           Tiles in full view are marked with brighter red color.
           Tiles in partial view are marked with darker red color.
        """
        if self.selected_unit:
            losh_list = base.engine.getLOSHList(Point2(self.selected_unit.x, self.selected_unit.y))
            for tile in losh_list:
                tile_node = base.graphics_engine.node_data[int(tile[0].x)][int(tile[0].y)]
                if tile[1] == 0:
                    self.changeTileColor(tile_node, _TILE_FULL_LOS)
                elif tile [1] == 1:
                    self.changeTileColor(tile_node, _TILE_PARTIAL_LOS)
                else:
                    self.changeTileColor(tile_node, _TILE_RESET)      
    
    def switchLos(self):
        """Switches the display of line of sight for the selected unit on or off."""
        if self.los_visible == True:
            self.resetAllTileColor()
            self.los_visible = False
        else:
            self.displayLos()
            self.los_visible = True
            
    def displayUnitLos(self):
        """Displays visual indicator of tiles which are in line of sight from selected unit to enemy unit.
           Tiles in full view are marked with brighter red color.
           Tiles in partial view are marked with darker red color.        
           Currently enemy unit coordinates are hardcoded.
        """
        if self.selected_unit:
            los_list = base.engine.getLOS(Point2(self.selected_unit.x, self.selected_unit.y), Point2(13,13))
            for tile in los_list:
                tile_node = base.graphics_engine.node_data[int(tile[0].x)][int(tile[0].y)]
                if tile[1] == 0:
                    self.changeTileColor(tile_node, _TILE_FULL_LOS)
                elif tile [1] == 1:
                    self.changeTileColor(tile_node, _TILE_PARTIAL_LOS)
                else:
                    self.changeTileColor(tile_node, _TILE_RESET)
                
    def switchUnitLos(self):
        """Switched the display of line of sight from selected unit to enemy unit on or off."""
        if self.unit_los_visible == True:
            self.resetAllTileColor()
            self.unit_los_visible = False
        else:
            self.displayUnitLos()
            self.unit_los_visible = True
        
    def mouseLeftClick(self):
        """Handles left mouse click actions."""
        selected = self.getMouseHoveredObject()
        if selected:
            node_type = selected.findNetTag("type").getTag("type")
            if node_type == "unit":
                unit_id = int(selected.findNetTag("id").getTag("id"))
                unit = base.engine.units[unit_id] 
                if self.selected_unit != unit:
                    self.selectUnit(unit)
            elif node_type == "tile":
                p = selected.getParent().getPos()
                u = base.graphics_engine.unit_data[int(p.x)][int(p.y)]
                if u:
                    unit = base.engine.units[int(u.id)]
                else:
                    unit = None
                if unit:
                    if self.selected_unit != unit:
                        self.selectUnit(unit)
                else:
                    pos = Point2(int(p.x), int(p.y))

                    
#===============================================================================
# CLASS Interface --- TASKS
#===============================================================================
 
    def hover(self, task):
        """Task to visually mark tile over which are mouse pointer hovers."""
        np = self.getMouseHoveredObject()
        if np:
            if self.hovered_tile != np:
                if self.hovered_tile:
                    self.changeTileColor(self.hovered_tile, _TILE_RESET)
                self.changeTileColor(np, _TILE_HOVERED)
                self.hovered_tile = np
        return task.cont  
    
    def updateCamera(self, task):
        """Task to update position of camera.""" 
        mpos = self.getMousePos()
        if mpos != None:
            if self.is_orbiting:
                self.orbit((self.mx - mpos.getX()) * 100, (self.my - mpos.getY()) * 100)
            else: 
                move_x = False
                move_y = False
                if self.keys['down']: 
                    rad_x1 = base.camera.getH() * (math.pi / 180.0) 
                    pan_rate1 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_y = True 
                if self.keys['up']: 
                    rad_x1 = base.camera.getH() * (math.pi / 180.0) + math.pi 
                    pan_rate1 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_y = True 
                if self.keys['left']: 
                    rad_x2 = base.camera.getH() * (math.pi / 180.0) + math.pi * 0.5 
                    pan_rate2 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_x = True
                if self.keys['right']: 
                    rad_x2 = base.camera.getH() * (math.pi / 180.0) - math.pi*0.5 
                    pan_rate2 = 0.2 * self.cam_dist / self.pan_rate_div 
                    move_x = True 
                
                if move_y: 
                    temp_x = self.target.getX() + math.sin(rad_x1) * pan_rate1 
                    temp_x = self.clamp(temp_x, self.pan_limits_x.getX(), self.pan_limits_x.getY()) 
                    self.target.setX(temp_x) 
                    temp_y = self.target.getY() - math.cos(rad_x1) * pan_rate1 
                    temp_y = self.clamp(temp_y, self.pan_limits_y.getX(), self.pan_limits_y.getY()) 
                    self.target.setY(temp_y) 
                    self.orbit(0, 0) 
                if move_x: 
                    temp_x = self.target.getX() - math.sin(rad_x2) * pan_rate2 
                    temp_x = self.clamp(temp_x, self.pan_limits_x.getX(), self.pan_limits_x.getY()) 
                    self.target.setX(temp_x) 
                    temp_y = self.target.getY() + math.cos(rad_x2) * pan_rate2 
                    temp_y = self.clamp(temp_y, self.pan_limits_y.getX(), self.pan_limits_y.getY()) 
                    self.target.setY(temp_y) 
                    self.orbit(0, 0)
            self.mx = mpos.getX()
            self.my = mpos.getY()
        return task.cont                       
