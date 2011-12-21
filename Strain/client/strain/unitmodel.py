from direct.actor.Actor import Actor
from panda3d.core import Vec4, Point4, Point3, Point2, NodePath, TextNode#@UnresolvedImport
from panda3d.core import PointLight#@UnresolvedImport
from panda3d.core import TransparencyAttrib, TextureStage#@UnresolvedImport
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, Func
import random
import utils

#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, parent, unit_id, wpn_list, off=False):
        self.parent = parent
        self.id = str(unit_id)

        self.node = NodePath("unit_"+self.id)
        #self.dummy_node = NodePath("dummy_unit_"+self.id)
        #self.dest_node = NodePath("dest_unit_"+self.id)
        
        # Get unit data from the Client
        unit = self.parent.parent.getUnitData(unit_id)
        if unit['owner_id'] == "1":
            self.team_color = Vec4(0.7, 0.2, 0.3, 1)
        elif unit['owner_id'] == "2":
            self.team_color = Vec4(0.106, 0.467, 0.878, 1)
        else:
            self.team_color = Vec4(0, 1, 0, 1)        
        self.model = utils.loadUnit(unit['name'], wpn_list)
        
        self.model.reparentTo(self.node)
        #self.dummy_node.reparentTo(self.node)
        #self.dest_node.reparentTo(self.node)        
        
        if not off:
            scale = 0.25
            h = 180
            pos = Point3(int(unit['pos'][0]), int(unit['pos'][1]), 0)
            pos = self.calcWorldPos(pos)
        else:
            scale = 1
            h = 0
            pos = Point3(0, 1.7, -2.1)
        
        # Bake in rotation transform because model is created facing towards screen (h=180)
        self.model.setScale(scale)
        self.model.setH(h)
        self.model.flattenLight() 
        self.node.setPos(pos)

        #self.model.setLightOff()
        self.node.setTag("type", "unit")
        self.node.setTag("id", str(self.id))        
        self.node.setTag("player_id", str(unit['owner_id']))
        self.node.setTag("team", str(unit['owner_id']))

        # If unit model is not rendered for portrait, set its heading as received from server
        if not off:
            self.setHeading(unit)
            
        self.marker = Actor("ripple2") 
        self.marker.reparentTo(self.node)
        self.marker.setP(-90)
        self.marker.setScale(0.7, 0.7, 0.7)
        self.marker.setColor(self.team_color)
        
        
        plight = PointLight('plight')
        plight.setColor(Point4(0.2, 0.2, 0.2, 1))
        plnp = self.node.attachNewNode(plight)
        plnp.setPos(0, 0, 0)
        
        self.marker.setLight(plnp)
        self.marker.setTransparency(TransparencyAttrib.MAlpha)
        self.marker.setAlphaScale(0.5) 
        self.marker.setTag("type", "unit_marker")
        
        self.marker.setPos(0, 0, 0.02)
        #self.marker.flattenLight()
        #self.marker.hide()
        
        self.last_overwatch = False
        
        self.passtime = 0
        self.setIdleTime()
        
        self.target_unit = None
    
    def setIdleTime(self):
        self.idletime = random.randint(10, 20)
    
    def reparentTo(self, node):
        self.node.reparentTo(node)
    
    def getAnimName(self, anim_type):
        num = random.randint(1, self.anim_count_dict[anim_type])
        return anim_type + str(num).zfill(2)    
    
    def calcWorldPos(self, pos):
        return pos + Point3(0.5, 0.5, 0.3)  
        
    def getHeadingTile(self, unit):
        x = int(unit['pos'][0])
        y = int(unit['pos'][1])  
        heading = unit['heading']  
        
        if heading == utils.HEADING_NW:
            o = Point2(x-1, y+1)
        elif heading == utils.HEADING_N:
            o = Point2(x, y+1)
        elif heading == utils.HEADING_NE:
            o = Point2(x+1, y+1)
        elif heading == utils.HEADING_W:
            o = Point2(x-1, y)
        elif heading == utils.HEADING_E:
            o = Point2(x+1, y)
        elif heading == utils.HEADING_SW:
            o = Point2(x-1, y-1)
        elif heading == utils.HEADING_S:
            o = Point2(x, y-1)
        elif heading == utils.HEADING_SE:
            o = Point2(x+1, y-1)
        return o
    
    def setHeading(self, heading):
        tile_pos = self.getHeadingTile(heading)
        dest_node = NodePath("dest_node")
        dest_node.setPos(render, tile_pos.getX()+0.5, tile_pos.getY()+0.5, 0.3)
        self.node.lookAt(dest_node)

    def getActorInterval(self, anim_type, loop=0, duration=None, startFrame=None, endFrame=None):
        return ActorInterval(self.model, anim_type, loop = loop, duration = duration, startFrame=startFrame, endFrame=endFrame)
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()
    
