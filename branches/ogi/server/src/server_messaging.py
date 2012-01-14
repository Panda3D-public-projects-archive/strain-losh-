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
import util


TCP_PORT = 56005


MOVE = 'move'                   #values - list of actions ('move',tile) ('rotate',tile) ('overwatch',overwatchresult) ('detected',enemy)
NEW_TURN = 'new_turn'           #value - turn number
ENGINE_SHUTDOWN = 'shutdown'    #no values
ERROR = 'error'                 #value - error message
ENGINE_STATE = 'engine_state'   #value - dictionary of values
LEVEL = 'level'                 #value - pickled level
END_TURN = 'end_turn'           #no values
UNIT = 'unit'                   #value - pickled unit
SHOOT = 'shoot'                 #value - (which unit, target unit)
CHAT = 'chat'                   #value - string for chat
OVERWATCH = 'overwatch'         #value - id of unit going on overwatch, this message toggles overwatch on/off
SET_UP = 'set_up'               #value - id of unit setting up heavy weapon
VANISH = 'vanish'               #value - id of unit vanishing
SPOT = 'spot'                   #value - id of unit spotted
ROTATE = 'rotate'               #value - new heading 

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
            EngMsg.log.info("Closing connection with: %s @ %s", name, address)
    
        EngMsg.activeConnections = []
        
        EngMsg.cManager = None
        EngMsg.cListener = None
        EngMsg.cReader = None
        EngMsg.cWriter = None
        EngMsg.tcpSocket = None
     
        EngMsg.handshakedConnections.clear()
    
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
                threading.Thread(target=EngMsg.handshake, args=( [newConnection, engine._instance.players] ) ).start()

                
                 
        #check if we have a new handshaked connection
        try:
            conn, success, player_name = EngMsg.handshakedConnections.pop()            
            if success:
                
                tmp_player = None
                
                if player_name == 'observer':
                    tmp_player = engine._instance.observer
                    tmp_player.connection = conn
                else:
                
                    #go through all players
                    for player in engine._instance.players:
                        if player.name == player_name:
                            
                            #see if there is already a connection for this player, if yes than disconnect it
                            if player.connection != None:
                                EngMsg.error("Disconnecting because this player is connecting from other connection", player.connection )
                                EngMsg.disconnect( player.connection, player.connection.getAddress(), player.name )
                                EngMsg.log.info("Player %s disconnected because he was logging in from other connection", player.name)
                                
                            #remember this connection
                            player.connection = conn
                            tmp_player = player
                
                EngMsg.cReader.addConnection(conn)
                EngMsg.log.info("Client connected: %s @ %s", tmp_player.name, conn.getAddress() )
                EngMsg.activeConnections.append( ( conn, conn.getAddress(), tmp_player.name ) )
                
                #send all backlogged messages to this player
                for msg in tmp_player.msg_lst:
                    EngMsg.sendMsg( msg, conn )
                
                #clear all messages because we sent them, but not if this is observer
                if tmp_player.name != 'observer':
                    tmp_player.msg_lst = []
                
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
        
            for p in engine._instance.players:
                if p.connection == connection:
                    p.connection = None
                    #remember this state for this player              
                    p.addEngineStateMsg( util.compileState( engine._instance, p) )
                
                
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
        
        if name == 'observer':
            print "observer connected"
            EngMsg.handshakedConnections.append( (connection, True, name) )
            s.SendData('Welcome')
            return
                
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
        
        #send it to observer as well
        engine._instance.observer.addMsg( msg )
    
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
    def move(unit_id, move_actions, source = None):
        EngMsg._sendMsg((MOVE, (unit_id, move_actions)), source) 
                                                                      
    @staticmethod
    def shootMsg( shoot_actions, source = None):
        EngMsg._sendMsg( (SHOOT, shoot_actions), source )
        print shoot_actions 
                                                                      
    @staticmethod
    def chat( msg, sender, source = None):
        EngMsg._sendMsg( (CHAT, msg, sender), source) 
                                                                      
    @staticmethod
    def sendState(engine_state, source):
        EngMsg._sendMsg((ENGINE_STATE, engine_state), source)
    
    @staticmethod
    def sendLevel(pickled_level):
        EngMsg._sendMsg((LEVEL, pickled_level))
    
    @staticmethod
    def error(error_msg, source = None):
        EngMsg._sendMsg((ERROR, error_msg), source)
    
    @staticmethod
    def sendNewTurn( data, source ):
        EngMsg._sendMsg( (NEW_TURN, data), source )
    
    @staticmethod
    def sendUnit(pickled_unit, source = None):
        EngMsg._sendMsg((UNIT, pickled_unit), source)

    @staticmethod
    def sendMsg( msg, source = None):
        EngMsg._sendMsg( msg, source )

        
      
