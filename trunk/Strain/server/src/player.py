from server_messaging import *
import datetime
import cPickle as pickle

class Player:
    
    def __init__ (self, in_id , name, team, parent):
        self.parent = parent
        self.id = in_id
        self.name = name 
        self.team = team
        self.units = []
        self.visible_enemies = []
        self.detected_enemies = []
        self.defeated = False
        self.deployed = False

