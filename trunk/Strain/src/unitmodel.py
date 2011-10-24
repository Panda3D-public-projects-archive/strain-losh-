from direct.actor.Actor import Actor
from panda3d.core import Point4, Point3, Point2, NodePath#@UnresolvedImport
import random
from unit import Unit

#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, unit, scale=0.25, h=180, pos=None):
        self.anim_count_dict = {}
        self.model = self.load(unit.type)
        self.id = str(unit.id)
        self.unit = unit
        
        # Bake in rotation transform because model is created facing towards screen (h=180)
        self.model.setScale(scale)
        self.model.setH(h)
        self.model.flattenLight() 
        
        x = int(unit.pos.getX())
        y = int(unit.pos.getY())
        
        if pos:
            self.model.setPos(pos)
        else:
            self.model.setPos(self.calcWorldPos(x, y))

        self.model.setLightOff()
        self.model.setTag("type", "unit")
        self.model.setTag("id", str(self.id))
        
        #TODO: ogs: ovo sam ti promijenio jer vise nema owner, nego owner_id (ak je owner bio unutra, pickle bi zapicklao i cijeli player objekt unutra
        self.model.setTag("player_id", str(unit.owner_id))
        
        #TODO: ogs: ovo sam ti zakomentirao
        #self.model.setTag("player_name", str(unit.owner.name))
        
        #TODO: ogs: ovo sam ti promijenio da koristi privremeno owner_id ionak imamo sam 2 plejer zasad
        self.model.setTag("team", str(unit.owner_id))       

        self.node = NodePath(self.id)
        self.dummy_node = NodePath("dummy_"+self.id)
        self.dest_node = NodePath("dest_"+self.id)
        
        #TODO: ogs: ovo sam ti promijenio ad isto koristi owner_id
        if unit.owner_id == "1":
            self.team_color = Point4(1, 0, 0, 0)
        elif unit.owner_id == "2":
            self.team_color = Point4(0, 0, 1, 0)

        if self.unit.heading == Unit.HEADING_NW:
            o = Point2(x-1, y+1)
        elif self.unit.heading == Unit.HEADING_N:
            o = Point2(x, y+1)
        elif self.unit.heading == Unit.HEADING_NE:
            o = Point2(x+1, y+1)
        elif self.unit.heading == Unit.HEADING_W:
            o = Point2(x-1, y)
        elif self.unit.heading == Unit.HEADING_E:
            o = Point2(x+1, y)
        elif self.unit.heading == Unit.HEADING_SW:
            o = Point2(x-1, y-1)
        elif self.unit.heading == Unit.HEADING_S:
            o = Point2(x, y-1)
        elif self.unit.heading == Unit.HEADING_SE:
            o = Point2(x+1, y-1)
        
        self.dest_node.setPos(o.getX()+0.5, o.getY()+0.5, 0.3)
        self.model.lookAt(self.dest_node)
        
        self.model.reparentTo(self.node)
        self.dummy_node.reparentTo(self.node)
        self.dest_node.reparentTo(self.node)
        
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
        
    def play(self, anim):
        self.model.play(anim)
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()
    
