'''
Created on 4.10.2011.

@author: krav
'''
import sys
import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionListener, QueuedConnectionReader, ConnectionWriter #@UnresolvedImport
from pandac.PandaModules import NetAddress, NetDatagram, PointerToConnection #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator 
import threading
import collections
import util
from strain.share import *
import traceback

#max message size je 65k (0xffff) if we want to send a larger message, we need something else
#a level has cca 7k


class Network:
    
    
    def __init__(self, sterner, notify, db_api):
    
        self.sterner = sterner
        self.cManager = None
        self.cListener = None
        self.cReader = None
        self.cWriter = None
        self.tcpSocket = None
    
        self.activeConnections = []
        
        #used by handshaking threads to put results in
        self.handshakedConnections = collections.deque()
        
        self.notify = notify
        self.db_api = db_api
    
    
    
    
    def startServer( self ):
        self.cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(self.cManager, 0)
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        self.cWriter = ConnectionWriter(self.cManager, 0)

        backlog = 5
        self.tcpSocket = self.cManager.openTCPServerRendezvous(TCP_PORT , backlog)        
        
        self.cListener.addConnection(self.tcpSocket)
    
    
    
    
    def stopServer( self ):
        
        self.notify.info( "Stopping server!" )
        
        for connection in self.activeConnections[:]:
            self.notify.info("Closing connection with: %s", connection.getAddress() )
            self.disconnect( connection )
    
        self.activeConnections = []
        
        self.cManager = None
        self.cListener = None
        self.cReader = None
        self.cWriter = None
        self.tcpSocket = None
     
        self.handshakedConnections.clear()
    
    
    
    
    def handleConnections( self ):
        
        #check for new connections
        if self.cListener.newConnectionAvailable():
        
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
        
            if self.cListener.getNewConnection(rendezvous, netAddress, newConnection):
                newConnection = newConnection.p()
                newConnection.setNoDelay(1)
                              
                #try handshaking
                threading.Thread(target=self.handshake, args=( [newConnection] ) ).start()

                
                 
        #check if we have a new handshaked connection
        try:
            conn, success, player_id = self.handshakedConnections.pop()            
            if success:
                #add this connection to cReader                        
                self.cReader.addConnection(conn)
                self.notify.info("Client connected: %s", conn.getAddress() )
                self.activeConnections.append( conn )
                
                #tell sterner someone connected
                self.sterner.playerConnected( player_id, conn )
            else:
                self.disconnect( conn )
                self.notify.info("Client didn't pass handshaking.")   
                             
        except IndexError:
            pass
                   
                   
        #check for disconnects
        for connection in self.activeConnections[:]:   
            if not connection.getSocket().Active():
                #once socket disconnects there is no address in it so this will just write 0.0.0.0
                #self.notify.info("Client disconnected: %s", str(connection.getAddress()) )
                self.disconnect( connection )
    

    
    def handshake( self, connection ):
        #get socket and set it to non blocking
        s = connection.getSocket()
        s.SetNonBlocking()
        
        if self.getData(s, 3) != 'LOSH?':
            s.SendData("Wrong server!")
            self.handshakedConnections.append( (connection, False, 0) )
            return
        s.SendData('LOSH!')

        if self.getData(s, 3) != 'Sterner?':
            s.SendData("Wrong server!")            
            self.handshakedConnections.append( (connection, False, 0) )
            return
        s.SendData('Regix!')        
        
        
        msg = self.getData(s, 3)
        try:
            msg = msg.split(':')
            if msg[0] == COMMUNICATION_PROTOCOL_STRING:
                ver = msg[1]
                if ver != COMMUNICATION_PROTOCOL_VERSION:
                    s.SendData( "Wrong version!" )
                    raise Exception("Client with wrong version trying to connect from:" + str( connection.getAddress() ))
            else:                    
                s.SendData("Wrong communication protocol")
                raise Exception("Wrong communication protocol")
        except:
            self.handshakedConnections.append( (connection, False, 0) )
            self.notify.error( "Could not handshake! Info:%s", traceback.format_exc() )
            return
        
        
        #if we passed everything ok, than its a great success!        
        s.SendData( HANDSHAKE_SUCCESS )
        
        #now we expect username and password
        msg = self.getData(s, 3)
        try:
            login_data = pickle.loads(msg)
            
            if login_data[0] != STERNER_LOGIN:
                s.SendData( "Wrong login message." )
                raise Exception("Wrong login message.")
            
            username = login_data[1]
            pswd = login_data[2]
             
            user_data = self.db_api.returnPlayer( username )
            if not user_data or pswd != user_data[3]:
                s.SendData( "Wrong username/password" )
                raise Exception( "Wrong username/password" )

            #send client success message and his id
            s.SendData( LOGIN_SUCCESS + ":" + str(user_data[0]) )
            
            #everything is ok, tell main thread who connected
            self.handshakedConnections.append( (connection, True, user_data[0]) )
            
        except:
            self.handshakedConnections.append( (connection, False, 0) )
            self.notify.error( "Could not handshake! Info:%s", traceback.format_exc() )
            return
             
        
    
    
    def disconnect( self, connection ):
        self.cListener.removeConnection( connection )
        self.cReader.removeConnection( connection )
        self.cManager.closeConnection( connection )

        self.sterner.playerDisconnected( connection )
        
        try:        
            self.activeConnections.remove( connection )
        except:
            pass
      
    
    def getData( self, socket, timeout ):
        t = time.time()        
        while 1:
            msg = socket.RecvData(1024)
            if msg:
                return msg            
            if( time.time() - t > timeout ):
                return None
            time.sleep(0.01)
        return None
    
    
    
    def broadcastMsg( self, msg ):
        # broadcast a message to all clients
        for connection in self.activeConnections: 
            netDatagram = NetDatagram()
            netDatagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
            if self.cWriter.send(netDatagram, connection):
                self.notify.debug( "Sent client:%s \tmessage:%s" , connection.getAddress(), msg[0] )
        
  
    
    
    def readMsg( self ):
        """Returns the (message, player id), if any, or None if there was nothing to read"""
        if self.cReader.dataAvailable():
            datagram = NetDatagram() 
            if self.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)
                msg = pickle.loads(dgi.getString())
                self.notify.info("Sterner received a message:%s, from:%s", msg, str(datagram.getConnection().getAddress()))
                return (msg, datagram.getConnection() )

          
        return None
          
    
    def _sendMsg( self, msg, source = None ):
        try:
            if source:
                for connection in self.activeConnections:
                    if connection == source:
                        netDatagram = NetDatagram()
                        netDatagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
                        if self.cWriter.send(netDatagram, connection):
                            self.notify.debug( "Sent client: %s \tmessage:%s" , connection.getAddress(), msg[0] )
            else:
                self.broadcastMsg(msg)
        except:
            self.notify.critical("Could not send message to clients, reason : %s", sys.exc_info()[1])
            return
        
        #self.log.info("Sterner posted a message: %s" , msg[0] )
    
      
