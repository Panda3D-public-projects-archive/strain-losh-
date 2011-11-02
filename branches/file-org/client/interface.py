from direct.showbase import DirectObject
from panda3d.core import Plane, Vec4, Vec3, Point4, Point3, Point2, NodePath#@UnresolvedImport
from pandac.PandaModules import GeomNode, CardMaker, TextNode#@UnresolvedImport
from pandac.PandaModules import TextureStage, TransparencyAttrib#@UnresolvedImport
from direct.gui.DirectGui import DirectFrame, DGG
from direct.gui.OnscreenText import OnscreenText
from engine.unit import Unit
from unitmodel import UnitModel
from console import GuiConsole

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
        self.unit_move_orientation = Unit.HEADING_NONE
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
        self.deselect_button = GuiButton("topleft", Point3(0.2, 0, -0.3), aspect, plane, "deselect_unit")
        self.punit_button = GuiButton("topleft", Point3(0.0, 0, -0.3), aspect, plane, "prev_unit")
        self.nunit_button = GuiButton("topleft", Point3(0.1, 0, -0.3), aspect, plane, "next_unit")
        self.endturn_button = GuiButton("topleft", Point3(0.0, 0, -0.5), aspect, plane, "end_turn")
        self.action_a = GuiButton("topleft", Point3(0.0, 0, -0.6), aspect, plane, "action_a")
        self.action_b = GuiButton("topleft", Point3(0.0, 0, -0.7), aspect, plane, "action_b")
        self.action_c = GuiButton("topleft", Point3(0.0, 0, -0.8), aspect, plane, "action_c")
        self.action_d = GuiButton("topleft", Point3(0.0, 0, -0.9), aspect, plane, "action_d")
        
        self.action_1 = GuiButton("topleft", Point3(1.5+0.01, 0, -0.09), aspect, plane, "deselect")
        self.action_2 = GuiButton("topleft", Point3(1.6+0.02, 0, -0.09), aspect, plane, "deselect")
        self.action_3 = GuiButton("topleft", Point3(1.7+0.03, 0, -0.09), aspect, plane, "deselect")
        self.action_4 = GuiButton("topleft", Point3(1.5+0.01, 0, -0.2), aspect, plane, "deselect")
        self.action_5 = GuiButton("topleft", Point3(1.6+0.02, 0, -0.2), aspect, plane, "deselect")
        self.action_6 = GuiButton("topleft", Point3(1.7+0.03, 0, -0.2), aspect, plane, "deselect")
        
        self.buttons["deselect"] = self.deselect_button
        self.buttons["prev_unit"] = self.punit_button
        self.buttons["next_unit"] = self.nunit_button
        self.buttons["end_turn"] = self.endturn_button
        self.buttons["action_a"] = self.action_a
        self.buttons["action_b"] = self.action_b
        self.buttons["action_c"] = self.action_c
        self.buttons["action_d"] = self.action_d
        self.buttons["action_1"] = self.action_1
        self.buttons["action_2"] = self.action_2
        self.buttons["action_3"] = self.action_3
        self.buttons["action_4"] = self.action_4
        self.buttons["action_5"] = self.action_5
        self.buttons["action_6"] = self.action_6
        
        self.hovered_gui = None
        
        self.console = GuiConsole(self.ge.a2dBottomLeft, 1.5, 0.4, aspect, self.ge)
        self.stats = GuiTextFrame(Point3(0.3, 0, 0), 0.4, 0.3, 5)
        self.stats2 = GuiTextFrame(Point3(0.7, 0, 0), 0.4, 0.3, 5)
        self.stats3 = GuiTextFrame(Point3(1.1, 0, 0), 0.4, 0.3, 5)
        self.status_bar = GuiTextFrame(Point3(1.5 + 0.01, 0, 0), 0.85, 0.08, 1)
        self.status_bar.write(1, "Player: mirko     Server: Online")
        
        self.accept('l', self.switchLos)
        self.accept('m', self.switchUnitMove)
        self.accept('escape', self.escapeEvent)
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

    def loadTurnArrows(self, dest):
        self.turn_arrow_dict = {}        
        for i in xrange(9):
            m = self.ge.loader.loadModel("sphere")
            m.setScale(0.07, 0.07, 0.07)
            x = dest.getX()+0.5
            y = dest.getY()+0.5   
            delta = 0.4   
            height = 0.8     
            if i == 0:
                pos = Point3(x-delta, y+delta, height)
                h = 45
                key = Unit.HEADING_NW
            elif i == 1:
                pos = Point3(x, y+delta, height)
                h = 0
                key = Unit.HEADING_N                
            elif i ==2:
                pos = Point3(x+delta, y+delta, height)
                h = -45
                key = Unit.HEADING_NE                
            elif i ==3:
                pos = Point3(x-delta, y, height)
                h = 90
                key = Unit.HEADING_W                
            elif i ==4:
                pos = Point3(x+delta, y, height)
                h = -90
                key = Unit.HEADING_E                
            if i == 5:
                pos = Point3(x-delta, y-delta, height)
                h = 135
                key = Unit.HEADING_SW                
            elif i == 6:
                pos = Point3(x, y-delta, height)
                h = 180
                key = Unit.HEADING_S                
            elif i ==7:
                pos = Point3(x+delta, y-delta, height)
                h = 225               
                key = Unit.HEADING_SE
            elif i == 8:
                pos = Point3(x, y, height)
                h = 0
                key = Unit.HEADING_NONE
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
        if key == Unit.HEADING_NONE:
            self.turn_arrow_dict[key].setColor(0,0,1)
        else:
            self.turn_arrow_dict[key].setColor(1,0,0)
        self.unit_move_orientation = key
        
    def displayLos(self):
        """Displays visual indicator of tiles which are in line of sight of the selected unit.
           Tiles in full view are marked with brighter red color.
           Tiles in partial view are marked with darker red color.
        """
        if self.selected_unit:
            losh_dict = self.selected_unit.unit.losh_dict
            for tile in losh_dict:
                tile_node = self.ge.tile_np_list[int(tile[0])][int(tile[1])]
                if losh_dict[tile] == 0:
                    self.changeTileColor(tile_node, _TILE_FULL_LOS)
                elif losh_dict[tile] == 1:
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
    
    def displayUnitMove(self):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        if self.selected_unit:
            move_dict = self.selected_unit.unit.move_dict
            self.movetext_np = NodePath("movetext_np")
            for tile in move_dict:
                text = TextNode('node name')
                text.setText( "%s" % move_dict[tile])
                textNodePath = self.movetext_np.attachNewNode(text)
                textNodePath.setColor(0, 0, 0)
                textNodePath.setScale(0.5, 0.5, 0.5)
                textNodePath.setPos(tile[0]+0.2, tile[1]+0.2, 0.5)
                textNodePath.lookAt(tile[0]+0.2, tile[1]+0.2, -100)
            self.movetext_np.reparentTo(self.ge.node)
            
    def switchUnitMove(self):
        """Switched the display of tiles available for movement for the selected unit."""
        if self.move_visible == True:
            self.movetext_np.removeNode()
            self.move_visible = False
        else:
            pass
            self.displayUnitMove()
            self.move_visible = True


    def selectUnit(self, unit):
        """Performs actions for unit selection.
           Clears previous selection, sets global Interface.selected_unit variable, marks selected unit tile,
           loads and renders selected unit model in an off screen buffer for portrait display.
        """
        self.deselectUnit()
        self.selected_unit = unit
        pos = self.selected_unit.node.getPos()
        #self.markSelectedTile(self.ge.tile_np_list[int(pos.getX())][int(pos.getY())])
        self.selected_unit.marker.loadAnims({"move":"ripple2"})  
        self.selected_unit.marker.loop("move")
        u = self.ge.unit_np_dict[int(unit.id)].unit
        self.off_model = UnitModel(u, scale=1, h=0, pos=Point3(0,-8,-1.7), off=True)
        self.off_model.reparentTo(self.ge.alt_render)
        self.off_model.play(self.off_model.getAnimName("idle"))
        self.printUnitData()

    def escapeEvent(self):
        if self.selected_unit:
            self.deselectUnit()
        else:
            messenger.send("shutdown-event")

    def deselectUnit(self):
        """Performs actions for unit deselection.
           Clears unit tile, cleans up off screen models, 
           clears Interface.selected_unit variable.
        """
        self.clearUnitData()
        if self.selected_unit:
            #self.clearSelectedTile(self.selected_unit_tile)
            self.selected_unit.marker.stop()
            self.selected_unit.marker.unloadAnims({"move":"ripple2"}) 
            if self.off_model:
                self.ge.destroyUnit(self.off_model)
            self.ge.clearOutlineShader(self.selected_unit.model)
            self.selected_unit = None

        
    def selectPrevUnit(self):
        """Selects previous unit in the same team with unspent action points."""
        None
        
    def selectNextUnit(self):
        """Selects next unit in the same team with unspent action points."""
        None
        
    def printUnitData(self):
        unit = self.selected_unit
        if unit:
            unit_type = self.ge.getUnitData(unit, "type")
            unit_HP = self.ge.getUnitData(unit, "HP")
            unit_AP = self.ge.getUnitData(unit, "AP")
            unit_default_HP = self.ge.getUnitData(unit, "default_HP")
            unit_default_AP = self.ge.getUnitData(unit, "default_AP")
            self.stats.write(1, unit_type)
            self.stats.write(5, "oruzje1")
            self.stats2.write(2, "HP: " + str(unit_HP) + "/" + str(unit_default_HP))
            self.stats2.write(3, "AP: " + str(unit_AP) + "/" + str(unit_default_AP))
            self.stats2.write(4, "stat3: XX/YY")
            self.stats3.write(2, "stat4: XX/YY")
            self.stats3.write(3, "stat5: XX/YY")
            self.stats3.write(4, "stat6: XX/YY")
            
    def clearUnitData(self):
        self.stats.write(1, "")
        self.stats.write(5, "")
        self.stats2.write(2, "")
        self.stats2.write(3, "")
        self.stats2.write(4, "")
        self.stats3.write(2, "")
        self.stats3.write(3, "")
        self.stats3.write(4, "")
                
    def endTurn(self):
        """Ends the turn"""
        self.ge.createEndTurnMsg() 

    def mouseLeftClick(self):
        """Handles left mouse click actions.
           Procedure first checks for gui clicks, if there are none then it checks 3d collision.
        """
        self.destination = None
        if self.hovered_gui == self.deselect_button:
            self.deselectUnit()
            self.console.unfocus()
        elif self.hovered_gui == self.punit_button:
            self.selectPrevUnit()
            self.console.unfocus()
        elif self.hovered_gui == self.nunit_button:
            self.selectNextUnit()
            self.console.unfocus() 
        elif self.hovered_gui == self.endturn_button:
            self.endTurn()
            self.console.unfocus()
        elif self.hovered_gui == self.console:
            self.console.focus()
        else:
            self.console.unfocus()    
            selected = self.getMouseHoveredObject()
            if selected:
                node_type = selected.findNetTag("type").getTag("type")
                if node_type == "unit" or node_type == "unit_marker":
                    unit_id = int(selected.findNetTag("id").getTag("id"))
                    unit = self.ge.unit_np_dict[unit_id] 
                    if self.selected_unit != unit:
                        self.selectUnit(unit)
                    else:
                        # Remember movement tile so we can send orientation message when mouse is depressed
                        self.unit_move_destination = Point2(int(unit.node.getX()), int(unit.node.getY()))
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
        if self.selected_unit and self.unit_move_destination and self.unit_move_orientation != Unit.HEADING_NONE:   
            # Send movement message to engine
            x = self.unit_move_destination.getX()
            y = self.unit_move_destination.getY()
            if self.unit_move_orientation == Unit.HEADING_NW:
                o = Point2(x-1, y+1)
            elif self.unit_move_orientation == Unit.HEADING_N:
                o = Point2(x, y+1)
            elif self.unit_move_orientation == Unit.HEADING_NE:
                o = Point2(x+1, y+1)
            elif self.unit_move_orientation == Unit.HEADING_W:
                o = Point2(x-1, y)
            elif self.unit_move_orientation == Unit.HEADING_E:
                o = Point2(x+1, y)
            elif self.unit_move_orientation == Unit.HEADING_SW:
                o = Point2(x-1, y-1)
            elif self.unit_move_orientation == Unit.HEADING_S:
                o = Point2(x, y-1)
            elif self.unit_move_orientation == Unit.HEADING_SE:
                o = Point2(x+1, y-1)
            self.ge.createMoveMsg(self.selected_unit, (self.unit_move_destination.x, self.unit_move_destination.y), 
                                                            (o.x, o.y))
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
                    #self.changeUnitColor(self.hovered_unit, _UNIT_RESET)
                    self.ge.clearOutlineShader(self.hovered_unit)
                    self.hovered_unit = None
                if self.hovered_tile != np:
                    if self.hovered_tile:
                        self.changeTileColor(self.hovered_tile, _TILE_RESET)
                    self.changeTileColor(np, _TILE_HOVERED)
                    self.hovered_tile = np
            elif node_type == "unit_marker":
                np_unit = self.ge.unit_np_dict[int(np.findNetTag("id").getTag("id"))].model
                if self.hovered_tile:
                    self.changeTileColor(self.hovered_tile, _TILE_RESET)  
                    self.hovered_tile = None              
                if self.hovered_unit != np_unit:
                    if self.hovered_unit:
                        #self.changeUnitColor(self.hovered_unit, _UNIT_RESET)
                        self.ge.clearOutlineShader(self.hovered_unit)
                    #self.changeUnitColor(np_unit, _UNIT_HOVERED)
                    self.hovered_unit = np_unit
                    self.ge.setOutlineShader(np_unit, self.ge.unit_np_dict[int(np.findNetTag("id").getTag("id"))].team_color)                
            elif node_type == "unit":
                np_unit = np.getParent()
                if self.hovered_tile:
                    self.changeTileColor(self.hovered_tile, _TILE_RESET)  
                    self.hovered_tile = None              
                if self.hovered_unit != np_unit:
                    if self.hovered_unit:
                        #self.changeUnitColor(self.hovered_unit, _UNIT_RESET)
                        self.ge.clearOutlineShader(self.hovered_unit)
                    #self.changeUnitColor(np_unit, _UNIT_HOVERED)
                    self.hovered_unit = np_unit
                    self.ge.setOutlineShader(np_unit, self.ge.unit_np_dict[int(np.findNetTag("id").getTag("id"))].team_color) 
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
                        if self.dummy_turn_dest_node.getX() >= 0:
                            x = int(self.dummy_turn_dest_node.getX())
                        else:
                            x = int(self.dummy_turn_dest_node.getX()-1)
                        if self.dummy_turn_dest_node.getY() >= 0:
                            y = int(self.dummy_turn_dest_node.getY())
                        else:
                            y = int(self.dummy_turn_dest_node.getY()-1)    
                        dest_node_pos = Point2(x, y)
                        pos_node_pos = Point2(int(self.dummy_turn_pos_node.getX()), int(self.dummy_turn_pos_node.getY()))
                        if dest_node_pos == pos_node_pos:
                            key = Unit.HEADING_NONE
                        elif h >= -22.5 and h < 22.5:
                            key = Unit.HEADING_N
                        elif h >= 22.5 and h < 67.5:
                            key = Unit.HEADING_NW
                        elif h >= 67.5 and h < 112.5:
                            key = Unit.HEADING_W
                        elif h >= 112.5 and h < 157.5:
                            key = Unit.HEADING_SW
                        elif (h >= 157.5 and h <= 180) or (h >= -180 and h < -157.5):
                            key = Unit.HEADING_S
                        elif h >= -157.5 and h < -112.5:
                            key = Unit.HEADING_SE
                        elif h >= -112.5 and h < -67.5:
                            key = Unit.HEADING_E
                        elif h >= -67.5 and h < -22.5:
                            key = Unit.HEADING_NE
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
        self.node.reparentTo(aspect2d)#@UndefinedVariable
        self.redraw()
    
    def setTexture(self, tex):
        self.back_node.setTexture(tex)
    
    def redraw(self):
        if self.hugpos == "topleft":
            p = base.a2dTopLeft.getPos()#@UndefinedVariable
            p.setZ(p.getZ() - self.height)
        elif self.hugpos == "topright":
            p = base.a2dTopRight.getPos()#@UndefinedVariable
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
        self.node = aspect2d.attachNewNode("guibutton")#@UndefinedVariable
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.node.setAlphaScale(0.5) 
        geom = GeomNode('plane')
        geom.addGeomsFrom(plane.getChild(0).getChild(0).node())
        self.frame = self.node.attachNewNode(geom) 
        self.frame.setScale(0.05)
        self.node.setTexture(loader.loadTexture(name+".png"))#@UndefinedVariable
        self.hugpos = hugpos
        self.offset = offset
        self.redraw(aspect)

    def redraw(self, aspect, flag="wide"):
        if self.hugpos == "topleft":
            p = base.a2dTopLeft.getPos()#@UndefinedVariable
            p.setX(p.getX() + self.offset.getX() + 0.05)
            p.setZ(p.getZ() + self.offset.getZ() - 0.05)
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
                  
