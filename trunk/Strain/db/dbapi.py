# Prerequisites:  cx_oracle
from cx_Oracle import *

class DBApi():
    def __init__(self):
        self.conn = Connection(user='ognjenk', password='ogs', dsn=makedsn('zg-invplusdb', '1521', 'inv10dev'))
    
    def close(self):
        self.conn.close()
    
    def createPlayer(self, email, username, password):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)        
        cur.execute('INSERT INTO STR_PLAYER(ID, EMAIL, USERNAME, PASSWORD) ' \
                    'VALUES (str_ply_seq.nextval,:email,:username,:password) ' \
                    'RETURNING ID INTO :id',
                    {'email' : email,
                     'username' : username,
                     'password' : password,
                     'id' : id
                    }
                   )
        cur.close()
        self.conn.commit()
        return id.getvalue()        
    
    def deletePlayer(self, username):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM STR_PLAYER ' \
                    'WHERE username = :username',
                    {'username' : username
                    }
                   )
        cur.close()
        self.conn.commit()
    
    def returnPlayer(self, username):
        cur = self.conn.cursor()
        cur.execute("SELECT ID, EMAIL, USERNAME, PASSWORD FROM STR_PLAYER WHERE username = :username", {'username':username})
        row = cur.fetchall()
        cur.close()
        return row
    
    def returnLevel(self, name):
        cur = self.conn.cursor()
        select = "SELECT ID, NAME, DESCRIPTION, MAP FROM STR_LEVEL " \
                 "WHERE NAME = :name"
        return_rows = []
        try:
            cur.execute(select, {'name':name})
            for row in cur:
                id = row[0]
                name = row[1]
                description = row[2]
                map = row[3].read()
                return_rows.append((id, name, description, map))
        except DatabaseError, exception:
            error, = exception
            print "Oracle error: ", error.message
        else:
            print "Data processed."
        finally:
            # Housekeeping...
            cur.close()
        return return_rows
    
    def createGame(self, level_name):
        level_row = self.returnLevel(level_name)
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        cur.execute('INSERT INTO STR_GAME(ID, LVL_ID) ' \
                    'VALUES (str_gam_seq.nextval,:lvl_id) ' \
                    'RETURNING ID INTO :id',
                    {'lvl_id' : level_row[0][0],
                     'id' : id
                    }
                   )
        cur.close()
        self.conn.commit()
        self.addPlayerToGame(id.getvalue(), 'REPLAY', 0)
        return id.getvalue()
        
    def addPlayerToGame(self, game_id, player_name, team, order):
        player_id = self.returnPlayer(player_name)[0][0]
        cur = self.conn.cursor()
        id = cur.var(NUMBER)        
        cur.execute('INSERT INTO STR_GAME_PLAYERS(ID, GAM_ID, PLY_ID, TEAM_ID) ' \
                    'VALUES (str_gpl_seq.nextval,:gam_id, :ply_id, :team_id, :order)' \
                    'RETURNING ID INTO :id',
                    {'gam_id' : game_id,
                     'ply_id' : player_id,
                     'team_id' : team,
                     'order' : order,
                     'id' : id
                    }
                   )
        cur.close()
        self.conn.commit()
        return id.getvalue()        
                
    def returnPlayerInGame(self, game_id, player_name):
        cur = self.conn.cursor()
        cur.execute('SELECT GPL.ID, GPL.GAM_ID, GPL.PLY_ID, GPL.TEAM_ID, ' \
                    'GPL.ORDER, GPL.VICTORY_POINTS ' \
                    'FROM STR_GAME_PLAYERS GPL, STR_PLAYER PLY ' \
                    'WHERE GPL.PLY_ID = PLY.ID AND PLY.username = :username AND GPL.GAM_ID = :gam_id', 
                    {'username' : player_name,
                     'gam_id' : game_id
                    }
                   )
        row = cur.fetchall()
        cur.close()
        return row
        
    def addMessage(self, game_id, player_name, message_type, message, turn_number):
        cur = self.conn.cursor()
        id = cur.var(NUMBER)
        game_player_id = self.returnPlayerInGame(game_id, player_name)[0]
        cur.execute('INSERT INTO STR_GPL_MESSAGE(ID, GPL_ID, MESSAGE_ID, MESSAGE, TURN_NUMBER) ' \
                    'VALUES (str_gpm_seq.nextval,:gpl_id, :message_id, :message, :turn_number)' \
                    'RETURNING ID INTO :id',
                    {'gpl_id' : game_player_id,
                     'message_id' : message_type,
                     'message' : message,
                     'turn_number' : turn_number,
                     'id' : id
                    }
                   )
        cur.close()
        self.conn.commit()
        return id.getvalue()        
        
#MAIN
dbapi = DBApi()
#dbapi.createPlayer('ogi@loshdev', 'ogi', 'ogi')
#dbapi.createPlayer('krav@loshdev', 'krav', 'krav')
#dbapi.createPlayer('vjeko@loshdev', 'vjeko', 'vjeko')
print dbapi.returnPlayer('ogi') == None
#id = dbapi.createGame('base2')
#dbapi.addPlayerToGame(int(id), 'ogi', 1)
#dbapi.addPlayerToGame(int(id), 'krav', 2)