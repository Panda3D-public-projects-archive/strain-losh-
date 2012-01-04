'''
Created on 26. pro. 2011.

@author: Vjeko
'''
from panda3d.core import NodePath, CardMaker, GeomNode, TransparencyAttrib, TextNode, TextFont#@UnresolvedImport
from direct.gui.DirectGui import DirectFrame, DGG, DirectWaitBar
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from utils import *

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
        cm.setFrame(0, width, 0, height)
        n = self.frame_node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        #cm = CardMaker("cm_right")
        #cm.setFrame(0, border_size, 0, height)
        #n = self.frame_node.attachNewNode(cm.generate())
        #n.setPos(width - border_size, 0, 0)
        #cm = CardMaker("cm_top")
        #cm.setFrame(0, width, height - border_size, width)
        #n = self.frame_node.attachNewNode(cm.generate())
        #n.setPos(0, 0, 0)
        #cm = CardMaker("cm_bottom")
        #cm.setFrame(0, width, 0, border_size)
        #n = self.frame_node.attachNewNode(cm.generate())
        #n.setPos(0, 0, 0)
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
        elif self.hugpos == "bottomleft":
            p = base.a2dBottomLeft.getPos()#@UndefinedVariable
            p.setX(p.getX() + 0.107)
            p.setZ(p.getZ())
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
        self.enabled = True
        self.name = name
        self.node = aspect2d.attachNewNode("guibutton")#@UndefinedVariable
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.node.setAlphaScale(1) 
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
            
    def turnOn(self):
        self.node.setTexture(loader.loadTexture(self.name+"_on.png"))#@UndefinedVariable
        
    def turnOff(self):
        self.node.setTexture(loader.loadTexture(self.name+".png"))#@UndefinedVariable    
            
    def enable(self):
        self.node.setTexture(loader.loadTexture(self.name+".png"))#@UndefinedVariable
        self.enabled = True
        
    def disable(self):
        self.node.setTexture(loader.loadTexture("empty.png"))#@UndefinedVariable
        self.enabled = False
            
    def removeNode(self):
            self.node.removeNode()   

#===============================================================================
# CLASS GuiButton2 --- DEFINITION
#===============================================================================
class GuiButton2:
    def __init__(self, hugpos, offset, aspect, plane, name):
        self.enabled = True
        self.name = name
        
        self.frame = DirectFrame(   relief = DGG.FLAT
                                  , frameColor = (0, 0, 0, 0)
                                  , scale = 1
                                  , frameSize = (-0.3, 0.3, -0.3, 0.3) ) #32/600=0.05333
        self.frame.setScale(0.0533)
        
        self.imageObject = OnscreenImage(image = name+".png", pos = (0, 0, 0))
        self.imageObject.setTransparency(TransparencyAttrib.MAlpha)
        self.imageObject.setAlphaScale(1) 
        self.imageObject.reparentTo(self.frame)
        
        self.hugpos = hugpos
        self.offset = offset
        self.redraw(aspect)

    def redraw(self, aspect, flag="wide"):
        if self.hugpos == "top":
            p = base.a2dTopLeft.getPos()#@UndefinedVariable
            p.setX(p.getX() + self.offset.getX() + 0.05)
            p.setZ(p.getZ() + self.offset.getZ() - GUI_TOP_OFFSET - 0.05)
        elif self.hugpos == "bottom":
            p = base.a2dBottomLeft.getPos()#@UndefinedVariable
            p.setX(p.getX() + self.offset.getX() + 0.05)
            p.setZ(p.getZ() + self.offset.getZ() + GUI_BOTTOM_OFFSET - 0.05)
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
            
    def turnOn(self):
        self.imageObject.setImage(self.name+"_on.png")#@UndefinedVariable
        self.imageObject.setTransparency(TransparencyAttrib.MAlpha)
        
    def turnOff(self):
        self.imageObject.setImage(self.name+".png")#@UndefinedVariable
        self.imageObject.setTransparency(TransparencyAttrib.MAlpha)    
            
    def enable(self):
        self.imageObject.setImage(self.name+".png")#@UndefinedVariable
        self.imageObject.setTransparency(TransparencyAttrib.MAlpha)
        self.enabled = True
        
    def disable(self):
        self.imageObject.setImage("empty.png")#@UndefinedVariable
        self.imageObject.setTransparency(TransparencyAttrib.MAlpha)
        self.enabled = False
            
    def removeNode(self):
        self.frame.removeNode()   
                      
