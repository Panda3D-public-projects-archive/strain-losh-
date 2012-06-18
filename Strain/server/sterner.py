'''
Created on 16 May 2012

@author: krav
'''
import sys
sys.path.append('./../client')
sys.path.append('./src')
sys.path.append('./../db')
import engine
import threading
import sys
import time
from server_messaging import *
from util import *
from engine import EngineThread
from dbproxyapi import DBProxyApi as DBApi
import traceback


STERNER_TIME_LIMIT = 0 #seconds, if it is 0 than it is infinite

#messages from clients that do no go through to engines, their lifespan
MESSAGE_TIMEOUT = 10 #seconds

ENGINE_IDLE_MAX = 0 #in seconds, if it is 0 than it is infinite


class LockedDict:
    
    def __init__(self):
        self.lock = threading.Lock()
        
        # K-game id, V- ( msg, timestamp )
        self.msg_dict = {}
        
        

    def getMyMsgs(self, id ):
        msg_list = []
        tmp_msgs = []

        #try to acquire lock
        if not self.lock.acquire( False ):
            return None
            
        try:            
            #if there are no msg for us return
            if id not in self.msg_dict:
                return None
    
            #if the list is empty return
            if not self.msg_dict[id]:
                return None
    
            #if there are msgs, get them first and delete them from dict
            tmp_msgs = self.msg_dict[id]

            del self.msg_dict[id]

            #release lock
        finally:
            self.lock.release()

        #go through message_list and remove timestamps
        for msg in tmp_msgs:
            msg_list.append(msg[0])


        return msg_list

    
    
    def putMsg(self, id, msg):
        #try to acquire lock
        if not self.lock.acquire( False ):
            return False
            
        try:            
            #if there are no msgs for this id create new list
            if id not in self.msg_dict:
                self.msg_dict[id] = []
                
            #append this msg
            self.msg_dict[id].append( (msg, time.time()) )
        finally:
            self.lock.release()

        return True


    
    def purgeOldMessages(self):
        #try to acquire lock
        if not self.lock.acquire( False ):
            return
        try:
            #go through all message lists  
            for k in self.msg_dict.keys():
                msg_lst = self.msg_dict[k]
                #go through all messages in a message list
                for msg in msg_lst[:]:
                    #if this is old message, remove it
                    if time.time() - msg[1] >= MESSAGE_TIMEOUT:
                        msg_lst.remove( msg )
                    if not msg_lst:
                        del self.msg_dict[k]
                
        finally:
            self.lock.release()

