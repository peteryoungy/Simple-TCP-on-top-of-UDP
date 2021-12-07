import socket
import sys
from threading import Thread
import time
import struct
# import queue
from collections import deque
import logging

# note: set source ip/port
# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)
#
# print(hostname, local_ip)
# serverPort = 10025

#
# def send():
#
#     # serverAddress = ('192.168.192.134', 41192)
#
#     serverAddress = (address_of_udpl, port_number_of_udpl)
#
#     # establish a UDP socket
#     clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
#     # send
#
#     clientSocket.sendto("hello".encode(), serverAddress)
#     print("The first message has been sent")
#     # print(clientSocket.recvfrom(512)[0].decode())
#
#
#     clientSocket.close()

MSS = 576

class Sender:

    def __init__(self,file_path = 'sender.txt',
                 dest_ip = '192.168.192.129',
                 dest_port = 41192,
                 windowsize = MSS * 5,
                 recv_port = 10001):

        self.file_path = file_path
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.windowsize = windowsize
        self.recv_port = recv_port

        self.dest_address = (self.dest_ip, self.dest_port)
        # constant
        self.UN_4BYTES_MOD = 2 ^ 32  # max seq_num is 2^32-1
        self.header_length = 5  # 5
        self.MSS = 576
        self. full_tcp_seg_size = self.MSS + 20
        self.ALPHA = 0.125
        self.BETA = 0.25

        # window
        self.send_base = 0
        self.next_seq_num = 0
        # can not reach boundary
        self.boundary = (self.send_base + self.windowsize) % self.UN_4BYTES_MOD
        self.next_ack_num = 0

        self.total_seg_sent = 0

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
        self.fin_ack = 0
        # value of header length + ack + fin 16bit
        # self.h_len = 0

        # helper data structure
        self.buffer_q = deque()

        # timer
        self.is_timer_on = False
        self.timer_start_time = 0

        # sample
        self.sample_tuple = (-1,-1)


        # retrans
        self.dup_retrans = 0
        self.dup_num = 0

        # init
        self.file_handle = open(file_path, 'r')

        # initialize the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('', self.recv_port))

        #logger
        self._logger = logging.getLogger()

    def send_handler(self):
        while self.is_fin == 0 or len(self.buffer_q) != 0:
            self.send_worker()

            if self.is_timeout() or self.dup_retrans:
                self.retransmit()

        self._logger.debug("send_handler exit")


    def send_worker(self):

        while (self.next_seq_num + self.MSS) % self.UN_4BYTES_MOD <= self.boundary and \
                self.is_fin == 0:

            # 1. get payload
            content = self.file_handle.read(self.MSS)
            payload = content.encode() # default: utf8'

            self._logger.debug("content is {content}".format(content = content))
            self._logger.debug("payload is {payload}".format(payload = payload.hex()))

            # if waiting fin
            if not payload and self.send_base != self.next_seq_num:
                self.waiting_fin = 1
                break

            # if fin
            if not payload and self.send_base == self.next_seq_num:
                self.waiting_fin = 0
                self.is_fin = 1

                self._logger.debug("Sending a FIN...")

            # 1. generate tcp segment
            tcp_seg = self.generate_tcp_seg(payload)

            # 2. cache the tcp segment in a queue
            tcp_seg_tuple = (self.next_seq_num, tcp_seg)
            self.buffer_q.append(tcp_seg_tuple)

            # 3. check if need start the timer
            if not self.is_timer_on:
                self.start_timer()
                self.is_timer_on = True

            # check if need sampling
            if self.sample_tuple[0] == -1 and not self.is_fin:
                self.sample_tuple = (self.next_seq_num, time.time())

                self._logger.debug("Sampling with seq_num = {seq_num}, current time = {cur_time}".format(
                    seq_num = hex(self.sample_tuple[0]), cur_time = self.sample_tuple[1]
                ))

            # 4. send data by UDP
            self.client_socket.sendto(tcp_seg, self.dest_address)

            # 5.1 update window parameter
            self.next_seq_num += (len(tcp_seg) -20)
            self.next_seq_num = self.next_seq_num % self.UN_4BYTES_MOD

            # 5.2 update total number
            if not self.is_fin:
                self.total_seg_sent += 1


            # each time after send a packet, check if there's a timeout
            if self.is_timeout() or self.dup_retrans:
                self._logger.debug("Timeout.")
                # why break first and
                # self.retransmit()  # could comment out here
                break


    def generate_tcp_seg(self, payload):
        """
        generate the tcp_seg based on the current status
        :param payload: data
        :return:
        """
        # 1. generate the h_len value
        h_len = (self.header_length << 12) + (self.is_ack << 4) + self.is_fin

        # 2. after specify the h_len, we can compute the checksum
        checksum = self.get_checksum(h_len, payload)

        # 3. concat all parts
        tcp_segment = struct.pack('!2H2L4H',
                                  self.src_port, self.dest_port,
                                  self.next_seq_num,
                                  self.next_ack_num,
                                  h_len, 0, checksum, 0) + payload

        return tcp_segment

        # else:
        #     # set fin to 1 and send a fin packet
        #
        #     return


    def get_checksum(self, h_len, payload, test_bytes = None):

        checksum = 0

        header_sum = self.src_port + self.dest_port + \
                     (self.next_seq_num >> 16) + (self.next_seq_num & 0xFFFF) + \
                     (self.next_ack_num >> 16) + (self.next_ack_num & 0xFFFF) + \
                     h_len
        checksum += header_sum

        # print("headersum: {sum}".format(sum = hex(header_sum)))

        # 2. get the payload sum
        seg_len = len(payload)
        # print("seg_len : {length}".format(length = seg_len))  # 18

        # \x00 is a temporary change, the payload is still odd
        if seg_len % 2:
            seg_len += 1
        seg_stream = struct.pack('!' + str(seg_len) + 's', payload)

        for short in struct.unpack('!' + str(seg_len // 2) + 'H', seg_stream):
            checksum += short

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)

        checksum = (~checksum) & 0xFFFF
        self._logger.debug("checksum is {checksum}".format(checksum = hex(checksum)))
        return checksum


    def retransmit(self):

        # 1. get the original data
        seq_num, retrans_seg = self.buffer_q[0]

        self._logger.debug("Retransmit tcp_seg {seq_num}".format(seq_num = hex(seq_num)))

        # 2. double the time_interval and restart timer
        self.update_timeout_interval(-1)
        self.start_timer()

        # 3. retransmit the data
        self.client_socket.sendto(retrans_seg, self.dest_address)

        # clear the retrans status
        self.dup_retrans = 0
        self.dup_num = 0


    def is_timeout(self):
        """
        check if timeout occurs
        :return: whether it is timeout
        """
        cur_time = time.time()

        if cur_time - self.timer_start_time > self.timeout_interval:
            return True
        return False


    def start_timer(self):
        self.timer_start_time = time.time()

        self._logger.debug("Start timer, the current time is {}".format(
            self.timer_start_time))


    def ack_handler(self):

        while not self.fin_ack:
            self.ack_worker()



    def ack_worker(self):

        # 1. recv data
        # recv and recvfrom? recv lets you know the client address
        data_recv = self.client_socket.recv(20)

        if data_recv:

            header = struct.unpack('!2H2L4H', data_recv[0:20])
            ack_num = header[3]
            fin_sign = header[4] % 2

            # fin bit = 1
            if fin_sign:
                self._logger.debug("receive fin_ack from server, ack_handler exit")
                self.fin_ack = True
                self.close()
                return

            # a > send_base
            if (ack_num - self.send_base + 1 < self.windowsize and
                    ack_num - self.send_base + 1 > 0 ) or \
                    self.UN_4BYTES_MOD - self.send_base + ack_num < self.windowsize :

                # deal with windows size
                self.send_base = ack_num
                # self.send_base = self.send_base % self.UN_4BYTES_MOD

                # reset dup_num
                self.dup_num = 0

                # lookup for a sample hit
                if ack_num == self.sample_tuple[0]:
                    cur_time = time.time()
                    sample_rtt = cur_time - self.sample_tuple[1]
                    self.update_timeout_interval(sample_rtt)

                    print("hit sample_tuple: {seq_num}, {cur_time}".format(
                        seq_num = self.sample_tuple[0], cur_time = self.sample_tuple[1]
                    ))
                    # clear self.sample_tuple
                    self.sample_tuple = (-1, -1)

                # deal with packets pool
                # poll packets from queue until the queue.peek.sequence_number > y
                while len(self.buffer_q) > 0 and ack_num > self.buffer_q[0][0]:
                    self.buffer_q.popleft()

                # check if need restart timer
                if self.send_base != self.next_seq_num:
                    self.start_timer()

            # dup: a <= send_base
            else:
                self.dup_num += 1
                self._logger.debug("Receive duplicate {dup_num} times".format(
                    dup_num = self.dup_num))
                if self.dup_num == 3:
                    self.dup_retrans = 1
                    self._logger.debug("Need dup retrans")


    # why I set a default value?
    def update_timeout_interval(self, sample_rtt):

        if not self.dup_retrans:
            self.estimated_rtt = (1 - self.ALPHA) * self.estimated_rtt + self.ALPHA * sample_rtt
            self.dev_rtt = (1 - self.BETA) * self.dev_rtt + self.BETA * abs(sample_rtt - self.estimated_rtt)
            self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt

        else:
            self.timeout_interval = 2 * self.timeout_interval

        self._logger.debug("UPDATE timeout_interval: {timeout_interval}".format(
            timeout_interval=self.timeout_interval))



    def close(self):
        self.file_handle.close()

        self._logger.debug("Close the file: {}".format(self.file_path))




if __name__ == '__main__':

    # # tcpclient sender.txt 192.168.192.129 41192 2880 10001
    # file = sys.argv[1]  # 'sender.txt'
    # address_of_udpl = sys.argv[2]  # 192.168.192.129
    # port_number_of_udpl = int(sys.argv[3])  # 41192
    # windowsize = sys.argv[4]  # 2880
    # ack_port_number = sys.argv[5]  # 10001
    #
    # sender = Sender(file,
    #                 address_of_udpl,
    #                 int(port_number_of_udpl),
    #                 int(windowsize),
    #                 int(ack_port_number)
    #                 )

    sender = Sender()

    send_thread = Thread(target=sender.send_handler)
    # send_thread.setDaemon(True)
    send_thread.start()

    recv_thread = Thread(target=sender.ack_handler)
    # recv_thread.setDaemon(True)
    recv_thread.start()



