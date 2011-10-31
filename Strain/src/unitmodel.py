from direct.actor.Actor import Actor
from panda3d.core import Point4, Point3, Point2, NodePath#@UnresolvedImport
from panda3d.core import PointLight#@UnresolvedImport
from pandac.PandaModules import TransparencyAttrib#@UnresolvedImport
import random
from unit import Unit

#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, unit, scale=0.25, h=180, pos=None, off=False):
        self.anim_count_dict = {}
        self.model = self.load(unit.type)
        self.id = str(unit.id)
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
        
        x = int(unit.pos.getX())
        y = int(unit.pos.getY())
        
        if pos:
            self.node.setPos(pos)
        else:
            self.node.setPos(self.calcWorldPos(x, y))

        self.model.setLightOff()
        self.node.setTag("type", "unit")
        self.node.setTag("id", str(self.id))        
        self.node.setTag("player_id", str(unit.owner_id))
        self.node.setTag("team", str(unit.owner_id))

        # If unit model is not rendered for portrait, set its heading as received from server
        if not off:
            self.setHeading(self.unit.heading)

        if unit.owner_id == "1":
            self.team_color = Point4(1, 0, 0, 1)
        elif unit.owner_id == "2":
            self.team_color = Point4(0.106, 0.467, 0.878, 1)
        else:
            self.team_color = Point4(0, 1, 0, 1)
            
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

        if unit.type=="terminator":
            t = loader.loadTexture("terminator2.tga")#@UndefinedVariable
            self.model.setTexture(t, 1)

    def load(self, unit_type):
        if unit_type == 'terminator':
            model = Actor('terminator', {'run': 'terminator-run'
                                        ,'idle01': 'terminator-run'
                                        })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 1
        elif unit_type == 'marine_b':
            model = Actor('marine_b',   {'run': 'marine-run'
                                        ,'idle01': 'marine-fire'
                                        })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 1
        elif unit_type == 'commissar':
            model = Actor('commissar', {'run': 'commissar-run'
                                       ,'idle01': 'commissar-idle1'
                                       ,'idle02': 'commissar-idle2'
                                       ,'idle03': 'commissar-idle3'
                                       ,'fire': 'commissar-fire'
                                       })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 3
        elif unit_type == 'assault':
            model = Actor('assault', {'run': 'assault-run1'
                                       ,'run02': 'assault-run2'
                                       ,'idle01': 'assault-idle1'
                                       ,'idle02': 'assault-idle2'
                                       })
            self.anim_count_dict['run'] = 2
            self.anim_count_dict['idle'] = 2    
        elif unit_type == 'librarian':
            model = Actor('librarian', {'run': 'librarian-run1'
                                       ,'idle01': 'librarian-idle1'
                                       })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 1       
        elif unit_type == 'daemon_prince':
            model = Actor('daemon_prince', {'run': 'daemon_prince-run1'
                                       ,'idle01': 'daemon_prince-idle1'
                                       ,'idle02': 'daemon_prince-idle2'            
                                       })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 2      
        elif unit_type == 'terminator2':
            model = Actor('terminator2', {'run': 'terminator2-run'
                                        ,'idle01': 'terminator2-idle'
                                        ,'fire': 'terminator2-fire'
                                        })
            self.anim_count_dict['run'] = 1
            self.anim_count_dict['idle'] = 1   
            body = model.find("**/body")
            myTexture = loader.loadTexture("term_armour_com_dif.tga")
            body.setTexture(myTexture)
            h = model.find("**/head")
            myTexture = loader.loadTexture("terminator_head_dif.tga")
            h.setTexture(myTexture)      
            b = model.find("**/bolter")
            myTexture = loader.loadTexture("storm_bolter_dif.tga")
            b.setTexture(myTexture)   
            f = model.find("**/powerfist")
            myTexture = loader.loadTexture("terminator_powerfist_dif.tga")
            f.setTexture(myTexture)           
                                           
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
        x = int(self.unit.pos.getX())
        y = int(self.unit.pos.getY())        
        
        if heading == Unit.HEADING_NW:
            o = Point2(x-1, y+1)
        elif heading == Unit.HEADING_N:
            o = Point2(x, y+1)
        elif heading == Unit.HEADING_NE:
            o = Point2(x+1, y+1)
        elif heading == Unit.HEADING_W:
            o = Point2(x-1, y)
        elif heading == Unit.HEADING_E:
            o = Point2(x+1, y)
        elif heading == Unit.HEADING_SW:
            o = Point2(x-1, y-1)
        elif heading == Unit.HEADING_S:
            o = Point2(x, y-1)
        elif heading == Unit.HEADING_SE:
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
    