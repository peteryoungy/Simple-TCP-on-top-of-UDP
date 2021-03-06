import socket
import sys
from threading import Thread
from threading import Lock
import time
import struct
from collections import deque
import queue

MSS = 576

def get_local_time():
    """
    convert time to yyyy/mm/dd hours:minutes:secs
    """
    local_time = time.localtime()
    return "{0}/{1}/{2} {3}:{4}:{5} ".format(local_time[0], local_time[1], local_time[2],
                                             local_time[3], local_time[4], local_time[5])


class Sender:

    def __init__(self,file_path = 'files/read_from.txt',
                 dest_ip = '192.168.192.134',
                 dest_port = 41192,
                 windowsize = MSS * 10,
                 recv_port = 12114):

        self.file_path = file_path
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.windowsize = windowsize
        self.recv_port = recv_port

        self.dest_address = (self.dest_ip, self.dest_port)

        # constant
        self.UN_4BYTES_MOD = 4294967296  # max seq_num is 2^32-1
        self.header_length = 5  # 5
        self.MSS = 576
        self.DEFAULT_TIMEOUT_INTERVAL = 1

        # window parameter
        self.send_base = 0
        self.next_seq_num = 0
        self.boundary = self.windowsize
        self.next_ack_num = 0

        self.total_seg_sent = 0

        # timeout_interval
        self.ALPHA = 0.125
        self.BETA = 0.25
        self.estimated_rtt = 0
        self.dev_rtt = 0
        self.timeout_interval = self.DEFAULT_TIMEOUT_INTERVAL
        self.if_first_update = True     # initialize the estimatedRTT

        # tcp header
        self.src_port = 12111
        self.is_ack = 0
        self.is_fin = 0
        self.fin_ack = 0

        # buffer
        self.buffer_q = queue.Queue()

        # timer
        self.is_timer_on = False
        self.timer_start_time = 0

        # sample
        self.sample_tuple = (-1,-1)

        # retrans
        self.dup_retrans = 0
        self.dup_num = 0

        #logger
        self.send_logger_path = 'logger/send_logger.txt'
        self.ack_logger_path = 'logger/ack_logger.txt'

        # lock
        self.sample_tuple_lock = Lock()
        self.timeout_interval_lock = Lock()
        self.timer_start_time_lock = Lock()

        self.dup_lock = Lock()  # lock of dup_num and dup_retrans
        self.window_lock = Lock()   # lock of send_base and boundary

        self.is_timer_on_lock = Lock()


        # init file handle
        self.file_handle = open(file_path, 'r+')

        # initialize the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('', self.recv_port))

        # init logger
        self.send_logger = open(self.send_logger_path, 'w+')
        self.ack_logger = open(self.ack_logger_path, 'w+')

        self.logger_write('s', "Init finished")


    def logger_write(self, model, s):
        """
        Thread sender_handler write logs to logger/send_logger.txt
        Thread ack_handler write logs to logger/ack_logger.txt
        :param model: model == 's', called by send_handler, model == 'a', called by ack_handler
        :param s: log content
        :return:
        """

        if model != "s" and model != "a":
            print("logger_write: Model error")

        if model == "s":
            self.send_logger.write(get_local_time() + ": " +s + '\n')
            self.send_logger.flush()
        else:
            self.ack_logger.write(get_local_time() + ": " +s + '\n')
            self.ack_logger.flush()

        return


    def send_handler(self):
        """
        Thread send_handler works on this method. It calls self.send_worker() and self.retransmit()
        to be mainly responsible for packets sending and retransmission.
        :return:
        """

        print("Send Handler starts")
        while self.is_fin == 0 or not self.buffer_q.empty():
            self.send_worker()

            # timeout or 3 duplicate will trigger the retransmission
            if self.is_timeout() or self.get_dup_retrans():
                self.retransmit()

        self.sender_exit()


    def send_worker(self):
        """
        Send the next segment in the window.
        Each time after a packet was sent, check if there's retransmission.
        :return:
        """

        while (self.next_seq_num + self.MSS) % self.UN_4BYTES_MOD <= self.get_boundary() and \
                self.is_fin == 0:

            # 1. get content from file
            content = self.file_handle.read(self.MSS)
            payload = content.encode() # default: utf8'

            # self.logger_write('s', "Send Handler: content is {content}".format(content = content))
            # self.logger_write('s', "Send Handler: payload is {payload}".format(payload = payload.hex()))

            # Waiting until all the segments are successfully received by the server
            if not payload and self.get_send_base() != self.next_seq_num:
                self.waiting_fin = 1
                break

            # File transmission finished, send a FIN packet
            if not payload and self.get_send_base() == self.next_seq_num:
                self.waiting_fin = 0
                self.is_fin = 1

                self.logger_write('s', "Send Handler: Sending a FIN...")

            # 1. generate tcp segment
            tcp_seg = self.generate_tcp_seg(payload)

            self.logger_write('s', "Send Handler: Generate_tcp_seg.")

            # 2. push the tcp segment to a queue, for retransmission
            tcp_seg_tuple = (self.next_seq_num, tcp_seg)
            self.buffer_q.put(tcp_seg_tuple)

            self.logger_write('s', "Send Handler: append tcp_seg into self.buffer_q with seq_num:{seq_num}".format(
                seq_num = self.next_seq_num
            ))

            # 3. check if need start the timer
            with self.is_timer_on_lock:
                if not self.is_timer_on:
                    self.start_timer('s')
                    self.is_timer_on = True

            # 4. check if need sampling. When there's no segments being sampled currently,
            # do a new sampling.
            with self.sample_tuple_lock:
                if self.sample_tuple[0] == -1 and not self.is_fin:
                    self.sample_tuple = (self.next_seq_num, time.time())

                    self.logger_write('s', "Send Handler: Sampling with seq_num = {seq_num}, current time = {cur_time}".format(
                        seq_num = self.sample_tuple[0], cur_time = self.sample_tuple[1]
                    ))

            # 5. send data by UDP
            self.client_socket.sendto(tcp_seg, self.dest_address)

            self.logger_write('s', "Send handler: Send the tcp_seg")

            # 6.1 update window parameter
            self.next_seq_num += (len(tcp_seg) -20)
            self.next_seq_num = self.next_seq_num % self.UN_4BYTES_MOD

            self.logger_write('s', "Send Handler: Update self.next_seq_num to {seq_num}".format(
                seq_num = self.next_seq_num
            ))

            # 6.2 update total number
            if not self.is_fin:
                self.total_seg_sent += 1


            # each time after send a packet, check if there's a retransmission
            if self.is_timeout() or self.get_dup_retrans():
                self.logger_write('s', "Send Handler: Timeout.")
                break


    def generate_tcp_seg(self, payload):
        """
        Generate the tcp_seg based on the payload.
        :param payload: bytes form of the file content string
        :return: TCP segment to be sent
        """

        # 1. generate the h_len value, 16bits field which contains header_length, ACK and FIN
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



    def get_checksum(self, h_len, payload):
        """
        Compute the checksum of the segment.

        :param h_len: 16bits field which contains the header_length, ACK, FIN parts in the TCP header
        :param payload: bytes form of the file content string
        :return: the checksum of the TCP segment
        """

        checksum = 0

        # 1. get the header sum
        header_sum = self.src_port + self.dest_port + \
                     (self.next_seq_num >> 16) + (self.next_seq_num & 0xFFFF) + \
                     (self.next_ack_num >> 16) + (self.next_ack_num & 0xFFFF) + \
                     h_len
        checksum += header_sum
        # print("headersum: {sum}".format(sum = hex(header_sum)))

        # 2. get the payload sum
        seg_len = len(payload)

        # for odd length of payload, add a byte \x00, because checksum is computed based on 16 bits
        if seg_len % 2:
            seg_len += 1
        seg_stream = struct.pack('!' + str(seg_len) + 's', payload)

        for short in struct.unpack('!' + str(seg_len // 2) + 'H', seg_stream):
            checksum += short

        # 3. add the overflow bits
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)

        checksum = (~checksum) & 0xFFFF
        self.logger_write('s', "Send Handler: checksum is {checksum}".format(checksum = hex(checksum)))
        return checksum


    def retransmit(self):
        """
        In TCP, retransmit the unACKed segment with the smallest sequence number, which is actually the
        self.send_base
        :return:
        """

        self.logger_write('s', "Retransmit: Retransmit tcp_seg {seq_num}".format(
            seq_num=self.get_send_base()))

        # 1. get the TCP segment to be retransmitted from the head of the queue
        seq_num, retrans_seg = self.buffer_q.queue[0]

        # 2. Disable sampling. if seq_num == sample_tuple[0], set sample_tuple to (-1, -1)
        with self.sample_tuple_lock:
            if seq_num == self.sample_tuple[0]:
                self.sample_tuple = (-1, -1)

        # 3. double the time_interval and restart timer
        self.double_timeout_interval()
        self.start_timer('s')

        # 3. retransmit the data
        self.client_socket.sendto(retrans_seg, self.dest_address)

        # 4. clear the retransmission status
        with self.dup_lock:
            self.dup_retrans = 0
            self.dup_num = 0


    def is_timeout(self):
        """
        Check if timeout occurs.
        :return: if timeout, return True, otherwise return False
        """

        # When the timer is off, no timeout.
        if self.get_is_timer_on() is False:
            return False

        cur_time = time.time()

        if cur_time - self.get_timer_start_time() > self.get_timeout_interval():
            self.logger_write('s', "Timeout occurs for seq_num = {seq_num}".format(
                seq_num = self.get_send_base()
            ))
            return True
        return False


    def start_timer(self, model):
        """
        Start the timer by updating the self.timer_start_time
        :param model: 's' means this thread is called by the sender_handler,
        while 'a' means this method is called by the ack_handler
        :return:
        """

        if model != 's' and model != 'a':
            print("start_timer: Model Error")

        with self.timer_start_time_lock:
            self.timer_start_time = time.time()

        if model == 's':
            self.logger_write('s', "Start timer with timeout_interval = {time_out_interval}".format(
                time_out_interval = self.get_timeout_interval()))
        else:
            self.logger_write('a', "Start timer with timeout_interval = {time_out_interval}".format(
                time_out_interval = self.get_timeout_interval()))


    def ack_handler(self):
        """
        Thread ack_handler works on this method. It calls self.ack_worker() to handle
        ACKs from the server.
        :return:
        """

        print("ACK Handler starts")
        while not self.fin_ack:
            self.ack_worker()

        self.ack_exit()


    def ack_worker(self):
        """
        Handle ACKs from the server.
        :return:
        """

        # Blocking here, waiting for packets from the server
        data_recv = self.client_socket.recv(20)

        if data_recv:

            # 1. extracting header and ACK, FIN bit from the header
            header = struct.unpack('!2H2L4H', data_recv[0:20])
            ack_num = header[3]
            fin_sign = header[4] % 2

            # 2.1 if receive a FIN segment, thread exit
            if fin_sign:
                self.logger_write('a', "ACK Handler: receive fin_ack from server, ack_handler exit")
                self.fin_ack = True

                # clear the buffer_q
                while not self.buffer_q.empty():
                    self.buffer_q.get()

                return


            self.logger_write('a', 'Receive packets from server with ack_num = {ack_num}'.format(
                ack_num = ack_num
            ))

            # 2.2 If receive duplicate ACKs, add dup_num by 1, if dup_num == 3, set
            # dup_retrans to 1, the sender will check the status of dup_retrans for fast retransmit
            if ack_num == self.get_send_base():
                with self.dup_lock:
                    self.dup_num += 1
                    # self.set_dup_num(self.get_dup_num() + 1)
                    self.logger_write('a', "ACK Handler: Receive {ack_num} {dup_num} times".format(
                        ack_num = ack_num, dup_num = self.dup_num))
                    if self.dup_num == 3:
                        self.dup_retrans = 1
                        self.logger_write('a', "ACK Handler: Need dup retrans")

            # 2.3 If receive segments with sequence number equal to or larger than the expected
            # sequence number.
            # if (self.windowsize > ack_num - self.send_base + 1 > 0) or \
            #         self.UN_4BYTES_MOD - self.send_base + ack_num < self.windowsize:
            else:

                # 1. update send_base and send_boundary
                with self.window_lock:
                    self.send_base = ack_num
                    self.boundary = (self.send_base + self.windowsize) % self.UN_4BYTES_MOD
                    self.logger_write('a', "Update send_base = {send_base}, Update boundary = {boundary}".format(
                        send_base = self.send_base, boundary = self.boundary
                    ))

                # 2. reset the duplicate number
                self.set_dup_num(0)

                # 3. lookup for a sample hit. Check whether this segment is sampled before
                with self.sample_tuple_lock:
                    if self.sample_tuple[0] != -1 and ack_num >= self.sample_tuple[0]:
                        self.logger_write('a', "ACK Handler: sample hit: ack_num = {ack_num},"
                                               "seq_num = {seq_num}".format(
                            ack_num=ack_num, seq_num=self.sample_tuple[0],))

                        # only when sequence number is equal, we use EWMA to update timeout_interval
                        if ack_num == self.sample_tuple[0]:
                            cur_time = time.time()
                            sample_rtt = cur_time - self.sample_tuple[1]
                            self.update_timeout_interval(sample_rtt)

                        # Otherwise set the timeout_interval to default value
                        else:
                            self.reset_timeout_interval()

                        # clear self.sample_tuple
                        self.sample_tuple = (-1, -1)

                    # Otherwise set the timeout_interval to default value
                    else:
                        self.reset_timeout_interval()


                # 4. deal with segments buffer: poll packets from the buffer until the
                # queue.peek.sequence_number > ack_num
                while not self.buffer_q.empty() and ack_num > self.buffer_q.queue[0][0]:
                    self.logger_write('a', "ack_num = {ack_num}, pop seg {seq_num}".format(
                        ack_num = ack_num, seq_num = self.buffer_q.queue[0][0]
                    ))
                    self.buffer_q.get()

                # 5. check if we need restart timer or close the timer
                if self.get_send_base() != self.next_seq_num:
                    self.start_timer('a')
                else:
                    self.set_is_timer_on(False)


    def reset_timeout_interval(self):
        """
        Reset the timeout_interval to default value
        :return:
        """

        with self.timeout_interval_lock:

            self.timeout_interval = self.DEFAULT_TIMEOUT_INTERVAL

            self.logger_write('s', "Reset timeout_interval: {timeout_interval}".format(
                timeout_interval=self.timeout_interval))

            return

    def double_timeout_interval(self):
        """
        Double the timeout_interval when retransmit a segment
        :return:
        """

        with self.timeout_interval_lock:
            self.timeout_interval = 2 * self.timeout_interval

            self.logger_write('s', "Retransmit: Double the timeout_interval: {timeout_interval}".format(
                timeout_interval=self.timeout_interval))
            return


    def update_timeout_interval(self, sample_rtt):
        """
        Update the timeout_interval which is defined in TCP protocol.
        When it is a retransmission, double the current timeout_interval
        :param sample_rtt: sampleRTT
        :return:
        """

        with self.timeout_interval_lock:

            # If it is the first update of timeout_interval, initialize estimatedRTT to sampleRTT and
            # devRTT to 0
            if self.if_first_update:
                self.if_first_update = False
                self.estimated_rtt = sample_rtt
                self.dev_rtt = 0
                self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt

                self.logger_write('a', "Initialize estimatedRTT = {esrtt}, devRTT = 0, timeout_interval"
                                       " = {timeout_interval}".format(
                    esrtt = self.estimated_rtt, timeout_interval = self.timeout_interval
                ))
                return

            # use EWMA formula
            self.logger_write('a', "sampleRTT = {sprtt}, original estimatedRTT = {esrtt}, "
                                   "original devRTT = {dvrtt}".format(
                sprtt=sample_rtt, esrtt=self.estimated_rtt, dvrtt=self.dev_rtt
            ))
            self.estimated_rtt = (1 - self.ALPHA) * self.estimated_rtt + self.ALPHA * sample_rtt
            self.dev_rtt = (1 - self.BETA) * self.dev_rtt + self.BETA * abs(sample_rtt - self.estimated_rtt)
            self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt

            self.logger_write('a', "Update timeout_interval = {timeout_interval}".format(
                timeout_interval = self.timeout_interval))


    def ack_exit(self):
        """
        Define things need to do when the ack_handler is about to exit.
        Close the txt file and turn off the timer.
        :return:
        """

        self.logger_write('a', "ACK Handler: Close the file: {}".format(self.file_path))
        self.file_handle.close()

        self.logger_write('a', "Close the timer.")
        self.set_is_timer_on(False)
        print("ACK Handler exits")


    def sender_exit(self):
        """
        Define things need to do when the send_handler is about to exit.
        Close the logger file
        :return:
        """

        self.logger_write('s', "Close Logger")
        self.send_logger.close()
        self.ack_logger.close()

        print("Send Handler exits.")


##  Define some multi-thread safe getter and setter methods #########################################################

    def get_timeout_interval(self):
        with self.timeout_interval_lock:
            return self.timeout_interval


    def set_dup_num(self, num):
        with self.dup_lock:
            self.dup_num = num


    def get_dup_retrans(self):
        with self.dup_lock:
            return self.dup_retrans


    def get_send_base(self):
        with self.window_lock:
            return self.send_base


    def get_boundary(self):
        with self.window_lock:
            return self.boundary


    def set_is_timer_on(self, flag):
        with self.is_timer_on_lock:
            self.is_timer_on = flag


    def get_is_timer_on(self):
        with self.is_timer_on_lock:
            return self.is_timer_on


    def get_timer_start_time(self):
        with self.timer_start_time_lock:
            return self.timer_start_time





if __name__ == '__main__':

    # # tcpclient files/read_from.txt 192.168.192.134 41192 2880 12114
    file = sys.argv[1]
    address_of_udpl = sys.argv[2]
    port_number_of_udpl = int(sys.argv[3])
    windowsize = sys.argv[4]
    ack_port_number = sys.argv[5]

    sender = Sender(file,
                    address_of_udpl,
                    int(port_number_of_udpl),
                    int(windowsize),
                    int(ack_port_number)
                    )

    # sender = Sender()

    send_thread = Thread(target=sender.send_handler)
    send_thread.start()

    recv_thread = Thread(target=sender.ack_handler)
    recv_thread.start()



