'''
Created on 13 Oct 2012

@author: krav
'''

ACTION_NEW_TURN     = 1
ACTION_TURN_END     = 2
ACTION_SHOOT_BEGIN  = 3
ACTION_SHOOT_OVER   = 4


class BuffInterface():
    
    def action(self, action, var, events ):
        pass
    
    
    
#--------------------------------------------------------
class PrecisionShot(BuffInterface):
    
    def __init__(self, unit):
        self.owner = unit
        #10%
        self.modifier = 0.1
    
    def action(self, action, var, events ):
    
        if action == ACTION_SHOOT_BEGIN:
            var[0] += self.modifier

        elif action == ACTION_SHOOT_OVER:
            self.owner.buffs.remove( self ) 
    
        elif action == ACTION_TURN_END:
            self.owner.buffs.remove( self )
            
    
    
#--------------------------------------------------------
class Morale(BuffInterface):
    
    def __init__(self, unit):
        self.owner = unit
        #+1 to ap on beginning of turn
        self.modifier = 1
    
    def action(self, action, var, events ):
    
        if action == ACTION_NEW_TURN:
            self.owner.ap += self.modifier
            
        elif action == ACTION_TURN_END:
            self.owner.buffs.remove( self )
    
    
#--------------------------------------------------------
class Bleed(BuffInterface):
    
    def __init__(self, unit, current_turn, bleed_damage, duration):
        #-1 hp on end of turn
        self.owner = unit
        self.turn_start = current_turn
        self.duration = duration
        #amount of dmg
        self.str = bleed_damage
        #ignores armor
        self.power = True
    
    def action(self, action, var, events ):
    
        if action == ACTION_TURN_END:
            events.append( self.owner.iAmHit( self ) )
            if var == self.turn_start + self.duration:
                self.owner.buffs.remove( self )

    
    
    
    
    