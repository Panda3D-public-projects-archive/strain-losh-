from panda3d.core import *

class UnitMarkerRenderer():
    def __init__(self, parent):
        self.parent = parent
        
    def markHovered(self, unit_id):
        if self.parent.parent.local_engine.isThisMyUnit(unit_id):
            self.setHovered(unit_id)
        else:
            None
            #if self.parent.parent.sel_unit_id != None:
            #    self.setTargeted(unit_id)
            
    def unmarkHovered(self, unit_id):
        if self.parent.parent.local_engine.isThisMyUnit(unit_id):
            self.clearHovered(unit_id)
        else:
            None
            #self.clearTargeted(unit_id)
    
    def setHovered(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id] 
        if unit.isHovered == False and unit.isSelected == False:
            self.parent.shader_manager.setOutlineShader(unit.model)  
            unit.isHovered = True
            
    def clearHovered(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id] 
        if unit.isHovered == True:
            self.parent.shader_manager.clearOutlineShader(unit.model)              
            unit.isHovered = False
        
    def setSelected(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        self.parent.shader_manager.clearOutlineShader(unit.model)
        unit.isHovered = False
        unit.marker.reparentTo(unit.node)
        unit.isSelected = True
            
    def clearSelected(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        unit.marker.detachNode()
        unit.isSelected = False 
        
    def setTargeted(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        #self.parent.setOutlineShader(self.model, color=Vec4(1,0,0,0)) 
        self.parent.parent.movement.showTargetInfo(unit_id)
        unit.isTargeted = True 
    
    def clearTargeted(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        if unit.isTargeted:
            #self.parent.clearOutlineShader(self.model)
            self.parent.parent.movement.clearTargetInfo(unit_id)
            self.isTargeted = False               