#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class LegoUnitModel:
    def __init__(self, parent, unit_id, off=False):
        self.parent = parent
        self.id = str(unit_id)

        self.node = NodePath("unit_"+self.id)
        
        # Get unit data from the Client
        unit = self.parent.parent.getUnitData(unit_id)
        if unit['owner_id'] == "1":
            self.team_color = Vec4(0.7, 0.2, 0.3, 1)
        elif unit['owner_id'] == "2":
            self.team_color = Vec4(0.106, 0.467, 0.878, 1)
        else:
            self.team_color = Vec4(0, 1, 0, 1)        
        self.model, self.parts = utils.loadLegoUnit()
        
        self.model.reparentTo(self.node)       
        
        if not off:
            scale = 0.25
            h = 180
            pos = Point3(int(unit['pos'][0]), int(unit['pos'][1]), 0)
            pos = self.calcWorldPos(pos)
        else:
            scale = 1
            h = 0
            pos = Point3(0, 4.1, -1)
        
        # Bake in rotation transform because model is created facing towards screen (h=180)
        self.model.setScale(scale)
        self.model.setH(h)
        self.model.flattenLight() 
        self.node.setPos(pos)

        #self.model.setLightOff()
        self.node.setTag("type", "unit")
        self.node.setTag("id", str(self.id))        
        self.node.setTag("player_id", str(unit['owner_id']))
        self.node.setTag("team", str(unit['owner_id']))

        # If unit model is not rendered for portrait, set its heading as received from server
        if not off:
            self.setHeading(unit)
        
        self.last_overwatch = False
        
        self.passtime = 0
        self.setIdleTime()
        
        self.target_unit = None
    
    def setIdleTime(self):
        self.idletime = random.randint(10, 20)
    
    def reparentTo(self, node):
        self.node.reparentTo(node)
    
    def getAnimName(self, anim_type):
        num = random.randint(1, self.anim_count_dict[anim_type])
        return anim_type + str(num).zfill(2)   
    
    def getActorInterval(self, anim_type, loop=0, duration=None, startFrame=None, endFrame=None):
        p = Parallel()
        for part in self.parts:
            a = ActorInterval(part, anim_type, loop=loop, duration=duration, startFrame=startFrame, endFrame=endFrame)
            p.append(a)
        return p
    
    def calcWorldPos(self, pos):
        return pos + Point3(0.5, 0.5, 0.3)  
        
    def getHeadingTile(self, unit):
        x = int(unit['pos'][0])
        y = int(unit['pos'][1])  
        heading = unit['heading']  
        
        if heading == utils.HEADING_NW:
            o = Point2(x-1, y+1)
        elif heading == utils.HEADING_N:
            o = Point2(x, y+1)
        elif heading == utils.HEADING_NE:
            o = Point2(x+1, y+1)
        elif heading == utils.HEADING_W:
            o = Point2(x-1, y)
        elif heading == utils.HEADING_E:
            o = Point2(x+1, y)
        elif heading == utils.HEADING_SW:
            o = Point2(x-1, y-1)
        elif heading == utils.HEADING_S:
            o = Point2(x, y-1)
        elif heading == utils.HEADING_SE:
            o = Point2(x+1, y-1)
        return o
    
    def setHeading(self, heading):
        tile_pos = self.getHeadingTile(heading)
        dest_node = NodePath("dest_node")
        dest_node.setPos(render, tile_pos.getX()+0.5, tile_pos.getY()+0.5, 0.3)
        self.node.lookAt(dest_node)
        
        
    def cleanup(self):
        for part in self.parts:
            part.cleanup()
        
    def remove(self):
        for part in self.parts:
            part.remove()  
