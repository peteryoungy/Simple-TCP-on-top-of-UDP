import socket

# note: set source ip/port
# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)
#
# print(hostname, local_ip)
# serverPort = 10025
serverAddress = ('192.168.192.134', 41192)

# establish a UDP socket
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# send
clientSocket.sendto("hello".encode(), serverAddress)
print("The first message has been sent")
# print(clientSocket.recvfrom(512)[0].decode())


clientSocket.close()