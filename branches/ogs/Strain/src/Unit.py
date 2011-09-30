from pandac.PandaModules import Point2, Point3, NodePath, Vec3
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

         

     
       
        
