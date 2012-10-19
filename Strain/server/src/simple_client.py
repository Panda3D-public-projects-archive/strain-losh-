'''
Created on 18 Oct 2012

@author: krav
'''
from twisted.internet.protocol import Factory, BaseProtocol
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import Int16StringReceiver, IntNStringReceiver

class ConnectionToServer(Int16StringReceiver):

    def __init__(self, factory):
        self.factory = factory

    def makeConnection(self, transport):
        print "make connection, transport:", transport
        return BaseProtocol.makeConnection(self, transport)


    def stringReceived(self, string):
        print "string recv:", string
        

    def sendString(self, string):
        print "sending string:", string        
        #string = zlib.compress(string)
        
        return IntNStringReceiver.sendString(self, string)


    def connectionMade(self):
        print "connection made!"
        

    def connectionLost(self, reason):
        print "connection lost"
        reactor.stop() #@UndefinedVariable


class ChatFactory(Factory):

    def buildProtocol(self, addr):
        return ConnectionToServer(self)
    
    
def runEverySecond( fact ):
    print "a second has passed", fact.connections


def gotProtocol(p):
    #p.sendString("Hello")
        
    reactor.callLater(1, p.sendString, "LOSH?") #@UndefinedVariable
    reactor.callLater(1.2, p.sendString, "Sterner?") #@UndefinedVariable
    reactor.callLater(1.4, p.sendString, 'comm_version:0.2') #@UndefinedVariable
    #reactor.callLater(3, p.sendString, pickle.dumps(zlib) )
    reactor.callLater(1.6, p.sendString, "login,Red,Red") #@UndefinedVariable
    #reactor.callLater(5, p.transport.loseConnection)
    
    
if __name__ == "__main__":
    port = 8081
    point = TCP4ClientEndpoint(reactor, "localhost", port)
    fact = ChatFactory()
    d = point.connect(fact)
    d.addCallback(gotProtocol)    

    #l = task.LoopingCall(runEverySecond, fact)
    #l.start(1) # call every second
    
        
    print "trying port:",port
    reactor.run() #@UndefinedVariable



