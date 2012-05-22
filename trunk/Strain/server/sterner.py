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
    
            #if there are msgs, save them, delete them and release lock
            msgs = self.msg_dict[id]
            del self.msg_dict[id]
            
        finally:
            self.lock.release()

        return msgs

    
    
    def putSingleMsg(self, id, msg):
    
        #try to acquire lock
        if not self.lock.acquire( False ):
            return None
            
        try:            
            #if there are no msgs for this id create new list
            if id not in self.msg_dict:
                self.msg_dict[id] = [msg]
            else:
                #if there are msgs, append these msg
                self.msg_dict[id].append( msg )
            
        finally:
            self.lock.release()

   
    
    
class Sterner:
    
    
    def __init__(self):
        self.notify = Notify( 'Sterner.log' )
        
        self.network = Network( self, self.notify )
        self.network.startServer()
        
        #LockedDict for distributing messages from network to Engine threads
        self.from_network = LockedDict()
        
        #dict to save logged in players 
        # K: player_id , V: panda connection
        self.logged_in_players = {}
        
        
        
        self.notify.info( "Sterner started." )
        print "Sterner started."
        
        pass
    
    
    
    def start( self ):
        
        t = time.time()
        #-----------------main loop------------------
        while True:
        
            self.network.handleConnections()
        
            #get msg from network
            msg = self.network.readMsg()
            if msg:
                print msg
                self.handleMsg( msg )
            
            
            time.sleep(0.1) 
        
            #print self.logged_in_players
            
            if time.time() - t > 20:
                break
        #-----------------main loop------------------
        
        
        self.network.stopServer()
        
        pass
        
    
    
    def handleMsg(self, message):
        #if this is msg for Sterner, handle it
        msg = message[0]
        source = message[1]
        print source.getAddress()
        
        if msg[0] == STERNER_ID:            
            
            if msg[1] == STERNER_LOGIN:
                print "user:", msg[2]
                print "pass:", msg[3]
                
                if msg[2] == '':
                    player_id = 101
                else:
                    player_id = 102
                    
                    
                #check if this player already logged in, if so disconnect him
                if player_id in self.logged_in_players:
                    self.network.disconnect(self.logged_in_players[player_id])

                #remember this new player, if this player had some previous connection, in logged_in_players, this will overwrite it                
                self.logged_in_players[ player_id ] = source
                
                #send LOGIN_SUCCESS to client
                self.network.sendMsg( LOGIN_SUCCESS, source)
                
                
                
            return
        

            
        #otherwise delegate msg to some engine thread
        #self.from_network.putSingleMsg(msg[0], msg[1])
            
        
        
        
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
