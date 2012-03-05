#############################################################################
# IMPORTS
#############################################################################

# python imports
import string

# panda3D imports
from panda3d.core import *
from direct.gui.DirectGui import *


# strain related imports


#========================================================================
#

unit_dict = {}
unit_dict['NONE'] = {'name':'NONE', 'cost':0}
unit_dict['Standard'] = {'name':'Standard', 'cost':200}
unit_dict['Sergeant'] = {'name':'Sergeant', 'cost':250}
unit_dict['Medic'] = {'name':'Medic', 'cost':200}
unit_dict['Heavy'] = {'name':'Heavy', 'cost':220}
unit_dict['Scout'] = {'name':'Scout', 'cost':180}
unit_dict['Jumper'] = {'name':'Jumper', 'cost':200}


name_list = ['NONE (0)', 'Standard (200)', 'Sergeant (250)', 'Medic (200)', 'Heavy (220)', 'Scout (180)', 'Jumper (200)']

class Selector():
    def __init__(self, parent, x, y, i):
        self.parent = parent
        self.cost = 0
        font = loader.loadFont('monommm_5.ttf')
        self.dom = DirectOptionMenu(text="Unit", scale=0.05, items=name_list, initialitem=0, highlightColor=(1,0,0,1),command=self.itemSel
                            ,relief=DGG.RAISED, popupMarkerBorder = (.5, .5), pressEffect=0, text_scale=0.8, item_text_font=font, text_font=font)

        self.dom.setPos(x, 0, y)
        self.dom.reparentTo(self.parent.root)
        
    def itemSel(self, arg):
        ind = arg.find(' ')
        arg_mod = arg[0:ind]
        cost_diff = self.cost - unit_dict[arg_mod]['cost'] 
        
        if self.parent.budget + cost_diff < 0:
            self.dom['text'] = 'NONE (0)'
        else:
            self.cost = unit_dict[arg_mod]['cost']
            self.parent.refreshBudget(cost_diff)
       
class Squadselector():
    def __init__(self, parent, player, budget):
        self.parent = parent
        self.player = player
        self.player_id = None

        self.root = aspect2d.attachNewNode('root_selector')

        self.budget = budget

        self.pickers = []
        
        for i in xrange(10):
            s = Selector(self, -1, 0.8-i/10., i)
            self.pickers.append(s)
        
            
        p = DirectLabel(text=self.player, scale=0.05)
        p.setPos(-1, 0, 0.9)
        p.reparentTo(self.root)
        
        self.b = DirectLabel(text=str(self.budget), scale=0.05)
        self.b.setPos(-0.7, 0, 0.9)
        self.b.reparentTo(self.root)
        
        self.go = DirectButton(text='GO!', command=self.go)
        self.go.setPos(0,0,0)
        self.go.setScale(0.05)
        self.go.reparentTo(self.root)
        
        self.cancel = DirectButton(text='Cancel!', command=self.cancel)
        self.cancel.setPos(0,0,-0.2)
        self.cancel.setScale(0.05)
        self.cancel.reparentTo(self.root)
    
    def go(self):
        for p in self.pickers:
            l = p.dom.get()
            ind = l.find(' ')
            l_mod = l[0:ind]
            if l_mod != 'NONE':
                print l_mod
    
    def cancel(self):
        self.root.removeNode()
        self.parent.fsm.request('LoginScreen')
    
    def refreshBudget(self, val):
        self.budget += val
        self.b['text'] = str(self.budget)
        


        




        
    
            