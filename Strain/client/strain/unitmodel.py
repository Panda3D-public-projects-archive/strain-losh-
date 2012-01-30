#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from panda3d.core import Vec4, Point3, NodePath, CardMaker#@UnresolvedImport
from panda3d.core import PointLight, BitMask32#@UnresolvedImport
from panda3d.core import TransparencyAttrib, AntialiasAttrib#@UnresolvedImport
from panda3d.core import CollisionNode, CollisionPolygon#@UnresolvedImport
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, LerpColorInterval, Wait#@UnresolvedImport

# strain related imports
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
        self.owner_id = unit['owner_id']
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
            self.setHeading(unit['heading'])
        
        self.target_unit = None
        
        self.tex_circle1 = loader.loadTexture('circle.png')
        self.tex_circle2 = loader.loadTexture('circle2.png')
        self.tex_target = loader.loadTexture('target.png')

        
        cm = CardMaker('cm') 
        self.marker = self.node.attachNewNode(cm.generate()) 
        self.marker.setP(render, -90)
        self.marker.setPos(-0.5, -0.5, 0)
        self.marker.setTexture(self.tex_circle1)
        self.marker.setColor(0, 1, 0)
        self.marker.setDepthOffset(1)
        #cpos.node().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
        self.marker.setTransparency(TransparencyAttrib.MAlpha)
        self.marker.setBin('highlight', 25)
        self.marker.setCollideMask(0)
        self.marker.setLightOff()
        self.marker.detachNode()
        self.marker_interval = Sequence(LerpColorInterval(self.marker, 0.3, (0.4, 0.1, 0.1, 1)),
                                        LerpColorInterval(self.marker, 0.3, (1, 0, 0, 1)),
                                        )        
        
        
        cquad1 = CollisionPolygon(Point3(-0.5, -0.5, 0), Point3(-0.5, -0.5, 1), Point3(-0.5, 0.5, 1), Point3(-0.5, 0.5, 0))
        cquad2 = CollisionPolygon(Point3(0.5, -0.5, 0), Point3(0.5, -0.5, 1), Point3(-0.5, -0.5, 1), Point3(-0.5, -0.5, 0))
        cquad3 = CollisionPolygon(Point3(0.5, 0.5, 0), Point3(0.5, 0.5, 1), Point3(0.5, -0.5, 1), Point3(0.5, -0.5, 0))
        cquad4 = CollisionPolygon(Point3(-0.5, 0.5, 0), Point3(-0.5, 0.5, 1), Point3(0.5, 0.5, 1), Point3(0.5, 0.5, 0))
        cquad5 = CollisionPolygon(Point3(0.5, -0.5, 1), Point3(0.5, 0.5, 1), Point3(-0.5, 0.5, 1), Point3(-0.5, -0.5, 1))
        
        self.cnodePath = self.node.attachNewNode(CollisionNode('cnode'))
        self.cnodePath.node().addSolid(cquad1)
        self.cnodePath.node().addSolid(cquad2)
        self.cnodePath.node().addSolid(cquad3)
        self.cnodePath.node().addSolid(cquad4)  
        self.cnodePath.node().addSolid(cquad5)
        # DEBUG
        #cnodePath.show()
        self.setCollisionOn()
        
        self.isHovered = False
        self.isSelected = False
        self.isTargeted = False
        self.isEnemyVisible = False
        
    def setCollisionOn(self):
        self.cnodePath.setCollideMask(BitMask32.bit(1)) 
        
    def setCollisionOff(self):
        self.cnodePath.setCollideMask(BitMask32.bit(0))  
    
    def markHovered(self):
        if self.owner_id == self.parent.parent.player_id:
            self.setHovered()
        else:
            self.setTargeted()
            
    def unmarkHovered(self):
        if self.owner_id == self.parent.parent.player_id:
            self.clearHovered()
        else:
            self.clearTargeted()
    
    def setHovered(self):
        if not self.isHovered and not self.isSelected and not self.isEnemyVisible and not self.isTargeted:
            self.marker.clearTexture()
            self.marker.setTexture(self.tex_circle2)
            self.marker.setColor(0.2, 0.78, 0.157)
            self.marker.reparentTo(self.node)      
            self.isHovered = True
            
    def clearHovered(self):
        if self.isHovered:
            self.marker.detachNode()            
            self.isHovered = False
            
    def setSelected(self):
        if not self.isSelected and not self.isEnemyVisible and not self.isTargeted:
            self.marker.clearTexture()
            self.marker.setTexture(self.tex_circle1)
            self.marker.setColor(0, 1, 0)
            self.marker.reparentTo(self.node)
            self.isHovered = False
            self.isSelected = True
            
    def clearSelected(self):
        if self.isSelected:
            self.marker.detachNode()
            self.isSelected = False
            
    def setTargeted(self):
        if not self.isTargeted:
            self.marker_interval.loop()
            self.isTargeted = True 
    
    def clearTargeted(self):
        if self.isTargeted:
            self.marker_interval.pause()
            self.marker.setColor(1, 0, 0)
            self.isTargeted = False
            
    def setEnemyVisible(self):
        if not self.isEnemyVisible:
            self.marker.clearTexture()
            self.marker.setTexture(self.tex_target)
            self.marker.setColor(1, 0, 0)
            self.marker.reparentTo(self.node)
            self.isEnemyVisible = True
            
    def clearEnemyVisible(self):
        if self.isEnemyVisible:
            self.marker.detachNode()
            self.isEnemyVisible= False
            
    def clearAllFlags(self):
        self.marker.detachNode()
        self.isHovered = False
        self.isSelected = False
        self.isTargeted = False
        self.isEnemyVisible = False
        
    def calcWorldPos(self, pos):
        return pos + Point3(0.5, 0.5, utils.GROUND_LEVEL)
    
    def setHeading(self, heading):
        self.model.setH(utils.getHeadingAngle(heading))
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()  
