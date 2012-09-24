# Prerequisites:  cx_oracle
from cx_Oracle import *
import datetime
import glob
import os
import copy 

"""
DB_SCHEMA_OWNER = 'krav'
DB_SCHEMA_PASS = 'goon666'
DB_IP = '127.0.0.1'
DB_PORT = '1521'
DB_SID = 'XE'
"""

DB_SCHEMA_OWNER = 'straindb'
DB_SCHEMA_PASS = 'straindb'
DB_IP = '178.79.164.4'
DB_PORT = '1521'
DB_SID = 'XE'


class DBApi():
    
    def __init__(self):
        self.conn = Connection(user=DB_SCHEMA_OWNER, password=DB_SCHEMA_PASS, dsn=makedsn(DB_IP, DB_PORT, DB_SID), threaded = True)
        
    def close(self):
        self.conn.close()
    
    def getLast3News(self):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, NEWS_DATE, TITLE, TEXT FROM ' \
                    '(SELECT ID, NEWS_DATE, TITLE, TEXT, ROWNUM FROM STR_NEWS ORDER BY ID DESC)' \
                    ' WHERE ROWNUM <= 3'
                    )
        row = cur.fetchall()
        cur.close()
        return row   
    
    def createPlayer(self, email, username, password):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)        
        try:
            cur.execute('INSERT INTO STR_PLAYER(ID, EMAIL, NAME, PASS) ' \
                        'VALUES (str_ply_seq.nextval,:email,:username,:password) ' \
                        'RETURNING ID INTO :id',
                        {'email' : email,
                         'username' : username,
                         'password' : password,
                         'id' : id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row inserted..."
        finally:
            cur.close()
        return id.getvalue() 
            
    def returnPlayer(self, username):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, EMAIL, NAME, PASS FROM STR_PLAYER WHERE name = :username', {'username':username})
        row = cur.fetchall()
        cur.close()
        if row:
            return row[0]
        return row
    
    def createGame(self, level_name, army_size, first_player_id, create_time, version, public, game_name):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        try:
            cur.execute('INSERT INTO STR_GAME(ID, MAP, BUDGET, TURN, ACTIVE_PLAYER_ID, STATUS, DATE_CREATED, VERSION, PUBLIC_GAME, GAME_NAME, RESERVED) ' \
                        'VALUES (str_gam_seq.nextval,:level_name, :army_size, 0, :first_ply_id, 0, :create_time, :version, :public_game, :game_name, 0) ' \
                        'RETURNING ID INTO :id',
                        {'level_name' : level_name,
                         'army_size' : army_size,
                         'first_ply_id' : first_player_id,
                         'create_time' : create_time,
                         'version' : version,
                         'public_game' : public,
                         'game_name' : game_name,
                         'id' : id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row inserted..."
        finally:
            cur.close()
        return int(id.getvalue())
    
    def addPlayerToGame(self, game_id, player_id, team, order, accepted):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        try:
            cur.execute('INSERT INTO STR_GAME_PLAYER(ID, GAM_ID, PLY_ID, TEAM_ID, ORDER_NUM, ACCEPTED) ' \
                        'VALUES (str_gpl_seq.nextval,:game_id, :player_id, :team, :order_num, :accepted) ' \
                        'RETURNING ID INTO :id',
                        {'game_id' : game_id,
                         'player_id' : player_id,
                         'team' : team,
                         'order_num' : order,
                         'accepted' : accepted,
                         'id' : id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row inserted..."
        finally:
            cur.close()
        return id.getvalue()
    
    def addGamePlayerEvent(self, game_id, player_id, event):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        cur.setinputsizes(event=CLOB)
        try:
            cur.execute('INSERT INTO STR_GPL_EVENT(ID, GPL_ID, EVENT, EVENT_DATE) ' \
                        'VALUES (str_get_seq.nextval,:gpl_id, :event, :event_date) ' \
                        'RETURNING ID INTO :id',
                        {'gpl_id' : self.getGamePlayer(game_id, player_id)[0],
                         'event' : event,
                         'event_date' : datetime.datetime.now(),
                         'id' : id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row inserted..."
        finally:
            cur.close()
        return id.getvalue()
    
    def addGameEvent(self, game_id, event):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        cur.setinputsizes(event=CLOB)
        try:
            cur.execute('INSERT INTO STR_GAME_EVENT(ID, GAM_ID, EVENT, EVENT_DATE) ' \
                        'VALUES (str_gat_seq.nextval,:gam_id, :event, :event_date) ' \
                        'RETURNING ID INTO :id',
                        {'gam_id' : game_id,
                         'event' : event,
                         'event_date' : datetime.datetime.now(),
                         'id' : id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row inserted..."
        finally:
            cur.close()
        return id.getvalue()    
   
    def getMyGames(self, player_id, status, accepted):
        cur = self.conn.cursor()
        cur.execute('SELECT GAM_ID, GAM_MAP, GAM_BUDGET, GAM_TURN, GAM_ACTIVE_PLAYER_ID, GAM_STATUS, GAM_DATE_CREATED, GAM_DATE_FINISHED, '\
                    'GAM_VERSION, GAM_PUBLIC_GAME, GAM_GAME_NAME, GAM_RESERVED '
                    'FROM STR_V_GAME_PLAYERS '\
                    'WHERE PLY_ID = :player_id AND GAM_STATUS = :status AND GPL_ACCEPTED = :accepted',
                    {'player_id' : player_id,
                     'status' : status,
                     'accepted' : accepted
                     }
                    )
        row = cur.fetchall()
        cur.close()
        return row        
   
    def getMyUnacceptedGames(self, player_id):
        return self.getMyGames(player_id, 0, 0)
    
    def getMyWaitingGames(self, player_id):
        return self.getMyGames(player_id, 0, 1)
    
    def getMyActiveGames(self, player_id):
        return self.getMyGames(player_id, 1, 1)
    
    def getGamePlayer(self, game_id, player_id):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, GAM_ID, PLY_ID, TEAM_ID, ORDER_NUM, ACCEPTED '\
                    'FROM STR_GAME_PLAYER '\
                    'WHERE PLY_ID = :player_id AND GAM_ID = :game_id',
                    {'player_id' : player_id,
                     'game_id' : game_id
                     }
                    )
        row = cur.fetchall()
        cur.close()
        if row:
            return row[0]
        return row
    
    def getGameAllPlayers(self, game_id):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, GAM_ID, PLY_ID, TEAM_ID, ORDER_NUM, ACCEPTED '\
                    'FROM STR_GAME_PLAYER '\
                    'WHERE GAM_ID = :game_id',
                    {'game_id' : game_id
                     }
                    )
        row = cur.fetchall()
        cur.close()
        return row  
    
    def getAllPlayers(self):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, NAME FROM STR_PLAYER ')
        row = cur.fetchall()
        cur.close()
        return row
    
    def getAllLevels(self):
        path = os.getcwd() + './../server/data/levels/*.txt'
        lst = []
        for infile in glob.glob( path ):
            h,t = os.path.split(infile)
            lst.append( t.split(".")[0] )
        return lst    

    def getAllActiveGames(self):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, MAP, BUDGET, TURN, ACTIVE_PLAYER_ID, STATUS, DATE_CREATED, DATE_FINISHED, VERSION, PUBLIC_GAME, GAME_NAME, RESERVED '\
                    'FROM STR_GAME WHERE STATUS != 2'
                    )
        row = cur.fetchall()
        cur.close()
        return row 
    
    def getAllFinishedGames(self):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, MAP, BUDGET, TURN, ACTIVE_PLAYER_ID, STATUS, DATE_CREATED, DATE_FINISHED, VERSION, PUBLIC_GAME, GAME_NAME, RESERVED '\
                    'FROM STR_GAME WHERE STATUS = 1'
                    )
        row = cur.fetchall()
        cur.close()
        return row 
    
    def getAllEmptyPublicGames(self):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, MAP, BUDGET, TURN, ACTIVE_PLAYER_ID, STATUS, DATE_CREATED, DATE_FINISHED, VERSION, PUBLIC_GAME, GAME_NAME, RESERVED '\
                    'FROM STR_GAME WHERE PUBLIC_GAME = 1 AND STATUS = 0'
                    )
        row = cur.fetchall()
        cur.close()
        return row
    
    def getGame(self, game_id, filter = False):
        if filter:
            sel = 'SELECT ID, MAP, BUDGET, TURN, ACTIVE_PLAYER_ID, STATUS, DATE_CREATED, DATE_FINISHED, VERSION, PUBLIC_GAME, GAME_NAME, RESERVED '\
                  'FROM STR_GAME WHERE ID = :game_id'
        else:
            sel = 'SELECT ID, MAP, BUDGET, TURN, ACTIVE_PLAYER_ID, STATUS, DATE_CREATED, DATE_FINISHED, VERSION, PUBLIC_GAME, GAME_NAME, RESERVED, PICKLED_ENGINE '\
                  'FROM STR_GAME WHERE ID = :game_id'

        cur = self.conn.cursor()
        cur.execute(sel,
                    {'game_id' : game_id
                     }
                    )
        row = cur.fetchall()
        cur.close()
        if row:
            return row[0]
        return row  
    
    def getGamePlayerEvents(self, game_id, player_id):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, GPL_ID, EVENT, EVENT_DATE '\
                    'FROM STR_GPL_EVENT WHERE GPL_ID = :gpl_id ORDER BY EVENT_DATE',
                    {'gpl_id' : self.getGamePlayer(game_id, player_id)[0]
                     }
                    )
        row = cur.fetchall()
        row = [(r[0], r[1], r[2].read(), r[3]) for r in row]
        cur.close()
        return row
    
    def getGameEvents(self, game_id):
        cur = self.conn.cursor()
        cur.execute('SELECT ID, GAM_ID, EVENT, EVENT_DATE '\
                    'FROM STR_GAME_EVENT WHERE GAM_ID = :gam_id ORDER BY EVENT_DATE',
                    {'gam_id' : game_id
                     }
                    )
        row = cur.fetchall()
        row = [(r[0], r[1], r[2].read(), r[3]) for r in row]
        cur.close()
        return row    
    
    def deleteGame(self, game_id):
        cur = self.conn.cursor()
        try:
            cur.execute('DELETE FROM STR_GAME_PLAYER ' \
                        'WHERE GAM_ID = :game_id',
                        {'game_id' : game_id,
                         }
                        )
            cur.execute('DELETE FROM STR_GAME ' \
                        'WHERE ID = :game_id',
                        {'game_id' : game_id,
                         }
                        )            
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row deleted..."
        finally:
            cur.close()
            
    def finishGame(self, game_id):
        #TODO: ogs: ovo ne provjerava da li je game vec u statusu = 2 i uvijek radi UPDATE
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        try:
            cur.execute('UPDATE STR_GAME SET STATUS = 2, DATE_FINISHED = :finish_time WHERE ID = :game_id',
                        {'finish_time' : datetime.datetime.now(),
                         'game_id' : game_id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row updated..."
        finally:
            cur.close()
        return id.getvalue()
        #TODO: krav: napravit i to da se pobrisu potezi od svakog plejera posebno, kad se dodaju, al da ostane od obs replaj            

    def playerAcceptGame(self, game_id, player_id):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        try:
            cur.execute('UPDATE STR_GAME_PLAYER SET ACCEPTED = 1 WHERE GAM_ID = :game_id',
                        {'game_id' : game_id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row updated..."
        finally:
            cur.close()
        return id.getvalue()        
    
    def finishAllGamesExceptVersion(self, ver):
        for g in self.getAllActiveGames():
            #set finish status and timestamp to each game that is not this version
            if g[5] != 2 and g[8] != ver:
                self.finishGame(g[0])
                
                #set all game_players accepted = 1 in these games
                for g_p in self.getGameAllPlayers(g[0]):
                    self.playerAcceptGame(g[0], g_p[0])
    
    def updateGamePlayer(self, game_player):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        try:
            cur.execute('UPDATE STR_GAME_PLAYER SET TEAM_ID = :team_id, ORDER_NUM = :order_num, ACCEPTED = :accepted WHERE GAM_ID = :gam_id AND PLY_ID = :ply_id',
                        {'team_id' : game_player[3],
                         'order_num' : game_player[4],
                         'accepted' : game_player[5],
                         'gam_id' : game_player[1],
                         'ply_id' : game_player[2]
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row updated..."
        finally:
            cur.close()
        return id.getvalue()  
    
    def updateGame(self, game):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        cur.setinputsizes(pickled_engine=CLOB)
        try:
            cur.execute('UPDATE STR_GAME SET MAP = :map, BUDGET = :budget, TURN = :turn, ACTIVE_PLAYER_ID = :act_ply_id, STATUS = :status,' \
                        'VERSION = :version_num, PUBLIC_GAME = :public_game, GAME_NAME = :game_name, RESERVED = :reserved, PICKLED_ENGINE = :pickled_engine ' \
                        ' WHERE ID = :game_id',
                        {'map' : game[1],
                         'budget' : game[2],
                         'turn' : game[3],
                         'act_ply_id' : game[4],
                         'status' : game[5],
                         'version_num' : game[8],
                         'public_game' : game[9],
                         'game_name' : game[10],
                         'reserved' : game[11],
                         'pickled_engine' : game[12],
                         'game_id' : game[0]
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row updated..."
        finally:
            cur.close()
        return id.getvalue()
    
    def setPickledEngine(self, game_id, pickled_engine):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        cur.setinputsizes(pickled_engine=CLOB)
        try:
            cur.execute('UPDATE STR_GAME SET PICKLED_ENGINE = :pickled_engine ' \
                        ' WHERE ID = :game_id',
                        {'pickled_engine' : pickled_engine,
                         'game_id' : game_id
                         }
                        )
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Pickled engine updated..."
        finally:
            cur.close()
        return id.getvalue()
    
    
    
    
    def deleteCustom(self):
        cur = self.conn.cursor()
        try:
            cur.execute('DELETE FROM STR_GPL_EVENT' )
            cur.execute('DELETE FROM STR_GAME_EVENT')            
            self.conn.commit()
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Row deleted..."
        finally:
            cur.close()    
    
    
if __name__ == "__main__":
    dbapi = DBApi()
    #player_id = dbapi.createPlayer('red@sterner.666', 'Blue', 'Blue')
    #print dbapi.returnPlayer('ogi')
    
    #game_id = dbapi.createGame('base2', 1000, dbapi.returnPlayer('ogi')[0], datetime.datetime.now(), '0.2', 1, 'Game_Name_03')
    #print game_id
    
    #game_player_id = dbapi.addPlayerToGame(21, dbapi.returnPlayer('ogi')[0][0], 0, 0, 1)
    #print game_player_id

    #game_player_id = dbapi.addPlayerToGame(21, dbapi.returnPlayer('krav')[0][0], 1, 1, 1)
    #print game_player_id
    
    for i in xrange(440,450):
        dbapi.deleteGame(i)
    #dbapi.deleteGame(423)
    #dbapi.deleteGame(443)
    print dbapi.getAllActiveGames()
    
    #dbapi.finishGame(21)
    #dbapi.finishAllGamesExceptVersion('0.1')

    #g_p = dbapi.getGamePlayer(21, 4)[0]
    #g_newp = (g_p[0], g_p[1], g_p[2], 0, 0, 1)
    #dbapi.updateGamePlayer(g_newp)

    #print dbapi.getLast3News()
    #print dbapi.getMyUnacceptedGames(dbapi.returnPlayer('ogi')[0][0])
    #print dbapi.getMyActiveGames(dbapi.returnPlayer('ogi')[0][0])
    #print dbapi.getMyWaitingGames(dbapi.returnPlayer('ogi')[0][0])
    #print dbapi.getGamePlayer(21, dbapi.returnPlayer('ogi')[0][0])
    #print dbapi.getGameAllPlayers(21)
    #print dbapi.getAllPlayers()
    #print dbapi.getAllLevels()
    #print dbapi.getAllActiveGames()
    #print dbapi.getAllFinishedGames()
    #print dbapi.getAllEmptyPublicGames()
    #print dbapi.getGame(21, True)
    
    #gm = dbapi.getGame(143, False)
    #gm = list(gm)
    #gm[12] = None
    #gm = tuple(gm)
    #dbapi.updateGame(gm)
    
    #dbapi.setPickledEngine(101, 'asd')
    
    #dbapi.addGamePlayerEvent(121,22, 'asd')
    #print dbapi.getGamePlayerEvents(161, 22)
    #print dbapi.getGameEvents(161)
    #dbapi.deleteCustom()
    dbapi.close()
    