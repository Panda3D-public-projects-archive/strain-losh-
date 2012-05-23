'''
Created on 4.10.2011.

@author: krav
'''
import sys
import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionListener, QueuedConnectionReader, ConnectionWriter #@UnresolvedImport
from pandac.PandaModules import NetAddress, NetDatagram, PointerToConnection #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator 
import time
import threading
import collections
import util
from strain.share import *
from socket import SHUT_RDWR


TCP_PORT = 80808




class Network:
    
    
    def __init__(self, sterner, lgr):
    
        self.sterner = sterner
        self.cManager = None
        self.cListener = None
        self.cReader = None
        self.cWriter = None
        self.tcpSocket = None
         
    
        self.activeConnections = []
        
        #used by handshaking threads to put results in
        self.handshakedConnections = collections.deque()
        
        self.log = lgr
    
    
    
    
    def startServer( self ):
        self.cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(self.cManager, 0)
        self.cReader = QueuedConnectionReader(self.cManager, 0)
        self.cWriter = ConnectionWriter(self.cManager, 0)

        backlog = 5
        self.tcpSocket = self.cManager.openTCPServerRendezvous(TCP_PORT , backlog)        
        
        self.cListener.addConnection(self.tcpSocket)
    
    
    
    
    def stopServer( self ):
        
        self.log.info( "Stopping server!" )
        
        for connection in self.activeConnections[:]:
            self.log.info("Closing connection with: %s", connection.getAddress() )
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
            conn, success = self.handshakedConnections.pop()            
            if success:
                #add this connection                        
                self.cReader.addConnection(conn)
                self.log.info("Client connected: %s", conn.getAddress() )
                self.activeConnections.append( conn )
            else:
                self.disconnect( conn )
                self.log.info("Client didn't pass handshaking.")   
                             
        except IndexError:
            pass
                   
                   
        #check for disconnects
        for connection in self.activeConnections[:]:   
            if not connection.getSocket().Active():
                #once socket disconnects there is no address in it so this will just write 0.0.0.0
                #self.log.info("Client disconnected: %s", str(connection.getAddress()) )
                self.disconnect( connection )
    

    
    def handshake( self, connection ):
        s = connection.getSocket()

        if self.getData(s, 3) != 'LOSH?':
            self.handshakedConnections.append( (connection, False) )
            return
        s.SendData('LOSH!')

        if self.getData(s, 3) != 'Sterner?':
            self.handshakedConnections.append( (connection, False) )
            return
        s.SendData('Regix!')        
        
        
        msg = self.getData(s, 3)
        msg = msg.split(':')
        
        if msg[0] == COMMUNICATION_PROTOCOL_STRING:
            try:
                ver = float(msg[1])
                if ver != COMMUNICATION_PROTOCOL_VERSION:
                    raise Exception("Wrong communication protocol version")
            except:
                self.handshakedConnections.append( (connection, False) )
                self.log.error( "Could not handshake:" + sys.exc_info()[1] )
                return
        
        
        #if we passed everything ok, than its a great success!        
        s.SendData( HANDSHAKE_SUCCESS )   
        self.handshakedConnections.append( (connection, True) )
        return 
                
    
    
    def disconnect( self, connection ):
        self.cListener.removeConnection( connection )
        self.cReader.removeConnection( connection )
        self.cManager.closeConnection( connection )

        self.sterner.playerDisconnected( connection )
        
        try:        
            self.activeConnections.remove( connection )
        except:
            print "Could not find this connection in activeConnections"
      
        
    
    
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
                self.log.debug( "Sent client:%s \tmessage:%s" , connection.getAddress(), msg[0] )
        
  
    
    
    def readMsg( self ):
        """Returns the (message, player id), if any, or None if there was nothing to read"""
        if self.cReader.dataAvailable():
            datagram = NetDatagram() 
            if self.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)
                msg = pickle.loads(dgi.getString())
                self.log.info("Sterner received a message:%s, from:%s", msg, str(datagram.getConnection().getAddress()))
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
                            self.log.debug( "Sent client: %s \tmessage:%s" , connection.getAddress(), msg[0] )
            else:
                self.broadcastMsg(msg)
        except:
            self.log.critical("Could not send message to clients, reason : %s", sys.exc_info()[1])
            return
        
        self.log.info("Sterner posted a message: %s" , msg[0] )
    
    
    def move( self, unit_id, move_actions, source = None ):
        self._sendMsg((MOVE, (unit_id, move_actions)), source) 
                                                                      
    
    def shootMsg( self, shoot_actions, source = None ):
        self._sendMsg( (SHOOT, shoot_actions), source ) 
                                                                      
    
    def chat( self, msg, sender, source = None ):
        self._sendMsg( (CHAT, msg, sender), source) 
                                                                      
    
    def sendState( self, engine_state, source ):
        self._sendMsg((ENGINE_STATE, engine_state), source)
    
    
    def sendLevel( self, compiled_level, source ):
        self._sendMsg((LEVEL, compiled_level), source)
    
    
    def error( self, error_msg, source = None ):
        self._sendMsg((ERROR, error_msg), source)
    
    
    def sendNewTurn( self, data, source ):
        self._sendMsg( (NEW_TURN, data), source )
    
    
    def sendUnit( self, pickled_unit, source = None ):
        self._sendMsg((UNIT, pickled_unit), source)

    
    def sendUse( self, unit_id, source = None ):
        self._sendMsg((USE, unit_id), source)

    
    def sendTaunt( self, unit_id, actions, source = None ):
        self._sendMsg((TAUNT, (unit_id, actions)), source)

    
    def sendDeploymentMsg( self, level, army_size, source = None ):
        deploy_dict = {}
        
        deploy_dict['level'] = util.compileLevel( level )
        deploy_dict['army_size'] = army_size
        
        self._sendMsg( ( DEPLOYMENT, deploy_dict ), source  )
        

    

    
    def sendMsg( self, msg, source = None):
        self._sendMsg( msg, source )


    
    def pong( self, source = None ):
        self._sendMsg( (PONG, time.time()), source )

        
      
