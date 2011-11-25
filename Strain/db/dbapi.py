# Prerequisites: sqlalchemy, cx_oracle
import sqlalchemy as sql

class DBApi():
    def __init__(self):
        self.db = sql.create_engine('oracle://ognjenk:ogs@zg-invplusdb:1521/inv10dev')
        
    def connect(self):
        self.conn = self.db.connect()
        
    def getUser(self, username):
        return self.conn.execute("select id, name, password from player where name = "+username)
        
#MAIN
dbapi = DBApi()
dbapi.connect()
result = dbapi.getUser("'ultramarines'")
print result.keys()
print result.returns_rows # vraca True i ako nema redaka u upitu
for row in result:
    print  row