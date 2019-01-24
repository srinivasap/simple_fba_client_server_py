# Simple FBA Client/Server Implementation with UPD Transport 

The FBA(Federated Byzantine Agreement) consensus protocol is the way to make agreement between untrusted network nodes. The well-known implementation of FBA in real world is the stellar blockchain network, which has the derived consensus, they called 'SCP'(Stellar Consensus Protocol).

Reference: https://github.com/spikeekips/simple-fba

## Prerequisite:
- Apart from what libraries required by simple-fba implementation, additional requirements for this assignemnt are listed in requirements.txt

## Implementation:
- fba_client.py publishes messages to fba_server.py using udp
- fab_server.py consumes messsages over udp and push for consensus
    - internal communication betweeen severs uses udp through custom UDPTransportProtocol implementation in network.py
    - fab_server.py is customization of simple-fba-simulator.py
- once ballot is accepted, message is parsed and stored to pickledb
