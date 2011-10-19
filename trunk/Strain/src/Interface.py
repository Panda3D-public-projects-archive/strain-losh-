from direct.showbase import DirectObject
from panda3d.core import Plane, Vec4, Vec3, Vec2, Point4, Point3, Point2, NodePath
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from pandac.PandaModules import GeomNode, CardMaker, TextNode
from pandac.PandaModules import Texture, TextureStage, RenderAttrib, DepthOffsetAttrib, TransparencyAttrib
from UnitModel import UnitModel
from Console import GuiConsole

#===============================================================================
# GLOBAL DEFINITIONS
#===============================================================================

_TILE_AVAILABLE_MOVE    = "_tile_available_move"
_TILE_HOVERED           = "_tile_hovered"
_TILE_FULL_LOS          = "_tile_full_los"
_TILE_PARTIAL_LOS       = "_tile_partial_los"
_TILE_UNIT_POS          = "_tile_unit_pos"
_TILE_MOVE              = "_tile_move"
_TILE_RESET             = "_tile_reset"

_UNIT_HOVERED           = "_unit_hovered"
_UNIT_RESET             = "_unit_reset"    

_UNIT_HEADING_NONE      = 0
_UNIT_HEADING_NW        = 1
_UNIT_HEADING_N         = 2
_UNIT_HEADING_NE        = 3
_UNIT_HEADING_W         = 4
_UNIT_HEADING_E         = 5
_UNIT_HEADING_SW        = 6
_UNIT_HEADING_S         = 7
_UNIT_HEADING_SE        = 8

#===============================================================================
# CLASS Interface --- DEFINITION
#===============================================================================

