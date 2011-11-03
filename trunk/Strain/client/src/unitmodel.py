from direct.actor.Actor import Actor
from panda3d.core import Vec4, Point4, Point3, Point2, NodePath#@UnresolvedImport
from panda3d.core import PointLight#@UnresolvedImport
from pandac.PandaModules import TransparencyAttrib#@UnresolvedImport
import random
import interface


#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, unit, scale=0.25, h=180, pos=None, off=False):
        self.anim_count_dict = {}
        self.model = self.load(unit['type'])
        self.id = str(unit['id'])
        self.unit = unit
        
        self.node = NodePath(self.id)
        self.dummy_node = NodePath("dummy_"+self.id)
        self.dest_node = NodePath("dest_"+self.id)
        
        self.model.reparentTo(self.node)
        self.dummy_node.reparentTo(self.node)
        self.dest_node.reparentTo(self.node)        
        
        # Bake in rotation transform because model is created facing towards screen (h=180)
        self.model.setScale(scale)
        self.model.setH(h)
        self.model.flattenLight() 
        
        x = int(unit['pos'][0])
        y = int(unit['pos'][1])
        
        if off:
            self.node.setPos(Point3(0,-8,-2))
        else:
            self.node.setPos(self.calcWorldPos(x, y))

        self.model.setLightOff()
        self.node.setTag("type", "unit")
        self.node.setTag("id", str(self.id))        
        self.node.setTag("player_id", str(unit['owner_id']))
        self.node.setTag("team", str(unit['owner_id']))

        # If unit model is not rendered for portrait, set its heading as received from server
        if not off:
            self.setHeading(self.unit['heading'])

        if unit['owner_id'] == "1":
            self.team_color = Vec4(1, 0, 0, 1)
        elif unit['owner_id'] == "2":
            self.team_color = Vec4(0.106, 0.467, 0.878, 1)
        else:
            self.team_color = Vec4(0, 1, 0, 1)
            
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
        
        self.passtime = 0
        self.setIdleTime()    

        if unit['type']=="terminator":
            t = loader.loadTexture("terminator2.tga")#@UndefinedVariable
            self.model.setTexture(t, 1)

    def load(self, unit_type):
        if unit_type == 'marine_common':
            model = Actor('marine_melee_axe_range_pistol', {'run': 'marine_melee_axe_range_pistol-run'
                                                           ,'idle01': 'marine_melee_axe_range_pistol-idle_stand'
                                                           ,'idle02': 'marine_melee_axe_range_pistol-idle_stand2'
                                                           ,'idle03': 'marine_melee_axe_range_pistol-idle_stand3'
                                                           ,'melee01': 'marine_melee_axe_range_pistol-melee'
                                                           ,'melee02': 'marine_melee_axe_range_pistol-melee2'
                                                           ,'fire01': 'marine_melee_axe_range_pistol-fire_stand'                                    
                                                           })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 3
            armor = model.find("**/power_armor_common")
            armor.setTexture(loader.loadTexture("power_armour_common_dif.tga"))
            armor_hide = model.find("**/power_armor_epic")
            armor_hide.hide()
            melee_weapon = model.find("**/power_axe_common")
            melee_weapon.setTexture(loader.loadTexture("power_axe_common_dif.tga"))
            melee_weapon_hide = model.find("**/power_axe_epic")
            melee_weapon_hide.hide()      
            range_weapon = model.find("**/bolt_pistol_common")
            range_weapon.setTexture(loader.loadTexture("bolt_pistol_common_dif.tga"))
            range_weapon_hide = model.find("**/bolt_pistol_epic")
            range_weapon_hide.hide()  
            head = model.find("**/space_marine_head")
            head.setTexture(loader.loadTexture("space_marine_head_dif.tga"))       
            pack = model.find("**/space_marine_backpack")
            pack.setTexture(loader.loadTexture("space_marine_backpack_dif.tga"))                       
        elif unit_type == 'marine_epic':
            model = Actor('marine_melee_axe_range_pistol', {'run': 'marine_melee_axe_range_pistol-run'
                                                           ,'idle01': 'marine_melee_axe_range_pistol-idle_stand'
                                                           ,'idle02': 'marine_melee_axe_range_pistol-idle_stand2'
                                                           ,'idle03': 'marine_melee_axe_range_pistol-idle_stand3'
                                                           ,'melee01': 'marine_melee_axe_range_pistol-melee'
                                                           ,'melee02': 'marine_melee_axe_range_pistol-melee2'
                                                           ,'fire01': 'marine_melee_axe_range_pistol-fire_stand'                                    
                                                           })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 3
            armor = model.find("**/power_armor_epic")
            armor.setTexture(loader.loadTexture("power_armour_epic_dif.tga"))
            armor_hide = model.find("**/power_armor_common")
            armor_hide.hide()
            melee_weapon = model.find("**/power_axe_epic")
            melee_weapon.setTexture(loader.loadTexture("power_axe_epic_dif.tga"))
            melee_weapon_hide = model.find("**/power_axe_common")
            melee_weapon_hide.hide()      
            range_weapon = model.find("**/bolt_pistol_epic")
            range_weapon.setTexture(loader.loadTexture("bolt_pistol_epic_dif.tga"))
            range_weapon_hide = model.find("**/bolt_pistol_common")
            range_weapon_hide.hide()  
            head = model.find("**/space_marine_head")
            head.setTexture(loader.loadTexture("space_marine_head_dif.tga"))    
            pack = model.find("**/space_marine_backpack")
            pack.setTexture(loader.loadTexture("space_marine_backpack_dif.tga"))                    
        elif unit_type == 'commissar':
            model = Actor('commissar', {'run': 'commissar-run'
                                       ,'idle01': 'commissar-idle1'
                                       ,'idle02': 'commissar-idle2'
                                       ,'idle03': 'commissar-idle3'
                                       ,'fire': 'commissar-fire'
                                       })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 3                                           
        return model
    
    def setIdleTime(self):
        self.idletime = random.randint(10, 20)
    
    def getAnimName(self, anim_type):
        num = random.randint(1, self.anim_count_dict[anim_type])
        return anim_type + str(num).zfill(2)    
    
    def calcWorldPos(self, x, y):
        return Point3(x + 0.5, y + 0.5, 0.3)
    
    def reparentTo(self, node):
        self.node.reparentTo(node)
        
    def setPos(self, pos):
        self.node.setPos(pos)   
        
    def getHeadingTile(self, heading):
        x = int(self.unit['pos'][0])
        y = int(self.unit['pos'][1])        
        
        if heading == interface.HEADING_NW:
            o = Point2(x-1, y+1)
        elif heading == interface.HEADING_N:
            o = Point2(x, y+1)
        elif heading == interface.HEADING_NE:
            o = Point2(x+1, y+1)
        elif heading == interface.HEADING_W:
            o = Point2(x-1, y)
        elif heading == interface.HEADING_E:
            o = Point2(x+1, y)
        elif heading == interface.HEADING_SW:
            o = Point2(x-1, y-1)
        elif heading == interface.HEADING_S:
            o = Point2(x, y-1)
        elif heading == interface.HEADING_SE:
            o = Point2(x+1, y-1)
        return o
    
    def setHeading(self, heading):
        tile_pos = self.getHeadingTile(heading)
        self.dest_node.setPos(render, tile_pos.getX()+0.5, tile_pos.getY()+0.5, 0.3)
        self.model.lookAt(self.dest_node)
        
    def play(self, anim):
        self.model.play(anim)
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()
    
