import sys
import time
from threading import Thread
import queue
from collections import deque
# def test():
#     a = int(sys.argv[1])
#     b = int(sys.argv[2])
#
#
#     return a + b
#
# print(test())

# # doubt about checksum in the code
# a = 0b1011101110110101
# b = 0b1000111100001100
#
# print("a + b: " + bin(a+b))
#
# c = 65535 - (a + b)
# print("c : " + bin(c))




# ## test check sum
# def ip_checksum(ip_header, size):
#     cksum = 0
#     pointer = 0
#
#     # The main loop adds up each set of 2 bytes. They are first converted to strings and then concatenated
#     # together, converted to integers, and then added to the sum.
#     while size > 1:
#         cksum += int((str("%02x" % (ip_header[pointer],)) +
#                       str("%02x" % (ip_header[pointer + 1],))), 16)
#         size -= 2
#         pointer += 2
#     if size:  # This accounts for a situation where the header is odd
#         cksum += ip_header[pointer]
#
#     cksum = (cksum >> 16) + (cksum & 0xffff)
#     cksum += (cksum >> 16)
#
#     return (~cksum) & 0xFFFF
#
# header = {}
#
# # header[0] = 0x45
# # header[1] = 0x00
# # header[2] = 0x00
# # header[3] = 0xe8
# # header[4] = 0x00
# # header[5] = 0x00
# # header[6] = 0x40
# # header[7] = 0x00
# # header[8] = 0x40
# # header[9] = 0x11
# # header[10] = 0x0
# # header[11] = 0x0
# # header[12] = 0x0a
# # header[13] = 0x86
# # header[14] = 0x33
# # header[15] = 0xf1
# # header[16] = 0x0a
# # header[17] = 0x86
# # header[18] = 0x33
# # header[19] = 0x76
#
# header[0] = 0x45
# header[1] = 0x00
# header[2] = 0x00
# header[3] = 0x3c
# header[4] = 0x1c
# header[5] = 0x46
# header[6] = 0x40
# header[7] = 0x00
# header[8] = 0x40
# header[9] = 0x06
# header[10] = 0x0
# header[11] = 0x0
# header[12] = 0xac
# header[13] = 0x10
# header[14] = 0x02
# header[15] = 0x63
# header[16] = 0xac
# header[17] = 0x10
# header[18] = 0x0a
# header[19] = 0x0c
#
# print("Checksum is: %x" % (ip_checksum(header, len(header)),))
# # print("Should be BD92")
# print("Should be b9e6")
#
#
#
# def get_chech_sum(ip_header, size):
#
#     cksum = 0
#     pointer = 0
#
#     # The main loop adds up each set of 2 bytes. They are first converted to strings and then concatenated
#     # together, converted to integers, and then added to the sum.
#     while size > 1:
#         cksum += int((str("%02x" % (ip_header[pointer],)) +
#                       str("%02x" % (ip_header[pointer + 1],))), 16)
#         size -= 2
#         pointer += 2
#     if size:  # This accounts for a situation where the header is odd
#         cksum += ip_header[pointer]
#
#     cksum = (cksum >> 16) + (cksum & 0xffff)
#     cksum += (cksum >> 16)
#
#     return (~cksum) & 0xFFFF


# # test time.time()
# print(time.time())

# # test int to hex
# a = b'1'
# b = b'2'
# c= (a + b).decode()
# print(type(c))
# print((a + b).decode())

# # test hex
# # print(bytes.fromhex('12').decode('utf-8'))

# # string and bytes
# a = b'11'
# b = "hello"
# c = a + b
# print(type(c))
# print(c)

# # multi-thread test
# class A:
#
#     def __init__(self):
#         self.send_logger = open('../logger/send_logger.txt', 'w')
#         self.ack_logger = open('../logger/ack_logger.txt', 'w')
#         print("init")
#
#     def t1(self):
#         self.send_logger.write("send_logger")
#
#     def t2(self):
#         self.ack_logger.write("ack_logger")
#
#
# def test_multi_thread():
#     obj = A()
#
#     t1 = Thread(target=obj.t1)
#     # t1.setDaemon(True)
#
#     t2 = Thread(target=obj.t2)
#     # t2.setDaemon(True)
#
#     t1.start()
#     t2.start()
#
# test_multi_thread()


# # # read() test
# def read_file():
#     file = open('sender.txt','r')
#     counter = 0
#     while 1:
#         content = file.read(100)
#         counter += 1
#         if content:
#             print(content)
#
#         if content == "":
#             print("content is "".")
#
#         if not content:
#             print("not content")
#
#         if counter == 50:
#             break
#
# read_file()


# # dict test
#
# dict = {}
# dict[1] = 1
#
# if 2 not in dict.keys():
#     print("2 does not exist")
#
# del dict[1]
# if 1 not in dict.keys():
#     print("1 does not exist")


# # test tuple
# a = (1,2)
#
# # a1,a2 = a
# # print(a1,a2)
# a1 = a[0]
# print(a1)


# test Queue
q = queue.Queue()
q.put(5)
q.put(7)

"""
dir() is helpful if you don't want to read the documentation
and just want a quick reminder of what attributes are in your object
It shows us there is an attribute named queue in the Queue class
"""
for attr in dir(q):
    print(attr)


# Print first element in queue
print(q.qsize())
print("\nLooking at the first element")
print(q.queue[0])

print(q.qsize())
print("\nGetting the first element")
print(q.get())

print(q.qsize())
print("\nLooking again at the first element")
print(q.queue[0])



# # test deque
#
# q = deque()
# q. appendleft(3)
# q. appendleft(2)
# q. appendleft(1)
#
# q. append(4)
# q. append(5)
#
# print(len(q))
#
# print(q[4])
# print(q[2])
#
# print(len(q))


# # test write file
# file = open('receiver.txt','w')
# data = "test write"
# data = data.encode()
# file.write(data)
# file.close()



# # test bytes slicing
# # slicing: [startIndex, endIndex )
# origin_content = "test write"
# payload = origin_content.encode()
# print(len(payload))
# content = payload[0:].decode()
# print(content)
#
# file = open('receiver.txt','w')
# file.write(content)
# file.close()