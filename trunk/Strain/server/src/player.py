from server_messaging import *
import datetime
import cPickle as pickle

class Player:
    
    def __init__ (self, in_id , name, team):
        self.id = in_id
        self.name = name 
        self.team = team
        self.units = []
        self.visible_enemies = []
        self.detected_enemies = []
        self.connection = None
        self.msg_lst = []
        self.defeated = False
        pass


    def addMoveMsg(self, unit_id, move_actions):
        if self.connection:
            EngMsg.move( unit_id, move_actions, self.connection )
        else:
            self.msg_lst.append( (MOVE, (unit_id, move_actions)) )
            
            
    def addShootMsg(self, shoot_actions):
        if self.connection:
            EngMsg.shootMsg( shoot_actions, self.connection )
        else:
            self.msg_lst.append( (SHOOT, shoot_actions) )
            
            
    def addUnitMsg(self, pickled_unit):
        if self.connection:
            EngMsg.sendUnit( pickled_unit, self.connection )
        else:
            self.msg_lst.append( (UNIT, pickled_unit) )


    def addNewTurnMsg(self, data):
        if self.connection:
            EngMsg.sendNewTurn( data, self.connection )
        else:
            self.msg_lst.append( (NEW_TURN, data) )
            

    def addEngineStateMsg(self, state ):
        if self.connection:
            EngMsg.sendNewTurn( state, self.connection )
        else:
            self.msg_lst.append( (ENGINE_STATE, state) )
            

    def addMsg(self, msg ):
        if self.connection:
            EngMsg.sendMsg( msg, self.connection )
        else:
            self.msg_lst.append( msg )


    def addErrorMsg(self, msg ):
        if self.connection:
            EngMsg.error( msg, self.connection )
        else:
            self.msg_lst.append( (ERROR, msg) )


    def addChatMsg(self, msg, sender):
        if self.connection:
            EngMsg.chat( msg, sender, self.connection )
        else:
            self.msg_lst.append( (CHAT, msg, sender) )
        

    def saveMsgs(self):
        fname = util.getReplayName()
        print "saving replay to:", fname
        f = open( util.getReplayName(), 'w')
        print self.msg_lst
        pickle.dump( self.msg_lst, f )
                    
        f.close()
            
    

