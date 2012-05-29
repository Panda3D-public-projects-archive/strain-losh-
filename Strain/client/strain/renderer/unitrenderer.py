from panda3d.core import *
import strain.utils as utils
from direct.actor.Actor import Actor
import string
    
#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitRenderer:
    def __init__(self, parent, parent_node):
        self.parent = parent
        self.parent_node = parent_node
        self.node = None
        
    def loadForGameEngine(self, unit):
        self.id = str(unit['id'])
        self.node = self.parent_node.attachNewNode("UnitRendererNode_"+self.id)

        if unit['owner_id'] == 100:
            self.team_color = Vec4(0.7, 0.2, 0.3, 1)
        elif unit['owner_id'] == 101:
            self.team_color = Vec4(0.106, 0.467, 0.878, 1)
        else:
            self.team_color = Vec4(0, 1, 0, 1)
        
        self.owner_id = unit['owner_id']
        
        i = string.index(unit['name'], '_')
        self.model = self.loadModel(unit['name'][0:i], unit['name'][i+1:], unit['owner_id'])           
        self.model.reparentTo(self.node)
        
        scale = utils.UNIT_SCALE
        h = 180
        pos = Point3(int(unit['pos'][0]), int(unit['pos'][1]), 0)
        pos = self.calcWorldPos(pos)
        
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
        self.setHeading(unit['heading'])
        
        self.target_unit = None
        
        """
        self.tex_circle1 = loader.loadTexture('circle.png')
        self.tex_circle2 = loader.loadTexture('circle2.png')
        self.tex_target = loader.loadTexture('target.png')
        """
        self.tex_selected = loader.loadTexture('selected.png')
        
        cm = CardMaker('cm') 
        self.marker = self.node.attachNewNode(cm.generate()) 
        self.marker.setP(render, -90)
        self.marker.setPos(-0.5, -0.5, 0.0)
        self.marker.setTexture(self.tex_selected)
        self.marker.setDepthOffset(1)
        self.marker.setTransparency(TransparencyAttrib.MMultisample)
        self.marker.setBin('highlight', 25)
        self.marker.setLightOff()
        self.marker.detachNode()        
        
        self.isHovered = False
        self.isSelected = False
        self.isTargeted = False
        self.isEnemyVisible = False
        
        self.isOverwatch = False
        self.isSetup = False
        
        self.node_2d = aspect2d.attachNewNode('node_2d')
    
    def loadModel(self, race, type, team=0):
        model = Actor(utils.unit_type_dict[race][type])
        model.loadAnims(utils.anim_dict[race])
        if team == 100:
            tex = loader.loadTexture(utils.unit_type_dict[race][type] + ".png")
        elif team == 101:
            tex = loader.loadTexture(utils.unit_type_dict[race][type] + "2.png")
        else:
            tex = loader.loadTexture(utils.unit_type_dict[race][type] + ".png")
        model.setTexture(tex)
        return model 
        
    
            

    
    def setTargeted(self):
        if self.isEnemyVisible and not self.isTargeted:
            self.marker_interval.loop()
            self.parent.setOutlineShader(self.model, color=Vec4(1,0,0,0)) 
            self.parent.parent.movement.showTargetInfo(self)
            self.isTargeted = True 
    
    def clearTargeted(self):
        if self.isTargeted:
            self.marker_interval.pause()
            self.marker.setColor(1, 0, 0)
            self.parent.clearOutlineShader(self.model)
            self.parent.parent.movement.clearTargetInfo()
            self.isTargeted = False
            
    def setEnemyVisible(self):
        if not self.isEnemyVisible:
            self.marker.clearTexture()
            self.marker.setTexture(self.tex_target)
            self.marker.setColor(1, 0, 0)
            self.marker.reparentTo(self.node)                
            self.isEnemyVisible = True
            if self.parent.parent.movement.hovered_unit_id == self.id:
                self.setTargeted()
                
    def clearEnemyVisible(self):
        if self.isEnemyVisible:
            self.marker.detachNode()
            self.parent.clearOutlineShader(self.model)
            self.parent.parent.movement.clearTargetInfo()
            self.isEnemyVisible= False
            
    def clearAllFlags(self):
        self.marker.detachNode()
        self.isHovered = False
        self.isSelected = False
        self.isTargeted = False
        self.isEnemyVisible = False
    
    def calcWorldPos(self, pos):
        return Point3(utils.TILE_SIZE * (pos.getX() + 0.5), utils.TILE_SIZE * (pos.getY() + 0.5), utils.GROUND_LEVEL)
    
    def setHeading(self, heading):
        self.model.setH(utils.getHeadingAngle(heading))
        
    def cleanup(self):
        self.model.cleanup()
        self.node_2d.removeNode()
        self.model.remove()  
        