class GuiTextFrame:
    def __init__(self, offset, h_size, v_size, numLines, hugpos):
        self.numLines = numLines
        #if hugpos == "statusbar":
        #    color = (0,0,0,1)
        #else:
        #    color = (0.2, 0.2, 0.2, 0.8)
        color = (0.2, 0.2, 0.2, 0.9)
        self.frame = DirectFrame(   relief = DGG.FLAT
                                  , frameColor = color
                                  , scale = 1
                                  , frameSize = (0, h_size, 0, -v_size) )
        
        self.hugpos = hugpos
        self.offset = offset
        
        if hugpos == "top":
            self.frame.reparentTo(base.a2dTopLeft)#@UndefinedVariable
            self.frame.setPos(self.offset.getX(), 0, self.offset.getZ() - GUI_TOP_OFFSET)
        elif hugpos == "bottom":
            self.frame.reparentTo(base.a2dBottomLeft)#@UndefinedVariable
            self.frame.setPos(self.offset.getX(), 0, self.offset.getZ() + GUI_BOTTOM_OFFSET -0.085)
        elif hugpos == "statusbar":
            self.frame.reparentTo(base.a2dTopLeft)#@UndefinedVariable
            self.frame.setPos(self.offset.getX(), 0, self.offset.getZ())

        fixedWidthFont = loader.loadFont(GUI_FONT)#@UndefinedVariable
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
        if self.hugpos == "top":
            p = base.a2dTopLeft.getPos()#@UndefinedVariable
            p.setX(p.getX() + self.offset.getX() + 0.05)
            p.setZ(p.getZ() + self.offset.getZ() - GUI_TOP_OFFSET - 0.05)
        elif self.hugpos == "bottom":
            p = base.a2dBottomLeft.getPos()#@UndefinedVariable
            p.setX(p.getX() + self.offset.getX() + 0.05)
            p.setZ(p.getZ() + self.offset.getZ() + GUI_BOTTOM_OFFSET - 0.05)
        self.frame.setPos(p)

class GuiUnitInfo:
    def __init__(self, offset, parent, default_hp, hp, default_ap, ap):
            
        self.offset = offset
        self.frame = DirectFrame(   relief = DGG.FLAT
                                  , scale = 1
                                  , frameSize = (-0.5, 0.5, 0, -0.5)
                                  , parent = parent )
        self.frame.setBillboardPointEye()
        fixedWidthFont = loader.loadFont(GUI_FONT)#@UndefinedVariable        
        #fixedWidthFont.setPixelsPerUnit(60)
        #fixedWidthFont.setRenderMode(fontt.RMSolid)
        if not fixedWidthFont.isValid():
            print "pandaInteractiveConsole.py :: could not load the defined font %s" % str(self.font)
            fixedWidthFont = DGG.getDefaultFont()
        
        self.label = OnscreenText( parent = self.frame
                              , text = ""
                              , pos = (offset.getX(),offset.getZ()+0.1)
                              , align=TextNode.ACenter
                              , mayChange=True
                              , scale=0.1
                              , fg = (1,0,0,1)
                              #, shadow = (0, 0, 0, 1)
                              #, frame = (200,0,0,1) 
                              )
        self.label.setFont( fixedWidthFont )
        #self.label.setLightOff()

        self.all_icons = {}
        self.visible_icons = {}
        self.addIcon("overwatch")
        self.addIcon("set_up")
        
        self.ap_bar = DirectWaitBar(parent = self.frame
                                  , text = ""
                                  , range = default_ap
                                  , value = ap
                                  , pos = (offset.getX(),0,offset.getZ()-0.2)
                                  , barColor = (0,0,1,1)
                                  , frameColor = (0,0,0.5,0.2)
                                  , scale = (0.3,0.5,0.3))
        
        self.hp_bar = DirectWaitBar(parent = self.frame
                                  , text = ""
                                  , range = default_hp
                                  , value = hp
                                  , pos = (offset.getX(),0,offset.getZ()-0.27)
                                  , barColor = (0,1,0,1)
                                  , frameColor = (1,0,0,0.9)
                                  , scale = (0.3,0.5,0.3))

    def addIcon(self, name):
        self.all_icons[name] = OnscreenImage(parent = self.frame
                                            ,image = name + "_icon.png"
                                           #,pos = offset + (0,0,-0.1)
                                            ,scale = 0.125)
        
        self.all_icons[name].setTransparency(TransparencyAttrib.MAlpha)
        self.all_icons[name].hide()
        
    def write(self, text):
        self.label.setText(text)
        
    def redraw(self):
        return

    def remove(self):
        self.frame.remove()
        
    def reparentTo(self, parent):
        self.frame.reparentTo(parent)
        
    def hide(self):
        self.label.hide()
        
    def show(self):
        self.label.show()
    
    def refreshBars(self, hp, ap):
        self.ap_bar['value'] = ap
        self.hp_bar['value'] = hp
        self.ap_bar.setValue()
        self.hp_bar.setValue()
        
    def refreshIcons(self):
        count = len(self.visible_icons)
        start_pos =  (1 - count) * 0.25 / 2
        for icon in self.all_icons:
            if icon in self.visible_icons:
                self.visible_icons[icon].setPos(self.offset + (start_pos, 0, -0.05))
                self.visible_icons[icon].show()
                start_pos += 0.25
            else:
                self.all_icons[icon].hide()
            
    def hideOverwatch(self):
        if "overwatch" in self.visible_icons:
            self.visible_icons.pop("overwatch")
        self.refreshIcons()

    def showOverwatch(self):
        self.visible_icons["overwatch"] = self.all_icons["overwatch"]
        self.refreshIcons()
    
    def hideSetUp(self):
        if "set_up" in self.visible_icons:
            self.visible_icons.pop("set_up")
        self.refreshIcons()

    def showSetUp(self):
        self.visible_icons["set_up"] = self.all_icons["set_up"]
        self.refreshIcons()