class Interface(DirectObject.DirectObject):
    buttons = {}
    def __init__(self, ge):
        # Keep pointer to the GraphicsEngine parent class
        self.ge = ge
        
        # Initialize variables
        self.los_visible = False
        self.unit_los_visible = False
        self.move_visible = False
        
        self.hovered_tile = None
        self.hovered_unit = None
        self.selected_unit = None
        self.off_model = None
        self.selected_unit_tex = self.ge.loader.loadTexture("sel.png")
        self.selected_unit_tile = None
        
        self.movetext_np = None       
        
        self.move_timer = 0
        self.unit_move_destination = None
        self.unit_move_orientation = _UNIT_HEADING_NONE
        self.turn_np = NodePath("turn_arrows_np")
        self.turn_np.reparentTo(self.ge.render)
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0.3))  
        self.dummy_turn_pos_node = NodePath("dummy_turn_pos_node")
        self.dummy_turn_dest_node = NodePath("dummy_turn_dest_node")
        
        wp = self.ge.win.getProperties() 
        aspect = float(wp.getXSize()) / wp.getYSize()
        plane = self.ge.loader.loadModel('plane')
        plane.setScale(2)
        plane.flattenLight()
        self.unit_card = GuiCard(0.3, 0.3, 0.01, None, "topleft", Point4(0, 0, 0, 0))
        self.unit_card.setTexture(self.ge.alt_buffer.getTexture())
        self.deselect_button = GuiButton("topleft", Point3(0.3 + 0.05, 0, 0.95), aspect, plane, "deselect")
        self.punit_button = GuiButton("topleft", Point3(0.4 + 0.05, 0, 0.95), aspect, plane, "prev_unit")
        self.nunit_button = GuiButton("topleft", Point3(0.5 + 0.05, 0, 0.95), aspect, plane, "next_unit")
        self.endturn_button = GuiButton("topleft", Point3(0.6 + 0.05, 0, 0.95), aspect, plane, "end_turn")
        
        #Mirkova zelja moja zapovijed
        self.buttons["deselect"] = self.deselect_button
        self.buttons["prev_unit"] = self.punit_button
        self.buttons["next_unit"] = self.nunit_button
        self.buttons["end_turn"] = self.endturn_button
        
        self.hovered_gui = None
        
        self.console = GuiConsole(self.ge.a2dBottomLeft, 1.5, 0.4, aspect)
        
        self.accept('l', self.switchLos)
        self.accept('o', self.switchUnitLos)
        self.accept('m', self.switchUnitMove)
        self.accept("mouse1", self.mouseLeftClick)
        self.accept("mouse1-up", self.mouseLeftClickUp)
        
        self.ge.taskMgr.add(self.processGui, 'processGui_task')
        self.ge.taskMgr.add(self.hover, 'hover_task') 
        self.ge.taskMgr.add(self.turnUnit, 'turnUnit_task')       
    
    def redraw(self):
        wp = self.ge.win.getProperties() 
        aspect = float(wp.getXSize()) / wp.getYSize()
        if aspect >= 1:
            flag = "wide"
            calc_aspect = aspect
        elif aspect < 1 and aspect != 0:
            flag = "tall"
            calc_aspect = 1 / aspect
   
        self.unit_card.redraw()
        
        for button in self.buttons.values():
            button.redraw(calc_aspect, flag)

        self.hovered_gui = None

    def getMousePos(self):
        """Returns mouse coordinates if mouse pointer is inside Panda window."""
        if self.ge.mouseWatcherNode.hasMouse(): 
            return self.ge.mouseWatcherNode.getMouse() 
        return None

    def getMouseHoveredObject(self):
        """Returns the closest object in the scene graph over which we hover mouse pointer.
           Returns None if no objects found.
        """
        pos = self.getMousePos()
        if pos:
            self.ge.coll_ray.setFromLens(self.ge.camNode, pos.getX(), pos.getY())
            self.ge.coll_trav.traverse(self.ge.render)
            if self.ge.coll_queue.getNumEntries() > 0:
                self.ge.coll_queue.sortEntries()
                np = self.ge.coll_queue.getEntry(0).getIntoNodePath()
                return np
        return None

    def setUnitColorScale(self, unit, r, g, b, alpha):
        """Sets color scale of unit nodepath.
           r, g, b, a = 1, 1, 1, 1 resets the color scale
        """
        unit.setColorScale(r, g, b, alpha)
        
    def setTileColorScale(self, tile, r, g, b, alpha):
        """Sets color scale of tile nodepath.
        """
        tile.setColorScale(r, g, b, alpha)

    def changeUnitColor(self, unit, event, rgba=None):
        """Changes color of the unit nodepath according to event.
           Event defines the reason and scale for color change.
        """
        if   event == _UNIT_HOVERED:
            self.setUnitColorScale(unit, 0.1, 0.1, 0.1, 1)            
        elif event == _UNIT_RESET:
            unit.clearColorScale()
        else:
            unit.clearColorScale()

    def changeTileColor(self, tile, event, rgba=None, flag=None):
        """Changes color of the tile nodepath according to event.
           Event defines the reason and scale for color change.
        """
        if   event == _TILE_AVAILABLE_MOVE:
            self.setTileColorScale(tile, 2, 2, 2, 1)
        elif event == _TILE_HOVERED:
            self.setTileColorScale(tile, 2, 2, 2, 1)
        elif event == _TILE_FULL_LOS:
            self.setTileColorScale(tile, 2, 0.6, 0.6, 1)
        elif event == _TILE_PARTIAL_LOS:
            self.setTileColorScale(tile, 1, 0.6, 0.6, 1)
        elif event == _TILE_MOVE:
            print flag
            self.setTileColorScale(tile, 0.6, 0.6, 2, 1)
        elif event == _TILE_UNIT_POS:
            r = rgba.getX()
            g = rgba.getY()
            b = rgba.getZ()
            a = rgba.getW()
            self.setTileColorScale(tile, r, g, b, a)
        elif event == _TILE_RESET:
            tile.clearColorScale()
            #self.setTileColorScale(tile, 1, 1, 1, 1)
        else:
            tile.clearColorScale()
            #self.setTileColorScale(tile, 1, 1, 1, 1)
            
    def resetAllTileColor(self):
        """Resets the color of all tiles in the level."""
        for tile_list in self.ge.tile_np_list:
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
        if self.selected_unit.model.findNetTag("player_name").getTag("player_name") == "ultramarinac":
            color = Vec4(1, 0, 0, 1)
        else:
            color = Vec4(0, 0, 1, 1)
        self.setTileBlendTexture(tile, self.selected_unit_tex, color)
        self.selected_unit_tile = tile
        
    def clearSelectedTile(self, tile):
        """Clear the mark from the tile of the selected unit."""
        self.clearTileBlendTexture(tile)

    def loadTurnArrows(self, dest):
        self.turn_arrow_dict = {}        
        for i in xrange(8):
            """m = self.ge.loader.loadModel("arrow")
            m.setScale(0.1, 0.1, 0.1)
            m.setR(35)
            m.setLightOff()
            m.flattenLight()
            m.setColor(1, 1, 1)
            x = dest.getX()+0.5
            y = dest.getY()+0.5
            """
            m = self.ge.loader.loadModel("sphere")
            m.setScale(0.07, 0.07, 0.07)
            x = dest.getX()+0.5
            y = dest.getY()+0.5   
            delta = 0.4   
            height = 0.8     
            if i == 0:
                pos = Point3(x-delta, y+delta, height)
                h = 45
                key = _UNIT_HEADING_NW
            elif i == 1:
                pos = Point3(x, y+delta, height)
                h = 0
                key = _UNIT_HEADING_N                
            elif i ==2:
                pos = Point3(x+delta, y+delta, height)
                h = -45
                key = _UNIT_HEADING_NE                
            elif i ==3:
                pos = Point3(x-delta, y, height)
                h = 90
                key = _UNIT_HEADING_W                
            elif i ==4:
                pos = Point3(x+delta, y, height)
                h = -90
                key = _UNIT_HEADING_E                
            if i == 5:
                pos = Point3(x-delta, y-delta, height)
                h = 135
                key = _UNIT_HEADING_SW                
            elif i == 6:
                pos = Point3(x, y-delta, height)
                h = 180
                key = _UNIT_HEADING_S                
            elif i ==7:
                pos = Point3(x+delta, y-delta, height)
                h = 225               
                key = _UNIT_HEADING_SE
            m.setPos(pos)
            m.setH(h)
            m.reparentTo(self.turn_np)
            self.turn_arrow_dict[key] = m
        
    def removeTurnArrows(self):
        for child in self.turn_np.getChildren():
            child.remove()
        self.turn_arrow_dict = {}
            
    def markTurnArrow(self, key):
        for i in self.turn_arrow_dict.itervalues():
            i.setColor(1,1,1)
        if key != _UNIT_HEADING_NONE:
            self.turn_arrow_dict[key].setColor(1,0,0)
        self.unit_move_orientation = key
        
    def displayLos(self):
        """Displays visual indicator of tiles which are in line of sight of the selected unit.
           Tiles in full view are marked with brighter red color.
           Tiles in partial view are marked with darker red color.
        """
        if self.selected_unit:
            pass
            # TODO: krav: Dodati msg koji grafici vraca LOSHDict
            """
            losh_dict = self.ge.engine.getLOSHDict(Point2(self.selected_unit.x, self.selected_unit.y))
            for tile in losh_dict:
                tile_node = self.ge.tile_np_list[int(tile.x)][int(tile.y)]
                if losh_dict[tile] == 0:
                    self.changeTileColor(tile_node, _TILE_FULL_LOS)
                elif losh_dict[tile] == 1:
                    self.changeTileColor(tile_node, _TILE_PARTIAL_LOS)
                else:
                    self.changeTileColor(tile_node, _TILE_RESET)      
            """
            
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
            pass
            """
            los_list = self.ge.engine.getLOS(Point2(self.selected_unit.x, self.selected_unit.y), Point2(13,13))
            for tile in los_list:
                tile_node = self.ge.tile_np_list[int(tile[0].x)][int(tile[0].y)]
                if tile[1] == 0:
                    self.changeTileColor(tile_node, _TILE_FULL_LOS)
                elif tile [1] == 1:
                    self.changeTileColor(tile_node, _TILE_PARTIAL_LOS)
                else:
                    self.changeTileColor(tile_node, _TILE_RESET)
            """
             
    def switchUnitLos(self):
        """Switched the display of line of sight from selected unit to enemy unit on or off."""
        if self.unit_los_visible == True:
            self.resetAllTileColor()
            self.unit_los_visible = False
        else:
            self.displayUnitLos()
            self.unit_los_visible = True        
    
    def displayUnitMove(self):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        if self.selected_unit:
            pass
            """
            unit = self.ge.engine.units[self.selected_unit.id]
            ap = unit.current_AP
            move_dict = self.ge.engine.getMoveDict(unit)
            self.movetext_np = NodePath("movetext_np")
            for tile in move_dict:
                text = TextNode('node name')
                text.setText( "%s" % move_dict[tile])
                textNodePath = self.movetext_np.attachNewNode(text)
                textNodePath.setColor(0, 0, 0)
                textNodePath.setScale(0.5, 0.5, 0.5)
                textNodePath.setPos(tile.x+0.2, tile.y+0.2, 0.5)
                textNodePath.lookAt(tile.x+0.2, tile.y+0.2, -100)
            self.movetext_np.reparentTo(self.ge.node)
            """
            
    def switchUnitMove(self):
        """Switched the display of tiles available for movement for the selected unit."""
        if self.move_visible == True:
            pass
            #self.movetext_np.removeNode()
            #self.move_visible = False
        else:
            pass
            #self.displayUnitMove()
            #self.move_visible = True


    def selectUnit(self, unit):
        """Performs actions for unit selection.
           Clears previous selection, sets global Interface.selected_unit variable, marks selected unit tile,
           loads and renders selected unit model in an off screen buffer for portrait display.
        """
        self.deselectUnit()
        self.selected_unit = unit
        pos = self.selected_unit.model.getPos()
        self.markSelectedTile(self.ge.tile_np_list[int(pos.getX())][int(pos.getY())])
        u = self.ge.unit_np_dict[int(unit.id)].unit
        self.off_model = UnitModel(u, scale=1, h=0, pos=Point3(0,-8,-1.7))
        self.off_model.reparentTo(self.ge.alt_render)
        self.off_model.play(self.off_model.getAnimName("idle"))

    def deselectUnit(self):
        """Performs actions for unit deselection.
           Clears unit tile, cleans up off screen models, 
           clears Interface.selected_unit variable.
        """
        if self.selected_unit:
            self.clearSelectedTile(self.selected_unit_tile)
            if self.off_model:
                self.ge.destroyUnit(self.off_model)
            self.selected_unit = None
        
    def selectPrevUnit(self):
        """Selects previous unit in the same team with unspent action points."""
        None
        
    def selectNextUnit(self):
        """Selects next unit in the same team with unspent action points."""
        None
        
    def endTurn(self):
        """Ends the turn"""   

    def mouseLeftClick(self):
        """Handles left mouse click actions.
           Procedure first checks for gui clicks, if there are none then it checks 3d collision.
        """
        self.destination = None
        if self.hovered_gui == self.deselect_button:
            self.deselectUnit()
        elif self.hovered_gui == self.punit_button:
            self.selectPrevUnit()
        elif self.hovered_gui == self.nunit_button:
            self.selectNextUnit() 
        elif self.hovered_gui == self.endturn_button:
            self.endTurn()
        else:    
            selected = self.getMouseHoveredObject()
            if selected:
                node_type = selected.findNetTag("type").getTag("type")
                if node_type == "unit":
                    unit_id = int(selected.findNetTag("id").getTag("id"))
                    unit = self.ge.unit_np_dict[unit_id] 
                    if self.selected_unit != unit:
                        self.selectUnit(unit)
                    else:
                        # Remember movement tile so we can send orientation message when mouse is depressed
                        self.unit_move_destination = Point2(int(unit.model.getX()), int(unit.model.getY()))
                elif node_type == "tile":
                    p = selected.getParent().getPos()
                    u = self.ge.unit_np_list[int(p.x)][int(p.y)]
                    if u:
                        unit = u
                        if self.selected_unit == unit:
                            # Remember movement tile so we can send orientation message when mouse is depressed
                            self.unit_move_destination = Point2(p.x, p.y)
                    else:
                        unit = None
                        if self.selected_unit:
                            # Remember movement tile so we can send movement message when mouse is depressed
                            self.unit_move_destination = Point2(p.x, p.y)
                    if unit:
                        if self.selected_unit != unit:
                            self.selectUnit(unit)
                            
    def mouseLeftClickUp(self):
        """Handles left mouse click actions when mouse button is depressed.
           Used for unit movement.
        """
        if self.selected_unit and self.unit_move_destination and self.unit_move_orientation != _UNIT_HEADING_NONE:   
            # Send movement message to engine
            x = self.unit_move_destination.getX()
            y = self.unit_move_destination.getY()
            if self.unit_move_orientation == _UNIT_HEADING_NW:
                o = Point2(x-1, y+1)
            elif self.unit_move_orientation == _UNIT_HEADING_N:
                o = Point2(x, y+1)
            elif self.unit_move_orientation == _UNIT_HEADING_NE:
                o = Point2(x+1, y+1)
            elif self.unit_move_orientation == _UNIT_HEADING_W:
                o = Point2(x-1, y)
            elif self.unit_move_orientation == _UNIT_HEADING_E:
                o = Point2(x+1, y)
            elif self.unit_move_orientation == _UNIT_HEADING_SW:
                o = Point2(x-1, y-1)
            elif self.unit_move_orientation == _UNIT_HEADING_S:
                o = Point2(x, y-1)
            elif self.unit_move_orientation == _UNIT_HEADING_SE:
                o = Point2(x+1, y-1)
            self.ge.createMoveMsg(self.selected_unit, self.unit_move_destination, o)
        self.unit_move_destination = None
        self.move_timer = 0
        self.removeTurnArrows()

