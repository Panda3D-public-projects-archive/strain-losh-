from direct.actor.Actor import Actor
from panda3d.core import Vec4, Point4, Point3, Point2, NodePath, CardMaker#@UnresolvedImport
from panda3d.core import PointLight#@UnresolvedImport
from panda3d.core import TransparencyAttrib, AntialiasAttrib#@UnresolvedImport
import random
import utils
    
#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
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
        if unit['name'] == 'marine_common':        
            self.model = utils.loadUnit('marine', 'standard') 
        elif unit['name'] == 'marine_epic': 
            self.model = utils.loadUnit('marine', 'sergeant')
        elif unit['name'] == 'marine_hb': 
            self.model = utils.loadUnit('marine', 'heavy')
        
        self.model.reparentTo(self.node)
        if not off:
            scale = 0.4
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
        self.model.setAntialias(AntialiasAttrib.MMultisample)

        self.node.setTag("type", "unit")
        self.node.setTag("id", str(self.id))        
        self.node.setTag("player_id", str(unit['owner_id']))
        self.node.setTag("team", str(unit['owner_id']))

        # If unit model is not rendered for portrait, set its heading as received from server
        if not off:
            self.setHeading(unit)
        
        self.target_unit = None
        
        cm = CardMaker('cm') 
        self.marker = self.node.attachNewNode(cm.generate()) 
        self.marker.setP(render, -90)
        self.marker.setPos(-0.5, -0.5, 0)
        self.marker.setTexture(loader.loadTexture('circle.png'))
        self.marker.setColor(0, 1, 0)
        self.marker.setDepthOffset(1)
        #cpos.node().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
        self.marker.setTransparency(TransparencyAttrib.MAlpha)
        self.marker.setBin('highlight', 25)
        self.marker.setCollideMask(0)
        self.marker.detachNode()
    
    def showMarker(self):
        self.marker.reparentTo(self.node)
        
    def hideMarker(self):
        self.marker.detachNode()
    
    def setIdleTime(self):
        self.idletime = random.randint(10, 20)
    
    def reparentTo(self, node):
        self.node.reparentTo(node)  
        
    def calcWorldPos(self, pos):
        return pos + Point3(0.5, 0.5, utils.GROUND_LEVEL)  
        
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
        dest_node.setPos(render, tile_pos.getX()+0.5, tile_pos.getY()+0.5, utils.GROUND_LEVEL)
        self.node.lookAt(dest_node)
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()  
