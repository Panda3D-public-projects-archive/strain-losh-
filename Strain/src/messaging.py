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




IP_ADDRESS = 'localhost'
#IP_ADDRESS = 'krav.servebeer.com'
#NAME = 'blood angels'
NAME = 'ultramarines'
TCP_PORT = 56005

class Msg:


    MOVE = 1                #values - list of move actions ('move',tile) followed by ('rotate',tile)
    NEW_TURN = 2            #value - turn number
    ENGINE_SHUTDOWN = 3     #no values
    ERROR = 4               #value - error message
    ENGINE_STATE = 5        #value - dictionary of values
    LEVEL = 6               #value - pickled level
    END_TURN = 7            #no values
    UNIT = 8                #value - pickled unit

    
    
    def __init__(self, in_type, value=None):
        self.type = in_type
        self.values = value

    def __repr__(self):
        if self.type == Msg.ENGINE_STATE:
            return "type:ENGINE_STATE"
        elif self.type == Msg.MOVE:
            return "type:MOVE, value:%s" % str(self.values)
        elif self.type == Msg.NEW_TURN:
            return "type:NEW_TURN, value:%s" % str(self.values)
        elif self.type == Msg.ERROR:
            return "type:ERROR, value:%s" % str(self.values)
        elif self.type == Msg.LEVEL:
            return "type:LEVEL"
        elif self.type == Msg.END_TURN:
            return "type:END_TURN, value:%s" % str(self.values)
        elif self.type == Msg.UNIT:
            return "type:UNIT"  
        
        return "type:%d  value:%s" % (self.type, str(self.values))



