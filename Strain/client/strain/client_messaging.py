import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionReader, ConnectionWriter, NetDatagram #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator 
import time
from share import *
import threading
import socket


RETRY_ATTEMPTS = 3


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
    
    myConnection = None

    cManager = QueuedConnectionManager()
    cReader = QueuedConnectionReader(cManager, 0)
    cWriter = ConnectionWriter(cManager, 0)

    #ip adress and port
    ip_address = None
    port = None
    
    #set to id when we are logged into the main server, otherwise 0
    player_id = 0
    
    log = None

    #for saving a reference to the connection thread
    connection_thread = None

    #for connecting thread to count failed attempts
    num_failed_attempts = 0

    game_id = 0


    @staticmethod
    def connect():
        ClientMsg.log.info( "Trying to connect to server: %s:%s", ClientMsg.ip_address, ClientMsg.port )
                
        # how long until we give up trying to reach the server?
        timeout_in_miliseconds = 2000  # 2 seconds
        ClientMsg.myConnection = ClientMsg.cManager.openTCPClientConnection(ClientMsg.ip_address, ClientMsg.port, timeout_in_miliseconds)
        
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
    def setupAddress( ip_address, port ):
        ClientMsg.ip_address = ip_address
        ClientMsg.port = port
            
            
    @staticmethod
    def login( username, password ):
        #TODO: krav: vise verbose errori
        
        #if we are already logged in, just return
        if ClientMsg.player_id:
            return "Already logged in."
        
        #if we are not yet connected, try once more
        if not ClientMsg.myConnection:
            if not ClientMsg.connect():
                return "Cannot connect to server."
        
        #if not password:
        #    password = None
        
        #try to log in
        ClientMsg._sendMsg( (STERNER_ID, STERNER_LOGIN, username, password), True )
        t1 = time.time()
        while True:
            msg = ClientMsg.readMsg()
            if msg:
                if msg[0] == LOGIN_SUCCESS:
                    print "dobio welcome!!!\nid:", msg[1]
                    ClientMsg.player_id = int(msg[1])
                    return 0
                else:
                    #return error msg
                    return msg
            
            #wait for max of 3 seconds
            if time.time() - t1 > 3:
                return "Could not log in... timed out."
        
            time.sleep(0.01)
            
            
            
    @staticmethod
    def serverUp():
        if ClientMsg.myConnection:
            return True
        return False
                 
                    
    @staticmethod         
    def getGameId():
        return ClientMsg.game_id
                         
                 
    @staticmethod   
    def loggedIn():
        return ClientMsg.player_id
                        
                        
    @staticmethod
    def disconnect():
        if ClientMsg.myConnection:
            ClientMsg.cReader.removeConnection( ClientMsg.myConnection )
            ClientMsg.cManager.closeConnection( ClientMsg.myConnection )
            
        ClientMsg.myConnection = None
        ClientMsg.player_id = 0
            
            
            
    @staticmethod
    def handshake():
        s = ClientMsg.myConnection.getSocket()
        
        s.SendData('LOSH?')        
        if ClientMsg.getData(s, 2) != 'LOSH!':
            return False

        s.SendData('Sterner?')
        if ClientMsg.getData(s, 2) != 'Regix!':
            return False

        tmp_msg = COMMUNICATION_PROTOCOL_STRING + ':' + str(COMMUNICATION_PROTOCOL_VERSION)
        s.SendData( tmp_msg )

        if ClientMsg.getData(s, 2) != HANDSHAKE_SUCCESS:
            return False

        return True

            
    @staticmethod
    def threadFunction():
        
        while True:
                    
            #if we already tried RETRY_ATTEMPTS times, don't even bother
            if ClientMsg.num_failed_attempts >= RETRY_ATTEMPTS:
                ClientMsg.log.error("Failed to connect %d times, giving up.", ClientMsg.num_failed_attempts)
                return False
            
            if ClientMsg.connect():
                ClientMsg.num_failed_attempts = 0
                return True
            else:
                ClientMsg.num_failed_attempts += 1                

            time.sleep(1)
        
            
            
    @staticmethod
    def handleConnection():
        """Return True if connection is ok, returns False if there is no connection yet."""
        
        #if we are not connected
        if not ClientMsg.myConnection:

            #if we already tried RETRY_ATTEMPTS times, don't even bother
            if ClientMsg.num_failed_attempts >= RETRY_ATTEMPTS:
                return 
            
            #if there is an active connecting thread do nothing 
            if ClientMsg.connection_thread and ClientMsg.connection_thread.isAlive():
                return
            #if not, start one
            else:
                ClientMsg.connection_thread = threading.Thread(target=ClientMsg.threadFunction )
                ClientMsg.connection_thread.setName( 'Connection_thread')
                ClientMsg.connection_thread.start()
                return
            
       
        #check the connection, if there is none, disconnect everything and return false
        if not ClientMsg.myConnection.getSocket().Active():
            ClientMsg.log.error( "Lost connection to server: %s", ClientMsg.ip_address )
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
    def _sendMsg(msg, sterner = False):        
        if not ClientMsg.myConnection:
            return
        
        if not sterner:
            msg = ( ClientMsg.game_id, ClientMsg.player_id, ) + msg
            
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
    def taunt( unit_id ):
        ClientMsg._sendMsg( (TAUNT, unit_id) ) 

    @staticmethod
    def armyList( army_list ):
        ClientMsg._sendMsg( (ARMY_LIST, army_list) ) 
        
    @staticmethod
    def forceFirstTurn():
        ClientMsg._sendMsg( (FORCE_FIRST_TURN, 1) ) 
        
    @staticmethod
    def endTurn():
        ClientMsg._sendMsg((END_TURN,0))
        
    @staticmethod
    def ping():
        ClientMsg._sendMsg( (PING, time.time()) )
        
    @staticmethod
    def undefMsg1( value = 0 ):
        ClientMsg._sendMsg( (UNDEFINED_MSG_1, value ) )
        
    @staticmethod
    def undefMsg2( value = 0 ):
        #ClientMsg._sendMsg( (UNDEFINED_MSG_2, value ) )
        ClientMsg._sendMsg( (STERNER_ID, START_NEW_GAME, 'level2', 1000, ['Red', 'Blue'] ), True )


    #-----------------------STERNER MESSAGES---------------------------------------
    @staticmethod
    def getMyGames():
        ClientMsg._sendMsg( (STERNER_ID, GET_MY_GAMES ), True )
        
    @staticmethod
    def enterGame( game_id ):
        ClientMsg.game_id = game_id
        ClientMsg._sendMsg( (STERNER_ID, ENTER_GAME, game_id ), True )
        
    @staticmethod
    def startNewGame( map, budget, players ):
        ClientMsg._sendMsg( (STERNER_ID, START_NEW_GAME, map, budget, players ), True )
        
    @staticmethod
    def getAllPlayers():
        ClientMsg._sendMsg( (STERNER_ID, GET_ALL_PLAYERS ), True )
        
        
