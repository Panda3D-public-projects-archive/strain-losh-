#############################################################################
# IMPORTS
#############################################################################

# python imports
import string

# panda3D imports
from panda3d.core import *
from direct.gui.DirectGui import *
from panda3d.rocket import *
# strain related imports


#========================================================================
#

unit_dict = {}
unit_dict['Standard'] = {'name':'Standard', 'cost':100}
unit_dict['Sergeant'] = {'name':'Sergeant', 'cost':150}
unit_dict['Medic'] = {'name':'Medic', 'cost':100}
unit_dict['Heavy'] = {'name':'Heavy', 'cost':100}
unit_dict['Scout'] = {'name':'Scout', 'cost':100}
unit_dict['Jumper'] = {'name':'Jumper', 'cost':100}


name_list = ['NONE (0)', 'Standard (100)', 'Sergeant (150)', 'Medic (100)', 'Heavy (100)', 'Scout (100)', 'Jumper (100)']

class SquadSelector():
    def __init__(self, parent, player, budget):
        self.parent = parent
        self.player = player
        self.player_id = None

        self.budget = budget
        self.current_sum = 0
        
        self.pickers = []
        
        self.parent.rRegion.setActive(1)
        self.parent.rContext = self.parent.rRegion.getContext()
        
        self.doc = self.parent.rContext.LoadDocument('data/rml/squad.rml')
        
        inner_rml = " "
        for unit in unit_dict:
            name = unit_dict[unit]['name']
            cost = unit_dict[unit]['cost']
            inner_rml += '<div id="' + name + '" class="list_item"><div class="list_item_filler"></div><div class="item_image">'
            inner_rml += '<img src="../textures/unit_' + name.lower() + '_big_transparent_32.png" width="32px" height="32px" alt="" title="" />' 
            inner_rml += '</div><div class="item_text"><div class="item_name">' + name + '</div><div class="item_cost">Cost:' + str(cost) + '</div></div></div>'
        
        element = self.doc.GetElementById('list_container')
        element.inner_rml = inner_rml
        
        for child in element.child_nodes:
            child.AddEventListener('click', self.selectUnit, True)
        
        element = self.doc.GetElementById('btn_recruit')
        element.AddEventListener('click', self.recruitUnit, True)

        element = self.doc.GetElementById('btn_deploy')
        element.AddEventListener('click', self.deploySquad, True)
        
        funds_label = self.doc.GetElementById('funds')
        funds_label.inner_rml = 'Funds left: ' + str(self.budget)
            
        self.doc.Show()
        
    def deploySquad(self):
        self.parent.deploy_queue = []
        self.parent.deployed_dict = {}
        for p in self.pickers:
            self.parent.deploy_queue.append(p)
        self.parent.fsm.request('Deploy')

    def removeUnit(self):
        i = 0
        for child in event.current_element.parent_node.child_nodes:
            if child == event.current_element:
                break
            i = i + 1

        self.pickers.pop(i)
        inner_rml = self.pickersToRML()
        event.current_element.parent_node.inner_rml = inner_rml
        self.refreshFunds()
        self.addSquadItemEvents()

    def recruitUnit(self):
        
        if len(self.pickers) == 12:
            return
        
        unit_id = None
        list = self.doc.GetElementById('list_container')
        for list_item in list.child_nodes:
            if list_item.class_name == 'list_item_selected':
                unit_id = list_item.id
                break
        
        if unit_id == None:
            return

        if (self.current_sum + unit_dict[unit_id.capitalize()]['cost']) > self.budget:
            return
        
        self.pickers.append(unit_id)
        inner_rml = self.pickersToRML()
        squad = self.doc.GetElementById('squad_container')
        squad.inner_rml = inner_rml
        self.refreshFunds()
        self.addSquadItemEvents()
    
    def pickersToRML(self):
        inner_rml = ''
        for p in self.pickers:
            inner_rml += '<div class="unit_item"><div class="unit_item_image">'
            inner_rml += '<img src="../textures/unit_' + p.lower() + '_big_transparent_32.png" width="32px" height="32px" alt="" title="" />'
            inner_rml += '</div></div>'
        
        for i in xrange(1, 13 - len(self.pickers)):
            inner_rml += '<div class="unit_item_empty"></div>'
            
        return inner_rml
    
    def addSquadItemEvents(self):
        element = self.doc.GetElementById('squad_container')
        for child in element.child_nodes:
            if child.class_name == 'unit_item': 
                child.AddEventListener('click', self.removeUnit, True)
    
    def selectUnit(self):
        for child in event.current_element.parent_node.child_nodes:
            child.class_name = "list_item"
        event.current_element.class_name = "list_item_selected"

    def refreshFunds(self):
        funds = 0
        for p in self.pickers:
            funds += unit_dict[p.capitalize()]['cost']
            
        self.current_sum = funds
        
        funds_label = self.doc.GetElementById('funds')
        funds_label.inner_rml = 'Funds left: ' + str(self.budget - self.current_sum)
        
    def cleanup(self):
        self.parent.rRegion.setActive(0)
        self.parent.rContext.UnloadAllDocuments()
        
        