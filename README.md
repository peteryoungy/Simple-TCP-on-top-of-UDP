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







#### sender

```python
# constant
2^32
5
static full_tcp_seg_size = 576 + 20


# send affairs
segment size:fixed
windowsize: fixed
sendBase
NextSeqNum
boundary


# timeout_interval
alfa
beta
estimatedRTT
devRTT
timeoutInterval


#tcp header
sourcePort
DestPort
NextSeqNum
nextAckNum???
headerlength = 5

ACK
FIN

#timer
TIMER_ON
time_start_time
```







#### 1. send()

```python

while (nextSeqNum + full_seg_size) % 2^32 < boundary
	
    # 1. generate tcp segment
		
    # 3. cache the tcp segment in a queue
    queue.offer()
    
    # 2. check if need start the timer
    if(timer is off){
        start_timer()
    }
    
    # 4. send data by UDP
    udp.sendto(tcp_segment)
    
    # update window parameter
    nextSeqNum += length(tcp_segment) 
    nextSeqNum = nextSeqNum % 2^32

file_handler.close() # when the thread terminated
```

##### 如果加入sample？

每隔一段时间，sample一个packet, using a hash table to record

##### gernerate TCP segment 

```python
# generate tcp header
tcp_header

# read something from file
payload = file_handler.read(576)

#construct the tcp_segment
	 compute checksum
     struct.pack()
tcp_segment

return tcp_segment
```

###### generate TCP header

windowsize must be n*(576 + 20)

```
sourcePort \\ DestPort
      NextSeqNum
      nextAckNum???
headerlength = 5 ack = 0 fin = 0

if NextSeqNum  < boundary + 2 ^32 :
return the struct. header
```

when the content is None, set fin = 1

###### Compute Check Sum

```

```

##### How does the timer work?

check timer after send every packet

#### 2. timeout

start_timer()

```
timer_start_time = time.time()
```

is_timeout()

```
get
```



##### rertansmit

```
get the original data
send the data
set timeout_interval = 2*timeout_interval
start_timer()
```

##### how to get the original data?

use a queue, save sequence number and the already sent but not acked packet, make it a pair

when ack arrives, poll from the queue

whenever send a packet, push to the 

when retransmit, use queue.peek()



#### 3. receiveACK

event trigger

```python
while(receive data){

	check if corrupt(),if corrput exit
	
	check if ack,if not exit
	
	fetch the ack number y from data
	
	if y <= sendBase:
		exit
	
	if(y > sendBase){
		#deal with windows size
		sendBase = y
	    compute boundry, deal with overflow
	    
        #deal with sampling
        
        # deal with packets pool
		poll packets from queue until the queue.peek.sequence_number > y
        
        # check if need restart timer
		if(there are currently not-yet ack segments)		{
		
            restart timer
		}
        
	}
		
}
```

##### deal with sampling()

```python
use a hashmap<seq_no, start_time>

check seq_no in the hashmap, it not, exit
else
get current time
compute sampleRTT, estimeted RTT, devRTT, timeoutInterval
```

