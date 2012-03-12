#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from panda3d.core import Vec4, Point3, NodePath, CardMaker, TextNode#@UnresolvedImport
from panda3d.core import PointLight, BitMask32#@UnresolvedImport
from panda3d.core import TransparencyAttrib, AntialiasAttrib#@UnresolvedImport
from panda3d.core import CollisionNode, CollisionPolygon, CollisionSphere#@UnresolvedImport
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, LerpColorInterval, Wait#@UnresolvedImport
from direct.gui.OnscreenText import OnscreenText#@UnresolvedImport

# strain related imports
import utils
    
#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, parent, unit_id, off=False, wpn_list=None):
        self.parent = parent
        self.id = str(unit_id)
        self.off = off

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
        if unit['name'] == 'marine_standard':        
            self.model = utils.loadUnit('marine', 'standard', unit['owner_id']) 
        elif unit['name'] == 'marine_sergeant': 
            self.model = utils.loadUnit('marine', 'sergeant', unit['owner_id'])
        elif unit['name'] == 'marine_heavy': 
            self.model = utils.loadUnit('marine', 'heavy', unit['owner_id'])
        elif unit['name'] == 'marine_scout': 
            self.model = utils.loadUnit('marine', 'scout', unit['owner_id'])
        elif unit['name'] == 'marine_medic': 
            self.model = utils.loadUnit('marine', 'medic', unit['owner_id'])
        elif unit['name'] == 'marine_jumper': 
            self.model = utils.loadUnit('marine', 'jumper', unit['owner_id'])            
        self.model.reparentTo(self.node)
        
        if not off:
            scale = 0.3
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
        
        
        """
        cquad1 = CollisionPolygon(Point3(-0.5, -0.5, 0), Point3(-0.5, -0.5, 1), Point3(-0.5, 0.5, 1), Point3(-0.5, 0.5, 0))
        cquad2 = CollisionPolygon(Point3(0.5, -0.5, 0), Point3(0.5, -0.5, 1), Point3(-0.5, -0.5, 1), Point3(-0.5, -0.5, 0))
        cquad3 = CollisionPolygon(Point3(0.5, 0.5, 0), Point3(0.5, 0.5, 1), Point3(0.5, -0.5, 1), Point3(0.5, -0.5, 0))
        cquad4 = CollisionPolygon(Point3(-0.5, 0.5, 0), Point3(-0.5, 0.5, 1), Point3(0.5, 0.5, 1), Point3(0.5, 0.5, 0))
        cquad5 = CollisionPolygon(Point3(0.5, -0.5, 1), Point3(0.5, 0.5, 1), Point3(-0.5, 0.5, 1), Point3(-0.5, -0.5, 1))
        """
        
        """
        csphere1 = CollisionSphere(0, 0, 0.5, 0.6)
        cquad5 = CollisionPolygon(Point3(0.5, -0.5, 0), Point3(0.5, 0.5, 0), Point3(-0.5, 0.5, 0), Point3(-0.5, -0.5, 0))
        
        self.cnodePath = self.node.attachNewNode(CollisionNode('cnode'))
        """
        
        """
        self.cnodePath.node().addSolid(cquad1)
        self.cnodePath.node().addSolid(cquad2)
        self.cnodePath.node().addSolid(cquad3)
        self.cnodePath.node().addSolid(cquad4)  
        self.cnodePath.node().addSolid(cquad5)
        """
        
        """
        self.cnodePath.node().addSolid(csphere1)
        self.cnodePath.node().addSolid(cquad5)
        """
        # DEBUG
        #self.cnodePath.show()
        #self.setCollisionOn()
        
        self.isHovered = False
        self.isSelected = False
        self.isTargeted = False
        self.isEnemyVisible = False
        
        self.isOverwatch = False
        self.isSetup = False
        
        self.overwatch_anim = Sequence(self.model.actorInterval('crouch'), self.model.actorInterval('overwatch'))
        self.standup_anim = Sequence(self.model.actorInterval('stand_up'), self.model.actorInterval('idle'))
        self.setup_anim = Sequence(self.model.actorInterval('crouch'), self.model.actorInterval('setup'))
        
        rnp = self.model.exposeJoint(None,"modelRoot","Wrist.R")
        lnp = self.model.exposeJoint(None,"modelRoot","Wrist.L")
        
        if wpn_list:
            if wpn_list[0] == 'Defaulter':
                self.rwp = loader.loadModel('gun1')
                self.rwp.setTexture(loader.loadTexture('gun.png'))
            elif wpn_list[0] == 'Heavy Defaulter':
                self.rwp = loader.loadModel('gun1')
                self.rwp.setTexture(loader.loadTexture('gun_blue.png'))
            elif wpn_list[0] == 'Default Pistol':
                self.rwp = loader.loadModel('gun1')
                self.rwp.setTexture(loader.loadTexture('gun_green.png'))
            elif wpn_list[0] == 'Plasma Pistol':
                self.rwp = loader.loadModel('gun1')
                self.rwp.setTexture(loader.loadTexture('gun_orange.png'))
            else:
                self.rwp = None
            
            if wpn_list[1] == 'Chain Sword':
                self.lwp = loader.loadModel('gun1')
                self.lwp.setTexture(loader.loadTexture('gun_red.png')) 
            elif wpn_list[1] == 'Power Axe':
                self.lwp = loader.loadModel('gun1')
                self.lwp.setTexture(loader.loadTexture('gun_red.png'))    
            elif wpn_list[1] == 'Doctors Bag':
                self.lwp = loader.loadModel('gun1')
                self.lwp.setTexture(loader.loadTexture('gun_red.png'))                                                       
            else:
                self.lwp = None
                
            if self.rwp:
                self.rwp.reparentTo(rnp)
            if self.lwp:
                self.lwp.setScale(0.5,0.5,0.5)
                self.lwp.reparentTo(lnp)
        
        if not off:
            self.node_2d = aspect2d.attachNewNode('node_2d')

        self.model.setShaderAuto()
        
    def pauseAllAnims(self):
        self.overwatch_anim.pause()
        self.standup_anim.pause()
        self.setup_anim.pause()
    
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
            self.parent.setOutlineShader(self.model)  
            self.isHovered = True
            
    def clearHovered(self):
        if self.isHovered:
            self.marker.detachNode()  
            self.parent.clearOutlineShader(self.model)              
            self.isHovered = False
            
    def setSelected(self):
        if not self.isSelected and not self.isEnemyVisible and not self.isTargeted:
            self.marker.clearTexture()
            self.marker.setTexture(self.tex_circle1)
            self.marker.setColor(0, 1, 0)
            self.marker.reparentTo(self.node)
            self.isSelected = True
            self.parent.clearOutlineShader(self.model)
            self.isHovered = False
            
    def clearSelected(self):
        if self.isSelected:
            self.marker.detachNode()
            self.isSelected = False
    
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
        return pos + Point3(0.5, 0.5, utils.GROUND_LEVEL)
    
    def setHeading(self, heading):
        self.model.setH(utils.getHeadingAngle(heading))
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        if not self.off:
            self.node_2d.removeNode()
        self.model.remove()  
