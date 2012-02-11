import sys
import copy
from gtk.gdk import *
import pango #@UnresolvedImport

try:
    import pygtk #@UnresolvedImport
    pygtk.require( "2.0" )
except:
    pass

try:
    import gtk #@UnresolvedImport @UnusedImport
    import gtk.glade #@UnresolvedImport
except:
    sys.exit( 1 )


sys.path.append('./../client')
from strain.share import *



class LevelEditor:
    
    level = Level( "level2.txt" ) #@UndefinedVariable

    #size of boxes drawn on the editor
    rectSize = 20
    borderSize = 10
       
    #graphicContext
    gc = None
    gcWhite = None
    
    #so we know if the buttons are down
    left_button_down = 0
    right_button_down = 0
    
    def __init__( self ):
        
        #Set the Glade file
        self.gladefile = "editor.glade"  
        self.wTree = gtk.glade.XML( self.gladefile ) 
        
        #Get the Main Window, and connect the "destroy" event
        self.window = self.wTree.get_widget( "MainWindow" )
        if ( self.window ):
            self.window.connect( "destroy", gtk.main_quit )
            
            
        #Create our dictionary and connect it
        dic = {"on_ClearLevel_clicked" : self.on_ClearLevel_clicked,
               "on_writeLevel_clicked" : self.on_writeLevel_clicked,
               "on_spinbuttoncolumns_event" : self.on_spinbuttoncolumns_event, #debug
               "on_spinbuttonrows_map_event" : self.on_spinbuttonrows_map_event,
               "on_spinbuttoncolumns_map_event" : self.on_spinbuttoncolumns_map_event,
               "on_drawingarea1_motion_notify_event" : self.on_drawingarea1_motion_notify_event,
               #"on_drawingarea1_event" : self.on_drawingarea1_event,#debug
               "on_spinbuttoncolumns_value_changed" : self.on_spinbuttoncolumns_value_changed,
               "on_spinbuttonrows_value_changed" : self.on_spinbuttonrows_value_changed,
               "on_drawingarea1_expose_event" : self.on_drawingarea1_expose_event,
               "on_drawingarea1_button_press_event": self.on_drawingarea1_button_press_event,
               "on_drawingarea1_button_release_event" : self. on_drawingarea1_button_release_event,
               "on_saveButton_clicked" : self.on_saveButton_clicked,
               "on_loadButton_clicked" : self.on_loadButton_clicked,
               "on_MainWindow_destroy" : gtk.main_quit }
        self.wTree.signal_autoconnect( dic )

    def on_spinbuttoncolumns_event( self, widget, event ):
        #print event.type
        pass

    def on_spinbuttonrows_map_event( self, widget, event ):
        #widget.set_value( self.level.maxY )
        self.updateSpinButtonRows( self.level.maxY )
        
    def on_spinbuttoncolumns_map_event( self, widget, event ):
        #widget.set_value( self.level.maxX )
        self.updateSpinButtonColumns( self.level.maxX )

    def on_drawingarea1_motion_notify_event( self, widget, event ):        
        #convert screen coords to level coords
        """tmpX = int( event.x / ( self.rectSize + 5 ) )
        tmpY = int( event.y / ( self.rectSize + 5 ) )
        
        if self.left_button_down:        
            if self.level.markElement( tmpX, tmpY, 1 ):
                self.drawLevel( tmpX, tmpY )
                        
        if self.right_button_down:            
            if self.level.markElement( tmpX, tmpY, 0 ):
                self.drawLevel( tmpX, tmpY )"""               
    
    def on_ClearLevel_clicked( self, widget ):
        x = self.level.maxX
        y = self.level.maxY
        self.level.changeColumnNumber( 0 )
        self.level.changeRowNumber( 0 )                                
        self.level.changeColumnNumber( x )
        self.level.changeRowNumber( y )                                
        self.updateDrawingArea()
        
    def on_drawingarea1_event( self, widget, event ):
        #print event.type
        #if event.type == gtk.gdk.MAP:
        #    print "mapa"
        pass
        
    def on_spinbuttoncolumns_value_changed( self, widget ):
        
        #prevent this from going to 0 if it was not 1 first
        if widget.get_value() == 0:
            if self.level.maxX != 1:
                self.updateSpinButtonColumns( self.level.maxX )
                return 
            
        self.level.changeColumnNumber( widget.get_value() )
        self.updateDrawingArea()
   
    def on_spinbuttonrows_value_changed( self, widget ):
        
        #prevent this from going to 0 if it was not 1 first
        if widget.get_value() == 0:
            if self.level.maxY != 1:
                self.updateSpinButtonRows( self.level.maxY )
                return
             
        self.level.changeRowNumber( widget.get_value() )           
        self.updateDrawingArea()
        
    def updateSpinButtonRows( self, value ):
        widget = self.wTree.get_widget( "spinbuttonrows" )
        widget.set_value( value )
        
    def updateSpinButtonColumns( self, value ):
        widget = self.wTree.get_widget( "spinbuttoncolumns" )
        widget.set_value( value )
        
    def on_saveButton_clicked( self, widget ):
        self.saveLevelToFile( widget.parent )
            
    def on_loadButton_clicked( self, widget ):
        self.loadLevel()

    def loadLevel( self ):
        
        dialog = gtk.FileChooserDialog( 
                                       title="Open level",
                                       parent=self.wTree.get_widget( "MainWindow" ),
                                       action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                       buttons=( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK ),
                                       backend="/home/krav" )                                       
    
        if dialog.run() != gtk.RESPONSE_OK:
            return 
        
        filename = dialog.get_filename()
        
        dialog.destroy()            
        
        self.level.loadFromFile( filename )
        self.updateSpinButtonColumns( self.level.maxX )
        self.updateSpinButtonRows( self.level.maxY )
        self.drawLevel()
    
    def on_writeLevel_clicked( self, widget ):
        print "level::rows=", self.level.maxY, "::::cols=", self.level.maxX
        for row in self.level._data:
            print row
    
    def saveLevelToFile( self, window=None ):
        """Dump level to a file""" 
        """
        dialog = gtk.FileChooserDialog( 
                                       title="Save level",
                                       parent=self.wTree.get_widget( "MainWindow" ),
                                       action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK )#,
                                       #backend="/home/krav" 
                                       )
    
        if dialog.run() != gtk.RESPONSE_OK:
            return 
        
        filename = dialog.get_filename()
        #filename = "level.txt"
        
        dialog.destroy()        
        
        self.level.saveToFile( filename )

        #show OK message
        dialog = gtk.MessageDialog( 
                              parent=self.wTree.get_widget( "MainWindow" ),
#                              flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                              flags=gtk.DIALOG_MODAL,
                              type=gtk.MESSAGE_INFO,
                              buttons=gtk.BUTTONS_OK,
                              message_format="File -" + filename + "- saved OK." )
        
        #needed so the dialog closes when OK is pressed
        dialog.connect( 'response', lambda dialog, response: dialog.destroy() )
        dialog.show()
        """
        self.level.saveLevel()
           
                    
    def on_drawingarea1_button_release_event( self, widget, event ):
        if event.button == 1:
            self.left_button_down = 0
        elif event.button == 3:
            self.right_button_down = 0
            
                    
    def on_drawingarea1_button_press_event( self, widget, event ):
        # gtk.gdk.BUTTON_PRESS | gtk.gdk._2BUTTON_PRESS

        if event.x > (self.level.maxX * (self.borderSize + self.rectSize)) + self.borderSize:
            return
        
        if event.y > (self.level.maxY * (self.borderSize + self.rectSize)) + self.borderSize:
            return

        wls = ['Wall1', 'Wall2', 'Wall3', 'Ruin', 'ClosedDoor', 'OpenedDoor', 'ForceField']
        
        if event.type == gtk.gdk.BUTTON_PRESS:    
            tmpX = int( ( event.x ) / (self.rectSize+self.borderSize)  )
            tmpY = int( ( event.y ) / (self.rectSize+self.borderSize)  )
            tmpY = self.level.maxY - tmpY - 1
                    
            txr= event.x % (self.rectSize + self.borderSize )
            tyr= event.y % (self.rectSize + self.borderSize )
                        
            if txr >= self.borderSize and tyr >= self.borderSize:
                if event.button == 1:                    
                    self.level.increaseElement( tmpX, tmpY)    
                    
                if event.button == 3:                    
                    self.level.decreaseElement( tmpX, tmpY)                
            
            if txr > self.borderSize and tyr < self.borderSize:
                if event.button == 1:
                    elmt = self.level._grid[ 2*tmpX+1][(2*tmpY)+2]                     
                    if elmt:
                        idx = wls.index( elmt.name ) + 1
                        if idx + 1 == len(wls):
                            idx = 0
                    else:
                        idx = 0
                    self.level._grid[ 2*tmpX+1][(2*tmpY)+2] = self.level._walls[ wls[idx] ]
                    print self.level._grid[ 2*tmpX+1][(2*tmpY)+2].name
                if event.button == 3:                    
                    self.level._grid[ 2*tmpX+1][(2*tmpY)+2] = 0

            if txr < self.borderSize and tyr > self.borderSize:
                if event.button == 1:                    
                    elmt = self.level._grid[ 2*tmpX][(2*tmpY)+1]                     
                    if elmt:
                        idx = wls.index( elmt.name ) + 1
                        if idx + 1 == len(wls):
                            idx = 0
                    else:
                        idx = 0
                    self.level._grid[ 2*tmpX][(2*tmpY)+1] = self.level._walls[ wls[idx] ]
                    print self.level._grid[ 2*tmpX][(2*tmpY)+1].name
                if event.button == 3:                    
                    self.level._grid[ 2*tmpX][(2*tmpY)+1] = 0


        self.updateDrawingArea()
            
    def drawLine( self, widget, x1, y1, x2, y2 ):
        """Draws a line between the given points"""   
        gdkwindow = widget.window        
        gdkwindow.draw_line( self.gcGrey, x1, y1, x2, y2 )


    def drawRect( self, widget, x1, y1, width, height, fill ):
        """Draws a rectangle at give coords and width and height. If fill is
            true, than a filled rect will be drawn, only an outline otherwise."""        
        gdkwindow = widget.window    
                    
        if fill:
            gdkwindow.draw_rectangle( self.gc, 1, x1, y1, width, height )
        else:
            gdkwindow.draw_rectangle( self.gcGrey, 1, x1, y1, width, height )


    def on_drawingarea1_expose_event( self, widget, event ):
        
        mycolor = Color( '#FF0078' )
           
        self.gcWhite = widget.window.new_gc( foreground=mycolor )
        self.gcGrey = widget.window.new_gc( foreground = gtk.gdk.Color( blue = 65000 ) )
        self.gc = widget.window.new_gc()
                                
        self.drawLevel()


    def drawLevel( self, inX= - 1, inY= - 1 ):
        widget = self.wTree.get_widget( "drawingarea1" )          

        lyt = pango.Layout( gtk.Widget.create_pango_context( widget ) )

        data = copy.deepcopy( self.level._level_data )
        
        for l in data:
            l.reverse()

       
        #draw grid - x
        for i in range( self.level.maxX + 1 ):
            maxHeight = self.level.maxY * ( self.rectSize + self.borderSize ) + self.borderSize -1                 
            gridx = ( self.rectSize + self.borderSize ) * i 
            self.drawLine( widget, gridx, 0, gridx, maxHeight )
            self.drawLine( widget, gridx + (self.borderSize - 1), 0, gridx + (self.borderSize - 1), maxHeight )
        
        #draw grid - y
        for i in range( self.level.maxY + 1 ):
            maxWidth = self.level.maxX * ( self.rectSize + self.borderSize )+ self.borderSize -1
            gridy = ( self.rectSize + self.borderSize ) * i 
            self.drawLine( widget, 0, gridy, maxWidth, gridy )
            self.drawLine( widget, 0, gridy + (self.borderSize - 1), maxWidth, gridy + (self.borderSize-1) )
    
        #fill grid
        grid = copy.deepcopy(self.level._grid)
        for l in grid:
            l.reverse()
    
        for x in xrange( self.level.maxX*2 +1):
            for y in xrange( self.level.maxY*2 +1):
                if not grid[x][y]:
                    continue
                #vertical walls
                if x % 2 == 0 and y % 2 == 1:
                    x1 = x/2 * (self.borderSize + self.rectSize)
                    j = ((self.borderSize+self.rectSize)/2*(y-1))+ self.borderSize
                    for a in xrange( self.borderSize ):
                        self.drawLine(widget, x1+a, j, x1+a, j+self.rectSize)
                        
                #horizontal walls
                if y % 2 == 0 and x % 2 == 1:
                    y1 = y/2 * (self.borderSize + self.rectSize)
                    i = ((self.borderSize+self.rectSize)/2*(x-1))+ self.borderSize
                    for a in xrange( self.borderSize ):
                        self.drawLine(widget, i, y1+a, i+self.rectSize, y1+a)

                
        
        #fill squares
        for x in xrange( self.level.maxX ):
            for y in xrange( self.level.maxY ):
                
                if not data[x][y]:
                    continue
                
                sqX = self.borderSize + ( (self.rectSize+self.borderSize) * x ) #+ x
                sqY = self.borderSize + ( (self.rectSize+self.borderSize) * y ) #+ y
                
                if data[x][y] == 1:
                    self.drawRect(widget, sqX, sqY, self.rectSize, self.rectSize, 0)
                else:
                    self.drawRect(widget, sqX, sqY, self.rectSize, self.rectSize, 1)
                
                background = Color( red=35535, green=35535, blue=35535 )
                lyt.set_text( str( data[x][y]))     
            
                widget.window.draw_layout( self.gc, sqX + 7, sqY + 3, lyt, None, background )
                
                    


    def updateDrawingArea( self ):
        widget = self.wTree.get_widget( "drawingarea1" )  
        widget.queue_draw()
        