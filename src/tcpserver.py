import socket
import sys
import time
import struct


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
        self.buffer_d = {}

        # header
        self.header_length = 5
        self.is_ack = 1
        self.is_fin = 0

        self.expected_seq_num = 0

        # statistic
        self.is_first = True
        self.first_recv_time = 0
        self.prog_running_time = 0

        self.bytes_received = 0

        # initialize socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', self.recv_port))

        # open the file
        self.file_handle = open(self.file_path,'w+')

        # logger

        print("Init finished")


    def recv_handler(self):
        print("Server starts...")
        while not self.is_fin:
            self.recv_worker()

        self.recv_exit()

    def recv_worker(self):

        print("Wait for receiving...")
        # self.data_recv, client_send_address = self.server_socket.recvfrom(MSS + 20)
        self.data_recv = self.server_socket.recv(MSS + 20)

        # snapshot the first recv time
        if self.is_first:
            self.is_first = False
            self.first_recv_time = time.time()

        if self.is_corrupt():
            print("The packet is corrupt.")
            self.send_ack("")

            print("Send ACK with ack_num = {ack_num}".format(
                ack_num = self.expected_seq_num
            ))
            return

        header = struct.unpack('!2H2L4H', self.data_recv[0:20])
        payload = self.data_recv[20:]
        content = payload.decode()

        # fin bit is 1
        if header[4] % 2:
            print("Receive a FIN packet")
            self.is_fin = 1
            self.send_ack("")
            print("Send ACK with ack_num = {ack_num}".format(
                ack_num = self.expected_seq_num
            ))

            return

        cur_seq_num = header[2]
        if cur_seq_num < self.expected_seq_num:
            self.send_ack("")

            print("Send ACK with ack_num = {ack_num}".format(
                ack_num = self.expected_seq_num
            ))

        elif cur_seq_num == self.expected_seq_num:

            print("Get a sequence number hit with seq_num = {seq_num}".format(
                seq_num = cur_seq_num))
            # write in file
            self.write(content)

            # update self.expected_seq_num
            self.expected_seq_num += len(payload)
            self.expected_seq_num = self.expected_seq_num % self.UN_4BYTES_MOD

            # look for a buffer hit
            while self.expected_seq_num in self.buffer_d.keys():

                print("Get a buffer hit with seq_num = {seq_num}".format(
                    seq_num = self.expected_seq_num))

                content = self.buffer_d[self.expected_seq_num]
                self.write(content)
                del self.buffer_d[self.expected_seq_num]

                self.expected_seq_num += len(content.encode())
                self.expected_seq_num = self.expected_seq_num % self.UN_4BYTES_MOD

            # send ack
            self.send_ack("")

            print("Send ACK with ack_num = {ack_num}".format(
                ack_num = self.expected_seq_num
            ))
        else:
            # Store the packets in a buffer when the cur_seq_num > expected_seq_num
            self.buffer_d[cur_seq_num] = content

            print("Store reorder seg with seq_num = {seq_num}".format(
                seq_num = cur_seq_num
            ))

            self.send_ack("")

            print("Send ACK with ack_num = {ack_num}".format(
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


    def is_corrupt(self):

        temp = self.data_recv

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
        print("writing to file...")
        self.file_handle.write(s)
        self.file_handle.flush()

        # update bytes_received
        self.bytes_received += len(s.encode())

    def recv_exit(self):
        self.file_handle.close()

        print("Close file {}".format(self.file_path))

        # record the running time
        self.prog_running_time = time.time() - self.first_recv_time
        print("Server receives {bytes_received} bytes in {prog_running_time} seconds".format(
            bytes_received = self.bytes_received, prog_running_time = self.prog_running_time
        ))

        print("Server exits.")




if __name__ == '__main__':

    # tcpserver files/write_to.txt 12112 192.168.192.1 12114
    file = sys.argv[1]
    listening_port = int(sys.argv[2])
    dest_ip = sys.argv[3]
    dest_port = int(sys.argv[4])

    receiver = Receiver(file, listening_port, dest_ip, dest_port)

    # receiver = Receiver()

    receiver.recv_handler()
