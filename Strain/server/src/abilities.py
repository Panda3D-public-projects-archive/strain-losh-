'''
Created on 13 Oct 2012

@author: krav
'''

ABILITY_TYPE_SELF_BUFF      = 1
"""
ABILITY_TYPE_TARGET_ALLY    = 2
ABILITY_TYPE_TARGET_ENEMY   = 3
ABILITY_TYPE_ALLY_IN_FRONT  = 4
ABILITY_TYPE_TARGET_TILE    = 5
"""

class AbilityInterface():
    
    def __init__(self, unit):
        self.owner = unit
        self.id = -1
        self.name = "Undefined ability"
        self.passive = True
        self.cooldown = 0
        self.text = "Ability description goes here, if you see this text, send an email to vjekoslav.znidarsic@gmail.com and ask him about biskviten."
        self.type = -1
        
        
#--------------------------------------------------------
class Morale( AbilityInterface ):
    
    def __init__(self, unit):
        self.owner = unit
        self.id = 1
        self.name = "Morale"
        self.passive = True
        self.cooldown = 0
        
        self.range = 3
        
        self.text = "Unit gives a morale boost. All units within " + self.range + " tiles at the end of turn receive +1 AP next turn."
    








