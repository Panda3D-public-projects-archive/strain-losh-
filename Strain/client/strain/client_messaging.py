import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionReader, ConnectionWriter, NetDatagram #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator 
import time


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
USE = 'use'                     #value - id of unit trying to use
VANISH = 'vanish'               #value - id of unit vanishing
SPOT = 'spot'                   #value - id of unit spotted
ROTATE = 'rotate'               #value - new heading 



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
    def connect(player, ip_address, tcp_port):
        ClientMsg.log.info( "Trying to connect to server: %s:%s", ip_address, tcp_port )
        
        ClientMsg.cManager = QueuedConnectionManager()
        ClientMsg.cReader = QueuedConnectionReader(ClientMsg.cManager, 0)
        ClientMsg.cWriter = ConnectionWriter(ClientMsg.cManager, 0)
        
        # how long until we give up trying to reach the server?
        timeout_in_miliseconds = 3000  # 3 seconds
        ClientMsg.myConnection = ClientMsg.cManager.openTCPClientConnection(ip_address, tcp_port, timeout_in_miliseconds)
        
        if ClientMsg.myConnection:
            ClientMsg.myConnection.setNoDelay(1)
            
            #try handshaking
            if not ClientMsg.handshake(player):
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
    def handleConnection(player, ip_address, tcp_port):
        """Return True if connection is ok, returns False if there is no connection."""
        
        #if we are not connected, try to connect
        if not ClientMsg.myConnection:

            #TODO: krav: ovo je za debug komentirano            
            #if ClientMsg.num_failed_attempts > 5:
            #    return False
            
            #if we already tried 5 times, don't even bother
            if ClientMsg.num_failed_attempts == 5:
                ClientMsg.log.error("Failed to connect %d times, giving up.", ClientMsg.num_failed_attempts)
                ClientMsg.num_failed_attempts += 1
                return False
            
            if ClientMsg.connect(player, ip_address, tcp_port):
                #every time we reconnect to server, get the engine state 
                #ClientMsg.getEngineState()
                ClientMsg.num_failed_attempts = 0             
                return True
            else:
                ClientMsg.num_failed_attempts += 1                
                return False
            
        
        #check the connection, if there is none, disconnect everything and return false
        if not ClientMsg.myConnection.getSocket().Active():
            ClientMsg.log.error( "Lost connection to server: %s", ip_address )
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
    def handshake(player):
        s = ClientMsg.myConnection.getSocket()

        s.SendData('LOSH?')        
        
        if ClientMsg.getData(s, 2) != 'LOSH!':
            return False

        s.SendData('Strain?')
                
        if ClientMsg.getData(s, 2) != 'Send your name':
            return False

        s.SendData(player)

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
    def shoot(shooter_id, target_id):
        ClientMsg._sendMsg((SHOOT, { 'shooter_id':shooter_id,
                                           'target_id':target_id})) 
    @staticmethod
    def shutdownEngine():
        ClientMsg._sendMsg((ENGINE_SHUTDOWN,0)) 
        
    @staticmethod
    def chat( msg, to_allies=False ):
        ClientMsg._sendMsg( (CHAT, msg, to_allies) ) 
        
    @staticmethod
    def overwatch( unit_id ):
        ClientMsg._sendMsg( (OVERWATCH, unit_id) ) 
        
    @staticmethod
    def setUp( unit_id ):
        ClientMsg._sendMsg( (SET_UP, unit_id) ) 
        
    @staticmethod
    def use( unit_id ):
        ClientMsg._sendMsg( (USE, unit_id) ) 
        
    @staticmethod
    def endTurn():
        ClientMsg._sendMsg((END_TURN,0))
        
        
