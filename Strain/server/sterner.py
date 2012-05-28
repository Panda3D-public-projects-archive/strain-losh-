'''
Created on 16 May 2012

@author: krav
'''
import engine
import threading
import sys
import time
from server_messaging import *
from util import *
from engine import EngineThread



class LockedDict:
    
    def __init__(self):
        self.lock = threading.Lock()
        
        self.msg_dict = {}
        
        

    def getMyMsgs(self, id ):

        msgs = []

        #try to acquire lock
        if not self.lock.acquire( False ):
            return None
            
        try:            
            #if there are no msgs for us return
            if id not in self.msg_dict:
                return
    
            #if there are msgs, save them, delete them from dict and release lock
            msgs = self.msg_dict[id]
            del self.msg_dict[id]
            
        finally:
            self.lock.release()

        return ( msgs, id )

    
    
    def putMsgList(self, id, msg):
        #try to acquire lock
        if not self.lock.acquire( False ):
            return None
            
        try:            
            #if there are no msgs for this id create new list
            if id not in self.msg_dict:
                self.msg_dict[id] = msg
            else:
                #if there are msgs, append these msg
                self.msg_dict[id].extend( msg )
        finally:
            self.lock.release()



    def getAllMsgsDict(self):
        all_msgs = {}
        
        #try to acquire lock
        if not self.lock.acquire( False ):
            return None
        try:            
            all_msgs = self.msg_dict
            self.msg_dict = {}
        finally:
            self.lock.release()
    
        return all_msgs
    

    
class Sterner:
    
    
    def __init__(self):
        self.notify = Notify( 'Sterner.log' )
        
        self.network = Network( self, self.notify )
        self.network.startServer()
        
        #LockedDict for distributing messages from network to Engine threads
        self.from_network = LockedDict()
        #LockedDict for sending msgs to network
        self.to_network = LockedDict()
        
        #dict to save logged in players 
        # K: player_id , V: panda connection
        self.logged_in_players = {}
        
        self.test_thread = EngineThread( TEST_GAME_ID, self.from_network, self.to_network, self.notify )
        self.test_thread.start()
        
        self.notify.info( "Sterner started." )
        
        
    
    
    
    def start( self ):
        
        t = time.time()
        #-----------------main loop------------------
        while True:
        
            self.network.handleConnections()
        
            #get msg from network
            tmp_msg = self.network.readMsg()
            if tmp_msg:
                
                print "sterner dobio:",tmp_msg
                msg, source = tmp_msg
                
                #chek if this messge is for sterner or not
                if msg[0] == STERNER_ID:
                    self.handleSternerMsg( msg, source )
                else:
                    self.from_network.putMsgList( msg[0], msg[1:] )
            
            
            #put msgs on network            
            all_msgs = self.to_network.getAllMsgsDict()
            if all_msgs:
                for player_id in all_msgs:
                    for msg in all_msgs[player_id]:
                        try:
                            self.network._sendMsg( msg, self.logged_in_players[ int(player_id)] )
                        except:
                            print "trazim: %s... svi: %s" % (player_id, str(self.logged_in_players))

            
            time.sleep(0.1) 
        
            
            if time.time() - t > 25000:
                self.test_thread.stop = True
                break
        #-----------------main loop------------------
        
        
        self.network.stopServer()
        

        pass
        
    
    
    def getIdFromConnection(self, connection):
        for player in self.logged_in_players:
            if self.logged_in_players[player] == connection:
                return player
        return None
    
    
    
    def handleSternerMsg(self, message, source):
        
        if message[1] == STERNER_LOGIN:
            print "user:", message[2]
            print "pass:", message[3]
            
            if message[2] == 'Red':
                player_id = 100
            elif message[2] == 'Blue':
                player_id = 101
            else:
                player_id = 202
                
                
            #check if this player already logged in, if so disconnect him
            if player_id in self.logged_in_players:
                self.network.disconnect(self.logged_in_players[player_id])

            #remember this new player, if this player had some previous connection, in logged_in_players, this will overwrite it                
            self.logged_in_players[ player_id ] = source
            
            #send LOGIN_SUCCESS to client
            self.network.sendMsg( (LOGIN_SUCCESS, player_id), source )
            return
                
                

    def playerDisconnected(self, source):
        
        #go through all logged in players
        for pid in self.logged_in_players.keys():
            
            #if we find the one with this connection
            if self.logged_in_players[ pid ] == source:
                
                #remove him from the dict
                del self.logged_in_players[ pid ]
                
                #TODO: 0: remove all his messages from network queues
                return

    

########################################################################################################
########################################################################################################
if __name__ == "__main__":
    sterner = Sterner()

    sterner.start()
