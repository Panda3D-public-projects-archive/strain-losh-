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
        self.connection = None
        self.msg_lst = []
        self.defeated = False
        self.deployed = False
        pass


    def addMoveMsg(self, unit_id, move_actions):
        if self.connection:
            self.parent.move( unit_id, move_actions, self.connection )
        else:
            self.msg_lst.append( (MOVE, (unit_id, move_actions)) )
            
            
    def addShootMsg(self, shoot_actions):
        if self.connection:
            self.parent.shootMsg( shoot_actions, self.connection )
        else:
            self.msg_lst.append( (SHOOT, shoot_actions) )
            
            
    def addUnitMsg(self, pickled_unit):
        if self.connection:
            self.parent.sendUnit( pickled_unit, self.connection )
        else:
            self.msg_lst.append( (UNIT, pickled_unit) )


    def addUseMsg(self, unit_id):
        if self.connection:
            self.parent.sendUse( unit_id, self.connection )
        else:
            self.msg_lst.append( (UNIT, unit_id) )


    def addTauntMsg(self, unit_id, actions):
        if self.connection:
            self.parent.sendTaunt( unit_id, actions, self.connection )
        else:
            self.msg_lst.append( (TAUNT, (unit_id, actions)) )


    def addNewTurnMsg(self, data):
        #if self.connection:
        self.parent.sendNewTurn( data, self.id )
        #else:
        #    self.msg_lst.append( (NEW_TURN, data) )
            

    def addEngineStateMsg(self, state ):
        #if self.connection:
        self.parent.sendState( state, self.id )
        #else:
        #    self.msg_lst.append( (ENGINE_STATE, state) )
            

    def addLevelMsg(self, compiled_level ):
        if self.connection:
            self.parent.sendLevel( compiled_level, self.connection )
        else:
            self.msg_lst.append( (LEVEL, compiled_level) )
            

    def addMsg(self, msg ):
        if self.connection:
            self.parent.sendMsg( msg, self.connection )
        else:
            self.msg_lst.append( msg )


    def addErrorMsg(self, msg ):
        if self.connection:
            self.parent.error( msg, self.connection )
        else:
            self.msg_lst.append( (ERROR, msg) )


    def addChatMsg(self, msg, sender):
        if self.connection:
            self.parent.chat( msg, sender, self.connection )
        else:
            self.msg_lst.append( (CHAT, msg, sender) )
        

    def saveMsgs(self):
        fname = util.getReplayName()
        print "saving replay to:", fname
        f = open( util.getReplayName(), 'w')
        print self.msg_lst
        pickle.dump( self.msg_lst, f )
                    
        f.close()
            
    

