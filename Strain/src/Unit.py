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
        
    def get_sound(self, action):
        if action == 'select':
            s = randint(1, 4)
            return base.sound_manager.sounds['select'+self.soundtype+'0'+str(s)]
        elif action == 'movend':
            s = randint(1, 3)
            return base.sound_manager.sounds['movend'+self.soundtype+'0'+str(s)]
                
    def talk(self, action):
        self.get_sound(action).play()
        