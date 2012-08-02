from panda3d.core import *

from strain.renderer.levelrenderer import LevelRenderer
from strain.renderer.unitrenderer import UnitRenderer
from strain.renderer.gridrenderer import GridRenderer
from strain.renderer.coordrenderer import CoordRenderer
from strain.renderer.shadermanager import ShaderManager
from strain.renderer.unitmarkerrenderer import UnitMarkerRenderer
from strain.renderer.animationmanager import AnimationManager
from strain.share import *
from strain.utils import TILE_SIZE, GROUND_LEVEL

class RenderManager():    
    def __init__(self, parent):
        self.parent = parent
        self.node = render.attachNewNode('RenderManagerNode')
        
        self.level_renderer = LevelRenderer(self, self.node)
        self.grid_renderer = GridRenderer(self, self.node)
        base.accept('g', self.grid_renderer.toggle)
        self.coord_renderer = CoordRenderer(self, self.node)
        base.accept('h', self.coord_renderer.toggle)
        self.unit_marker_renderer = UnitMarkerRenderer(self)
        self.shader_manager = ShaderManager(self)
        self.animation_manager = AnimationManager(self)
        
        self.unit_renderer_dict = {}
        
                
    def refresh(self):
        """Refresh everything from local copy of server data."""
        #self.level_renderer.cleanup()
        self.level_renderer.create(self.parent.local_engine.level, self.parent.local_engine.level.maxX, self.parent.local_engine.level.maxY, TILE_SIZE, GROUND_LEVEL)
        self.grid_renderer.redraw(self.parent.local_engine.level.maxX, self.parent.local_engine.level.maxY, TILE_SIZE, GROUND_LEVEL)
        self.coord_renderer.redraw(self.parent.local_engine.level.maxX, self.parent.local_engine.level.maxY, TILE_SIZE, GROUND_LEVEL)
        for unit_renderer in self.unit_renderer_dict.itervalues():
            unit_renderer.node.removeNode()
            del unit_renderer
        self.unit_renderer_dict = {}
        for unit in self.parent.local_engine.units.itervalues():
            unit_renderer = UnitRenderer(self, self.node)
            unit_renderer.loadForGameEngine(unit)
            self.unit_renderer_dict[unit['id']] = unit_renderer
        
        #self.level_renderer.node.setShaderAuto()
    
    def refreshFow(self):
        self.level_renderer.updateLevelLos(self.parent.local_engine.getInvisibleTiles(), self.parent.local_engine.getInvisibleWalls())
        self.level_renderer.switchNodes()
        self.level_renderer.flattenNodes()
    
    def refreshEnemyUnitMarkers(self):
        for unit_id in self.parent.local_engine.units:
            if self.parent.local_engine.isThisEnemyUnit(unit_id):
                self.unit_marker_renderer.refreshTargetInfo(unit_id)
    
    def deleteUnit(self, unit_id):
        if self.unit_renderer_dict.has_key(unit_id):
            unit_renderer = self.unit_renderer_dict[unit_id]
            unit_renderer.cleanup()
            self.unit_renderer_dict.pop(unit_id)
            del unit_renderer
            
    def loadUnit(self, unit_id, show_now=True):
        unit = self.parent.local_engine.units[unit_id]
        unit_renderer = UnitRenderer(self, self.node)
        unit_renderer.loadForGameEngine(unit, show_now)
        self.unit_renderer_dict[unit['id']]= unit_renderer
        return unit_renderer
        
    def showUnit(self, unit_renderer, pos=None, heading=None):
        if pos:
            unit_renderer.node.setPos(pos)
        if heading:
            unit_renderer.node.setH(heading)
        unit_renderer.node.reparentTo(self.node)
        
    def hideUnit(self, unit_id):
        unit_renderer = self.unit_renderer_dict[unit_id] 
        self.unit_renderer_dict.pop(unit_id)
        #unit_renderer.clearTargeted()
        unit_renderer.node.remove()
        del unit_renderer
        
    def detachUnit(self, unit_id):
        unit_renderer = self.unit_renderer_dict[unit_id] 
        unit_renderer.node.detachNode()     
        

        