###################################################################################    
###################################################################################    
###################################################################################    
###################################################################################    
class Sterner:
    
    
    def __init__(self):
        self.notify = Notify( 'Sterner.log' )
        
        #database api
        self.db_api = DBApi()
        
        #start network server
        self.network = Network( self, self.notify, self.db_api )
        self.network.startServer()
        
        
        #dict to save logged in players 
        # K: player_id , V: panda connection
        self.logged_in_players = {}
        
        self.notify.info( "Sterner started." )
    
        #so we dont have different versions of games all at once
        self.db_api.finishAllGamesExceptVersion( COMMUNICATION_PROTOCOL_VERSION )
        
        #dequeue for sending msgs to network... format:(player_id, (msg))
        self.to_network = collections.deque()
        
        #dequeue for sending messages for engines and EngineHandlerThread, if msg[0] == STERNER_ID, than it is for handler
        self.msgs4engines = collections.deque()
        
        #dequeue in which EngineHandlerThread puts messages for Sterner
        self.fromHandler = collections.deque()
        
        self.engine_handler = EngineHandlerThread( self.fromHandler, self.msgs4engines, self.to_network, self.notify, self.db_api )
        self.engine_handler.start()
        
        
    
    def start( self ):
        
        #for time limit - debug option if we want to stop sterner automatically after some time
        t = time.time()
        
        #-----------================------main loop---------=====================---------
        #-----------================------main loop---------=====================---------
        #-----------================------main loop---------=====================---------
        while True:
        
            #needs to be called every tick to handle connections
            self.network.handleConnections()
        
            #get msg from network
            tmp_msg = self.network.readMsg()
            
            if tmp_msg:
                #print "sterner dobio:",tmp_msg
                try:
                    msg, source = tmp_msg

                    #check if this message is for sterner or not
                    if msg[0] == STERNER_ID:
                        self.handleSternerMsg( msg[1:], source )
                    else:
                        self.msgs4engines.append( msg )
                except:
                    self.notify.error("Error with message:%s\ninfo:%s", str(tmp_msg), traceback.format_exc() )
            
            
            #check to_network for messages, and if there are any send them to players
            try:
                while True:
                    src, msg = self.to_network.popleft() 
                    self.network._sendMsg( msg, self.logged_in_players[ src ] )
            #IndexError if there is nothing to pop
            #KeyError if engine is sending messages to disconnected/unknown players, we just ignore this
            except (IndexError, KeyError):
                pass
            
            
            #check for messages from Handler
            try:
                while True:
                    msg = self.fromHandler.popleft()
                    self.handleHandlerMessage( msg )
            except IndexError:
                pass
            
            
            #behave nicely with cpu            
            time.sleep(0.1) 
        
            #if we set the option for sterner auto shutdown, check the time period
            if STERNER_TIME_LIMIT and time.time() - t > STERNER_TIME_LIMIT:
                break
        #---------================--------main loop--------==================----------
        #---------================--------main loop--------==================----------
        #---------================--------main loop--------==================----------
        
        #shutdown everything we can
        self.engine_handler.stop = True
        self.network.stopServer()

        time.sleep(3)
        
        
        
    def handleHandlerMessage(self, msg):
        
        if msg[0] == NEW_GAME_STARTED:
            player_id = msg[1]
            source = self.logged_in_players[ player_id ]
            #we don't know if it was a public game or private game so refresh both lists
            self.network._sendMsg( (MY_WAITING_GAMES, self.db_api.getMyWaitingGames( player_id )), source )
            self.network._sendMsg( (EMPTY_PUBLIC_GAMES, self.db_api.getAllEmptyPublicGames()), source )
            
            

    
    def getIdFromConnection(self, connection):
        for player_id in self.logged_in_players:
            if self.logged_in_players[player_id] == connection:
                return player_id
        return None
    
    
    
    def handleSternerMsg(self, message, source):
        
        if message[0] == START_NEW_GAME:
            level = message[1]
            budget = message[2]
            player_ids = message[3]
            public_game = message[4]
            game_name = message[5]
            player_id = self.getIdFromConnection(source)            
            
            #check if there are at least 2 players
            if len( player_ids ) < 2:
                self.network._sendMsg( (ERROR, "Not enough players"), source )
                return
            
            #check if level is ok
            all_levels = self.db_api.getAllLevels()
            if level not in all_levels:
                self.network._sendMsg( (ERROR, "Wrong level"), source )
                return
                 
            #TODO: krav: check if budget is ok
            
            #if this is a private game check if player_ids are ok
            if not public_game:
                all_player_ids = [ int(x) for x,y in self.db_api.getAllPlayers() ]
                for p_id in player_ids:
                    if p_id not in all_player_ids:
                        self.network._sendMsg( (ERROR, "Wrong player id:%d"%p_id), source )
                        return
            #if public game, game creator's id must be one of the players, all others must be 0
            else:
                if player_id not in player_ids:
                        self.network._sendMsg( (ERROR, "You have to be in the game"), source )
                        return
                tmp_player_ids = player_ids[:]
                tmp_player_ids.remove( player_id )
                
                for p in tmp_player_ids:
                    if p != 0:
                        self.network._sendMsg( (ERROR, "You cannot assign players other than yourself in public games"), source )
                        return
                        
                    
            #check game name
            if not game_name:
                if not public_game:
                    game_name = 'Private game on ' + level 
                else:
                    game_name = 'Public game on ' + level
                

            #create the game and all players in the database, set game creator accept status to 1                    
            game_id = self.db_api.createGame(level, budget, player_id, time.time(), COMMUNICATION_PROTOCOL_VERSION, public_game, game_name )
            for i in xrange(0, len(player_ids)):
                if player_ids[i] == player_id:
                    self.db_api.addPlayerToGame(game_id, player_ids[i], i, i, 1)
                else:
                    self.db_api.addPlayerToGame(game_id, player_ids[i], i, i, 0)
            

            self.msgs4engines.append( (STERNER_ID, START_NEW_GAME, game_id, player_id ) )
            return
                
                
        elif message[0] == ALL_FINISHED_GAMES:
            self.network._sendMsg( (ALL_FINISHED_GAMES, self.db_api.getAllFinishedGames()), source )
            return
                
                
        elif message[0] == REFRESH_MY_GAME_LISTS:
            self.sendSternerData(source)
            return
                
                
                
        elif message[0] == DECLINE_GAME:
            game_id = message[1]
            player_id = self.getIdFromConnection(source)

            game = self.db_api.getGame(game_id, filter=True)

            #if there is no such game            
            if not game:
                self.network._sendMsg( (ERROR, "No such game."), source )
                return

            #if this is a public game, you cant decline that
            if game[9]:
                self.network._sendMsg( (ERROR, "You cannot decline public games, just don't join :)"), source )
                return

            #if this game already started
            if game[5] != 0: 
                self.network._sendMsg( (ERROR, "This game already started, if you want to concede do it from inside the game"), source )
                return

            #if you are not a player in this game
            game_player = self.db_api.getGamePlayer(game_id, player_id)
            if not game_player:
                self.network._sendMsg( (ERROR, "You cannot decline, you are not even part of this game!"), source )
                return
                
            #ok so delete the game
            self.db_api.deleteGame(game_id)
            
            #refresh his unaccepted games list
            self.network._sendMsg( (MY_UNACCEPTED_GAMES, self.db_api.getMyUnacceptedGames( player_id )), source )
            
            
            
        elif message[0] == ACCEPT_GAME:
            game_id = message[1]
            player_id = self.getIdFromConnection(source)

            game = self.db_api.getGame(game_id)
            
            #if there is no such game            
            if not game:
                self.network._sendMsg( (ERROR, "No such game."), source )
                return

            #check if this game already started or is finished            
            if game[5] == 1:
                self.network._sendMsg( (ERROR, "Game already started"), source )
                return
            elif game[5] == 2:
                self.network._sendMsg( (ERROR, "Game finished"), source )
                return
                
                
            #if this is a public game
            if game[9]:
                #if we are already in this game, return error
                game_player = self.db_api.getGamePlayer(game_id, player_id)
                if game_player:
                    self.network._sendMsg( (ERROR, "You are already in this game"), source )
                    return
                
                #find first empty slot, set this players id in its stead
                game_player = self.db_api.getGamePlayer(game_id, 0)
                game_player[2] = player_id
                #we update game_player later

            #if this is a private game
            else:
                #check if this player really did not accept this game yet
                game_player = self.db_api.getGamePlayer(game_id, player_id)
                if game_player[5] == 1:
                    self.network._sendMsg( (ERROR, "Already accepted this game"), source )
                    return
            
            #update this player's acceptance, for both cases (public/private game)
            game_player[5] = 1
            self.db_api.updateGamePlayer( game_player )
            
            #we accepted this game
            self.network._sendMsg( (ACCEPT_GAME, game_id), source )
            
            #refresh unaccepted games list
            self.network._sendMsg( (MY_UNACCEPTED_GAMES, self.db_api.getMyUnacceptedGames( player_id )), source )

            #try to see if this is the last player accepting and if so start the game            
            #if at least 1 player did not accept, return
            for player in self.db_api.getGameAllPlayers( game_id ):
                if player[5] == 0:
                    #refresh waiting games list
                    self.network._sendMsg( (MY_WAITING_GAMES, self.db_api.getMyWaitingGames( player_id )), source )                    
                    return 
            
            #ok all players accepted, start this game
            game[5] = 1
            self.db_api.updateGame(game)
            
            #refresh active games 
            self.network._sendMsg( (MY_ACTIVE_GAMES, self.db_api.getMyActiveGames( player_id )), source )            
            return
                

        elif message[0] == PING:
            self.network._sendMsg( (PONG, time.time()), source )
            return

        else:
            self.notify.error("Undefined message:%s", str(message))

        pass
                
                
                
    def sendSternerData(self, source):
        player_id = self.getIdFromConnection(source)
        self.network._sendMsg( (ALL_PLAYERS, self.db_api.getAllPlayers()), source )
        self.network._sendMsg( (ALL_LEVELS, self.db_api.getAllLevels()), source )            
        self.network._sendMsg( (MY_ACTIVE_GAMES, self.db_api.getMyActiveGames( player_id )), source )
        self.network._sendMsg( (MY_UNACCEPTED_GAMES, self.db_api.getMyUnacceptedGames( player_id )), source )
        self.network._sendMsg( (MY_WAITING_GAMES, self.db_api.getMyWaitingGames( player_id )), source )
        self.network._sendMsg( (EMPTY_PUBLIC_GAMES, self.db_api.getAllEmptyPublicGames()), source )
        self.network._sendMsg( (NEWS_FEED, self.db_api.getLast3News()), source )
        
                
                
    def playerConnected(self, player_id, source):
        #if this player already has a connection, disconnect him
        if player_id in self.logged_in_players:
            self.network.disconnect( self.logged_in_players[player_id] )

        #remember this player-connection
        self.logged_in_players[player_id] = source

        #send this new player everything he needs
        self.sendSternerData(source)


    def playerDisconnected(self, source):
        #go through all logged in players
        for pid in self.logged_in_players.keys():
            
            #if we find the one with this connection
            if self.logged_in_players[ pid ] == source:
                
                #remove him from the dict
                del self.logged_in_players[ pid ]
                return

    
    
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
class EngineHandlerThread( threading.Thread ):
    
    def __init__( self, from_handler, msgs4engines, to_network, notify, db_api ):
        threading.Thread.__init__(self)
        
        self.name = "EngineHandlerThread"

        self.to_sterner = from_handler
        self.msgs4engines = msgs4engines
        self.to_network = to_network
        self.notify = notify
        self.db_api = db_api

        #LockedDict for distributing messages to Engine threads
        self.from_network = LockedDict()

        #main dict where we will hold engine threads k:game_id, v:EngineThread
        self.engine_threads = {}
        
        self.setDaemon(True)
        self.stop = False
        
    
    
    def run(self):
        
        #first start EngineThread for each game that is active and not yet finished
        for game in self.db_api.getAllActiveGames():
            self.startNewEngineThread(game[0])
            
        
        ###############################################################################################
        ###############################################################################################
        while True:

            if self.stop:
                self.stopAllThreads()
                break

            #tmp list for messages
            msg_list = []
            
            #get everything from msgs4engines in msg_list
            try:
                while True:
                    tmp_msg = self.msgs4engines.popleft()
                    msg_list.append(tmp_msg)
            except IndexError:
                pass
                
            #now go through all the messages we got 
            for msg in msg_list:

                try:
                    #if this is a message from sterner
                    if msg[0] == STERNER_ID:
                        self.sternerMsg(msg[1:])
    
                    #this is a message for engines
                    else:
                        
                        #check if thread with this id is alive, if not ignore this message
                        if self.checkGameExists(msg[0]):
                            #try to put it in from_network
                            if not self.from_network.putMsg( msg[0], msg[1:] ):
                                #if we couldn't, put it back in msgs4engines for later                        
                                self.msgs4engines.append( msg )

                except:
                    self.notify.error("EgineHandlerThread - exception when handling this message:%s\ninfo:%s", str(msg), traceback.format_exc() )


            #handle Threads
            self.handleThreads()

            #do housekeeping on from_network()
            self.from_network.purgeOldMessages()


            #be nice
            time.sleep(0.1)
        ###############################################################################################
        ###############################################################################################
        
        
        
    def sternerMsg(self, msg):
        
        if msg[0] == START_NEW_GAME:
            game_id = msg[1]
            creator_id = msg[2]
            
            #first check if this EngineThread is running and if so log an error 
            if game_id in self.engine_threads:
                self.notify.error("Trying to start a game in progress! game_id:%s", str(game_id))
                return
            else:
                #there is no active thread for this game, try to resume one from db
                if self.startNewEngineThread(game_id):
                    self.to_network.append( (creator_id, (NEW_GAME_STARTED, game_id) ) )
                    self.to_sterner.append( (NEW_GAME_STARTED, creator_id) )
            
            
        
    def checkGameExists(self, game_id):
        #first check if there is an active engine thread with this game_id
        if game_id in self.engine_threads:
            return True

        #than check database if we need to resume an engine thread
        for game in self.db_api.getAllActiveGames():
            if game_id == game[0]:
                #resume this game
                return self.startNewEngineThread(game_id)
        
        self.notify.error("Couldn't find game:%s in active games!",str(game_id))
        return False
        
        
    def startNewEngineThread(self, game_id):
        tmp_thread = EngineThread( game_id, self.from_network, self.to_network, self.notify, self.db_api )
        tmp_thread.start()
        #give it time to init
        time.sleep(0.1)
        if tmp_thread.isAlive():
            self.engine_threads[game_id] = tmp_thread
            return True

        self.notify.error("Couldn't start a new thread with game id:%s", str(game_id))

        #who knows what happened, try to kill it by brute force
        try:
            tmp_thread.__stop()
            tmp_thread.stop = False
        except:
            pass

        return False
        
        
    def handleThreads(self):
        for t in self.engine_threads.keys():
            thrd = self.engine_threads[t]
            #see if any thread is dead, if so than delete if from dict
            if not thrd.isAlive():
                del self.engine_threads[t]
        
            #if this thread has been idle too long, suspend it and delete it from active list        
            if ENGINE_IDLE_MAX and time.time() - thrd.last_active_time > ENGINE_IDLE_MAX:
                thrd.suspend = True 
                del self.engine_threads[t]
        
        
        
    def stopAllThreads(self):
        for thr in self.engine_threads.values():
            thr.stop = True
    

