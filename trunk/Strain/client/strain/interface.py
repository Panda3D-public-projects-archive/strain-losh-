from direct.showbase import DirectObject
from panda3d.core import Plane, Vec3, Point4, Point3, Point2, NodePath#@UnresolvedImport
from panda3d.core import GeomNode, CardMaker, TextNode, Texture, TextureStage#@UnresolvedImport
from panda3d.core import TransparencyAttrib#@UnresolvedImport
from direct.gui.DirectGui import DirectFrame, DGG
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import LerpColorScaleInterval, LerpColorInterval, Wait, Sequence#@UnresolvedImport
from console import GuiConsole
from client_messaging import *
from gui_elements import *
import utils

#===============================================================================
# GLOBAL DEFINITIONS
#===============================================================================

_TILE_AVAILABLE_MOVE    = "_tile_available_move"
_TILE_HOVERED           = "_tile_hovered"
_TILE_FULL_LOS          = "_tile_full_los"
_TILE_PARTIAL_LOS       = "_tile_partial_los"
_TILE_UNIT_POS          = "_tile_unit_pos"
_TILE_NOT_IN_LOS        = "_tile_not_in_los"
_TILE_MOVE              = "_tile_move"
_TILE_RESET             = "_tile_reset"

_UNIT_HOVERED           = "_unit_hovered"
_UNIT_RESET             = "_unit_reset"    

#TODO: ovo je kopirano iz unit.py
HEADING_NONE      = 0
HEADING_NW        = 1
HEADING_N         = 2
HEADING_NE        = 3
HEADING_W         = 4
HEADING_E         = 5
HEADING_SW        = 6
HEADING_S         = 7
HEADING_SE        = 8
#===============================================================================
# CLASS Interface --- DEFINITION
#===============================================================================

