'''
Created on 22 Sep 2012

@author: krav
'''
import cPickle as pickle
import os

RED_ID = 22
BLUE_ID = 0

GAME_EVENTS_FILE_NAME = "db_proxy_game_events"
PLAYER_EVENTS_FILE_NAME = "db_proxy_player_"
PICKLED_ENGINE_FILE_NAME = "db_pickled_engine"


class DBLocalProxyApi():
    
    def __init__(self):
        #self.conn = Connection(user=DB_SCHEMA_OWNER, password=DB_SCHEMA_PASS, dsn=makedsn(DB_IP, DB_PORT, DB_SID), threaded = True)
        pass
        
    def close(self):
        #self.conn.close()
        pass



    def getGameAllPlayers(self, game_id):
        return [ (0, 0, RED_ID, 1, 1, 1), (0, 0, BLUE_ID, 1, 1, 1)  ]



    def getGame(self, game_id, filter = False):
        pickled = self.getPickledEngine()
        if not pickled:
            os.remove( GAME_EVENTS_FILE_NAME )
            os.remove( PLAYER_EVENTS_FILE_NAME + str(RED_ID) )
            os.remove( PLAYER_EVENTS_FILE_NAME + str(BLUE_ID) )
            
        return ( -1, "level2", 1000, 1, RED_ID, 0, 0, 0, '0.1', 0, "local test game", 0, pickled )

    
    
    def getGamePlayerEvents(self, game_id, player_id):
        print "getting gpe"
        fname = PLAYER_EVENTS_FILE_NAME + str(player_id)
        
        try:
            f = open( fname )
            lst = pickle.load(f)
            f.close()
            print "returning gpe"
            return lst
        except:
            print "returning gpe - empty"
            return []
    
    
    
    def addGamePlayerEvent(self, game_id, player_id, event):
        print "adding gpe"
        fname = PLAYER_EVENTS_FILE_NAME + str(player_id) 
        
        lst = self.getGamePlayerEvents(game_id, player_id)
        lst.append(event)
        
        f = open( fname, "w" )
        pickle.dump(lst, f)
        f.close()
        print "added game player event"

    
    def getGameEvents(self, game_id):
        print "getting ge"
        try:
            f = open( GAME_EVENTS_FILE_NAME )
            lst = pickle.load(f)
            f.close()
            print "returning ge"
            return lst
        except:
            print "returning ge - empty"
            return []        
            
    
    
    def addGameEvent(self, game_id, event):
        print "adding ge"
        lst = self.getGameEvents(game_id)
        lst.append(event)
        
        f = open( GAME_EVENTS_FILE_NAME, "w" )
        pickle.dump(lst, f)
        f.close()        
        print "added game event"
        

    def getPickledEngine(self):
        print "getting pickled"
        try:
            f = open( PICKLED_ENGINE_FILE_NAME )
            lst = pickle.load(f)
            f.close()
            print "returning pickled"
            return lst
        except:
            print "returning pickled - empty"
            return None        
        
        
        
    def setPickledEngine(self, game_id, pickled_engine):
        print "writing pickled"
        f = open( PICKLED_ENGINE_FILE_NAME, "w" )
        f.write( pickled_engine)
        f.close()
        print "set pickled engine"

    
if __name__ == "__main__":
    db_api = DBLocalProxyApi()
    
    
    db_api.close()
    