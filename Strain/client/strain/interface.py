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
from share import toHit

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
        self.panel = None   
        
        b=OnscreenImage(parent=render2dp, image="galaxy1.jpg") #@UndefinedVariable
        #base.cam.node().getDisplayRegion(0).setSort(20)
        base.cam2dp.node().getDisplayRegion(0).setSort(-20)#@UndefinedVariable
        
        self.move_timer = 0
        self.init_gui()
        
        self.accept('escape', self.escapeEvent)
        self.accept("mouse1", self.mouseLeftClick)
        self.accept("r", self.redraw)
        self.accept( 'window-event', self.windowEvent)
        
        taskMgr.add(self.processGui, 'processGui_task')#@UndefinedVariable 
    
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
        self.panel_pos = {}
        self.panel_idx = 0
        
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

    def escapeEvent(self):
        if self.parent.sel_unit_id != None:
            self.parent.deselectUnit()
        else:
            messenger.send("shutdown-event")#@UndefinedVariable
      
    def refreshStatusBar(self):
        self.status_bar.write(1, "Player: "+self.parent.player+"     Turn:" + str(self.parent.turn_number))
    
    def processUnitData(self, unit_id):
        """Refreshes status of action buttons for units."""
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
        """Refreshes unit info on GUI."""
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
        
    def refreshUnitInfo(self, unit_id):
        """Refreshes HP and AP bars, as well as buff/debuff status of units above unit models and on unit lists."""
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
            self.unit_panel[unit_id] = GuiUnitPanel(self.aspect, unit_id, self.getPanelPos(unit_id)
                                                , unit_type[7:100]
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
            ClientMsg.endTurn()
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

#===============================================================================
# CLASS Interface --- TASKS
#===============================================================================
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
    
    def toggleOverwatch(self):
        ClientMsg.overwatch( self.parent.sel_unit_id )
        
    def toggleSetUp(self):
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
            
    def getPanelPos(self, unit_id):
        if not unit_id in self.panel_pos:
            self.panel_idx = self.panel_idx + 1
            self.panel_pos[unit_id] = self.panel_idx
            
        return self.panel_pos[unit_id]