class Interface(DirectObject.DirectObject):
    buttons = {}
    aspect = 0
    def __init__(self, parent):
        # Keep pointer to the GraphicsEngine parent class
        self.parent = parent
        
        # Initialize variables
        self.los_visible = False
        self.unit_los_visible = False
        self.not_in_los_visible = False
        
        self.hovered_tile = None
        self.hovered_unit = None
        self.selected_unit = None
        self.off_model = None
        self.selected_unit_tile = None
        
        self.movetext_np = None    
        self.panel = None   
        
        b=OnscreenImage(parent=render2dp, image="galaxy1.jpg") #@UndefinedVariable
        #base.cam.node().getDisplayRegion(0).setSort(20)
        base.cam2dp.node().getDisplayRegion(0).setSort(-20)#@UndefinedVariable
        
        self.move_timer = 0
        self.unit_move_destination = None
        self.unit_move_orientation = HEADING_NONE
        self.turn_np = NodePath("turn_arrows_np")
        self.turn_np.reparentTo(render)#@UndefinedVariable
        self.dummy_turn_pos_node = NodePath("dummy_turn_pos_node")
        self.dummy_turn_dest_node = NodePath("dummy_turn_dest_node")
        
        self.init_gui()
        
        self.accept('escape', self.escapeEvent)
        self.accept("mouse1", self.mouseLeftClick)
        self.accept("mouse1-up", self.mouseLeftClickUp)
        self.accept("r", self.redraw)
        self.accept( 'window-event', self.windowEvent)
        
        self.move_tile_seq = Sequence()
        self.picked_move_tile_seq = Sequence()
        self.old_p = None
        self.old_move_dest = None
        
        taskMgr.add(self.processGui, 'processGui_task')#@UndefinedVariable
        taskMgr.add(self.hover, 'hover_task') #@UndefinedVariable
        taskMgr.add(self.turnUnit, 'turnUnit_task')     #@UndefinedVariable  
    
    def init_gui(self):
        wp = base.win.getProperties() #@UndefinedVariable
        self.aspect = float(wp.getXSize()) / wp.getYSize()
        plane = loader.loadModel('plane')#@UndefinedVariable
        plane.setScale(2)
        plane.flattenLight()
        
        self.unit_card = GuiCard(0.19, 0.215, 0, None, "bottomleft", Point4(0.2, 0.2, 0.2, 0.8))
        self.deselect_button = GuiButton2("bottom", Point3(0.0, 0, -0.2), self.aspect, plane, "deselect_unit")
        #self.punit_button = GuiButton2("top", Point3(0.0, 0, -0.3), aspect, plane, "prev_unit")
        self.nunit_button = GuiButton2("bottom", Point3(0.0, 0, -0.09), self.aspect, plane, "next_unit")
        self.endturn_button = GuiButton2("right", Point3(-0.1, 0, 0.24), self.aspect, plane, "end_turn")
        self.action_a = GuiButton2("right", Point3(-0.1, 0, 0.13), self.aspect, plane, "empty")
        self.action_b = GuiButton2("right", Point3(-0.1, 0, 0.02), self.aspect, plane, "empty")
        self.action_c = GuiButton2("right", Point3(-0.1, 0, -0.09), self.aspect, plane, "empty")
        self.action_d = GuiButton2("right", Point3(-0.1, 0, -0.2), self.aspect, plane, "empty")
        
        self.overwatch = GuiButton2("bottom", Point3(1.5+0.01, 0, -0.09), self.aspect, plane, "overwatch")
        self.set_up = GuiButton2("bottom", Point3(1.6+0.02, 0, -0.09), self.aspect, plane, "set_up")
        self.use = GuiButton2("bottom", Point3(1.7+0.03, 0, -0.09), self.aspect, plane, "use")
        self.taunt = GuiButton2("bottom", Point3(1.5+0.01, 0, -0.2), self.aspect, plane, "taunt")
        self.action_5 = GuiButton2("bottom", Point3(1.6+0.02, 0, -0.2), self.aspect, plane, "empty")
        self.action_6 = GuiButton2("bottom", Point3(1.7+0.03, 0, -0.2), self.aspect, plane, "empty")
        
        self.buttons["deselect"] = self.deselect_button
        #self.buttons["prev_unit"] = self.punit_button
        self.buttons["next_unit"] = self.nunit_button
        self.buttons["end_turn"] = self.endturn_button
        self.buttons["action_a"] = self.action_a
        self.buttons["action_b"] = self.action_b
        self.buttons["action_c"] = self.action_c
        self.buttons["action_d"] = self.action_d
        self.buttons["overwatch"] = self.overwatch
        self.buttons["set_up"] = self.set_up
        self.buttons["use"] = self.use
        self.buttons["taunt"] = self.taunt
        self.buttons["action_5"] = self.action_5
        self.buttons["action_6"] = self.action_6
        
        self.action_buttons = {}
        self.action_buttons["overwatch"] = self.overwatch
        self.action_buttons["set_up"] = self.set_up
        self.action_buttons["use"] = self.use
        self.action_buttons["taunt"] = self.taunt
        
        self.hovered_gui = None
        
        self.unit_info = {}
        self.unit_panel = {}
        
        self.console = GuiConsole(self, base.a2dBottomLeft, 1.503, 0.8, self.aspect, "bottom")#@UndefinedVariable
        self.stats = GuiTextFrame(Point3(0.3, 0, 0), 0.4, 0.22, 4, "bottom")#@UndefinedVariable
        self.stats2 = GuiTextFrame(Point3(0.7, 0, 0), 0.4, 0.22, 4, "bottom")#@UndefinedVariable
        self.stats3 = GuiTextFrame(Point3(1.1, 0, 0), 0.405, 0.22, 4, "bottom")#@UndefinedVariable
        self.status_bar = GuiTextFrame(Point3(0, 0, 0), 2 * self.aspect, GUI_TOP_OFFSET, 1, "statusbar")#@UndefinedVariable
        
    def redraw(self):
        wp = base.win.getProperties() #@UndefinedVariable
        self.aspect = float(wp.getXSize()) / wp.getYSize()
        if self.aspect >= 1:
            flag = "wide"
            calc_aspect = self.aspect
        elif self.aspect < 1 and self.aspect != 0:
            flag = "tall"
            calc_aspect = 1 / self.aspect
   
        self.unit_card.redraw()
        self.status_bar.redraw(self.aspect)
        for button in self.buttons.values():
            button.redraw(calc_aspect, flag)
            
        for panel in self.unit_panel.values():
            panel.getBounds(calc_aspect)
            
        self.hovered_gui = None

    def windowEvent(self, window=None):
        if window is not None: # window is none if panda3d is not started
            taskMgr.doMethodLater(0.05, self.redraw, 'Redraw task', extraArgs = [])
            #self.redraw()
             
    def getMousePos(self):
        """Returns mouse coordinates if mouse pointer is inside Panda window."""
        if base.mouseWatcherNode.hasMouse(): #@UndefinedVariable
            return base.mouseWatcherNode.getMouse() #@UndefinedVariable
        return None

    def loadTurnArrows(self, dest):
        self.turn_arrow_dict = {}        
        for i in xrange(9):
            m = loader.loadModel("sphere")#@UndefinedVariable
            m.setScale(0.07, 0.07, 0.07)
            x = dest.getX()+0.5
            y = dest.getY()+0.5   
            delta = 0.4   
            height = utils.GROUND_LEVEL + 0.8     
            if i == 0:
                pos = Point3(x-delta, y+delta, height)
                h = 45
                key = HEADING_NW
            elif i == 1:
                pos = Point3(x, y+delta, height)
                h = 0
                key = HEADING_N                
            elif i ==2:
                pos = Point3(x+delta, y+delta, height)
                h = -45
                key = HEADING_NE                
            elif i ==3:
                pos = Point3(x-delta, y, height)
                h = 90
                key = HEADING_W                
            elif i ==4:
                pos = Point3(x+delta, y, height)
                h = -90
                key = HEADING_E                
            if i == 5:
                pos = Point3(x-delta, y-delta, height)
                h = 135
                key = HEADING_SW                
            elif i == 6:
                pos = Point3(x, y-delta, height)
                h = 180
                key = HEADING_S                
            elif i ==7:
                pos = Point3(x+delta, y-delta, height)
                h = 225               
                key = HEADING_SE
            elif i == 8:
                pos = Point3(x, y, height)
                h = 0
                key = HEADING_NONE
            m.setPos(pos)
            m.setH(h)
            m.reparentTo(self.turn_np)
            m.setLightOff()
            self.turn_arrow_dict[key] = m
            
    def loadTurnArrows2(self, dest):
        self.turn_arrow_dict = {}        
        for i in xrange(1):
            cm = CardMaker('cm')
            m.setScale(0.01, 0.01, 0.01)#@UndefinedVariable
            x = dest.getX()+0.5
            y = dest.getY()+0.5  
            z = utils.GROUND_LEVEL 
            p3d = base.cam.getRelativePoint(render, Point3(x,y,z))#@UndefinedVariable
            p2d = Point2()
            base.camLens.project(p3d, p2d)#@UndefinedVariable
            m.setPos(p2d.getX(), 0, p2d.getY())#@UndefinedVariable
            m.reparentTo(render2d)#@UndefinedVariable
            m.setLightOff()#@UndefinedVariable
            #self.turn_arrow_dict[key] = m            
        
    def removeTurnArrows(self):
        for child in self.turn_np.getChildren():
            child.remove()
        self.turn_arrow_dict = {}
            
    def markTurnArrow(self, key):
        for i in self.turn_arrow_dict.itervalues():
            i.setColor(1,1,1)
        if key == HEADING_NONE:
            self.turn_arrow_dict[key].setColor(0,0,1)
        else:
            self.turn_arrow_dict[key].setColor(1,0,0)
        self.unit_move_orientation = key

    def escapeEvent(self):
        if self.selected_unit:
            self.deselectUnit()
        else:
            messenger.send("shutdown-event")#@UndefinedVariable
      
    def refreshStatusBar(self):
        self.status_bar.write(1, "Player: "+self.parent.player+"     Turn:" + str(self.parent.turn_number))
       
    def refreshUnitData(self, unit_id):
        if unit_id != None:
            self.processUnitData(unit_id)
    
    def processUnitData(self, unit_id):
        self.printUnitData(unit_id)
        self.setButtons(unit_id)
        if self.parent.units[unit_id]['overwatch'] == True:
            self.overwatch.turnOn()
        else:
            self.overwatch.turnOff()
        
        if 'set_up' in self.parent.units[unit_id]:
            if self.parent.units[unit_id]['set_up'] == True:
                self.set_up.turnOn()
            else:
                self.set_up.turnOff()
                
    def printUnitData(self, unit_id):
        unit = self.parent.getUnitData(unit_id)
        unit_type = unit['name']
        unit_HP = unit['hp']
        unit_AP = unit['ap']
        unit_default_HP = unit['default_hp']
        unit_default_AP = unit['default_ap']
        unit_weapon = ''
        self.stats.write(3, unit['ranged_weapon']['name'])
        self.stats.write(4, unit['melee_weapon']['name'])
        self.stats.write(1, unit_type)
        
        self.stats2.write(2, "HP: " + str(unit_HP) + "/" + str(unit_default_HP))
        self.stats2.write(3, "AP: " + str(unit_AP) + "/" + str(unit_default_AP))
        self.stats2.write(4, "stat3: XX/YY")
        self.stats3.write(2, "stat4: XX/YY")
        self.stats3.write(3, "stat5: XX/YY")
        self.stats3.write(4, "stat6: XX/YY")
        
        self.status_bar.write(1, "Player: "+self.parent.player+"     Turn:" + str(self.parent.turn_number))
        
        self.refreshUnitInfo(unit_id)
        
    def refreshUnitInfo(self, unit_id):
        unit = self.parent.getUnitData(unit_id)
        unit_type = unit['name']
        unit_HP = unit['hp']
        unit_AP = unit['ap']
        unit_default_HP = unit['default_hp']
        unit_default_AP = unit['default_ap']
        if unit_id not in self.unit_info:
            self.unit_info[unit_id] = GuiUnitInfo(Point3(0, 0, 1.1)
                                                , self.parent.sgm.unit_np_dict[unit_id].node
                                                , unit_type[7:100]
                                                , unit_default_HP, unit_HP
                                                , unit_default_AP, unit_AP)
            self.unit_panel[unit_id] = GuiUnitPanel(self.aspect, unit_id, unit_type[7:100]
                                                , unit_default_HP, unit_HP
                                                , unit_default_AP, unit_AP)
        else:
            self.unit_info[unit_id].reparentTo(self.parent.sgm.unit_np_dict[unit_id].node)
            self.unit_info[unit_id].refreshBars(unit_HP, unit_AP)
            self.unit_info[unit_id].show()
            self.unit_panel[unit_id].refreshBars(unit_HP, unit_AP)
        
        if self.parent.units[unit_id]['overwatch'] == True:
            self.overwatch.turnOn()
            self.unit_info[unit_id].showOverwatch()
            self.unit_panel[unit_id].showOverwatch()
        else:
            self.overwatch.turnOff()
            self.unit_info[unit_id].hideOverwatch()
            self.unit_panel[unit_id].hideOverwatch()
        
        if 'set_up' in self.parent.units[unit_id]:
            if self.parent.units[unit_id]['set_up'] == True:
                self.set_up.turnOn()
                self.unit_info[unit_id].showSetUp()
                self.unit_panel[unit_id].showSetUp()
            else:
                self.set_up.turnOff()
                self.unit_info[unit_id].hideSetUp()
                self.unit_panel[unit_id].hideSetUp()
                
        self.unit_info[unit_id].write(unit_type)
                
    def clearUnitData(self):
        self.stats.write(1, "")
        self.stats.write(3, "")
        self.stats.write(4, "")
        self.stats2.write(2, "")
        self.stats2.write(3, "")
        self.stats2.write(4, "")
        self.stats3.write(2, "")
        self.stats3.write(3, "")
        self.stats3.write(4, "")
        
        for unit_id in self.unit_info:
            self.unit_info[unit_id].hide()
        self.clearButtons()        
        
    def endTurn(self):
        """Ends the turn"""
        if not self.ge.interface_disabled:
            self.ge.createEndTurnMsg() 

    def mouseLeftClick(self):
        """Handles left mouse click actions.
           Procedure first checks for gui clicks, if there are none then it checks 3d collision.
        """
        self.destination = None
        if self.hovered_gui == self.deselect_button:
            self.parent.deselectUnit()
            self.console.unfocus()
        #elif self.hovered_gui == self.punit_button:
        #    self.parent.selectPrevUnit()
        #    self.console.unfocus()
        elif self.hovered_gui == self.nunit_button:
            self.parent.selectNextUnit()
            self.console.unfocus() 
        elif self.hovered_gui == self.endturn_button:
            self.parent.endTurn()
            self.console.unfocus()
        elif self.hovered_gui == self.overwatch:
            if self.overwatch.enabled:
                self.toggleOverwatch()
            self.console.unfocus()
        elif self.hovered_gui == self.set_up:
            if self.set_up.enabled:
                self.toggleSetUp()
            self.console.unfocus()
        elif self.hovered_gui == self.use:
            ClientMsg.use( self.parent.sel_unit_id )
            self.console.unfocus()
        elif self.hovered_gui == self.taunt:
            ClientMsg.taunt( self.parent.sel_unit_id )
            self.console.unfocus()
        #elif self.hovered_gui == self.console:
        #    self.console.focus()
        elif self.panel != None and self.hovered_gui == self.panel:
            self.parent.selectUnit(self.panel.unit_id)
        else:
            self.console.unfocus()    
            unit_id = self.parent.picker.hovered_unit_id;
            if unit_id != None:
                unit_id = int(unit_id)
                pickedCoord = self.parent.getCoordsByUnit(unit_id) 
                # Player can only select his own units
                if self.parent.isThisMyUnit(unit_id):
                    if unit_id != self.parent.sel_unit_id:
                        self.parent.selectUnit(unit_id)
                    else:
                        # Remember movement tile so we can send orientation message when mouse is depressed
                        # Do this only if it is our turn
                        if self.parent.player == self.parent.turn_player:
                            self.unit_move_destination = pickedCoord                          
                elif self.parent.isThisEnemyUnit(unit_id):
                    if self.parent.sel_unit_id != None and self.parent.player == self.parent.turn_player:
                        self.parent.sgm.unit_np_dict[self.parent.sel_unit_id].target_unit = self.parent.sgm.unit_np_dict[unit_id]
                        if self.parent._anim_in_process == False:
                            ClientMsg.shoot(self.parent.sel_unit_id, unit_id)
            else:
                # We clicked on the grid, find if unit is placed on those coords
                pickedCoord = Point2(int(self.parent.picker.hovered_point.getX()), int(self.parent.picker.hovered_point.getY()))
                unit_id = self.parent.getUnitByCoords(pickedCoord)
                
                # If unit is there, check if it is our unit. If it is, select it.
                # If enemy unit is there, we are trying to attack.
                # If unit is not there, check if we have unit selected. If we do, we are trying to move it.
                if unit_id != None:
                    if self.parent.isThisMyUnit(unit_id):
                        if unit_id != self.parent.sel_unit_id:
                            self.parent.selectUnit(unit_id)
                        else:
                            # Remember movement tile so we can send orientation message when mouse is depressed
                            # Do this only if it is our turn
                            if self.parent.player == self.parent.turn_player:
                                self.unit_move_destination = pickedCoord
                    elif self.parent.isThisEnemyUnit(unit_id):
                        if self.parent.sel_unit_id != None and self.parent.player == self.parent.turn_player:
                            if self.parent._anim_in_process == False:
                                ClientMsg.shoot(self.parent.sel_unit_id, unit_id)
                else:
                    if self.parent.sel_unit_id != None and self.parent.player == self.parent.turn_player:
                        # Remember movement tile so we can send movement message when mouse is depressed
                        # Do this only if it is our turn
                        if self.parent.units[self.parent.sel_unit_id]['move_dict'].has_key(tuple(pickedCoord)):
                            self.unit_move_destination = pickedCoord
                            
    def mouseLeftClickUp(self):
        """Handles left mouse click actions when mouse button is depressed.
           Used for unit movement.
        """
        if self.parent.sel_unit_id != None and self.unit_move_destination and self.unit_move_orientation != HEADING_NONE:   
            # Send movement message to engine
            x = self.unit_move_destination.getX()
            y = self.unit_move_destination.getY()
            if self.unit_move_orientation == HEADING_NW:
                o = Point2(x-1, y+1)
            elif self.unit_move_orientation == HEADING_N:
                o = Point2(x, y+1)
            elif self.unit_move_orientation == HEADING_NE:
                o = Point2(x+1, y+1)
            elif self.unit_move_orientation == HEADING_W:
                o = Point2(x-1, y)
            elif self.unit_move_orientation == HEADING_E:
                o = Point2(x+1, y)
            elif self.unit_move_orientation == HEADING_SW:
                o = Point2(x-1, y-1)
            elif self.unit_move_orientation == HEADING_S:
                o = Point2(x, y-1)
            elif self.unit_move_orientation == HEADING_SE:
                o = Point2(x+1, y-1)
            ClientMsg.move(self.parent.sel_unit_id, (x, y), (o.x, o.y))
        self.unit_move_destination = None
        self.unit_move_orientation = HEADING_NONE
        self.move_timer = 0
        self.removeTurnArrows()

    def startMoveTileInterval(self, tile):
        self.move_tile_seq = Sequence(LerpColorInterval(tile, 0.3, (0, 0, 0, 0.5)),
                                      LerpColorInterval(tile, 0.3, utils.WALKABLE_TILE_COLOR)
                                     )
        self.move_tile_seq.loop()
        
    def stopMoveTileInterval(self, tile):
        self.move_tile_seq.pause()
        tile.setColor(utils.WALKABLE_TILE_COLOR)

        
    def startPickedMoveTileInterval(self, tile):
        self.picked_move_tile_seq = Sequence(LerpColorInterval(tile, 0.2, (1, 0, 0, 0.5)),
                                             LerpColorInterval(tile, 0.2, utils.WALKABLE_TILE_COLOR)
                                            )
        self.picked_move_tile_seq.loop()
        
    def stopPickedTileMoveInterval(self, tile):
        self.picked_move_tile_seq.pause()
        tile.setColor(utils.WALKABLE_TILE_COLOR)


