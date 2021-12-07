import tcpclient
import tcpserver
# file = sys.argv[1]  #
# address_of_udpl = sys.argv[2]  # 192.168.192.134
# port_number_of_udpl = int(sys.argv[3])  # 41192
# windowsize = sys.argv[4]  #
# ack_port_number = sys.argv[5]  # 10027

def get_checksum_check():
    sender = tcpclient.Sender('sender.txt',
                              '192.168.192.134',
                              41192,
                              576 * 5,
                              10001)

    # print(bytes.fromhex('12').decode('utf-8'))
    payload = bytes.fromhex('4500003c1c4640004006ac100263ac100a0c')
    # payload = bytes.fromhex('4500')
    h_len  = 0x5000
    print(hex(sender.get_checksum(h_len,payload)))

def generate_tcp_seg_test():
    sender = tcpclient.Sender('sender.txt',
                              '192.168.192.134',
                              41192,
                              576 * 5,
                              10001)
    payload = bytes.fromhex('4500003c1c4640004006ac100263ac100a0c')
    tcp_seg = sender.generate_tcp_seg(payload)
    print(tcp_seg.hex())

# generate_tcp_seg_test()


def is_corrupt():
    test_recv = bytes.fromhex('2729a0e8000000000000000050000000a1d400004500003c1c4640004006ac100263ac100a0c')

    tcpserver.is_corrupt(test_recv)
is_corrupt()