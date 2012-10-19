'''
Created on 4.10.2011.

@author: krav
'''
from threading import Thread
import collections
from twisted.internet.protocol import Factory 
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import Int16StringReceiver, IntNStringReceiver
from share import * #@UnusedWildImport
import threading
import sys


HANDSHAKE_TIMEOUT = 6 #seconds


#max message size je 65k (0xffff) if we want to send a larger message, we need something else
#a level has cca 7k

def f(s):
    print s, "f-", threading.currentThread().name,"-----"

class Connection(Int16StringReceiver):

    def __init__(self, factory):
        self.factory = factory
        self.logged_in_players = self.factory.logged_in_players
        self.player_id = -1
        self.player_name = None
        self.handshaked = 0
        self.handshake_phase = 0

    def checkHandshakeTimeout(self):
        #if we already disconnected in the meantime just return
        if not self.connected:
            return
        if not self.handshaked:
            print "Handshake timed out with:", self.transport.hostname
            self.transport.abortConnection()
            return
        print "ok"


    def makeConnection(self, transport):
        self.connected = 1
        self.transport = transport
        
        #print "make connection, transport:", transport
        #print "reactor-", threading.currentThread().name
        
        reactor.callLater( HANDSHAKE_TIMEOUT, self.checkHandshakeTimeout) #@UndefinedVariable
        #self.handshaked = 666
        
        #reactor.callInThread(f, "------")
        

    def stringReceived(self, string):
        
        if not self.handshaked:
            self.goThroughHandshake( string )
            return
        #string = zlib.decompress(string)
        #print "string recv:", string
        
    """
    def dataReceived(self, data):
        print "data recv:", data
        return IntNStringReceiver.dataReceived(self, data)
    """

    def goThroughHandshake(self, string):
        
        #================================phase 0=====================================
        if self.handshake_phase == 0:
            if string != "LOSH?":
                self.transport.loseConnection()
            else:
                self.handshake_phase = 1
                self.sendString("LOSH!")
                
        #================================phase 1=====================================
        elif self.handshake_phase == 1:
            if string != "Sterner?":
                self.transport.loseConnection()
            else:
                self.handshake_phase = 2
                self.sendString("Regnix!")


        #================================phase 2=====================================
        elif self.handshake_phase == 2:
            try:
                msg = string.split(':')
                if msg[0] == COMMUNICATION_PROTOCOL_STRING:
                    ver = msg[1]
                    if ver != COMMUNICATION_PROTOCOL_VERSION:
                        self.sendString( "Wrong version! Version needed:" + ver, ", You have:" + msg[1] )
                        raise Exception( "Client with wrong version trying to connect from:" + self.transport.hostname ) 
                else:                    
                    self.sendString("Wrong communication protocol")
                    raise Exception("Wrong communication protocol")
            except:
                self.transport.loseConnection()
                return
            
            #passed phase 2
            self.sendString( HANDSHAKE_SUCCESS )
            self.handshake_phase = 3
                
        #================================phase 3=====================================
        elif self.handshake_phase == 3:
            #check username & pass
            reactor.callInThread(self.checkUsernameAndPass, string) #@UndefinedVariable


    def checkUsernameAndPass(self, string):
        try:
            login_data = string.split(',')
            
            if login_data[0] != STERNER_LOGIN:
                raise Exception("Wrong login message.")
            
            username = login_data[1]
            pswd = login_data[2]
             
            user_data = self.factory.db_api.returnPlayer( username )
            if not user_data or pswd != user_data[3]:
                raise Exception( "Wrong username/password" )
        
        except Exception as e:
            reactor.callFromThread( self.sendStringAndDisconnect, e ) #@UndefinedVariable
            return
        except:
            reactor.callFromThread( self.sendStringAndDisconnect, "Unable to verify username and password" ) #@UndefinedVariable
            return
        
        #username and pass check went ok, return back to reactor thread and call handshakePassed()
        reactor.callFromThread( self.handshakePassed, user_data ) #@UndefinedVariable



    def sendStringAndDisconnect(self, string ):
        self.sendString( str(string) )
        self.transport.loseConnection()


    def handshakePassed(self, my_user_data):
        self.handshaked = 1
        self.player_id = my_user_data[0]
        self.player_name = my_user_data[2]
        print "++++++++player_id", self.player_id
        #if this players was already logged in from another connection, close that connection
        if self.player_id in self.logged_in_players:
            print "----tryiong to disc"
            self.logged_in_players[self.player_id].transport.abortConnection()
            
        #remember this connection 
        self.logged_in_players[self.player_id] = self
        print "Player %s logged in from %s." % (self.player_name, self.transport.hostname )        
        
        #send client success message and his id
        self.sendString( LOGIN_SUCCESS + ":" + str(self.player_id) )
        

    def sendString(self, string):
        #print "sending string:", string        
        return IntNStringReceiver.sendString(self, string)


    def connectionMade(self):
        pass

        
    def connectionLost(self, reason):
        self.connected = 0
        #if this is exactly this connection in logged_in_players delete it
        if self.player_id in self.logged_in_players and self.logged_in_players[self.player_id] == self:
                del self.logged_in_players[self.player_id]
        print "Connection lost, reason:", reason
 


class SternerNetwork(Factory):
    
            
    def __init__(self, sterner, notify, db_api):
        self.sterner = sterner
        self.notify = notify
        self.db_api = db_api
        
        self.reactor_thread = None
        
        self.logged_in_players = {}
        
        #used by handshaking threads to put results in
        self.handshakedConnections = collections.deque()
    
        endpoint = TCP4ServerEndpoint(reactor, TCP_PORT)
        #fact = ChatFactory()
        #endpoint.listen(fact)
        endpoint.listen( self )
    
        #this will hold messages that need to be sent to clients
        self.to_network = collections.deque()
    
        #this will hold messages that were received from network
        self.from_network = collections.deque();
    
        #l = task.LoopingCall(runEverySecond, fact)
        #l.start(1) # call every second
    
    
    def startServer( self ):
        self.reactor_thread = Thread( target=reactor.run, name="TwistedReactorThread",kwargs={'installSignalHandlers':0} )#@UndefinedVariable
        self.reactor_thread.start()
 
        
    
    def stopServer( self ):
        reactor.stop() #@UndefinedVariable
    
        self.handshakedConnections.clear()
        self.to_network.clear()
        self.from_network.clear()
    

    def buildProtocol(self, addr):
        return Connection(self)

    
             
        
    def broadcastMsg( self, msg ):
        # broadcast a message to all clients
        for connection in self.activeConnections: 
            #netDatagram = NetDatagram()
            #netDatagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
            #if self.cWriter.send(netDatagram, connection):
            #    self.notify.debug( "Sent client:%s \tmessage:%s" , connection.getAddress(), msg[0] )
            pass
        
  
    
    
    def readMsg( self ):
        """Returns the (message, player id), if any, or None if there was nothing to read"""
        if self.from_network:
            return self.from_network.pop()
        else:
            return None
        
    
    def sendMsg( self, msg, source = None ):
        self.to_network.append( msg )        
        self.log.info("Sterner posted a message: %s" , msg[0] )
    
      
