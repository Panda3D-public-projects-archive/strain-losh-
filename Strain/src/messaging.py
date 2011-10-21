'''
Created on 4.10.2011.

@author: krav
'''
import sys
import cPickle as pickle
from pandac.PandaModules import *
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
        if self.type == 5 or self.type == 6 or self.type == 8:
            return "type:%d  value:" % (self.type)
        return "type:%d  value:%s" % (self.type, self.values)



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
            Engine.logger.info("Closing connection with:%s", client)
    
    @staticmethod
    def listenForConnections():
        
        if EngMsg.cListener.newConnectionAvailable():
        
            rendezvous = PointerToConnection() #@UndefinedVariable
            netAddress = NetAddress() #@UndefinedVariable
            newConnection = PointerToConnection() #@UndefinedVariable
        
            if EngMsg.cListener.getNewConnection(rendezvous, netAddress, newConnection):
                newConnection = newConnection.p()
                EngMsg.activeConnections.append(newConnection) # Remember connection
                EngMsg.cReader.addConnection(newConnection)     # Begin reading connection    
                Engine.logger.info("Client connected:%s::%s,", netAddress, newConnection)
                print "Client connected:", newConnection
    
    
    @staticmethod
    def broadcastMsg(msg):

        # broadcast a message to all clients
        for client in EngMsg.activeConnections: 
            myPyDatagram = PyDatagram()
            myPyDatagram.addString(pickle.dumps(msg))
            if EngMsg.cWriter.send(myPyDatagram, client):
                Engine.logger.debug("Sent client message:%s", msg )
        
    
    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        if EngMsg.cReader.dataAvailable():
            datagram = PyDatagram()
            if EngMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)
                msg = pickle.loads(dgi.getString())
                Engine.logger.info("Engine received a message:%s", msg)
                return msg
          
        return None
          
    @staticmethod
    def _sendMsg(msg):
        try:
            EngMsg.broadcastMsg(msg)
        except:
            Engine.logger.critical("Could not send message to clients, reason :%s", sys.exc_info()[1])
    
        Engine.logger.info("Engine posted a message: %s", msg)
        
    
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
        print "trying to connect to server."
        ClientMsg.cManager = QueuedConnectionManager() #@UndefinedVariable
        ClientMsg.cListener = QueuedConnectionListener(ClientMsg.cManager, 0) #@UndefinedVariable
        ClientMsg.cReader = QueuedConnectionReader(ClientMsg.cManager, 0) #@UndefinedVariable
        ClientMsg.cWriter = ConnectionWriter(ClientMsg.cManager, 0) #@UndefinedVariable
        
        backlog = 5
        ClientMsg.tcpSocket = ClientMsg.cManager.openTCPServerRendezvous(TCP_PORT, backlog)
        ClientMsg.cListener.addConnection(ClientMsg.tcpSocket)
        
         # how long until we give up trying to reach the server?
        timeout_in_miliseconds = 3000  # 3 seconds               
        ClientMsg.myConnection = ClientMsg.cManager.openTCPClientConnection(IP_ADDRESS, TCP_PORT, timeout_in_miliseconds)
        
        if ClientMsg.myConnection:
            print "Client connected to:", ClientMsg.myConnection
            ClientMsg.cReader.addConnection(ClientMsg.myConnection)

    @staticmethod
    def readMsg():
        """Return the message, if any, or None if there was nothing to read"""
        if not ClientMsg.myConnection:        
            ClientMsg.connect()
        
        if ClientMsg.cReader.dataAvailable():            
            datagram = PyDatagram()                          
            if ClientMsg.cReader.getData(datagram):
                dgi = PyDatagramIterator(datagram)                
                msg = pickle.loads(dgi.getString())                
                #TODO: ogs: sredit da ti ovdje pise u GraphicsEngine, nemres stavit import jer je onda ciklicki povezano
                #GraphicsEngine.logger.info("Client received a message:", msg)
                Engine.logger.info("Client received a message:%s", msg.type)
                                
                return msg
          
        return None    
    
    @staticmethod
    def sendMsg(msg):
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
        Engine.logger.debug("Client posted a message: %s", msg)

    
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
        
        
