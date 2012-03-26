# Prerequisites: sqlalchemy, cx_oracle
from cx_Oracle import *

class DBApi():
    def __init__(self):
        self.conn = Connection(user='ognjenk', password='ogs', dsn=makedsn('zg-invplusdb', '1521', 'inv10dev'))
    
    def close(self):
        self.conn.close()
    
    def createPlayer(self, email, username, password):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO STR_PLAYER(ID, EMAIL, USERNAME, PASSWORD) ' \
                    'VALUES (str_ply_seq.nextval,:email,:username,:password)',
                    {'email' : email,
                     'username' : username,
                     'password' : password
                    }
                   )
        cur.close()
        self.conn.commit()
    
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
        
#MAIN
dbapi = DBApi()
#dbapi.createPlayer('asd', 'asd', 'asd')
print dbapi.returnLevel('base2')