from pandac.PandaModules import Point2, Point3, NodePath, Vec3
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, SoundInterval
from random import randint

class Unit():
    
    def __init__(self, id, owner, type, x, y ):
        self.id = id
        self.owner = owner
        self.type = type
        self.x = int(x)
        self.y = int(y)
           
        if self.type == 'terminator':
            self.default_AP = 8
            self.soundtype = '02'
        elif self.type == 'marine_b':
            self.default_AP = 5
            self.soundtype = '01'
        elif self.type == 'commissar':
            self.default_AP = 5
            self.soundtype = '01'            

        self.pos = Point2( self.x, self.y )
        self.current_AP = self.default_AP
        self.health = 10
        self.move_tiles = []
        self.open_tile_list = []
        self.closed_tile_list = []
        
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
        base.level.node_data[int(self.pos.x)][int(self.pos.y)] = None
        base.level.node_data[int(dest.x)][int(dest.y)] = self
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
        #self.calc_los()
        while self.open_tile_list:
            n = self.open_tile_list[0]
            ignore = False
            for c in self.closed_tile_list:
                if n == c:
                    ignore = True
                    break
            if base.level.game_data[int(n[0].x)][int(n[0].y)] and (int(n[0].x) != self.x and int(n[0].y) != self.pos.y):
                self.open_tile_list.remove(n)
                ignore = True
                break
            if ignore != True:
                self.closed_tile_list.append(n)
                self.open_tile_list.remove(n)
                if n[2] < self.current_AP:
                    #add adjacent nodes to the open list
                    x = n[0].x - 1
                    y = n[0].y
                    if x >= 0 and x < base.level.maxX and y >= 0 and y < base.level.maxY:
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
                    if x >= 0 and x < base.level.maxX and y >= 0 and y < base.level.maxY:
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
                    if x >= 0 and x < base.level.maxX and y >= 0 and y < base.level.maxY:
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
                    if x >= 0 and x < base.level.maxX and y >= 0 and y < base.level.maxY:
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

         

    def calc_los(self):
        #look at tiles adjacent to the unit, if there is a partial cover among them, treat it as a normal visible tile
        myX = int( self.pos.x )
        myY = int( self.pos.y )
        
        #list_passed_tiles = zeros( base.level.maxX, base.level.maxY )
        list_passed_tiles = []         
        list_visible_tiles = []
        
        #fill list_passed_tiles with zeros
        for i in range(0, base.level.maxX ):
            a = []
            for j in range(0, base.level.maxY ):
                a.append(0)
            list_passed_tiles.append(a) 
        
        
        
        
        for i in range( -1, 2 ):
            for j in range( -1, 2 ):
                curX = myX + i
                curY = myY + j
                
                #ignore my own tile
                if( i == 0 and j == 0 ):
                    continue
                                
                #level bounds
                if (curX < 0) or (curY < 0) or curX > base.level.maxX-1 or curY > base.level.maxY-1:
                    continue
                
                if( list_passed_tiles[curX][curY] == 1 ):
                    continue                    
                
                curValue = base.level._level_data[curX][curY]
                
                #it is too tall for us to see over
                if( curValue > 1 ):
                    continue
                
                #else add it into a visible list
                list_visible_tiles.append( (curX, curY))
                list_passed_tiles[curX][curY] = 1
                
                #print i,j
        

        print list_passed_tiles
        print list_visible_tiles
        pass
        
       
        
