import sys

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class FBAClient(DatagramProtocol):
    p_server_ip = '127.0.0.1' 
    p_server_port = None

    def __init__(self, port):
        self.p_server_port = port
    
    def startProtocol(self):
        print("Sending data to host {} port {}".format(self.p_server_ip, self.p_server_port))
        self.transport.connect(self.p_server_ip, int(self.p_server_port))
        # sending test data to server 
        self.transport.write(b"foo:$10")
        self.transport.write(b"bar:$30")
        self.transport.write(b"foo:$20")
        self.transport.write(b"bar:$20")
        self.transport.write(b"foo:$30")
        self.transport.write(b"bar:$10")

    def datagramReceived(self, data, host):
        print("Transaction successful (data: {}, host: {})".format(data, host))

    def connectionRefused(self):
        print("No server listening {}:{}".format(self.p_server_ip, self.p_server_port))

"""
Main - the entry point
"""
if __name__ == '__main__':
    reactor.listenUDP(0, FBAClient(sys.argv[1]))
    reactor.run()


