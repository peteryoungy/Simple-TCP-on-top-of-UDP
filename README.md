### Overview

CSEE 4119 PA2

Implement a simple version of TCP on top of UDP.

### File Structure

```
Simple-TCP-on-top-of-UDP
├── src					 
│   ├── tcpclient.py              # Source code of tcp client
│   ├── tcpserver.py              # Source code of tcp server
├── files							
│   ├── read_from_5000.txt        # txt file to be sent, 5000+ bytes
│   ├── read_from.txt             # txt file to be sent, 110000+ bytes
│   ├── write_to.txt              # Server write content to this file
├── logger
│   ├── send_logger.txt           # Log file of thread send_handler in tcpclient.py
│   ├── ack_logger.txt            # Log file of thread ack_handler in tcpclient.py
├── test
│   ├── test.py                   # Some little test methods for learning, you can ignore it.
│   ├── unitest.py                # Simple unitest of some methods in src/, you can ignore it.
├── screen_dump
│   ├── newudpl_result.png        # Screenshot of results of newudpl
│   ├── server_result_head        # Screenshot of the head of the results of tcpserver.py
│   ├── server_result_tail        # Screenshot of the tail of the results of tcpserver.py
├── SUMMARY.md                    # Design considerations of the whole program
└── README.md                     # README	
```

##### For source code: [Code](./src)

##### For program design documentation: [Program Design](./Summary.md)

##### For Log info: [Log of client](./logger)     [Log of server and newudpl](./screen_dump)

### Test Command

This is my test command. I think it also works well with different ip addresses, port numbers, windowsize. 

##### Client

```bash
tcpclient files/read_from.txt 192.168.192.134 41192 5760 12114
```

##### newudpl

```bash
./newudpl -i 192.168.192.1:* -o 192.168.192.134:12112 -L 10 -O 10 -B 10
```

##### Server

```
tcpserver files/write_to.txt 12112 192.168.192.1 12114
```

### Known Bugs

There is a **exponential explosion of timeout interval** when the link is easy to make errors. I use `-L 10 -O 10 -B 10` as the test parameter and it works well. However when you improve these numbers, such as `-L 50`, the program appears stopped. However, it is not stopped. The reanson is that the timeout interval is toooo large and both the client and server are waiting for the single packet to be transmitted.

I want to add a timeout interval limitation in the program, such as when the  timeout interval is bigger than 32, always set the timeout interval as 32 when more retransmission occurs, but I think professor didn't mention rules like this in class-------I don't want to create some rules by myself, so I give up this solution. 

**For a good test result, use my parameter or use the file with smaller number of bytes: files/read_from_5000.txt.**

### Features

- Mainly basd on the basic features of TCP	


- fast retransmission

