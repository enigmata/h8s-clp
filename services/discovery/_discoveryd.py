# Hive discovery daemon: Waits forever for discovery pings, returning various attributes of its host

DISCOVERY_PORT = 50000

import sys
from socket import *

udp_receive_socket = socket( AF_INET, SOCK_DGRAM )
udp_receive_socket.bind( ( '', DISCOVERY_PORT ))

udp_reply_socket = socket( AF_INET, SOCK_DGRAM )
udp_reply_socket.bind( ( '', 0 ) )

while 1:
    ping_msg, discoverer = udp_receive_socket.recvfrom( 4096, 0 )
    print( discoverer, ping_msg )
    udp_reply_socket.sendto( 'Pi', discoverer )

# from SocketServer import UDPServer, BaseRequestHandler
# 
# class DiscoveryPingHandler( BaseRequestHandler ):
#     def handle( self ):
#         print( 'Discovery ping from', self.client_address )
#         print( 'Discovery daemon', self.server.server_address )
#         ping_msg, udp_socket = self.request
#         udp_socket.sendto( 'Discovered: ', self.server.server_address ) 
# 
# if __name__ == '__main__':
#     discovery_server = UDPServer( ( '', DISCOVERY_PORT ), DiscoveryPingHandler )
#     discovery_server.serve_forever()
# 
