'''
Created on 29 May 2012

@author: krav
'''
import random
import sys
import os
import glob
import copy     
import time


PLAYERS = "players.txt"
PLAYERS_HEADER = "#0:id, 1:email, 2:name, 3:pass"

GAMES = "games.txt"
GAMES_HEADER = "#0:id, 1:map, 2:budget, 3:turn, 4:active_player_id, 5:status (0=waiting,1=in progress, 2=finished),\n\
# 6:date created, 7:date finished, 8:version, 9:public, 10:name, 11:reserved, 10:pickled engine"

GAME_PLAYERS = "game_players.txt"
GAME_PLAYERS_HEADER = "#0:id, 1:game_id, 2:ply_id, 3:team_id, 4:order_num, 5:accepted"

NEWS = "news.txt"
NEWS_HEADER = "#0:id, 1:date, 2:title, 3:text"


class DBProxyApi():
    
    def __init__(self):
        
        self.players = self.loadFile(PLAYERS)
        self.games = self.loadFile(GAMES)
        self.game_players = self.loadFile(GAME_PLAYERS)
        self.news = self.loadFile(NEWS)
        
        
        
    def loadFile(self, fname):
        lst = []
        player_file = open("./../db/" + fname, "r")
        for line in player_file:
            if line[0] == '#':
                continue
            
            line = line.strip()
            line = line.split(',')
            
            #try to convert everything to int or float if it has a dot in it
            conv_line = []
            for entry in line:
                conv_entry = entry
                try:
                    if '.' in entry:
                        conv_entry = float( entry )
                    else:
                        conv_entry = int( entry )
                except:
                    pass
                    
                conv_line.append( conv_entry )
            
            lst.append(conv_line)
            
        player_file.close()
        return lst
        
    
    def close(self):
        pass
    
    
    def getLast3News(self):
        return self.news[-3:]
    
    
    def createPlayer(self, email, username, password):
        rnd = random.randint( 1000, sys.maxint )
        self.players.append( [rnd,email,username,password] )
        self.saveToFile(self.players, PLAYERS, PLAYERS_HEADER)
    
    
    def saveToFile(self, list, fname,header):
        f = open("./../db/" + fname, "w")
        f.write(header)
        #f.write('\n')
        for a in list:
            line = "\n"
            for b in a:
                line += str(b)
                line += ','
            line = line[:-1]
            #line += '\n'
            #print line
            f.write( line )
        f.close()
        
    
    def returnPlayer(self, username):
        for p in self.players:
            if p[2] == username:
                return p
    
    
    def getMyActiveGames(self, player_id):
        lst = []
        for g in self.game_players:
            if g[2] == player_id:
                game = self.getGame(g[1])
                if game:
                    if game[5] == 1:
                        lst.append( game )
        return lst

    
    
    def getGamePlayer(self, game_id, player_id):
        for p in self.game_players:
            if p[1] == game_id and p[2] == player_id:
                return p
        return None
    
    
    def updateGamePlayer(self, game_player):
        for p in self.game_players:
            if p[1] == game_player[1] and p[2] == game_player[2]:

                for i in xrange( 0, len(game_player) ):
                    p[i] = game_player[i]
        self.saveToFile(self.game_players, GAME_PLAYERS, GAME_PLAYERS_HEADER)
    
    
    def updateGame(self, game):
        for g in self.games:
            if g[0] == game[0]:
                for i in xrange( 0, len(game) ):
                    g[i] = game[i]
        self.saveToFile(self.games, GAMES, GAMES_HEADER)
    
    
    def getMyUnacceptedGames(self, player_id):
        game_id_list = []
        ret_lst = []
        for p in self.game_players:
            if p[2] == player_id and p[5] == 0:
                game_id_list.append( p[1] )
        for g in self.games:
            if g[0] in game_id_list:
                ret_lst.append(g)
        return ret_lst
    
    
    def getMyWaitingGames(self, player_id):
        game_id_list = []
        ret_lst = []
        for p in self.game_players:
            if p[2] == player_id and p[5] == 1:
                game_id_list.append( p[1] )
        for g in self.games:
            if g[0] in game_id_list and g[5] == 0:
                ret_lst.append(g)
        return ret_lst
    
    
    
    def getGameAllPlayers( self, game_id ):
        lst = []
        for p in self.game_players:
            if p[1] == game_id:
                lst.append(p)
        return lst
    
    
    def getAllFinishedGames(self):
        lst = []
        for game in self.games:
            if game[5]:
                lst.append(game)
        return lst


    def getAllEmptyPublicGames(self):
        lst = []
        for game in self.games:
            if game[9] and game[5] == 0:
                lst.append(game)
        return lst

    
    def getGame(self, game_id):
        for g in self.games:
            if g[0] == game_id:
                return g

    
    def getAllLevels(self):
        path = os.getcwd() + './../server/data/levels/*.txt'
        lst = []
        for infile in glob.glob( path ):
            infile = infile.split('\\')[-1]
            lst.append( infile.split(".")[0] )
        return lst
    
    
    def getAllPlayers(self):
        ret_lst = []
        for p in self.players:
            print p
            ret_lst.append( [ p[0], p[2] ] )
            
        return ret_lst
    
    
    def createGame(self, level_name, army_size, first_player_id, create_time, version, public, game_name):
        id = self.games[-1][0] + 1
        self.games.append( [id, level_name, army_size, 0, first_player_id, 0, create_time, 0, version, public, game_name, 0, 0] )
        self.saveToFile(self.games, GAMES, GAMES_HEADER)
        return id

        
    def addPlayerToGame(self, game_id, player_id, team, order, accepted):
        id = self.game_players[-1][0] + 1
        self.game_players.append( [id, game_id, player_id, team, order, accepted] )
        self.saveToFile(self.game_players, GAME_PLAYERS, GAME_PLAYERS_HEADER)


    def deleteGame(self, game_id):
        for g in self.games[:]:
            if g[0] == game_id:
                self.games.remove(g)
        self.saveToFile(self.games, GAMES, GAMES_HEADER)
        
        for g_p in self.game_players[:]:
            if g_p[1] == game_id:
                self.game_players.remove(g_p)
        self.saveToFile(self.game_players, GAME_PLAYERS, GAME_PLAYERS_HEADER)


    def finishAllGamesExceptVersion(self, ver):
        for g in self.games:
            #set finish status and timestamp to each game that is not this version
            if g[5] != 2 and g[8] != ver:
                self.finishGame(g[0])
                
                #set all game_players accepted = 1 in these games
                for g_p in self.game_players:
                    if g_p[1] == g[0]:
                        g_p[5] = 1
                
        self.saveToFile(self.game_players, GAME_PLAYERS, GAME_PLAYERS_HEADER)
        

    def finishGame(self, game_id):
        g = self.getGame(game_id)
        g[5] = 2
        g[7] = time.time()
        #TODO: krav: napravit i to da se pobrisu potezi od svakog plejera posebno, kad se dodaju, al da ostane od obs replaj
        self.saveToFile(self.games, GAMES, GAMES_HEADER)


    def getAllActiveGames(self):
        lst = []
        for g in self.games:
            if g[5] != 2:
                lst.append(g)
        return lst

    