#===============================================================================
# CLASS Interface --- TASKS
#===============================================================================
    def hover(self, task):
        """Visually marks and selects tiles or units over which mouse cursor hovers."""
        np = self.getMouseHoveredObject()
        if np:
            node_type = np.findNetTag("type").getTag("type")
            if node_type == "tile":
                if self.hovered_unit:
                    self.changeUnitColor(self.hovered_unit, _UNIT_RESET)
                    self.hovered_unit = None
                if self.hovered_tile != np:
                    if self.hovered_tile:
                        self.changeTileColor(self.hovered_tile, _TILE_RESET)
                    self.changeTileColor(np, _TILE_HOVERED)
                    self.hovered_tile = np
            elif node_type == "unit":
                np_unit = np.getParent()
                if self.hovered_tile:
                    self.changeTileColor(self.hovered_tile, _TILE_RESET)  
                    self.hovered_tile = None              
                if self.hovered_unit != np_unit:
                    if self.hovered_unit:
                        self.changeUnitColor(self.hovered_unit, _UNIT_RESET)
                    self.changeUnitColor(np_unit, _UNIT_HOVERED)
                    self.hovered_unit = np_unit
        else:
            if self.hovered_unit:
                self.changeUnitColor(self.hovered_unit, _UNIT_RESET)
            if self.hovered_tile:
                self.changeTileColor(self.hovered_tile, _TILE_RESET)                
        return task.cont 
    
    def processGui(self, task):
        """Visually marks and selects GUI element over which mouse cursor hovers."""
        if self.ge.mouseWatcherNode.hasMouse(): 
            mpos = self.ge.mouseWatcherNode.getMouse()
            hovering_over_something = False
            
            #Vidi me kako iteriram kroz dictionary
            for button in self.buttons.values():
                button.frame.setAlphaScale(0.5)
                if mpos.x >= button.pos_min_x and mpos.x <= button.pos_max_x and mpos.y >= button.pos_min_y and mpos.y <= button.pos_max_y:
                    self.hovered_gui = button
                    button.frame.setAlphaScale(1)
                    hovering_over_something = True
                    self.console.hide()
            #Hovering iznad konzole
            # TODO: vjeks: srediti da kad konzola ima fokus da se ne hajda! 
            if  mpos.x >= self.console.pos_min_x and mpos.x <= self.console.pos_max_x and mpos.y >= self.console.pos_min_y and mpos.y <= self.console.pos_max_y:                 
                self.hovered_gui = self.console
                hovering_over_something = True
                self.console.show()
                                
            if not hovering_over_something:
                self.hovered_gui = None
                self.console.hide()
  
        return task.cont    

    def turnUnit(self, task):
        if self.unit_move_destination: 
            if self.move_timer < 0.1:
                dt = globalClock.getDt()
                self.move_timer += dt
                if self.move_timer > 0.1:
                    self.loadTurnArrows(self.unit_move_destination)
                    pos = Point3(self.unit_move_destination.getX()+0.5, self.unit_move_destination.getY()+0.5, 0.3)
                    self.dummy_turn_pos_node.setPos(pos)
            else: 
                if self.ge.mouseWatcherNode.hasMouse(): 
                    mpos = self.ge.mouseWatcherNode.getMouse() 
                    pos3d = Point3() 
                    nearPoint = Point3() 
                    farPoint = Point3() 
                    self.ge.camLens.extrude(mpos, nearPoint, farPoint) 
                    if self.plane.intersectsLine(pos3d, self.ge.render.getRelativePoint(self.ge.camera, nearPoint), self.ge.render.getRelativePoint(self.ge.camera, farPoint)): 
                        self.dummy_turn_dest_node.setPos(pos3d)
                        self.dummy_turn_pos_node.lookAt(self.dummy_turn_dest_node)
                        h = self.dummy_turn_pos_node.getH()
                        dest_node_pos = Point2(int(self.dummy_turn_dest_node.getX()), int(self.dummy_turn_dest_node.getY()))
                        pos_node_pos = Point2(int(self.dummy_turn_pos_node.getX()), int(self.dummy_turn_pos_node.getY()))
                        if dest_node_pos == pos_node_pos:
                            key = _UNIT_HEADING_NONE
                        elif h >= -22.5 and h < 22.5:
                            key = _UNIT_HEADING_N
                        elif h >= 22.5 and h < 67.5:
                            key = _UNIT_HEADING_NW
                        elif h >= 67.5 and h < 112.5:
                            key = _UNIT_HEADING_W
                        elif h >= 112.5 and h < 157.5:
                            key = _UNIT_HEADING_SW
                        elif (h >= 157.5 and h <= 180) or (h >= -180 and h < -157.5):
                            key = _UNIT_HEADING_S
                        elif h >= -157.5 and h < -112.5:
                            key = _UNIT_HEADING_SE
                        elif h >= -112.5 and h < -67.5:
                            key = _UNIT_HEADING_E
                        elif h >= -67.5 and h < -22.5:
                            key = _UNIT_HEADING_NE
                        self.markTurnArrow(key)
        return task.cont


