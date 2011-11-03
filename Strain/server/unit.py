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
        
           
        if self.type == 'marine_common':
            self.default_AP = 5
            self.default_HP = 5
            self.soundtype = '02'
        elif self.type == 'marine_epic':
            self.default_AP = 6
            self.default_HP = 6
            self.soundtype = '01'
        elif self.type == 'commissar':
            self.default_AP = 5
            self.default_HP = 5
            self.soundtype = '01'                                                   

        self.pos = ( x, y )
        self.current_AP = self.default_AP
        self.health = self.default_HP
        
