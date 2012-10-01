'''
Created on 22 Sep 2012

@author: krav
'''
import cPickle as pickle
import os
import zlib
import traceback

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
            try:
                os.remove( GAME_EVENTS_FILE_NAME )
                os.remove( PLAYER_EVENTS_FILE_NAME + str(RED_ID) )
                os.remove( PLAYER_EVENTS_FILE_NAME + str(BLUE_ID) )
            except:
                pass
            
        return ( -1, "level2", 1000, 1, RED_ID, 0, 0, 0, '0.1', 0, "local test game", 0, pickled )

    
    
    def getGamePlayerEvents(self, game_id, player_id):
        fname = PLAYER_EVENTS_FILE_NAME + str(player_id)
        
        try:
            f = open( fname, "rb" )
            buf = f.read()
            unz = zlib.decompress(buf)
            lst = pickle.loads(unz)
            f.close()
            return lst
        except:
            return []
    
    
    
    def addGamePlayerEvent(self, game_id, player_id, event):
        fname = PLAYER_EVENTS_FILE_NAME + str(player_id) 
        
        lst = self.getGamePlayerEvents(game_id, player_id)
        lst.append(event)
        
        f = open( fname, "wb" )
        st = pickle.dumps(lst)
        zst = zlib.compress(st)
        f.write(zst)
        f.close()

    
    def getGameEvents(self, game_id):
        try:
            f = open( GAME_EVENTS_FILE_NAME, "rb" )
            buf = f.read()
            unz = zlib.decompress(buf)
            lst = pickle.loads(unz)
            f.close()
            return lst
        except:
            return []        
            
    
    
    def addGameEvent(self, game_id, event):
        lst = self.getGameEvents(game_id)
        lst.append(event)
        
        f = open( GAME_EVENTS_FILE_NAME, "wb" )
        st = pickle.dumps(lst)
        zst = zlib.compress(st)
        f.write( zst )
        f.close()        
        

    def getPickledEngine(self):
        try:
            f = open( PICKLED_ENGINE_FILE_NAME, "rb" )
            buf = f.read()
            unz = zlib.decompress(buf)
            lst = pickle.loads(unz)
            f.close()
            return lst
        except:
            print traceback.format_exc()
            return None        
        
        
        
    def setPickledEngine(self, game_id, pickled_engine):
        f = open( PICKLED_ENGINE_FILE_NAME, "wb" )
        st = pickle.dumps( pickled_engine )
        zst = zlib.compress(st)
        f.write(zst)
        f.close()


    
if __name__ == "__main__":
    db_api = DBLocalProxyApi()
    
    
    db_api.close()
    