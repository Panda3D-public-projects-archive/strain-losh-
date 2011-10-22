'''
Created on 4.10.2011.

@author: krav
'''
import sys
import cPickle as pickle
from pandac.PandaModules import *
# TODO: krav (by ogs): Daj sredi ovaj wild import
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import engine as Engine


IP_ADDRESS = 'localhost'
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
    
     
    
    @staticmethod
    def startServer():
        EngMsg.cManager = QueuedConnectionManager() #@UndefinedVariable
        EngMsg.cListener = QueuedConnectionListener(EngMsg.cManager, 0) #@UndefinedVariable
        EngMsg.cReader = QueuedConnectionReader(EngMsg.cManager, 0) #@UndefinedVariable
        EngMsg.cWriter = ConnectionWriter(EngMsg.cManager, 0) #@UndefinedVariable
        
  
        backlog = 5
        tcpSocket = EngMsg.cManager.openTCPServerRendezvous(TCP_PORT , backlog)        
        
        EngMsg.cListener.addConnection(tcpSocket)
    
    @staticmethod
    def close():
        for client in EngMsg.activeConnections:
            EngMsg.cManager.closeConnection(client)
            Engine.notify.info("Closing connection with:%s", client.getAddress())
    
    @staticmethod
    def handleConnections():
        
        #check for new connections
        if EngMsg.cListener.newConnectionAvailable():
        
            rendezvous = PointerToConnection() #@UndefinedVariable
            netAddress = NetAddress() #@UndefinedVariable
            newConnection = PointerToConnection() #@UndefinedVariable
        
            if EngMsg.cListener.getNewConnection(rendezvous, netAddress, newConnection):
                newConnection = newConnection.p()
                newConnection.setNoDelay(1)
                EngMsg.activeConnections.append( ( newConnection, newConnection.getAddress() ) ) # Remember connection
                EngMsg.cReader.addConnection(newConnection)     # Begin reading connection        
                Engine.notify.info("Client connected:%s", netAddress )

                   
        #check for diconnects
        for connection, address in EngMsg.activeConnections[:]:   
            if not connection.getSocket().Active():
                print "Client disconnected:", address
                Engine.notify.info("Client diconnected:%s", address)
                EngMsg.cListener.removeConnection( connection )
                EngMsg.cReader.removeConnection( connection )
                EngMsg.cManager.closeConnection( connection )
                EngMsg.activeConnections.remove( ( connection, address ) )
                
    @staticmethod
    def broadcastMsg(msg):

        # broadcast a message to all clients
        for client, address in EngMsg.activeConnections: 
            myPyDatagram = PyDatagram()
            myPyDatagram.addString(pickle.dumps(msg))
            if EngMsg.cWriter.send(myPyDatagram, client):
                Engine.notify.debug( "Sent client:%s\tmessage:%s" , address, msg )
        
    
    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        if EngMsg.cReader.dataAvailable():
            datagram = NetDatagram() #@UndefinedVariable
            if EngMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)
                msg = pickle.loads(dgi.getString())
                  
                #print datagram.getConnection()
                #for c, a in EngMsg.activeConnections:
                #    print c
                #    if datagram.getConnection() == c:
                #        print "isto je"
                
                
                Engine.notify.info("Engine received a message:%s, from:%s", msg, str(datagram.getConnection().getAddress()))
                #return (msg, datagram.getConnection() )
                return msg
          
        return None
          
    @staticmethod
    def _sendMsg(msg):
        try:
            EngMsg.broadcastMsg(msg)
        except:
            Engine.notify.critical("Could not send message to clients, reason :%s", sys.exc_info()[1])
            return
        
        Engine.notify.info("Engine posted a message: %s" , msg )
    
    @staticmethod
    def move(unit_id, move_actions):
        EngMsg._sendMsg(Msg(Msg.MOVE, (unit_id, move_actions))) 
                                                                      
    @staticmethod
    def sendState(engine_state):
        EngMsg._sendMsg(Msg(Msg.ENGINE_STATE, engine_state))
    
    @staticmethod
    def sendLevel(pickled_level):
        EngMsg._sendMsg(Msg(Msg.LEVEL, pickled_level))
    
    @staticmethod
    def sendErrorMsg(error_msg):
        EngMsg._sendMsg(Msg(Msg.ERROR, error_msg))
    
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
    
    @staticmethod
    def connect():
        print "Trying to connect to server:",IP_ADDRESS,":",TCP_PORT
        
        ClientMsg.cManager = QueuedConnectionManager() #@UndefinedVariable
        ClientMsg.cReader = QueuedConnectionReader(ClientMsg.cManager, 0) #@UndefinedVariable
        ClientMsg.cWriter = ConnectionWriter(ClientMsg.cManager, 0) #@UndefinedVariable
        
        # how long until we give up trying to reach the server?
        timeout_in_miliseconds = 3000  # 3 seconds               
        ClientMsg.myConnection = ClientMsg.cManager.openTCPClientConnection(IP_ADDRESS, TCP_PORT, timeout_in_miliseconds)
        
        if ClientMsg.myConnection:
            ClientMsg.myConnection.setNoDelay(1)
            ClientMsg.cReader.addConnection(ClientMsg.myConnection)
            
            #print( dir(ClientMsg.myConnection) )
            print "Client connected to:", ClientMsg.myConnection.getAddress()
            return 1
            
        return 0
            
    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        if not ClientMsg.myConnection:        
            if not ClientMsg.connect():
                return None
            
        if ClientMsg.cReader.dataAvailable():
            datagram = PyDatagram()                          
            if ClientMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)                
                msg = pickle.loads(dgi.getString())                
                #TODO: ogs: sredit da ti ovdje pise u GraphicsEngine, nemres stavit import jer je onda ciklicki povezano
                Engine.notify.info("Client received a message:%s", msg)
                                
                return msg
        return None    
    
    @staticmethod
    def sendMsg(msg):
        
        if not ClientMsg.myConnection:
            if not ClientMsg.connect():
                return
        
        datagram = PyDatagram()        
        datagram.addString(pickle.dumps(msg, pickle.HIGHEST_PROTOCOL))   
        ClientMsg.cWriter.send(datagram, ClientMsg.myConnection)

        
    @staticmethod
    def close():
        ClientMsg.cManager.closeConnection(ClientMsg.myConnection)
    
    @staticmethod
    def _sendMsg(msg):
        
        if not ClientMsg.myConnection:        
            ClientMsg.connect()

        ClientMsg.sendMsg(msg)
                 
        #TODO: ogs: sredit da ti ovdje pise u GraphicsEngine, nemres stavit import jer je onda ciklicki povezano
        #GraphicsEngine.logger.debug("Client posted a message: %s", msg)
        Engine.notify.debug("Client posted a message: %s", msg)

    
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
        
        
