from direct.showbase import DirectObject
from panda3d.core import Plane, Vec3, Point4, Point3, Point2, NodePath#@UnresolvedImport
from pandac.PandaModules import GeomNode, CardMaker, TextNode#@UnresolvedImport
from pandac.PandaModules import TextureStage, TransparencyAttrib#@UnresolvedImport
from direct.gui.DirectGui import DirectFrame, DGG
from direct.gui.OnscreenText import OnscreenText
from unitmodel import UnitModel
from console import GuiConsole

import utils

#===============================================================================
# CLASS Interface --- DEFINITION
#===============================================================================

class Interface(DirectObject.DirectObject):
    buttons = {}
    def __init__(self, parent):
        # Keep pointer to the GraphicsEngine parent class
        self.parent = parent
        
        # Initialize variables
        self.los_visible = False
        self.unit_los_visible = False
        self.move_visible = False
        self.not_in_los_visible = False
        
        self.selected_unit = None
        self.off_model = None
        
        self.movetext_np = None       
        
        self.move_timer = 0
        self.unit_move_destination = None
        self.unit_move_orientation = utils.HEADING_NONE
        self.turn_np = NodePath("turn_arrows_np")
        self.turn_np.reparentTo(render)
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0.3))  
        self.dummy_turn_pos_node = NodePath("dummy_turn_pos_node")
        self.dummy_turn_dest_node = NodePath("dummy_turn_dest_node")
        
        wp = base.win.getProperties() 
        aspect = float(wp.getXSize()) / wp.getYSize()
        plane = loader.loadModel('plane')
        plane.setScale(2)
        plane.flattenLight()
        self.unit_card = GuiCard(0.3, 0.3, 0.01, None, "topleft", Point4(0, 0, 0, 0))
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
        
        self.console = GuiConsole(base.a2dBottomLeft, 1.5, 0.4, aspect)
        self.stats = GuiTextFrame(Point3(0.3, 0, 0), 0.4, 0.3, 5)
        self.stats2 = GuiTextFrame(Point3(0.7, 0, 0), 0.4, 0.3, 5)
        self.stats3 = GuiTextFrame(Point3(1.1, 0, 0), 0.4, 0.3, 5)
        self.status_bar = GuiTextFrame(Point3(1.5 + 0.01, 0, 0), 0.85, 0.08, 1)
        self.status_bar.write(1, "Player: mirko     Server: Online")
        
        self.accept('m', self.switchUnitMove)
        self.accept('escape', self.escapeEvent)
        
        taskMgr.add(self.processGui, 'processGui_task')
        taskMgr.add(self.turnUnit, 'turnUnit_task')       
    
    def redraw(self):
        wp = base.win.getProperties() 
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


    def loadTurnArrows(self, dest):
        self.turn_arrow_dict = {}        
        for i in xrange(9):
            m = loader.loadModel("sphere")
            m.setScale(0.07, 0.07, 0.07)
            x = dest.getX()+0.5
            y = dest.getY()+0.5   
            delta = 0.4   
            height = 0.8     
            if i == 0:
                pos = Point3(x-delta, y+delta, height)
                h = 45
                key = utils.HEADING_NW
            elif i == 1:
                pos = Point3(x, y+delta, height)
                h = 0
                key = utils.HEADING_N                
            elif i ==2:
                pos = Point3(x+delta, y+delta, height)
                h = -45
                key = utils.HEADING_NE                
            elif i ==3:
                pos = Point3(x-delta, y, height)
                h = 90
                key = utils.HEADING_W                
            elif i ==4:
                pos = Point3(x+delta, y, height)
                h = -90
                key = utils.HEADING_E                
            if i == 5:
                pos = Point3(x-delta, y-delta, height)
                h = 135
                key = utils.HEADING_SW                
            elif i == 6:
                pos = Point3(x, y-delta, height)
                h = 180
                key = utils.HEADING_S                
            elif i ==7:
                pos = Point3(x+delta, y-delta, height)
                h = 225               
                key = utils.HEADING_SE
            elif i == 8:
                pos = Point3(x, y, height)
                h = 0
                key = utils.HEADING_NONE
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
        if key == utils.HEADING_NONE:
            self.turn_arrow_dict[key].setColor(0,0,1)
        else:
            self.turn_arrow_dict[key].setColor(1,0,0)
        self.unit_move_orientation = key

    
    def displayUnitMove(self):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        if self.selected_unit:
            move_dict = self.selected_unit.unit['move_dict']
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
            
    def switchUnitMove(self, flag=None):
        """Switched the display of tiles available for movement for the selected unit.
           If flag=="show" tiles will be displayed.
           If flag=="hide" tiles will be hidden.
           If flag==None method functions as a switch (on/off)
        """

        if flag == "show" or (not flag and not self.move_visible):
            display = True
        elif flag == "hide" or (not flag and self.move_visible):
            display = False
        else:
            return
        
        if display:
            self.displayUnitMove()
            self.move_visible = True
        else:
            self.movetext_np.removeNode()
            self.move_visible = False

    def escapeEvent(self):
        if self.selected_unit:
            self.deselectUnit()
        else:
            messenger.send("shutdown-event")

        
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
        if not self.ge.interface_disabled:
            self.ge.createEndTurnMsg() 

    

#===============================================================================
# CLASS Interface --- TASKS
#===============================================================================

    
    def processGui(self, task):
        """Visually marks and selects GUI element over which mouse cursor hovers."""
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse()
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
                            key = utils.HEADING_NONE
                        elif h >= -22.5 and h < 22.5:
                            key = utils.HEADING_N
                        elif h >= 22.5 and h < 67.5:
                            key = utils.HEADING_NW
                        elif h >= 67.5 and h < 112.5:
                            key = utils.HEADING_W
                        elif h >= 112.5 and h < 157.5:
                            key = utils.HEADING_SW
                        elif (h >= 157.5 and h <= 180) or (h >= -180 and h < -157.5):
                            key = utils.HEADING_S
                        elif h >= -157.5 and h < -112.5:
                            key = utils.HEADING_SE
                        elif h >= -112.5 and h < -67.5:
                            key = utils.HEADING_E
                        elif h >= -67.5 and h < -22.5:
                            key = utils.HEADING_NE
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

        fixedWidthFont = loader.loadFont("monoMMM_5.ttf")#@UndefinedVariable
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


                  
