import socket
import sys
from threading import Thread
import time
import struct
# import queue
import logging
from collections import deque

# # create udp socket
# serverPort = 10027
# serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# serverSocket.bind(('', serverPort))
# print("The server is ready to receive")
#
# # receive sth
# message, clientAddress = serverSocket.recvfrom(1024)
# print(message, clientAddress)

MSS  = 576


class Receiver:

    def __init__(self, file = 'files/write_to.txt',
                 listening_port = 12112,
                 dest_ip = '192.168.192.1',
                 dest_port = 12114):

        self.file_path = file
        self.recv_port = listening_port

        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.client_address = (dest_ip, dest_port)

        # constant
        self.UN_4BYTES_MOD = 4294967296

        # receive
        self.src_port = 11113
        self.client_address = (dest_ip, dest_port)
        self.data_recv = None

        # header
        self.header_length = 5
        self.is_ack = 1
        self.is_fin = 0

        self.expected_seq_num = 0

        # initialize socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', self.recv_port))

        # open the file
        self.file_handle = open(self.file_path,'w+')

        # logger
        self._logger = logging.getLogger()

        print("Init finished")


    def recv_handler(self):
        print("Server handler starts")
        while not self.is_fin:
            self.recv()

    def recv(self):

        print("Wait for receiving...")
        # self.data_recv, client_send_address = self.server_socket.recvfrom(MSS + 20)
        self.data_recv = self.server_socket.recv(MSS + 20)

        if self.is_corrupt():
            print("The packet is corrupt.")
            self.send_ack("")

            print("Send ACK with number: {ack_num}".format(
                ack_num = self.expected_seq_num
            ))
            return

        header = struct.unpack('!2H2L4H', self.data_recv[0:20])
        payload = self.data_recv[20:]
        content = payload.decode()

        # fin bit is 1
        if header[4] % 2:
            self._logger.debug("Receive a FIN")
            self.is_fin = 1
            self.send_ack("")
            print("Send ACK with number: {ack_num}".format(
                ack_num = self.expected_seq_num
            ))
            self.close()
            return

        cur_seq_num = header[2]
        if cur_seq_num < self.expected_seq_num:
            self.send_ack("")

            print("Send ACK with number: {ack_num}".format(
                ack_num = self.expected_seq_num
            ))

        elif cur_seq_num == self.expected_seq_num:

            print("Sequence number hit: {seq_num}".format(seq_num = cur_seq_num))
            # write in file
            self.write(content)
            # update self.expected_seq_num
            self.expected_seq_num += len(payload)
            self.expected_seq_num = self.expected_seq_num % self.UN_4BYTES_MOD
            # send ack
            self.send_ack("")

            print("Send ACK with number: {ack_num}".format(
                ack_num = self.expected_seq_num
            ))
        else:
            # discard packets when cur_seq_num > self.expected_seq_num
            print("Receiver reorder segments...")
            self.send_ack("")

            print("Send ACK with number: {ack_num}".format(
                ack_num = self.expected_seq_num
            ))


    def send_ack(self, content):
        ack_seg = self.generate_tcp_seg(content.encode())
        self.server_socket.sendto(ack_seg, self.client_address)


    def generate_tcp_seg(self, payload):
        """
        generate the tcp_seg based on the current status
        :param payload: data
        :return:
        """
        # 1. generate the h_len value
        h_len = (self.header_length << 12) + (self.is_ack << 4) + self.is_fin

        # 2. no need to compute checksum

        # 3. concat all parts
        ack_seg = struct.pack('!2H2L4H',
                                  self.src_port, self.dest_port,
                                  0,
                                  self.expected_seq_num,
                                  h_len, 0, 0, 0) + payload

        # print("ack_seg is {ack_seg}".format(ack_seg = ack_seg.hex()))
        # print("length of the ack_seg is {length}".format(length = len(ack_seg)))

        return ack_seg


    def is_corrupt(self, test_recv = None):

        temp = self.data_recv
        # temp = test_recv

        byte_len = len(temp)
        if byte_len % 2:
            byte_len += 1
            temp += '\x00'

        checksum = 0
        for short in struct.unpack('!' + str(byte_len // 2) + 'H', temp):
            checksum += short

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)

        print("checksum is {checksum}".format(checksum = hex(checksum)))
        if checksum == 0xFFFF:
            return False
        return True

    def write(self, s):
        print("write to file...")
        self.file_handle.write(s)
        self.file_handle.flush()

    def close(self):
        self.file_handle.close()
        # no connect

        print("Close file {}".format(self.file_path))





if __name__ == '__main__':

    # # tcpserver recerver.txt 10027 192.168.192.1 10001
    # file = sys.argv[1]  # 'receiver.txt'
    # listening_port = int(sys.argv[2])  # 10027
    # dest_ip = sys.argv[3]  # '192.168.192.1'
    # dest_port = int(sys.argv[4])  # 10001
    #
    # receiver = Receiver(file, listening_port, dest_ip, dest_port)

    receiver = Receiver()
    receiver.recv_handler()
