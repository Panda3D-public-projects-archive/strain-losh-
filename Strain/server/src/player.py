
class Player:
    
    def __init__(self, in_id, name, team):
        self.id = in_id
        self.name = name 
        self.team = team
        self.unitlist = []
        self.list_visible_enemies = []
        self.connection = None
        pass
