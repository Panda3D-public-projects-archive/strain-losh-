
class Player:
    
    def __init__ (self, in_id , name, team):
        self.id = in_id
        self.name = name 
        self.team = team
        self.units = []
        self.visible_enemies = []
        self.detected_enemies = []
        self.connection = None
        pass