#===============================================================================
# CLASS GuiCard --- DEFINITION
#===============================================================================
class GuiCard:
    def __init__(self, width, height, border_size, pos, hugpos, color):
        self.hugpos = hugpos
        self.width = width
        self.height = height
        self.border_size = border_size
        self.pos = pos
        self.node = NodePath("guicard")
        self.frame_node = NodePath("frame")
        cm = CardMaker("cm_left")
        cm.setFrame(0, border_size, 0, height)
        n = self.frame_node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        cm = CardMaker("cm_right")
        cm.setFrame(0, border_size, 0, height)
        n = self.frame_node.attachNewNode(cm.generate())
        n.setPos(width - border_size, 0, 0)
        cm = CardMaker("cm_top")
        cm.setFrame(0, width, height - border_size, width)
        n = self.frame_node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        cm = CardMaker("cm_bottom")
        cm.setFrame(0, width, 0, border_size)
        n = self.frame_node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        self.frame_node.setColor(color)
        self.frame_node.flattenStrong()
        self.frame_node.reparentTo(self.node)
        cm = CardMaker("cm_back")
        cm.setFrame(0+border_size, width-border_size, 0+border_size, height-border_size)
        self.back_node = self.node.attachNewNode(cm.generate())
        self.back_node.setPos(0, 0, 0)
        self.back_node.setTransparency(1)
        self.node.reparentTo(aspect2d)
        self.redraw()
    
    def setTexture(self, tex):
        self.back_node.setTexture(tex)
    
    def redraw(self):
        if self.hugpos == "topleft":
            p = base.a2dTopLeft.getPos()
            p.setZ(p.getZ() - self.height)
        elif self.hugpos == "topright":
            p = base.a2dTopRight.getPos()
            p.setZ(p.getZ() - self.height)
        elif self.hugpos == None:
            p = self.pos
        self.node.setPos(p)
    
    def removeNode(self):
        self.node.removeNode()


