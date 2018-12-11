# cmpe273-assignment3

## Prerequisite:
- Apart from what libraries required by simple-fba implementation, additional requirements for this assignemnt are listed inre requirements.txt

## Implementation:
- fba_client.py publishes messages to fba_server.py using udp
- fab_server.py consumes messsages over udp and push for consensus
    - internal communication betweeen severs uses udp through custom UDPTransportProtocol implementation in network.py
    - fab_server.py is customization of simple-fba-simulator.py
- once ballot is accepted, message is parsed and stored to pickledb
