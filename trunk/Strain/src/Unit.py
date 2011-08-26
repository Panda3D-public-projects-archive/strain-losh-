from pandac.PandaModules import Point2, Point3, NodePath, Vec3
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, SoundInterval
from random import randint
#test
class Unit():
    def __init__(self, name, type, team, x, y, parent_node):
        if type == 'terminator':
            self.model = Actor('terminator', {'run': 'terminator-run', 'selected': 'terminator-run'})
            self.model.setScale(0.25)
            # bake in rotation transform because model is created facing towards screen
            self.model.setH(180) 
            self.model.flattenLight()
            self.default_AP = 15
            self.soundtype = '02'
        elif type == 'marine_b':
            self.model = Actor('marine_b', {'run': 'marine-run', 'selected': 'marine-fire'})
            #self.model.setPlayRate(1, 'run')
            self.model.setScale(0.25)
            # bake in rotation transform because model is created facing towards screen
            self.model.setH(180) 
            self.model.flattenLight()
            self.default_AP = 5
            self.soundtype = '01'      
        elif type == 'marine_hb':
            self.model = Actor('marine_hb', {'run': 'marine-run', 'selected': 'marine-fire'})
            #self.model.setPlayRate(1, 'run')
            self.model.setScale(0.25)
            # bake in rotation transform because model is created facing towards screen
            self.model.setH(180) 
            self.model.flattenLight()
            self.default_AP = 5
            self.soundtype = '01' 
        elif type == 'scout':
            self.model = Actor('scout', {'run': 'scout-walk', 'selected': 'scout-walk'})
            #self.model.setPlayRate(1, 'run')
            self.model.setScale(0.25)
            # bake in rotation transform because model is created facing towards screen
            self.model.setH(180) 
            self.model.flattenLight()
            self.default_AP = 5
            self.soundtype = '01'
        elif type == 'khorne':
            self.model = Actor('khorne', {'run': 'khorne-run', 'selected': 'khorne-run'})
            #self.model.setPlayRate(1, 'run')
            self.model.setScale(0.25)
            # bake in rotation transform because model is created facing towards screen
            self.model.setH(180) 
            self.model.flattenLight()
            self.defAP = 5
            self.soundtype = '01'	

        self.pos = Point2(x, y)
        self.team = team
        self.h = self.model.getH()
        self.current_AP = self.default_AP
        self.move_tiles = []
        self.open_tile_list = []
        self.closed_tile_list = []
        self.unit_node = NodePath('unit')
        self.model.reparentTo(self.unit_node)
        self.unit_node.reparentTo(parent_node)
        self.dummy_node = NodePath('dummy')
        self.dummy_node.reparentTo(parent_node)
        self.dest_node = NodePath('dest')
        self.dest_node.reparentTo(parent_node)
        self.name = name
        self.model.setPos(base.calc_unit_pos(self.pos))
        self.model.setTag('Unit', 'true')
        self.model.setTag('Name', name)
        
    def show(self):
        self.model.reparentTo(parent_node)
        
    def hide(self):
        self.model.reparentTo(hidden)
        
    def get_sound(self, action):
        if action == 'select':
            s = randint(1, 4)
            return base.sound_manager.sounds['select'+self.soundtype+'0'+str(s)]
        elif action == 'movend':
            s = randint(1, 3)
            return base.sound_manager.sounds['movend'+self.soundtype+'0'+str(s)]
                
    def talk(self, action):
        self.get_sound(action).play()
        
    def move(self, dest):
        intervals = []
        movement = []
        seq = Sequence()
        dur = 0
        end = None
        for n in self.closed_tile_list:
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
        #seq.start()
        s = SoundInterval(self.get_sound('movend'))
        move = Sequence(Parallel(anim, seq), s)
        move.start()
        self.pos = dest
        #self.currAP = self.currAP - n[2]
        
    def clear_open_list(self):
        del self.open_tile_list[0:]
        
    def clear_closed_list(self):
        del self.closed_tile_list[0:]
        
    def find_path(self):
        #add first node to open list
        self.clear_closed_list()
        self.clear_open_list()
        self.pos = base.calc_world_pos(self.model.getPos())
        start = (self.pos, None, 0)
        self.open_tile_list.append(start)
        self.calc_move_nodes()
        
    def calc_move_nodes(self):
        while self.open_tile_list:
            n = self.open_tile_list[0]
            ignore = False
            for c in self.closed_tile_list:
                if n == c:
                    ignore = True
                    break
            for u in base.units.itervalues():
                if u.model.getTag('Name') != self.name:
                    if u.pos == n[0]:
                        self.open_tile_list.remove(n)
                        ignore = True
                        break
            if ignore != True:
                self.closed_tile_list.append(n)
                self.open_tile_list.remove(n)
                if n[2] < self.current_AP:
                    #add adjacent nodes to the open list
                    x = n[0].x - base.tile_size
                    y = n[0].y
                    if x >= 0 and x < base.level.x and y >= 0 and y < base.level.y:
                        posleft = Point2(x, y)
                        new = (posleft, n, n[2]+1)
                        ignore = False
                        for i in self.open_tile_list:
                            if i[0] == new[0]:
                                if i[2] > new[2]:
                                    self.open_tile_list[self.open_tile_list.index(i)] = new[2]
                                ignore = True
                                break
                        if ignore != True:
                            self.open_tile_list.append(new)
                    x = n[0].x + 1
                    y = n[0].y
                    if x >= 0 and x < base.level.x and y >= 0 and y < base.level.y:
                        posright = Point2(x, y)
                        new = (posright, n, n[2]+1)
                        ignore = False
                        for i in self.open_tile_list:
                            if i[0] == new[0]:
                                if i[2] > new[2]:
                                    self.open_tile_list[self.open_tile_list.index(i)] = new[2]
                                ignore = True
                                break
                        if ignore != True:
                            self.open_tile_list.append(new)
                    x = n[0].x
                    y = n[0].y + 1
                    if x >= 0 and x < base.level.x and y >= 0 and y < base.level.y:
                        posup = Point2(x, y)
                        new = (posup, n, n[2]+1)
                        ignore = False
                        for i in self.open_tile_list:
                            if i[0] == new[0]:
                                if i[2] > new[2]:
                                    self.openList[self.open_tile_list.index(i)] = new[2]                            
                                ignore = True
                                break
                        if ignore != True:
                            self.open_tile_list.append(new)
                    x = n[0].x
                    y = n[0].y - 1
                    if x >= 0 and x < base.level.x and y >= 0 and y < base.level.y:
                        posdown = Point2(x, y)
                        new = (posdown, n, n[2]+1)
                        ignore = False
                        for i in self.open_tile_list:
                            if i[0] == new[0]:
                                if i[2] > new[2]:
                                    self.openList[self.open_tile_list.index(i)] = new[2]                            
                                ignore = True
                                break
                        if ignore != True:
                            self.open_tile_list.append(new)

         
        
        
