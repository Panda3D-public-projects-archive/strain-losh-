#############################################################################
# IMPORTS
#############################################################################

# python imports
import string
from collections import deque

# panda3D imports
from panda3d.core import *
from direct.gui.DirectGui import *
from panda3d.rocket import *
from squaddatasource import *
# strain related imports


#========================================================================
#

unit_dict = {}
unit_dict['NONE'] = {'name':'NONE', 'cost':0}
unit_dict['Standard'] = {'name':'Standard', 'cost':100}
unit_dict['Sergeant'] = {'name':'Sergeant', 'cost':150}
unit_dict['Medic'] = {'name':'Medic', 'cost':100}
unit_dict['Heavy'] = {'name':'Heavy', 'cost':100}
unit_dict['Scout'] = {'name':'Scout', 'cost':100}
unit_dict['Jumper'] = {'name':'Jumper', 'cost':100}


name_list = ['NONE (0)', 'Standard (100)', 'Sergeant (150)', 'Medic (100)', 'Heavy (100)', 'Scout (100)', 'Jumper (100)']

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
       
class SquadSelector():
    def __init__(self, parent, player, budget):
        self.parent = parent
        self.player = player
        self.player_id = None

        #self.root = aspect2d.attachNewNode('root_selector')

        self.budget = budget
        self.current_sum = 0
        
        self.pickers = []
        
#        for i in xrange(10):
#            s = Selector(self, -1, 0.8-i/10., i)
#            self.pickers.append(s)
#        
#            
#        p = DirectLabel(text=self.player, scale=0.05)
#        p.setPos(-1, 0, 0.9)
#        p.reparentTo(self.root)
#        
#        self.b = DirectLabel(text=str(self.budget), scale=0.05)
#        self.b.setPos(-0.7, 0, 0.9)
#        self.b.reparentTo(self.root)
#        
#        self.go = DirectButton(text='GO!', command=self.go)
#        self.go.setPos(0,0,0)
#        self.go.setScale(0.05)
#        self.go.reparentTo(self.root)
#        
#        self.cancel = DirectButton(text='Cancel!', command=self.cleanup)
#        self.cancel.setPos(0,0,-0.2)
#        self.cancel.setScale(0.05)
#        self.cancel.reparentTo(self.root)
    
        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        
        self.squadData = SquadDataSource("squad_data")
        self.squadDataFormatter = SquadDataFormatter("frm")
        
        self.doc = self.parent.rContext.LoadDocument('data/rml/squad.rml')
        self.doc.Show()
        
        for i in xrange(1, 9):
            ddId = "soldier" + str(i)
            element = self.doc.GetElementById(ddId)
            element.value = 'NONE'
            element.AddEventListener('change', self.itemChanged, True)
            self.pickers.append(element)
                   
        element = self.doc.GetElementById('ok')
        element.AddEventListener('click', self.go, True)
        element = self.doc.GetElementById('cancel')
        element.AddEventListener('click', self.cleanup, True)

        element = self.doc.GetElementById('plr')
        element.inner_rml = self.player
        element = self.doc.GetElementById('bgt')
        element.inner_rml = str(self.budget)

    def go(self):
        self.parent.deploy_queue = deque()
        self.parent.deployed_dict = {}
        for p in self.pickers:
            l = p.value
            #ind = l.find(' ')
            #l_mod = l[0:ind]
            if l != 'NONE':
                self.parent.deploy_queue.append(l)
        self.parent.fsm.request('Deploy')
    
    def cleanup(self):
        #self.root.removeNode()
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
    
    def refreshBudget(self, val):
        self.budget += val
        self.b['text'] = str(self.budget)
        
    def itemChanged(self):
        self.current_sum = 0
        for element in self.pickers:
            value = unit_dict[element.value]['cost']
            if self.current_sum + int(value) > self.budget:
                element.value = 'NONE'
            else:
                self.current_sum += int(value)
        
        element = self.doc.GetElementById('bgt')
        element.inner_rml = str(self.budget - self.current_sum)



        




        
    
            