'''
Created on 4.10.2011.

@author: krav
'''
from multiprocessing.queues import Queue
import Engine
import sys



class Msg:


    MOVE = 1                #values - list of move actions ('move',tile) followed by ('rotate',tile)
    NEW_TURN = 2            #value - turn number
    ENGINE_SHUTDOWN = 3     #no values
    ERROR = 4               #value - error message
    ENGINE_STATE = 5        #value - dictionary of values
    LEVEL = 6               #value - pickled level
    END_TURN = 7            #no values
    UNIT = 8                #value - pickled unit

    
    def decode(self, value = None ):
        for key in Msg.types.keys():
            if Msg.types[key] == value:
                return key

    
    
    def __init__(self, in_type, values = None ):
        self.type = in_type
        self.values = values

    def __repr__(self):
        return "type:%s  value:%s" % ( self.decode( self.type ), self.values )


class Messaging:
    
    __shared_state = {}
    
    
    #this queue will hold messages by engine for client
    client_queue = Queue()
    
    
    #this queue hold messages for engine
    engine_queue = Queue()
    
    
    def __init__(self):
        self.__dict__ = self.__shared_state
                
        pass
    
    




        
        
class EngMsg:
    
    
    @staticmethod
    def _putInQueue( msg ):
        try:
            Messaging.client_queue.put( msg, True, 2 )
        except:
            Engine.logger.critical("Could not put message in queue_for_client, reason :%s", sys.exc_info()[1] )
    
        Engine.logger.info("Engine posted a message: %s", msg)
        
    
    @staticmethod
    def move( unit_id, move_actions ):
        EngMsg._putInQueue( Msg( Msg.MOVE, (unit_id, move_actions) ) ) 
                                                                      
    @staticmethod
    def sendState( engine_state ):
        EngMsg._putInQueue( Msg( Msg.ENGINE_STATE, engine_state ) )
    
    @staticmethod
    def sendLevel( pickled_level ):
        EngMsg._putInQueue( Msg( Msg.LEVEL, pickled_level ) )
    
    @staticmethod
    def sendErrorMsg( error_msg ):
        EngMsg._putInQueue( Msg( Msg.ERROR, error_msg ) )
    
    @staticmethod
    def sendNewTurn( turn_num ):
        EngMsg._putInQueue( Msg( Msg.NEW_TURN, turn_num ) )
    
    
    @staticmethod
    def sendUnit( pickled_unit ):
        EngMsg._putInQueue( Msg( Msg.UNIT, pickled_unit ) )
    
class ClientMsg:
    
    
    @staticmethod
    def _putInQueue( msg ):
        try:
            Messaging.engine_queue.put( msg, True, 2 )
        except:
            Engine.logger.critical("Could not put message in queue_for_client, reason :%s", sys.exc_info()[1] )
    
        Engine.logger.debug("Client posted a message: %s", msg)


    
    @staticmethod
    def getEngineState():
        ClientMsg._putInQueue( Msg( Msg.ENGINE_STATE ) )
    
    @staticmethod
    def getLevel():
        ClientMsg._putInQueue( Msg( Msg.LEVEL ) )
    
    @staticmethod
    def move( unit_id, new_position, orientation ):
        ClientMsg._putInQueue( Msg( Msg.MOVE, { 'unit_id':unit_id, 
                                                                'new_position':new_position, 
                                                                'orientation':orientation } ) ) 

    @staticmethod
    def shutdownEngine():
        ClientMsg._putInQueue( Msg( Msg.ENGINE_SHUTDOWN ) ) 
        
    @staticmethod
    def endTurn():
        ClientMsg._putInQueue( Msg( Msg.END_TURN ) )
        
        