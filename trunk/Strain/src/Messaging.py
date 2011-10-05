'''
Created on 4.10.2011.

@author: krav
'''

from collections import deque


class Message:


    types = { 'move' : 1 #values - (unit_id, old_position, new_position)  
             }
    
    
    def decode(self, value ):
        for key in Message.types.keys():
            if Message.types[key] == value:
                return key

    
    
    def __init__(self, type, values ):
        self.type = type
        self.values = values

    def __repr__(self):
        return "type:%s  value:%s" % ( self.decode( self.type ), self.values )


class Messaging:
    
    __shared_state = {}
    
    
    queue_list = deque()
    
    
    def __init__(self):
        self.__dict__ = self.__shared_state
                
        pass
    
    
    @staticmethod
    def move( unit_id, old_position, new_position ):
        Messaging.queue_list.append( Message( Message.types['move'], ( unit_id, old_position, new_position ) ) )
    
    
        