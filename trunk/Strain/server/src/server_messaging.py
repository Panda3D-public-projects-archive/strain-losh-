'''
Created on 4.10.2011.

@author: krav
'''
import sys
import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionListener, QueuedConnectionReader, ConnectionWriter #@UnresolvedImport
from pandac.PandaModules import NetAddress, NetDatagram, PointerToConnection #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import engine 
import time
import threading
import collections
from engine import *




IP_ADDRESS = 'localhost'
#IP_ADDRESS = 'krav.servebeer.com'
#NAME = 'blood angels'
NAME = 'ultramarines'
TCP_PORT = 56005

MOVE = 1                #values - list of move actions ('move',tile) followed by ('rotate',tile)
NEW_TURN = 2            #value - turn number
ENGINE_SHUTDOWN = 3     #no values
ERROR = 4               #value - error message
ENGINE_STATE = 5        #value - dictionary of values
LEVEL = 6               #value - pickled level
END_TURN = 7            #no values
UNIT = 8                #value - pickled unit
SHOOT = 9               #value - target unit



class EngMsg:
    
    cManager = None
    cListener = None
    cReader = None
    cWriter = None
    tcpSocket = None
     
    activeConnections = []
    
    handshakedConnections = collections.deque()
    
    log = None
    
    @staticmethod
    def startServer( lgr ):
        EngMsg.cManager = QueuedConnectionManager()
        EngMsg.cListener = QueuedConnectionListener(EngMsg.cManager, 0)
        EngMsg.cReader = QueuedConnectionReader(EngMsg.cManager, 0)
        EngMsg.cWriter = ConnectionWriter(EngMsg.cManager, 0)

        EngMsg.log = lgr
  
        backlog = 5
        EngMsg.tcpSocket = EngMsg.cManager.openTCPServerRendezvous(TCP_PORT , backlog)        
        
        EngMsg.cListener.addConnection(EngMsg.tcpSocket)
    
    @staticmethod
    def stopServer():
        for client, address, name in EngMsg.activeConnections[:]:
            EngMsg.disconnect(client, address, name)
            EngMsg.logger.notify.info("Closing connection with: %s @ %s", name, address)
    
        EngMsg.activeConnections = []
        
        EngMsg.cManager = None
        EngMsg.cListener = None
        EngMsg.cReader = None
        EngMsg.cWriter = None
        EngMsg.tcpSocket = None
     
        EngMsg.handshakedConnections = None
    
    @staticmethod
    def handleConnections():
        
        #check for new connections
        if EngMsg.cListener.newConnectionAvailable():
        
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
        
            if EngMsg.cListener.getNewConnection(rendezvous, netAddress, newConnection):
                newConnection = newConnection.p()
                newConnection.setNoDelay(1)
                              
                #try handshaking
                threading.Thread(target=EngMsg.handshake, args=( [newConnection, engine._instance.players[:]] ) ).start()

                
                 
        #check if we have a new handshaked connection
        try:
            conn, success, player_name = EngMsg.handshakedConnections.pop()            
            if success:
                
                #go through all players
                for player in engine._instance.players:
                    if player.name == player_name:
                        
                        #see if there is already a connection for this player, if yes than disconnect it
                        if player.connection != None:
                            EngMsg.sendErrorMsg("Disconnecting because this player is connecting from other connection", player.connection )
                            EngMsg.disconnect( player.connection, player.connection.getAddress(), player.name )
                            EngMsg.log.info("Player %s disconnected because he was logging in from other connection", player.name)
                            
                        #remember this connection
                        player.connection = conn
                
                EngMsg.cReader.addConnection(conn)
                EngMsg.log.info("Client connected: %s @ %s", player_name, conn.getAddress() )
                EngMsg.activeConnections.append( ( conn, conn.getAddress(), player_name ) )
                
            else:
                #in this case, address and name parameter don't matter, cause there is nothing in activeConnections yet
                EngMsg.disconnect( conn, conn.getAddress(),'' )
                EngMsg.log.info("Client didn't pass handshaking.")                
        except IndexError:
            pass
                   
                   
        #check for disconnects
        for connection, address, name in EngMsg.activeConnections[:]:   
            if not connection.getSocket().Active():
                EngMsg.log.info("Client disconnected: %s @ %s", name, address)
                EngMsg.disconnect(connection, address, name)
    
    
    @staticmethod
    def disconnect( connection, address, name ):
            EngMsg.cListener.removeConnection( connection )
            EngMsg.cReader.removeConnection( connection )
            EngMsg.cManager.closeConnection( connection )
            try:
                EngMsg.activeConnections.remove( ( connection, address, name ) )
            except:
                pass
        
    
    @staticmethod
    def getData( socket, timeout ):
        t = time.time()        
        while 1:
            msg = socket.RecvData(1024)
            if msg:
                return msg            
            if( time.time() - t > timeout ):
                return None
            time.sleep(0.01)
        return None
    
    
    @staticmethod
    def handshake( connection, players ):
        s = connection.getSocket()

        if EngMsg.getData(s, 3) != 'LOSH?':
            EngMsg.handshakedConnections.append( (connection, False, '') )
            return
            
        s.SendData('LOSH!')

        if EngMsg.getData(s, 3) != 'Strain?':
            EngMsg.handshakedConnections.append( (connection, False, '') )
            return
             
        s.SendData('Send your name')        
        
        #check to see if there is a player with that name
        name = EngMsg.getData(s, 3)
        found = False        
        for player in players:
            if name == player.name:
                found = True
                break
                
        if not found:
            EngMsg.handshakedConnections.append( (connection, False, '') )
            return        
        
        s.SendData('Welcome')
        
        EngMsg.handshakedConnections.append( (connection, True, name) )
        return
                
    @staticmethod
    def broadcastMsg(msg):

        # broadcast a message to all clients
        for client, address, name in EngMsg.activeConnections: 
            netDatagram = NetDatagram()
            netDatagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
            if EngMsg.cWriter.send(netDatagram, client):
                EngMsg.log.debug( "Sent client: %s @ %s\tmessage:%s" , name, address, msg )
        
    
    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        if EngMsg.cReader.dataAvailable():
            datagram = NetDatagram() 
            if EngMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)
                msg = pickle.loads(dgi.getString())
                EngMsg.log.info("Engine received a message:%s, from:%s", msg, str(datagram.getConnection().getAddress()))
                return (msg, datagram.getConnection() )

          
        return None
          
    @staticmethod
    def _sendMsg(msg, source = None):
        try:
            if source:
                for conn, address, name in EngMsg.activeConnections:
                    if conn == source:
                        netDatagram = NetDatagram()
                        netDatagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))
                        if EngMsg.cWriter.send(netDatagram, conn):
                            EngMsg.log.debug( "Sent client: %s @ %s\tmessage:%s" , name, address, msg )
            else:
                EngMsg.broadcastMsg(msg)
        except:
            EngMsg.log.critical("Could not send message to clients, reason : %s", sys.exc_info()[1])
            return
        
        EngMsg.log.info("Engine posted a message: %s" , msg )
    
    @staticmethod
    def move(unit_id, move_actions):
        EngMsg._sendMsg((MOVE, (unit_id, move_actions))) 
                                                                      
    @staticmethod
    def sendState(engine_state, source):
        EngMsg._sendMsg((ENGINE_STATE, engine_state), source)
    
    @staticmethod
    def sendLevel(pickled_level):
        EngMsg._sendMsg((LEVEL, pickled_level))
    
    @staticmethod
    def sendErrorMsg(error_msg, source = None):
        EngMsg._sendMsg((ERROR, error_msg), source)
    
    @staticmethod
    def sendNewTurn(turn_num):
        EngMsg._sendMsg((NEW_TURN, turn_num))
    
    @staticmethod
    def sendUnit(pickled_unit):
        EngMsg._sendMsg((UNIT, pickled_unit))
    
    
      
