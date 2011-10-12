from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, SoundInterval
from panda3d.core import Point4, Point3, NodePath

#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, unit, player=None, scale=0.25, h=180, pos=None):
        self.model = self.load(unit.type)
        self.id = str(unit.id)
        if pos:
            self.model.setPos(pos)
        else:
            self.model.setPos(self.calcWorldPos(unit.x, unit.y))
        self.model.setLightOff()
        self.model.setTag("type", "unit")
        self.model.setTag("id", self.id)
        if player:
            self.model.setTag("player", str(player.id))
            self.model.setTag("team", player.team)
        
        self.model.setScale(scale)
        # Bake in rotation transform because model is created facing towards screen (h=180)
        self.model.setH(h)
        self.model.flattenLight()        

        self.node = NodePath(self.id)
        self.dummy_node = NodePath("dummy_"+self.id)
        self.dest_node = NodePath("dest_"+self.id)
        if player:
            if player.team == "1":
                self.team_color = Point4(1, 0, 0, 0)
            elif player.team == "2":
                self.team_color = Point4(0, 0, 1, 0)
        
        self.model.reparentTo(self.node)
        self.dummy_node.reparentTo(self.node)
        self.dest_node.reparentTo(self.node)

    def load(self, type):
        if type == 'terminator':
            model = Actor('terminator', {'run': 'terminator-run'
                                        ,'idle02': 'terminator-run'
                                        })
        elif type == 'marine_b':
            model = Actor('marine_b',   {'run': 'marine-run'
                                        ,'idle02': 'marine-fire'
                                        })
        elif type == 'commissar':
            model = Actor('commissar', {'run': 'commissar-run'
                                       ,'idle01': 'commissar-idle1'
                                       ,'idle02': 'commissar-idle2'
                                       ,'idle03': 'commissar-idle3'
                                       ,'fire': 'commissar-fire'
                                       })
        return model
    
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
    
    def createMoveAnimation(self, tile_list, dest):
        intervals = []
        movement = []
        seq = Sequence()
        dur = 0
        end = None
        for n in tile_list:
            if n[0] == dest:
                end = n
                break
        while end:
            endpos = base.calc_unit_pos(Point3(end[0].x, end[0].y, 0))
            parent = end[1]
            if parent is None:
                break
            else:
                startpos = base.calc_unit_pos(Point3(parent[0].x, parent[0].y, 0))
                tupple = (startpos, endpos)
                movement.append(tupple)             
            end = end[1]
        movement.reverse()
        h = self.model.getH()
        for m in movement:
            self.dummy_node.setPos(m[0].x, m[0].y, 0)
            self.dest_node.setPos(m[1].x, m[1].y, 0)
            self.dummy_node.lookAt(self.dest_node)
            endh = self.dummy_node.getH()
            if endh != h:
                i = self.model.quatInterval(0.2, hpr = Vec3(endh, 0, 0), startHpr = Vec3(h, 0, 0))
                intervals.append(i)
                h = endh
                dur = dur + 0.2
            i = self.model.posInterval(0.5, m[1], m[0])
            dur = dur + 0.5
            intervals.append(i)
        for i in intervals:
            seq.append(i)
        anim = ActorInterval(self.model, 'run', loop = 1, duration = dur)
        s = SoundInterval(self.get_sound('movend'))
        move = Sequence(Parallel(anim, seq), s)
        move.start()
