'''
Created on 4.10.2011.

@author: krav
'''
from multiprocessing.queues import Queue
import Engine
import sys



class Message:


    types = { 'move' : 1,           #values - (unit_id, old_position, new_position)  
              #'ap_change' : 2,      #values - new value
              'engine_shutdown' : 3,#no additional values
              'error' : 4,          #value - error message
              'engine_state' : 5,    #values - dictionary of values
              'level' : 6           #values - level
             }
    
    
    def decode(self, value = None ):
        for key in Message.types.keys():
            if Message.types[key] == value:
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
        EngMsg._putInQueue( Message( Message.types['move'], (unit_id, move_actions) ) ) 
                                                                      
    @staticmethod
    def sendState( engine_state ):
        EngMsg._putInQueue( Message( Message.types['engine_state'], engine_state ) )
    
    @staticmethod
    def sendLevel( pickled_level ):
        EngMsg._putInQueue( Message( Message.types['level'], pickled_level ) )
    
    @staticmethod
    def sendErrorMsg( error_msg ):
        EngMsg._putInQueue( Message( Message.types['error'], error_msg ) )
    
    
    
    
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
        ClientMsg._putInQueue( Message( Message.types['engine_state'] ) )
    
    @staticmethod
    def getLevel():
        ClientMsg._putInQueue( Message( Message.types['level'] ) )
    
    @staticmethod
    def move( unit_id, new_position, orientation ):
        ClientMsg._putInQueue( Message( Message.types['move'], { 'unit_id':unit_id, 
                                                                'new_position':new_position, 
                                                                'orientation':orientation } ) ) 

    @staticmethod
    def shutdownEngine():
        ClientMsg._putInQueue( Message( Message.types['engine_shutdown'] ) ) 
        
        
        
        