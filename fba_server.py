import json
import time
import argparse
import asyncio
import collections
import logging
import sys
import pickledb
from uuid import uuid1
from threading import Thread

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from fba_consensus import Consensus
from network import (
    BaseServer,
    UDPTransport,
    LocalTransport,
    Message,
    Node,
    Quorum,
)
from util import (
    log,
)

MESSAGE = None
loop = None
host = '127.0.0.1'
iport = None
sport = None
client_config = None
client_node = None
this_node_name = None
msg_proceeded_by_this_node = []
allowed_ports = [65101, 3000, 3000, 3001, 3002, 3003]

async def check_message_in_storage(node):
    global MESSAGE

    if check_message_in_storage.is_running:
        return

    check_message_in_storage.is_running = True

    found = list()
    log.main.info('%s: checking input message was stored: %s', node.name, MESSAGE)
    while len(found) < len(servers):
        for node_name, server in servers.items():
            if node_name in found:
                continue

            storage = server.consensus.storage

            is_exists = storage.is_exists(MESSAGE)
            if is_exists:
                log.main.critical(
                    '> %s: is_exists=%s state=%s ballot=%s',
                    node_name,
                    is_exists,
                    server.consensus.ballot.state,
                    # json.dumps(storage.ballot_history.get(MESSAGE.message_id), indent=2),
                    '',  # json.dumps(storage.ballot_history.get(MESSAGE.message_id)),
                )
                found.append(node_name)

            await asyncio.sleep(0.01)

    await asyncio.sleep(3)

    check_message_in_storage.is_running = False

    #MESSAGE = Message.new(uuid1().hex)
    #servers['n0'].transport.send(nodes['n0'].endpoint, MESSAGE.serialize(client_node))
    #log.main.info('inject message %s -> n0: %s', client_node.name, MESSAGE)

    return

check_message_in_storage.is_running = False

class TestConsensus(Consensus):
    def reached_all_confirm(self, ballot_message):
        asyncio.ensure_future(check_message_in_storage(self.node))
        return

class Server(BaseServer):
    node = None
    consensus = None

    def __init__(self, node, consensus, *a, **kw):
        assert isinstance(node, Node)
        assert isinstance(consensus, Consensus)

        super(Server, self).__init__(*a, **kw)

        self.node = node
        self.consensus = consensus

    def __repr__(self):
        return '<Server: node=%(node)s consensus=%(consensus)s>' % self.__dict__

    def message_receive(self, data_list):
        super(Server, self).message_receive(data_list)

        for i in data_list:
            log.server.debug('%s: hand over message to consensus: %s', self.name, i)
            self.consensus.receive(i)

        return

NodeConfig = collections.namedtuple(
    'NodeConfig',
    (
        'name',
        'endpoint',
        'port',
        'threshold',
    ),
)

class FBAServerMain(DatagramProtocol):
    server_ip = '127.0.0.1' 
    server_port = None

    def __init__(self, port):
        self.server_port = port

    def datagramReceived(self, data, address):
        # if repeat message received, ignore
        #print("{} in {}".format(str(data), msg_proceeded_by_this_node))
        if data.hex() in msg_proceeded_by_this_node:
            return
        msg_proceeded_by_this_node.append(data.hex())

        print("Data %s received from %s on port %s" % (repr(data), repr(address), self.server_port))
        self.transport.write(data, address)
        client_addr = int(address[1])
        next_port = self.server_port + 1
        if next_port > 3003:
            next_port = 3000
        next_name_name = node_name_port_mapping[next_port]
        #MESSAGE = Message.new(str(data))
        #servers[next_name_name].transport.send(nodes[next_name_name].endpoint, MESSAGE.serialize(nodes[this_node_name]))
        servers[next_name_name].transport.send(nodes[next_name_name].endpoint, data)
        log.main.info('Injected message %s -> %s: %s', client_node.name, this_node_name, str(data))
        # store data to db
        sdata = str(data)
        index = sdata.find(':')
        key = str(sdata[2:index])
        value = int(sdata[index+2 : len(sdata)-1])
        if db.get(key):
            old_value=db.get(key)
            new_value=old_value+value
            db.set(key,new_value)
        else:
            db.set(key,value)
        
def start_udp_listerner():
    reactor.listenUDP(iport, FBAServerMain(iport))
    reactor.run(installSignalHandlers=0)

"""
Main - the entry point
"""
if __name__ == '__main__':
    # setting defaults
    log.set_level(logging.DEBUG) # log level at INFO
    nodes = 4 # number of validator nodes in the same quorum
    trs = 80 # check threshold

    client_config = NodeConfig('client', None, None, None)
    client_node = Node(client_config.name, client_config.endpoint, None, client_config.port,)
    log.main.debug('client node created: %s', client_node)

    node_name_port_mapping = dict()
    nodes_config = dict()
    for i in range(nodes):
        name = 'n%d' % i
        port = 3000 + i
        endpoint = 'sock://127.0.0.1:%d' % port
        nodes_config[name] = NodeConfig(name, endpoint, port, trs)
        node_name_port_mapping[port] = name

    quorums = dict()
    for name, config in nodes_config.items():
        validator_configs = filter(lambda x: x.name != name, nodes_config.values())

        quorums[name] = Quorum(
            config.threshold,
            list(map(lambda x: Node(x.name, x.endpoint, None, x.port), validator_configs)),
        )
    
    nodes = dict()
    transports = dict()
    consensuses = dict()
    servers = dict()

    loop = asyncio.get_event_loop()

    for name, config in nodes_config.items():
        nodes[name] = Node(name, config.endpoint, quorums[name], config.port)
        log.main.debug('nodes created: %s', nodes)

        #transports[name] = UDPTransport(name, config.endpoint, loop, host, config.port)
        transports[name] = LocalTransport(name, config.endpoint, loop)
        log.main.debug('transports created: %s', transports)

        consensuses[name] = TestConsensus(nodes[name], quorums[name], transports[name])
        log.main.debug('consensuses created: %s', consensuses)

        servers[name] = Server(nodes[name], consensuses[name], name, transport=transports[name])
        log.main.debug('servers created: %s', servers)
    
    sport = sys.argv[1]
    iport = int(sport)
    allowed_ports.remove(iport) # for this server
    # start this node server
    this_node_name = node_name_port_mapping[iport]
    servers[this_node_name].start()

    try:
        # load db
        db_name = 'assignment3_'+sport+'.db'
        db = pickledb.load(db_name, True)
        db.dump()
        
        # start udp listener on a separate thread
        threads = []
        t = Thread(target=start_udp_listerner)
        threads.append(t)
        t.start()
        
        #MESSAGE = Message.new(uuid1().hex)
        #servers[this_node_name].transport.send(nodes[this_node_name].endpoint, MESSAGE.serialize(client_node))
        #log.main.info('Injected message %s -> %s: %s', client_node.name, this_node_name, MESSAGE)

        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        log.main.debug('goodbye~')
        sys.exit(1)
    finally:
        loop.close()