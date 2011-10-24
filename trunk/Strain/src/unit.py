from pandac.PandaModules import Point2 #@UnresolvedImport
from random import randint





class Unit():
    
    
    HEADING_NONE      = 0
    HEADING_NW        = 1
    HEADING_N         = 2
    HEADING_NE        = 3
    HEADING_W         = 4
    HEADING_E         = 5
    HEADING_SW        = 6
    HEADING_S         = 7
    HEADING_SE        = 8
    
    
    def __init__(self, in_id, owner_id, in_type, x, y ):
        
        self.id = in_id
        self.owner_id = owner_id
        self.type = in_type
        
        self.heading = Unit.HEADING_N
        self.rotate_cost = 0
        
        self.losh_dict = {}
        
        self.move_dict = {}
        
        self.resting = False
        
           
        if self.type == 'terminator':
            self.default_AP = 8
            self.default_HP = 10
            self.soundtype = '02'
        elif self.type == 'marine_b':
            self.default_AP = 5
            self.default_HP = 9
            self.soundtype = '01'
        elif self.type == 'commissar':
            self.default_AP = 5
            self.default_HP = 8
            self.soundtype = '01'        
        elif self.type == 'assault':
            self.default_AP = 7
            self.default_HP = 5
            self.soundtype = '01'   
        elif self.type == 'librarian':
            self.default_AP = 7
            self.default_HP = 5
            self.soundtype = '01'  
        elif self.type == 'daemon_prince':
            self.default_AP = 15
            self.default_HP = 8
            self.soundtype = '01'                                        

        self.pos = Point2( x, y )
        self.current_AP = self.default_AP
        self.health = self.default_HP
        
    def get_sound(self, action):
        if action == 'select':
            s = randint(1, 4)
            return base.sound_manager.sounds['select'+self.soundtype+'0'+str(s)] #@UndefinedVariable
        elif action == 'movend':
            s = randint(1, 3)
            return base.sound_manager.sounds['movend'+self.soundtype+'0'+str(s)] #@UndefinedVariable
                
    def talk(self, action):
        self.get_sound(action).play()
        
