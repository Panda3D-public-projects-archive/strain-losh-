from direct.showbase import DirectObject
from direct.gui.DirectGui import DirectFrame, DirectEntry, DGG
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Point3#@UnresolvedImport
from pandac.PandaModules import TextNode#@UnresolvedImport
import textwrap, re, string
from utils import *
import utils
from strain.client_messaging import ClientMsg



class GuiConsole(DirectObject.DirectObject):
    
    def __init__(self, class_parent, parent, h_size, v_size, aspect, hugpos):
        self.h_size = h_size
        self.v_size = v_size
        self.scale = 0.04
        self.parent = class_parent
        self.numlines = int(v_size/self.scale - 2)
        
        self.pos_min_x = 0
        self.pos_min_y = 0
        self.pos_max_x = self.h_size
        self.pos_max_y = 0.7
        
        if aspect > 0:
            self.pos_max_x /= aspect
        else:
            self.pos_max_y *= aspect

        self.consoleFrame = DirectFrame( relief = DGG.RIDGE
                                         , frameColor = (0, 0, 0, 0)
                                         , scale = self.scale
                                         , frameSize = (0, self.h_size / self.scale, 0, self.v_size / self.scale) )
        
        if parent == base.a2dBottomLeft:#@UndefinedVariable
            self.pos_min_x -= 1
            self.pos_min_y -= 1
            self.pos_max_x -= 1 
            self.pos_max_y -= 1
      
        if hugpos == "bottom":
            self.consoleFrame.setPos(0, 0, GUI_BOTTOM_OFFSET - 0.085)
            self.pos_min_x = 0
            self.pos_min_y = GUI_BOTTOM_OFFSET - 0.085 - 0.07
            self.pos_max_x = self.h_size
            self.pos_max_y = GUI_BOTTOM_OFFSET - 0.085
        
        fixedWidthFont = loader.loadFont(GUI_FONT)#@UndefinedVariable
        #fixedWidthFont.setPixelsPerUnit(60)
        #fixedWidthFont.setRenderMode(fixedWidthFont.RMSolid)
        if not fixedWidthFont.isValid():
            print "pandaInteractiveConsole.py :: could not load the defined font %s" % str(self.font)
            fixedWidthFont = DGG.getDefaultFont()
      
        
        #fixedWidthFont.setPageSize(512,512)
        #fixedWidthFont.setPixelsPerUnit(60)
        
        self.consoleEntry = DirectEntry ( self.consoleFrame
                                    , text        = ""
                                    , command     = self.onEnterPress
                                    #, width       = self.h_size/self.scale -2
                                    , pos         = (0.01, 0, 0.02)
                                    , initialText = "Enter text..."
                                    , numLines    = 1
                                    , focus       = 0
                                    , entryFont   = fixedWidthFont
                                    , scale       = 1
                                    , frameColor  = (0,0,0,0.2)
                                    , text_fg     = (0, 1, 0, 1)
                                    , text_shadow = (0, 0, 0, 1))
        
        
        #self.consoleEntry = DirectEntry(self.consoleFrame)
        
        
        self.consoleEntry["frameSize"]=(0,self.h_size/self.scale,0,1)
        self.consoleEntry["width"]=self.h_size/self.scale
        self.consoleEntry["focusInCommand"]=self.focusInCallback;
        self.consoleEntry["focusOutCommand"]=self.focusOutCallback;
        
        self.consoleFrame.reparentTo(parent)
        
        self.textBuffer = list()
        self.textBufferLength = 100
        for i in xrange(self.textBufferLength):
            self.textBuffer.append(['', (100,100,100,1)])
        self.textBufferPos = self.textBufferLength-self.numlines
        
        # output lines
        self.consoleOutputList = list()
        for i in xrange( self.numlines ):
            label = OnscreenText( parent = self.consoleFrame
                              , text = ""
                              , pos = (0, i+1.5)
                              , align=TextNode.ALeft
                              , mayChange=1
                              , scale=1.0
                              , fg = (100,100,100,1)
                              , shadow = (0, 0, 0, 1))
                            # , frame = (200,0,0,1) )
            label.setFont( fixedWidthFont )
            self.consoleOutputList.append( label )        
        
        self.linelength = 57
        self.linewrap = textwrap.TextWrapper()
        self.linewrap.width = self.linelength
        self.toggleConsole()
        
    def focusInCallback(self):
        self.parent.parent.camera.disableKeyMovement()

    def focusOutCallback(self):
        self.parent.parent.camera.enableKeyMovement()
    
    def show(self):
        if self.consoleFrame.isHidden():
            self.consoleFrame.toggleVis()

    def hide(self):
        pass
        #if not self.consoleFrame.isHidden():
        #    self.consoleFrame.toggleVis()
            
    def toggleConsole(self):
        self.consoleFrame.toggleVis()
        hidden = self.consoleFrame.isHidden()
        #self.consoleEntry['focus'] != hidden
        if hidden:
            #self.ignoreAll()
            self.accept( 'control', self.toggleConsole )
            self.accept( 'enter', self.manageFocus )
            self.accept( 'escape', self.unfocus)
        else:
            #self.ignoreAll()
            #self.accept( 'page_up', self.scroll, [-5] )
            #self.accept( 'page_up-repeat', self.scroll, [-5] )
            #self.accept( 'page_down', self.scroll, [5] )
            #self.accept( 'page_down-repeat', self.scroll, [5] )
            #self.accept( 'window-event', self.windowEvent)
              
            #self.accept( 'arrow_up'  , self.scrollCmd, [ 1] )
            #self.accept( 'arrow_down', self.scrollCmd, [-1] )
              
            self.accept( 'control', self.toggleConsole )
            self.accept( 'enter', self.manageFocus )
            self.accept( 'escape', self.unfocus)
            #self.accept( self.autocomplete_key, self.autocomplete )
            #self.accept( self.autohelp_key, self.autohelp )
              
            # accept v, c and x, where c & x copy's the whole console text
            #messenger.toggleVerbose()
            #for osx use ('meta')
            #if sys.platform == 'darwin':
            #  self.accept( 'meta', self.unfocus )
            #  self.accept( 'meta-up', self.focus )
            #  self.accept( 'meta-c', self.copy )
            #  self.accept( 'meta-x', self.cut )
            #  self.accept( 'meta-v', self.paste )
            #for windows use ('control')
            #if sys.platform == 'win32' or sys.platform == 'linux2':
            #  self.accept( 'control', self.unfocus )
            #  self.accept( 'control-up', self.focus )
            #  self.accept( 'control-c', self.copy )
            #  self.accept( 'control-x', self.cut )
            #  self.accept( 'control-v', self.paste )
          
    def onEnterPress(self, textEntered):
        # set to last message
        self.textBufferPos = self.textBufferLength-self.numlines
        # clear line
        self.consoleEntry.enterText('')
        self.consoleOutput(textEntered, utils.CONSOLE_PLAYER1_TEXT)
        ClientMsg.chat( textEntered )
        self.focus()

    def manageFocus(self):
        if self.consoleFrame.isHidden():
            self.consoleFrame.toggleVis()
            
        if self.consoleEntry["focus"] == 0:
            self.focus()
            
    def consoleOutput(self, printString, msgType):
        if msgType == utils.CONSOLE_SYSTEM_ERROR:
            self.write(printString, utils.CONSOLE_SYSTEM_ERROR_TEXT_COLOR)
        elif msgType == utils.CONSOLE_SYSTEM_MESSAGE:
            self.write(printString, utils.CONSOLE_SYSTEM_MESSAGE_TEXT_COLOR)
        elif msgType == utils.CONSOLE_PLAYER1_TEXT:
            self.write(printString, utils.CONSOLE_PLAYER1_TEXT_COLOR)
        else:
            self.write(printString, utils.CONSOLE_PLAYER2_TEXT_COLOR)
                
        
    def write( self, printString, color=(100,100,100,0.5) ):
        # remove not printable characters (which can be input by console input)
        printString = re.sub( r'[^%s]' % re.escape(string.printable[:95]), "", printString)
    
        splitLines = self.linewrap.wrap(printString)
        for line in splitLines:
            self.textBuffer.append( [line, color] )
            self.textBuffer.pop(0)
        
        self.updateOutput()
  
    def updateOutput( self ):
        for lineNumber in xrange(self.numlines):
            lineText, color = self.textBuffer[lineNumber + self.textBufferPos]
            self.consoleOutputList[self.numlines - lineNumber - 1].setText( lineText )
            self.consoleOutputList[self.numlines - lineNumber - 1]['fg'] = color

    def focus( self ):
        self.consoleEntry['focus'] = 1
      
    def unfocus( self ):
        self.consoleEntry['focus'] = 0
    
    def getTightBounds(self):
        l,r,b,t = self.consoleFrame.getBounds() 
        print l,r,b,t
        bottom_left = Point3(l,0,b) 
        top_right = Point3(r,0,t) 
        return (bottom_left,top_right) 