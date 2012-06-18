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
        self.msg_lst = []
        self.defeated = False
        self.deployed = False



    def _doMsg(self, msg):
        self.parent.to_network.append( (self.id, msg) )        



    def addMoveMsg(self, unit_id, move_actions):
        self._doMsg( (MOVE, (unit_id, move_actions)) )
            
            
    def addShootMsg(self, shoot_actions):
        self._doMsg( (SHOOT, shoot_actions) )
            
            
    def addUnitMsg(self, pickled_unit):
        self._doMsg( (UNIT, pickled_unit) )


    def addUseMsg(self, unit_id):
        self._doMsg( (USE, unit_id) )


    def addTauntMsg(self, unit_id, actions):
        self._doMsg( (TAUNT, (unit_id, actions)) )


    def addNewTurnMsg(self, data):
        self._doMsg( (NEW_TURN, data) )
            

    def addEngineStateMsg(self, state ):
        self._doMsg( (ENGINE_STATE, state) )
            

    def addLevelMsg(self, compiled_level ):
        self._doMsg( (LEVEL, compiled_level) )
            

    def addMsg(self, msg ):
        self._doMsg( msg )


    def addErrorMsg(self, msg ):
        self._doMsg( (ERROR, msg) )


    def addChatMsg(self, msg, sender):
        self._doMsg( (CHAT, msg, sender) )
        

    def saveMsgs(self):
        fname = util.getReplayName()
        print "saving replay to:", fname
        f = open( util.getReplayName(), 'w')
        print self.msg_lst
        pickle.dump( self.msg_lst, f )
                    
        f.close()
            
    

