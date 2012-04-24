try:
    import pygtk
    pygtk.require( "2.0" )
except:
      pass
  
try:
    import gtk
    import gtk.glade
except:
    import traceback;traceback.print_exc()
    
    
import os
print os.getcwd()

import windowClass
from windowClass import LevelEditor    


mainWindow = LevelEditor()
gtk.main()