class EngMsg:
    
    cManager = None
    cListener = None
    cReader = None
    cWriter = None
    tcpSocket = None
     
    activeConnections = []
    
    handshakedConnections = collections.deque()
    
    
    @staticmethod
    def startServer():
        EngMsg.cManager = QueuedConnectionManager()
        EngMsg.cListener = QueuedConnectionListener(EngMsg.cManager, 0)
        EngMsg.cReader = QueuedConnectionReader(EngMsg.cManager, 0)
        EngMsg.cWriter = ConnectionWriter(EngMsg.cManager, 0)
        
  
        backlog = 5
        EngMsg.tcpSocket = EngMsg.cManager.openTCPServerRendezvous(TCP_PORT , backlog)        
        
        EngMsg.cListener.addConnection(EngMsg.tcpSocket)
    
    @staticmethod
    def stopServer():
        for client, address, name in EngMsg.activeConnections[:]:
            EngMsg.disconnect(client, address, name)
            engine.notify.info("Closing connection with: %s @ %s", name, address)
    
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
                threading.Thread(target=EngMsg.handshake, args=( [newConnection, engine.Engine.getInstance().players[:]] ) ).start()

                
                 
        #check if we have a new handshaked connection
        try:
            conn, success, player_name = EngMsg.handshakedConnections.pop()            
            if success:
                
                #go through all players
                for player in engine.Engine.getInstance().players:
                    if player.name == player_name:
                        
                        #see if there is already a connection for this player, if yes than disconnect it
                        if player.connection != None:
                            EngMsg.sendErrorMsg("Disconnecting because this player is connecting from other connection", player.connection )
                            #TODO: krav: da se na klijentu eksli diskonekta i da se vidi kaj se desilo
                            EngMsg.disconnect( player.connection, player.connection.getAddress(), player.name )
                            engine.notify.info("Player %s disconnected because he was logging in from other connection", player.name)
                            
                        #remember this connection
                        player.connection = conn
                
                EngMsg.cReader.addConnection(conn)
                engine.notify.info("Client connected: %s @ %s", player_name, conn.getAddress() )
                EngMsg.activeConnections.append( ( conn, conn.getAddress(), player_name ) )
                
            else:
                #in this case, address and name parameter don't matter, cause there is nothing in activeConnections yet
                EngMsg.disconnect( conn, conn.getAddress(),'' )
                engine.notify.info("Client didn't pass handshaking.")                
        except IndexError:
            pass
                   
                   
        #check for disconnects
        for connection, address, name in EngMsg.activeConnections[:]:   
            if not connection.getSocket().Active():
                engine.notify.info("Client disconnected: %s @ %s", name, address)
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
        
        #TODO: krav: stavit neki SSL ovdje i provjerit username/pass
        
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
            netDatagram.addString(pickle.dumps(msg))
            if EngMsg.cWriter.send(netDatagram, client):
                engine.notify.debug( "Sent client: %s @ %s\tmessage:%s" , name, address, msg )
        
    
    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        if EngMsg.cReader.dataAvailable():
            datagram = NetDatagram() 
            if EngMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)
                msg = pickle.loads(dgi.getString())
                engine.notify.info("Engine received a message:%s, from:%s", msg, str(datagram.getConnection().getAddress()))
                return (msg, datagram.getConnection() )

          
        return None
          
    @staticmethod
    def _sendMsg(msg, source = None):
        try:
            if source:
                for conn, address, name in EngMsg.activeConnections:
                    if conn == source:
                        netDatagram = NetDatagram()
                        netDatagram.addString(pickle.dumps(msg))
                        if EngMsg.cWriter.send(netDatagram, conn):
                            engine.notify.debug( "Sent client: %s @ %s\tmessage:%s" , name, address, msg )
            else:
                EngMsg.broadcastMsg(msg)
        except:
            engine.notify.critical("Could not send message to clients, reason : %s", sys.exc_info()[1])
            return
        
        engine.notify.info("Engine posted a message: %s" , msg )
    
    @staticmethod
    def move(unit_id, move_actions):
        EngMsg._sendMsg(Msg(Msg.MOVE, (unit_id, move_actions))) 
                                                                      
    @staticmethod
    def sendState(engine_state, source):
        EngMsg._sendMsg(Msg(Msg.ENGINE_STATE, engine_state), source)
    
    @staticmethod
    def sendLevel(pickled_level):
        EngMsg._sendMsg(Msg(Msg.LEVEL, pickled_level))
    
    @staticmethod
    def sendErrorMsg(error_msg, source = None):
        EngMsg._sendMsg(Msg(Msg.ERROR, error_msg), source)
    
    @staticmethod
    def sendNewTurn(turn_num):
        EngMsg._sendMsg(Msg(Msg.NEW_TURN, turn_num))
    
    @staticmethod
    def sendUnit(pickled_unit):
        EngMsg._sendMsg(Msg(Msg.UNIT, pickled_unit))
    
    
    
    
