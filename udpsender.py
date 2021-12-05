import socket
import sys
from threading import Thread
import time
import struct
# note: set source ip/port
# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)
#
# print(hostname, local_ip)
# serverPort = 10025



def send():

    # serverAddress = ('192.168.192.134', 41192)

    serverAddress = (address_of_udpl, port_number_of_udpl)

    # establish a UDP socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # send

    clientSocket.sendto("hello".encode(), serverAddress)
    print("The first message has been sent")
    # print(clientSocket.recvfrom(512)[0].decode())


    clientSocket.close()

class Sender:

    def __init__(self,file_path, dest_ip, dest_port, windowsize, recv_port):

        self.file_path = file_path
        self.dest_ip = dest_ip
        self.dest_port = int(dest_port)
        self.windowsize = int(windowsize)
        self.recv_port = int(recv_port)

        # constant
        self.UN_4BYTES_MODULE = 2 ^ 32 # max seq_num is 2^32-1
        self.header_length = 5  #5
        self.MSS = 576
        self. full_tcp_seg_size = self.MSS + 20
        self.ALPHA = 0.125
        self.BETA = 0.25

        # window
        self.send_base = 0
        self.next_seq_num = 0
        self.boundary = (self.send_base + self.windowsize) % self.UN_4BYTES_MODULE
        self.next_ack_num = 0


        # timeout_interval
        self.ALPHA = 0.125
        self.BETA = 0.25
        self.estimated_rtt = 1
        self.dev_rtt = 0
        self.timeout_interval = 1

        # tcp header
        self.src_port = 10025
        # self.src_port = 0  #
        # self.dest_port = dest_port
        # NextSeqNum
        # nextAckNum???
        self.is_ack = 0
        self.is_fin = 0
        # value of header length + ack + fin 16bit
        self.h_len = 0


        # timer
        self.timer_on = False
        self.timer_start_time = 0

        # sample
        self.sample_interval = 3
        self.seg_sent = 0

        # init
        self.file_handle = open(file_path, 'r')


    def send_handler(self):
        self.send_packets()

        if self.is_timeout():
            self.retransmit()
        return


    # def send_packets(self):
    #
    #     while (self.next_seq_num + self.full_tcp_seg_size) % self.UN_4BYTES_MODULE < self.boundary:
    #
    #         # 1. generate tcp segment
    #
    #         # 2. cache the tcp segment in a queue
    #         queue.offer()
    #
    #         # 3. check if need start the timer
    #         if (timer is off){
    #             self.start_timer()
    #         }
    #
    #         # check if need sampling
    #
    #         # 4. send data by UDP
    #         udp.sendto(tcp_segment)
    #
    #         # update window parameter
    #         nextSeqNum += length(tcp_segment)
    #         nextSeqNum = nextSeqNum % self.UN_4BYTES_MODULE
    #
    #     return


    def generate_tcp_seg(self):

        # 1. get payload
        payload = self.file_handle.read(self.MSS)  ## this be ok????
        payload = payload.encode()
        print("payload is {payload}".format(payload = payload.hex()))
        # # test
        # payload = bytes.fromhex('4500003c1c4640004006ac100263ac100a0c')

        if payload:
            # 2. compute checksum
            checksum = self.get_checksum(payload)
            print("checksum is {checksum}".format(checksum = hex(checksum)))

            # 3. generate tcp header

            tcp_segment = struct.pack('!2H2L4H',
                                      self.src_port, self.dest_port,
                                      self.next_seq_num,
                                      self.next_ack_num,
                                      self.h_len, 0, checksum, 0) + payload

            return tcp_segment

        # else:
        #     # set fin to 1 and send a fin packet
        #
        #     return


    def get_checksum(self, payload, test_bytes = None):

        checksum = 0
        # 1. get the header sum
        self.h_len = (self.header_length << 12) + (self.is_ack << 4) + self.is_fin

        header_sum = self.src_port + self.dest_port + \
                     (self.next_seq_num >> 16) + (self.next_seq_num & 0xFFFF) + \
                     (self.next_ack_num >> 16) + (self.next_ack_num & 0xFFFF) + \
                     self.h_len
        checksum += header_sum

        # # test block
        # print(hex(5<<12))
        # print(hex(10025))
        # print(hex((5<<12) + 10025))

        # print(hex(checksum))
        # print("headersum: {sum}".format(sum = hex(header_sum)))
        # checksum = 0

        # 2. get the payload sum
        seg_len = len(payload)
        print("seg_len : {length}".format(length = seg_len))  # 18

        # \x00 is a temporary change, the payload is still odd
        if seg_len % 2:
            seg_len += 1
        seg_stream = struct.pack('!' + str(seg_len) + 's', payload)

        for short in struct.unpack('!' + str(seg_len // 2) + 'H', seg_stream):
            checksum += short

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)

        return (~checksum) & 0xFFFF



    def generate_tcp_header(self):

        return


    def retransmit(self):

        return


    def is_timeout(self):
        """
        check if timeout occurs
        :return: whether it is timeout
        """
        cur_time = time.time()

        if cur_time - self.timer_start_time > self.timeout_interval:
            return True
        return False


    def ack_handler(self):
        return





    def close(self):
        self.file.close()




if __name__ == '__main__':


    file = sys.argv[1]  #
    address_of_udpl = sys.argv[2]  # 192.168.192.134
    port_number_of_udpl = int(sys.argv[3])  # 41192
    windowsize = sys.argv[4]  #
    ack_port_number = sys.argv[5]  # 10027

    sender = Sender(file, address_of_udpl, port_number_of_udpl, windowsize, ack_port_number)

    send_thread = Thread(target=sender.send_handler)
    send_thread.setDaemon(True)
    send_thread.start()

    recv_thread = Thread(target=sender.ack_handler)
    recv_thread.setDaemon(True)
    recv_thread.start()



