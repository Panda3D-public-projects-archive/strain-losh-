#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from panda3d.core import TextNode, NodePath, Point2, Point3, TransparencyAttrib#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectFrame, DGG, DirectButton


# strain related imports
import utils


#========================================================================
#

class Slot():
    def __init__(self, type, icon, pos, size, transparency, id):
        print size
        self.button = DirectButton(frameTexture = icon, 
                                   pos = pos, 
                                   frameSize = size, 
                                   pad = (0.5, 0.5), 
                                   relief=1, 
                                   rolloverSound = None, 
                                   command = self.onClick,
                                   extraArgs = [id])
        self.button.bind(DGG.ENTER, self.onEnter)
        self.button.bind(DGG.EXIT, self.onExit)
        self.button.reparentTo(aspect2d)
        if transparency:
            self.button.setTransparency(TransparencyAttrib.MAlpha)

    def onClick(self, *args):
        print "click"
        
    def onEnter(self, *args):
        print "enter"
        
    def onExit(self, *args):
        print "exit"
        

class Squadselector(DirectObject):
    def __init__(self, parent, player):
        self.parent = parent
        self.player = player
        self.player_id = None
        self.settings = {'background-size':      (-base.getAspectRatio(), base.getAspectRatio(),  -1, 1),
                        'background-image':     'res/back.png',
                        'slot-size':            (0.25, 0.25),
                        'item-size':            (0.2, 0.2),
                        'slot-margin':           0.001,
                        'informer-popup-delay':  0.5,
                        'default-slot-image':   'res/base_slot.png',
                        'informer-font':        'res/arial.ttf',
                        'informer-bg-color':    (0.15, 0.067, 0.035, 0.92),
                        'informer-text-color':  (1, 1, 1, 1),
                        'use-transparency':     True
                        }
        self.unit_slots = []
        for y in xrange(2):
            for x in xrange(3):
                fx = self.settings['slot-size'][0] + self.settings['slot-margin']
                fy = self.settings['slot-size'][1] + self.settings['slot-margin']
                pos = (fx * x, 0, -fy * y)
                size = (0, self.settings['slot-size'][0], 0, self.settings['slot-size'][1])
                self.unit_slots.append(Slot('unit', 'marine_sergeant_slot.png', pos, size, True, 1))
    
            