#===============================================================================
# CLASS Interface --- TASKS
#===============================================================================
    def hover(self, task):
        """Visually marks tiles over which mouse cursor hovers."""
        if self.unit_move_destination:
            if self.old_p != None:
                old_tile = self.parent.sgm.tile_cards[self.old_p[0]][self.old_p[1]]
                self.stopMoveTileInterval(old_tile)
                self.old_p = None
            move_x = int(self.unit_move_destination.getX())
            move_y = int(self.unit_move_destination.getY())
            if (move_x, move_y) != self.old_move_dest:
                tile = self.parent.sgm.tile_cards[move_x][move_y]
                self.startPickedMoveTileInterval(tile)
                self.old_move_dest = (move_x, move_y)
        else:
            if self.parent.turn_player != self.parent.player:
                return task.cont
            if self.old_move_dest != None:
                old_move_tile = self.parent.sgm.tile_cards[self.old_move_dest[0]][self.old_move_dest[1]]
                self.stopPickedTileMoveInterval(old_move_tile)
                self.old_move_dest = None
            if self.parent.sel_unit_id != None:
                move_dict = self.parent.units[self.parent.sel_unit_id]['move_dict']
                p = (int(self.parent.picker.hovered_point.getX()), int(self.parent.picker.hovered_point.getY()))
                if p != self.old_p:
                    if move_dict.has_key(p):
                        if self.old_p != None:
                            old_tile = self.parent.sgm.tile_cards[self.old_p[0]][self.old_p[1]]
                            self.stopMoveTileInterval(old_tile)
                        tile = self.parent.sgm.tile_cards[p[0]][p[1]]
                        self.startMoveTileInterval(tile)
                        self.old_p = p
                    else:
                        if self.old_p != None:
                            old_tile = self.parent.sgm.tile_cards[self.old_p[0]][self.old_p[1]]
                            self.stopMoveTileInterval(old_tile)
                            self.old_p = None
        
        return task.cont
    
     
    def processGui(self, task):
        """Visually marks and selects GUI element over which mouse cursor hovers."""
        if base.mouseWatcherNode.hasMouse(): #@UndefinedVariable
            mpos = base.mouseWatcherNode.getMouse()#@UndefinedVariable
            hovering_over_something = False
            
            for panel_iterator in self.unit_panel.values():
                panel_iterator.frame.setAlphaScale(0.8)
                if mpos.x >= panel_iterator.pos_min_x and mpos.x <= panel_iterator.pos_max_x and mpos.y >= panel_iterator.pos_min_y and mpos.y <= panel_iterator.pos_max_y:
                    self.panel = panel_iterator
                    self.hovered_gui = self.panel
                    self.panel.frame.setAlphaScale(1)
                    hovering_over_something = True
                    self.console.hide()
            #Vidi me kako iteriram kroz dictionary
            for button in self.buttons.values():
                button.frame.setAlphaScale(0.8)
                if mpos.x >= button.pos_min_x and mpos.x <= button.pos_max_x and mpos.y >= button.pos_min_y and mpos.y <= button.pos_max_y:
                    self.hovered_gui = button
                    button.frame.setAlphaScale(1)
                    hovering_over_something = True
                    self.console.hide()
            #Hovering iznad konzole
            # TODO: vjeks: ovaj uvjet ne radi, pos_min x i y su krivi
            """
            if  mpos.x >= self.console.pos_min_x and mpos.x <= self.console.pos_max_x and mpos.y >= self.console.pos_min_y and mpos.y <= self.console.pos_max_y:                 
                self.hovered_gui = self.console
                hovering_over_something = True
                self.console.show()
            """                 
            if not hovering_over_something:
                self.hovered_gui = None
                self.console.hide()
  
        return task.cont    

    def turnUnit(self, task):
        if self.unit_move_destination: 
            #print self.unit_move_destination
            if self.move_timer < 0.1:
                dt = globalClock.getDt()#@UndefinedVariable
                self.move_timer += dt
                if self.move_timer > 0.1:
                    self.loadTurnArrows(self.unit_move_destination)
                    pos = Point3(self.unit_move_destination.getX()+0.5, self.unit_move_destination.getY()+0.5, 0.3)
                    self.dummy_turn_pos_node.setPos(pos)
            else: 
                pos3d = self.parent.picker.hovered_point
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
                    key = HEADING_NONE
                # TODO: ogs: kad Debeli popravi turn poruku mozemo ovaj dolje kod zamijeniti s zakomentiranim
                #else:
                    #key = utils.clampToHeading(h)
                
                elif h >= -22.5 and h < 22.5:
                    key = HEADING_N
                elif h >= 22.5 and h < 67.5:
                    key = HEADING_NW
                elif h >= 67.5 and h < 112.5:
                    key = HEADING_W
                elif h >= 112.5 and h < 157.5:
                    key = HEADING_SW
                elif (h >= 157.5 and h <= 180) or (h >= -180 and h < -157.5):
                    key = HEADING_S
                elif h >= -157.5 and h < -112.5:
                    key = HEADING_SE
                elif h >= -112.5 and h < -67.5:
                    key = HEADING_E
                elif h >= -67.5 and h < -22.5:
                    key = HEADING_NE
                self.markTurnArrow(key)
        return task.cont

    def toggleOverwatch(self):
        unit = self.parent.units[self.parent.sel_unit_id]
        ClientMsg.overwatch( self.parent.sel_unit_id )
        ClientMsg.taunt( self.parent.sel_unit_id )
        
    def toggleSetUp(self):
        unit = self.parent.units[self.parent.sel_unit_id]
        ClientMsg.setUp( self.parent.sel_unit_id )
    
    def setButtons(self, unit_id):
        for button in self.action_buttons.itervalues():
            button.enable()
        #if self.parent.units[unit_id]['heavy_weapon'] == False:
        if not 'set_up' in self.parent.units[unit_id]:
            self.set_up.disable()
            
        if 'can_use' in self.parent.units[unit_id]:
            if self.parent.units[unit_id]['can_use'] == False:
                self.use.disable()
            
    def clearButtons(self):
        for button in self.action_buttons.itervalues():
            button.disable()

