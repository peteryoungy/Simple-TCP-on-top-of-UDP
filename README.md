### Introduction

CSEE4119 project.

### Demands

TCP 的特点

1. 没有握手连接，直接发送。 但是有FIN， 标志连接结束

2. 没有congestion control和 flow control
3. sequence number starts at 0
4. sender windows size is fixed and provided by command line
5. adjust timeout?
6. sender read data from a file and receiver write data to a file, both specified as command line parameters

receiver

```
tcpserver file listening_port address_for_acks port_for_acks
```

sender

```
tcpclient file address_of_udpl port_number_of_udpl windowsize ack_port_number
```

sender:

send packets to proxy, and receiver packets from receiver



receiver

receive packets from proxy, and send to sender