class GuiTextFrame:
    def __init__(self, offset, h_size, v_size, numLines):
        self.numLines = numLines
        self.frame = DirectFrame(   relief = DGG.FLAT
                                  , frameColor = (0, 0, 0, 0.2)
                                  , scale = 1
                                  , frameSize = (0, h_size, 0, -v_size) )
        
        self.frame.reparentTo(base.a2dTopLeft)#@UndefinedVariable
        self.offset = offset
        self.frame.setPos(self.offset.getX(), 0, self.offset.getZ())

        fixedWidthFont = loader.loadFont("config/monoMMM_5.ttf")#@UndefinedVariable
        if not fixedWidthFont.isValid():
            print "pandaInteractiveConsole.py :: could not load the defined font %s" % str(self.font)
            fixedWidthFont = DGG.getDefaultFont()
        
        if numLines == 1:
            self.lineHeight = 0.05
        else:
            self.lineHeight = v_size*0.9 / numLines
            
        # output lines
        self.frameOutputList = list()
        for i in xrange( self.numLines ):
            label = OnscreenText( parent = self.frame
                              , text = ""
                              , pos = (0.005, -(i+1)*self.lineHeight)
                              , align=TextNode.ALeft
                              , mayChange=1
                              , scale=0.04
                              , fg = (1,1,1,1)
                              , shadow = (0, 0, 0, 1))
                              #, frame = (200,0,0,1) )
            label.setFont( fixedWidthFont )
            self.frameOutputList.append( label )

    def write(self, lineNumber, text):
        if lineNumber > self.numLines:
            return
        self.frameOutputList[lineNumber - 1].setText(text)
        
    def redraw(self):
        p = base.a2dTopLeft.getPos()#@UndefinedVariable
        p.setX(p.getX() + self.offset.getX())
        p.setZ(p.getZ() - 0.05)
        self.frame.setPos(p)


                  
