import udpsender

# file = sys.argv[1]  #
# address_of_udpl = sys.argv[2]  # 192.168.192.134
# port_number_of_udpl = int(sys.argv[3])  # 41192
# windowsize = sys.argv[4]  #
# ack_port_number = sys.argv[5]  # 10027

def get_checksum_check():
    sender = udpsender.Sender('test.txt','192.168.192.134','0','2000', '0')

    # print(bytes.fromhex('12').decode('utf-8'))
    payload = bytes.fromhex('4500003c1c4640004006ac100263ac100a0c')
    # payload = bytes.fromhex('4500')
    print(hex(sender.get_checksum(payload)))

def generate_tcp_seg_test():
    sender = udpsender.Sender('test.txt', '192.168.192.134', '41192', '2000', '10027')
    tcp_seg = sender.generate_tcp_seg()
    print(tcp_seg.hex())

generate_tcp_seg_test()