#===============================================================================
# CLASS GuiButton --- DEFINITION
#===============================================================================
class GuiButton:
    def __init__(self, hugpos, offset, aspect, plane, name):
        self.node = aspect2d.attachNewNode("guibutton")
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.node.setAlphaScale(0.5) 
        geom = GeomNode('plane')
        geom.addGeomsFrom(plane.getChild(0).getChild(0).node())
        self.frame = self.node.attachNewNode(geom) 
        self.frame.setScale(0.05)
        self.node.setTexture(loader.loadTexture(name+".png"))
        self.hugpos = hugpos
        self.offset = offset
        self.redraw(aspect)

    def redraw(self, aspect, flag="wide"):
        if self.hugpos == "topleft":
            p = base.a2dTopLeft.getPos()
            p.setX(p.getX() + self.offset.getX())
            p.setZ(p.getZ() - 0.05)
        self.frame.setPos(p)
        if flag == "wide":
            posx, posy = self.frame.getTightBounds()
            self.pos_min_x = posx.getX() / aspect
            self.pos_min_y = posx.getZ()
            self.pos_max_x = posy.getX() / aspect
            self.pos_max_y = posy.getZ()
        elif flag == "tall":
            posx, posy = self.frame.getTightBounds()
            self.pos_min_x = posx.getX()
            self.pos_min_y = posx.getZ() / aspect
            self.pos_max_x = posy.getX()
            self.pos_max_y = posy.getZ() / aspect            
            
    def removeNode(self):
            self.node.removeNode()   
                  

