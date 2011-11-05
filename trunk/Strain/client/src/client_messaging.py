import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionReader, ConnectionWriter, NetDatagram #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator 
import time


IP_ADDRESS = 'localhost'
#IP_ADDRESS = 'krav.servebeer.com'
NAME = 'blood angels'
#NAME = 'ultramarines'
TCP_PORT = 56005

MOVE = 1                #values - list of move actions ('move',tile) followed by ('rotate',tile)
NEW_TURN = 2            #value - turn number
ENGINE_SHUTDOWN = 3     #no values
ERROR = 4               #value - error message
ENGINE_STATE = 5        #value - dictionary of values
LEVEL = 6               #value - pickled level
END_TURN = 7            #no values
UNIT = 8                #value - pickled unit
SHOOT = 9               #value - (which unit, target unit)


class Msg:
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
 
    
    
class ClientMsg:
    
    
    cManager = None
    cListener = None
    cReader = None
    cWriter = None
    tcpSocket = None
    myConnection = None
    
    num_failed_attempts = 0

    log = None

    @staticmethod
    def connect():
        ClientMsg.log.info( "Trying to connect to server: %s:%s", IP_ADDRESS, TCP_PORT )
        
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
                ClientMsg.log.error( "Did not pass handshake.")
                return False
            
            ClientMsg.cReader.addConnection(ClientMsg.myConnection)
            
            ClientMsg.log.info( "Connected to server: %s", ClientMsg.myConnection.getAddress() )
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
                ClientMsg.log.error("Failed to connect %d times, giving up.", ClientMsg.num_failed_attempts)
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
            ClientMsg.log.error( "Lost connection to server: %s", IP_ADDRESS )
            ClientMsg.disconnect()
            return False

        #we are connected and everything is ok
        return True
            
            
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
    def handshake():
        s = ClientMsg.myConnection.getSocket()

        s.SendData('LOSH?')        
        
        if ClientMsg.getData(s, 2) != 'LOSH!':
            return False

        s.SendData('Strain?')
                
        if ClientMsg.getData(s, 2) != 'Send your name':
            return False

        s.SendData(NAME)

        welcomeMsg = ClientMsg.getData(s, 2)
        
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
                ClientMsg.log.info("Client received a message:%s", msg)
                          
                return msg
                                            
        return None    

        
    @staticmethod
    def _sendMsg(msg):        

        if not ClientMsg.myConnection:
            return
         
        datagram = NetDatagram()        
        datagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))   
        ClientMsg.cWriter.send(datagram, ClientMsg.myConnection)
        ClientMsg.log.debug("Client posted a message: %s", msg)

    
    @staticmethod
    def getEngineState():
        ClientMsg._sendMsg((ENGINE_STATE,0))
    
    @staticmethod
    def getLevel():
        ClientMsg._sendMsg((LEVEL,0))
    
    @staticmethod
    def move(unit_id, new_position, orientation):
        ClientMsg._sendMsg((MOVE, { 'unit_id':unit_id,
                                           'new_position':new_position,
                                           'orientation':orientation })) 

    @staticmethod
    def shutdownEngine():
        ClientMsg._sendMsg((ENGINE_SHUTDOWN,0)) 
        
    @staticmethod
    def endTurn():
        ClientMsg._sendMsg((END_TURN,0))
        
        
