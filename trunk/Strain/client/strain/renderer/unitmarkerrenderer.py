from panda3d.core import *
import strain.utils as utils
from strain.share import toHit
from direct.gui.OnscreenText import OnscreenText

class UnitMarkerRenderer():
    def __init__(self, parent):
        self.parent = parent
        self.enemy_markers = {}
        taskMgr.add(self.markEnemyUnits, 'MarkEnemyUnitsTask', sort=2)
        
    def markHovered(self, unit_id):
        if self.parent.parent.local_engine.isThisMyUnit(unit_id):
            self.setHovered(unit_id)
        else:
            if self.parent.parent.sel_unit_id != None:
                self.setTargeted(unit_id)
            
    def unmarkHovered(self, unit_id):
        if self.parent.parent.local_engine.isThisMyUnit(unit_id):
            self.clearHovered(unit_id)
        else:
            self.clearTargeted(unit_id)
    
    def setHovered(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id] 
        if unit.isHovered == False and unit.isSelected == False:
            self.parent.shader_manager.setOutlineShader(unit.model)  
            unit.isHovered = True
            
    def clearHovered(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id] 
        if unit.isHovered == True:
            self.parent.shader_manager.clearShader(unit.model)              
            unit.isHovered = False
        
    def setSelected(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        self.parent.shader_manager.clearShader(unit.model)
        unit.isHovered = False
        unit.marker.reparentTo(unit.node)
        unit.isSelected = True
            
    def clearSelected(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        unit.marker.detachNode()
        unit.isSelected = False 
        
    def setTargeted(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        if unit.isTargeted == False:        
            self.parent.shader_manager.setFacingShader(unit.model, color=Vec4(1,0,0,0)) 
            unit.isTargeted = True 
    
    def clearTargeted(self, unit_id):
        unit = self.parent.unit_renderer_dict[unit_id]
        if unit.isTargeted == True:
            self.parent.shader_manager.clearShader(unit.model)
            unit.isTargeted = False
    
    def refreshTargetInfo(self, unit_id):
        if self.enemy_markers.has_key(unit_id):
            if self.parent.parent.turn_player == self.parent.parent.player_id and self.parent.parent.sel_unit_id != None:
                shooter = self.parent.parent.local_engine.units[self.parent.parent.sel_unit_id]
                target = self.parent.parent.local_engine.units[unit_id]   
                hit, desc = toHit(shooter, target, self.parent.parent.local_engine.level)
                text = str(hit)  + '%\n' + str(desc)
                bg = (1,0,0,0.7)
                fg = (1,1,1,1)            
                OnscreenText(parent = self.enemy_markers[unit_id]['info_node']
                              , text = text
                              , pos = (0.05, -0.05)
                              , align=TextNode.ACenter
                              , scale=0.04
                              , fg = fg
                              , bg = bg
                              , font = loader.loadFont(utils.GUI_FONT)
                              , shadow = (0, 0, 0, 1))
    
    def setMarker(self, unit_id):
        if self.enemy_markers.has_key(unit_id):
            self.enemy_markers[unit_id]['node'].reparentTo(aspect2d)
            self.enemy_markers[unit_id]['visible'] = True  
            if self.parent.unit_renderer_dict.has_key(unit_id): 
                unit_renderer = self.parent.unit_renderer_dict[unit_id] 
                self.enemy_markers[unit_id]['node'].setPos(self.calcMarkerPosition(unit_renderer))
        else:
            cm = CardMaker('')
            cm.setFrame(-0.05, 0.05, -0.05, 0.05)
            self.enemy_markers[unit_id] = {}
            self.enemy_markers[unit_id]['node'] = aspect2d.attachNewNode('')
            self.enemy_markers[unit_id]['marker_node'] = self.enemy_markers[unit_id]['node'].attachNewNode(cm.generate())
            self.enemy_markers[unit_id]['info_node'] = self.enemy_markers[unit_id]['node'].attachNewNode('')
            self.enemy_markers[unit_id]['marker_node'].setTexture(loader.loadTexture('action_preview_arrow.png'))
            self.enemy_markers[unit_id]['marker_node'].setTransparency(TransparencyAttrib.MAlpha)
            self.enemy_markers[unit_id]['node'].setPos(self.calcMarkerPosition(self.parent.unit_renderer_dict[unit_id]))            
            self.enemy_markers[unit_id]['visible'] = True
            
            if self.parent.parent.turn_player == self.parent.parent.player_id and self.parent.parent.sel_unit_id != None:
                shooter = self.parent.parent.local_engine.units[self.parent.parent.sel_unit_id]
                target = self.parent.parent.local_engine.units[unit_id]   
                hit, desc = toHit(shooter, target, self.parent.parent.local_engine.level)
                text = str(hit)  + '%\n' + str(desc)
                bg = (1,0,0,0.7)
                fg = (1,1,1,1)            
                OnscreenText(parent = self.enemy_markers[unit_id]['info_node']
                              , text = text
                              , pos = (0.05, -0.05)
                              , align=TextNode.ACenter
                              , scale=0.04
                              , fg = fg
                              , bg = bg
                              , font = loader.loadFont(utils.GUI_FONT)
                              , shadow = (0, 0, 0, 1))
            
    def clearMarker(self, unit_id):
        if self.enemy_markers.has_key(unit_id):
            self.enemy_markers[unit_id]['node'].detachNode()
            self.enemy_markers[unit_id]['visible'] = False    

    def calcMarkerPosition(self, unit_renderer):
        p = utils.nodeCoordInRender2d(unit_renderer.model)
        if p.x >= -0.95 and p.x <= 0.95 and p.z >= -0.95 and p.z <= 0.95: 
            pos = aspect2d.getRelativePoint(render2d, p)
        else:
            if p.x == 0:
                rez_x = 0
                if p.z > 0.95:
                    rez_z = 0.95
                elif p.z < -0.95:
                    rez_z = -0.95
            else:
                if abs(p.x) > abs(p.z):
                    if p.x > 0.95:
                        rez_x = 0.95
                    elif p.x < -0.95:
                        rez_x = -0.95
                    rez_z = p.z/p.x * rez_x
                elif abs(p.x) <= abs(p.z): 
                    if p.z > 0.95:
                        rez_z = 0.95
                    elif p.z < -0.95:
                        rez_z = -0.95
                    rez_x = p.x/p.z * rez_z
                
            rez = Point3(rez_x, 0, rez_z)
            pos = aspect2d.getRelativePoint(render2d, rez)
        return pos
            
    def markEnemyUnits(self, task):
        for unit_id in self.enemy_markers:
            if self.enemy_markers[unit_id]['visible'] == True:
                if self.parent.unit_renderer_dict.has_key(unit_id): 
                    unit_renderer = self.parent.unit_renderer_dict[unit_id] 
                    self.enemy_markers[unit_id]['node'].setPos(self.calcMarkerPosition(unit_renderer))
        return task.cont
