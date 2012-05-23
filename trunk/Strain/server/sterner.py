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
        
        self.test_thread = EngineThread( 100, self.from_network, self.to_network )
        self.test_thread.start()
        
        self.notify.info( "Sterner started." )
        print "Sterner started."
        
        pass
    
    
    
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
                    self.handleMsg( msg, source )
                else:
                    self.from_network.putMsgList( self.getIdFromConnection(source), msg )
            
            
            #put msgs on network            
            all_msgs = self.to_network.getAllMsgsDict()
            if all_msgs:
                for player_id in all_msgs:
                    for msg in all_msgs[player_id]:
                        #print "trazim: %s... svi: %s" % (player_id, str(self.logged_in_players))
                        try:
                            self.network._sendMsg( msg, self.logged_in_players[ int(player_id)] )
                        except:
                            print "ex"
                            pass

            
            time.sleep(0.1) 
        
            #print self.logged_in_players
            
            if time.time() - t > 2:
                break
        #-----------------main loop------------------
        
        
        self.network.stopServer()
        

        pass
        
    
    def getIdFromConnection(self, connection):
        for player in self.logged_in_players:
            if self.logged_in_players[player] == connection:
                return player
        return None
    
    
    def handleMsg(self, message, source):
        #if this is msg for Sterner, handle it
        msg = message
        
        print source.getAddress()
        
            
        
        if msg[1] == STERNER_LOGIN:
            print "user:", msg[2]
            print "pass:", msg[3]
            
            if msg[2] == '':
                player_id = 100
            else:
                player_id = 101
                
                
            #check if this player already logged in, if so disconnect him
            if player_id in self.logged_in_players:
                self.network.disconnect(self.logged_in_players[player_id])

            #remember this new player, if this player had some previous connection, in logged_in_players, this will overwrite it                
            self.logged_in_players[ player_id ] = source
            
            #send LOGIN_SUCCESS to client
            self.network.sendMsg( LOGIN_SUCCESS, source )
            
                
                
        return
        

            
        #otherwise delegate msg to some engine thread
        #self.from_network.putMsgList(msg[0], msg[1])
            
        
        
        
        pass


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