if __name__ == "__main__":
    dbapi = DBProxyApi()
    #dbapi.createPlayer("emailv@@@vvv", "ihaaa", "po")
    #print dbapi.returnPlayer('ogi')
    #print dbapi.getGame(100)
    #game_id = dbapi.createGame("test", 1000)
    #dbapi.addPlayerToGame(game_id, dbapi.returnPlayer('Red')[0], 0, 0)
    #dbapi.addPlayerToGame(game_id, dbapi.returnPlayer('ogi')[0], 1, 1)
    #print dbapi.getAllLevels()
    #all_players = dbapi.getAllPlayers()
    #print [ x for x,y in all_players ]
    #print dbapi.getMyActiveGames( 17 ) 
    #print dbapi.getAllFinishedGames()
    
    #g_p = copy.deepcopy(dbapi.getGamePlayer(100, 17))
    #g_p[3] = 0
    #g_p[4] = 0
    #g_p[5] = 1
    #dbapi.updateGamePlayer(g_p)
    
    #print dbapi.getGameAllPlayers( 100 )
    
    #g = copy.deepcopy(dbapi.getGame(101))
    #g[1] = 'halls0'
    #g[2] = 666
    #dbapi.updateGame(g)
    
    #print dbapi.getMyUnacceptedGames( 17 )
    #games = dbapi.getMyUnacceptedGames( 17 )
    #print [ g[0] for g in games  ]
    
    #dbapi.deleteGame( 104 )
    #dbapi.finishAllGamesExceptVersion( 0.1 )
    
    #print dbapi.getAllPublicGames()
    
    #print dbapi.getMyWaitingGames( 111 )
    
    print dbapi.getLast3News()
    
    print dbapi.news
    
    dbapi.close()
    
#MAIN
#dbapi = DBApi()
#print dbapi.returnPlayer('ogi')
#dbapi.addMessage(6, 'ogi', 1, 'asd', 1)
#dbapi.createPlayer('ogi@loshdev', 'ogi', 'ogi')
#dbapi.createPlayer('krav@loshdev', 'krav', 'krav')
#dbapi.createPlayer('vjeko@loshdev', 'vjeko', 'vjeko')
#id = dbapi.createGame('base2', 1000)
#dbapi.addPlayerToGame(int(id), 'ogi', 1, 1)
#dbapi.addPlayerToGame(int(id), 'krav', 2, 1)