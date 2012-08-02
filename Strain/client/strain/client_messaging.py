import cPickle as pickle
from pandac.PandaModules import QueuedConnectionManager, QueuedConnectionReader, ConnectionWriter, NetDatagram #@UnresolvedImport
from direct.distributed.PyDatagramIterator import PyDatagramIterator 
import time
from share import *
import threading
import socket


RETRY_ATTEMPTS = 3


    
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
    
    notify = None

    #for saving a reference to the connection thread
    connection_thread = None

    #for connecting thread to count failed attempts
    num_failed_attempts = 0

    game_id = 0


            
    @staticmethod
    def setupAddress( ip_address, port ):
        ClientMsg.ip_address = ip_address
        ClientMsg.port = port
            
            
    @staticmethod
    def login( username, password ):
        ClientMsg.notify.info( "Trying to connect to server: %s:%s", ClientMsg.ip_address, ClientMsg.port )
                
        # how long until we give up trying to reach the server?
        timeout_in_miliseconds = 2000  # 2 seconds
        ClientMsg.myConnection = ClientMsg.cManager.openTCPClientConnection(ClientMsg.ip_address, ClientMsg.port, timeout_in_miliseconds)
        
        if not ClientMsg.myConnection:
            return "Could not connect to server."

        
        #try handshaking and logging in
        err_msg = ClientMsg.handshakeAndLogin( username, password ) 
        if err_msg:
            ClientMsg.disconnect()
            ClientMsg.notify.error( err_msg )
            return err_msg
        
        #set no delay        
        ClientMsg.myConnection.setNoDelay(1)
        
        #some panda stuff
        ClientMsg.cReader.addConnection(ClientMsg.myConnection)

        #ok we connected to server        
        ClientMsg.notify.info( "Connected to server: %s", ClientMsg.myConnection.getAddress() )
        
            
            
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
            
        #TODO: net: ovdje se zna kad se klijent diskonektao tu treba reagirat nekak na to
        print "Disconnecting"
            
            
    @staticmethod
    def handshakeAndLogin( username, password ):

        s = ClientMsg.myConnection.getSocket()
        
        s.SendData('LOSH?')
        msg = ClientMsg.getData(s, 2)
        if not msg:
            return "Server not responsive."
        if msg != 'LOSH!':
            return msg

        s.SendData('Sterner?')
        msg = ClientMsg.getData(s, 2) 
        if not msg:
            return "Server not responsive."
        if msg != 'Regix!':
            return msg

        version_msg = COMMUNICATION_PROTOCOL_STRING + ':' + str(COMMUNICATION_PROTOCOL_VERSION)
        s.SendData( version_msg )
        msg = ClientMsg.getData(s, 2)
        if not msg:
            return "Server not responsive."
        if msg != HANDSHAKE_SUCCESS:
            return msg
        
        #handshake went ok, send username/pass
        s.SendData( pickle.dumps( (STERNER_LOGIN, username, password) ) )
        
        #now we expect LOGIN_SUCCESS and our player_id
        msg = ClientMsg.getData(s, 2)
        if not msg:
            return "Server not responsive."        
        try:
            split_msg = msg.split(":")
            
            #if this is NOT a LOGIN_SUCCESS message it is an error message, return it
            if split_msg[0] != LOGIN_SUCCESS:
                return msg
            
            #finally log in successful
            else:
                ClientMsg.player_id = int(split_msg[1])
                return None
            
        except:
            ClientMsg.notify.error( "Server sent a wrong message:%s", msg )
            return "Server sent a wrong message:" + msg
            

            
    @staticmethod
    def handleConnection():
        """Return True if connection is ok, returns False if there is no connection yet."""
        
        #if we are not connected just return False
        if not ClientMsg.myConnection:
            return False
       
        #check the if socket is alive, if not, disconnect everything and return false
        if not ClientMsg.myConnection.getSocket().Active():
            ClientMsg.notify.error( "Lost connection to server: %s", ClientMsg.ip_address )
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
                ClientMsg.notify.info("Client received a message:%s", msg)
                          
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
        ClientMsg.notify.debug("Client posted a message: %s", msg)


    @staticmethod
    def _debugSendMsg(msg):        
        if not ClientMsg.myConnection:
            return
                  
        print "DEBUG SEND MESSAGE:", msg
        datagram = NetDatagram()        
        datagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))   
        ClientMsg.cWriter.send(datagram, ClientMsg.myConnection)
        ClientMsg.notify.debug("Client posted a message: %s", msg)

    
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
        ClientMsg._sendMsg( (END_TURN,0) )
        
    @staticmethod
    def ping():
        ClientMsg._sendMsg( (PING, time.time()) )
        
        
    @staticmethod
    def undefMsg1( value = 0 ):
        ClientMsg._sendMsg( (UNDEFINED_MSG_1, value ) )
        
    @staticmethod
    def undefMsg2( value = 0 ):
        #ClientMsg._sendMsg( (UNDEFINED_MSG_2, value ) )
        ClientMsg._sendMsg( (STERNER_ID, START_NEW_GAME, 'base2', 1000, [ 17, 18 ] ), True )


    #-----------------------STERNER MESSAGES---------------------------------------
    @staticmethod
    def enterGame( game_id ):
        ClientMsg.game_id = game_id
        ClientMsg._sendMsg( (STERNER_ID, ENTER_GAME) )
        
        
    @staticmethod
    def getAllFinishedGames():
        ClientMsg._sendMsg( (STERNER_ID, ALL_FINISHED_GAMES ), True )
                
    @staticmethod
    def startNewGame( map, budget, players, public_game, game_name ):
        ClientMsg._sendMsg( (STERNER_ID, START_NEW_GAME, map, budget, players, public_game, game_name ), True )
        
    @staticmethod
    def acceptGame( game_id ):
        ClientMsg._sendMsg( (STERNER_ID, ACCEPT_GAME, game_id ), True )

    @staticmethod
    def declineGame( game_id ):
        ClientMsg._sendMsg( (STERNER_ID, DECLINE_GAME, game_id ), True )

    @staticmethod
    def refreshGameLists():
        ClientMsg._sendMsg( (STERNER_ID, REFRESH_MY_GAME_LISTS ), True )
         
