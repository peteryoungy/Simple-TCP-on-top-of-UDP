import socket

# create udp socket
serverPort = 10027
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind(('', serverPort))
print("The server is ready to receive")

# receive sth
message, clientAddress = serverSocket.recvfrom(1024)
print(message, clientAddress)

