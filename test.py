import sys
import time


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

a = b'11'
b = "hello"
c = a + b
print(type(c))
print(c)