class ClientMsg:
    
    
    cManager = None
    cListener = None
    cReader = None
    cWriter = None
    tcpSocket = None
    myConnection = None
    
    num_failed_attempts = 0
    
    @staticmethod
    def connect():
        #TODO: ogs: i ovo moras maknut na logger od klijenta
        engine.notify.info( "Trying to connect to server: %s:%s", IP_ADDRESS, TCP_PORT )
        
        ClientMsg.cManager = QueuedConnectionManager()
        ClientMsg.cReader = QueuedConnectionReader(ClientMsg.cManager, 0)
        ClientMsg.cWriter = ConnectionWriter(ClientMsg.cManager, 0)
        
        # how long until we give up trying to reach the server?
        timeout_in_miliseconds = 3000  # 3 seconds
        ClientMsg.myConnection = ClientMsg.cManager.openTCPClientConnection(IP_ADDRESS, TCP_PORT, timeout_in_miliseconds)
        
        if ClientMsg.myConnection:
            ClientMsg.myConnection.setNoDelay(1)
            
            #try handshaking
            if not ClientMsg.handshake():
                ClientMsg.disconnect()
                #TODO: ogs: i ovo moras maknut na logger od klijenta
                engine.notify.error( "Did not pass handshake.")
                return False
            
            ClientMsg.cReader.addConnection(ClientMsg.myConnection)
            
            #TODO: ogs: i ovo moras maknut na logger od klijenta
            engine.notify.info( "Connected to server: %s", ClientMsg.myConnection.getAddress() )
            return True
            
        return False
            
            
    @staticmethod
    def disconnect():
        if ClientMsg.myConnection:
            ClientMsg.cReader.removeConnection( ClientMsg.myConnection )
            ClientMsg.cManager.closeConnection( ClientMsg.myConnection )
            
        ClientMsg.myConnection = None
            
            
    @staticmethod
    def handleConnection():
        """Return True if connection is ok, returns False if there is no connection."""
        
        #if we are not connected, try to connect
        if not ClientMsg.myConnection:
            
            if ClientMsg.num_failed_attempts > 5:
                return False
            
            #if we already tried 5 times, don't even bother
            if ClientMsg.num_failed_attempts == 5:
                engine.notify.error("Failed to connect %d times, giving up.", ClientMsg.num_failed_attempts)
                ClientMsg.num_failed_attempts += 1
                return False
            
            if ClientMsg.connect():
                #every time we reconnect to server, get the engine state 
                ClientMsg.getEngineState()
                ClientMsg.num_failed_attempts = 0             
                return True
            else:
                ClientMsg.num_failed_attempts += 1                
                return False
            
        
        #check the connection, if there is none, disconnect everything and return false
        if not ClientMsg.myConnection.getSocket().Active():
            #TODO: ogs: prebacit i ovo na klijentov logger
            engine.notify.error( "Lost connection to server: %s", IP_ADDRESS )
            ClientMsg.disconnect()
            return False

        #we are connected and everything is ok
        return True
            
    @staticmethod
    def handshake():
        s = ClientMsg.myConnection.getSocket()

        s.SendData('LOSH?')        
        
        if EngMsg.getData(s, 2) != 'LOSH!':
            return False

        s.SendData('Strain?')
                
        if EngMsg.getData(s, 2) != 'Send your name':
            return False

        s.SendData(NAME)

        welcomeMsg = EngMsg.getData(s, 2)
        
        if welcomeMsg != 'Welcome':
            return False
        
        return True
            
    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        
        if not ClientMsg.myConnection:
            return None
        
        if ClientMsg.cReader.dataAvailable():
            datagram = NetDatagram()                          
            if ClientMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)                
                msg = pickle.loads(dgi.getString())                
                #TODO: ogs: sredit da ti ovdje pise u GraphicsEngine, nemres stavit import jer je onda ciklicki povezano
                engine.notify.info("Client received a message:%s", msg)
                          
                return msg
                                            
        return None    

        
    @staticmethod
    def _sendMsg(msg):        

        if not ClientMsg.myConnection:
            return
         
        datagram = NetDatagram()        
        datagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))   
        ClientMsg.cWriter.send(datagram, ClientMsg.myConnection)

                 
        #TODO: ogs: sredit da ti ovdje pise u GraphicsEngine, nemres stavit import jer je onda ciklicki povezano
        #GraphicsEngine.logger.debug("Client posted a message: %s", msg)
        engine.notify.debug("Client posted a message: %s", msg)

    
    @staticmethod
    def getEngineState():
        ClientMsg._sendMsg(Msg(Msg.ENGINE_STATE))
    
    @staticmethod
    def getLevel():
        ClientMsg._sendMsg(Msg(Msg.LEVEL))
    
    @staticmethod
    def move(unit_id, new_position, orientation):
        ClientMsg._sendMsg(Msg(Msg.MOVE, { 'unit_id':unit_id,
                                           'new_position':new_position,
                                           'orientation':orientation })) 

    @staticmethod
    def shutdownEngine():
        ClientMsg._sendMsg(Msg(Msg.ENGINE_SHUTDOWN)) 
        
    @staticmethod
    def endTurn():
        ClientMsg._sendMsg(Msg(Msg.END_TURN))
        
        
