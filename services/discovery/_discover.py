# discover: Broadcast to all hive discovery daemons and gather some minimal 
#           info on each discovered hive system

from socket import *

DISCOVERY_PORT = 50000

# Set up a UDP (datagram) socket to broadcast a hive discovery ping to each
# hive discovery daemon listening on the well-known DISCOVERY_PORT

udp_socket = socket( AF_INET, SOCK_DGRAM )
udp_socket.bind( ( '', 0 ) )
udp_socket.setsockopt( SOL_SOCKET, SO_BROADCAST, 1 )

# Broadcast out the discovery ping to all listening hive discovery daemons
udp_socket.sendto( 'hive_ping', ( '<broadcast>', DISCOVERY_PORT ))

# Retrieve identifying information from all discovered hive systems

while 1:
    hive_worker_data, hive_worker_address = udp_socket.recvfrom( 4096 )
    print( 'Discovered hive worker: ', hive_worker_address, 'info: ', hive_worker_data )


