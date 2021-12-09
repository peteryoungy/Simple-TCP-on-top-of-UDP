### Program Design

#### ⅠClient: tcpclient.py

There are three major events related to data transmission and retransmission in the tcpclient: data received from application above; timer timeout; and ACK receipt.

##### Part I: Send packets

###### Generate segments

There are mainly 4 steps when generating a complete TCP segment.

- Get the head field value without checksum
- Get the content to be sent
- Based on these 2 parts, compute the checksum
- Concatenate all the parts to form a single TCP segment

###### Buffer

I implement a buffer which saves all the segments that has been sent but not yet ACKed. I use a `queue.Queue()` to prove multi-thread safe.

- Every time before sending a segment, push the segment to the queue
- When client receives an valid ACK, pop all the element from the queue whose segment number is smaller than the ACK number
- When a retransmission occurs, get segment at the top of the queue and resend it

###### Sample 

We need to do sampling to implement dynamic timeout interval mechanism. It works with the following logic:

- There's at most 1 segment being sampled at any time. 
- When the sender is going to send a packet, it will check if a segment has already been sampled. If the answer is false, sender will sample this segment, record it as `t`.
- When a retransmission occurs, it will check whether the retransmitted segment is sampled. If it is, clear the sample record, because we don't want to do sampling with retransmission segments. 
- The client receive an valid ACK whose ACK number `y` is equal to or bigger than the lower bound `s` of the current window. 
  - If `y` == `s` and `y` == `t`, update the timeout interval with EWMA formular.
  - If `y` == `s` and `y` > `t`, reset the timeout interval to default value, clear the sample record.
  - Else, reset the timeout interval to default value.

##### Part II: Retransmission

The retransmission part works on the same thread with part1. The basic idea here is Round-Robin the part1 and part2. Each time after a segment is sent, the thread will check whether there's a retransmission sign. At any time, only one part is working. The reason I do this is to make code logic easier and avoid more concerns about the multi-thread synchronized. In addition, this could  also achieve good performance. 

In TCP, there are 2 conditions that will trigger the retransmission: timer timeout and duplicate more than 3 times.

###### Timer workflow

The timer is mainly used for a timeout retransmission.

- When a segment is going to be sent, it will check whether the timer is on. It not, it will start the timer.
- When a retransmission occurs, it will restart the timer with doubled timeout interval.
- When a valid ACK is received. 
  - If there's no unACKed segment in the window, it will turn off the timer.
  - Otherwise it will also restart the timer with the current timeout interval. 

###### Timeout Detection

The whole client maintains only one timer which indicates whether the earliest unACKed segment is timeout. 

When a timeout occurs, it will trigger a retransmission.

###### Fast Retransmission

The client will record number of duplicate ACK number it has received. If it is larger than 3, then will trigger a fast retransmission.

##### Part III: ACK receipt

The ACK receipt works on a different thread `ack_handler`. It receive ACKs from the server and update the status of teh client.

###### Thread synchronization

To prove multi-thread safe, I implement the thread synchronization with `threading.Lock()`. When Thread `send_handler` and thread`ack_handler` visit the shared memory at the same time, the lock will prove that at any time, only one thread can read or write. Here are all the locks I used in the program and its corresponding fields.

- window_lock: send_base, boundary 
- dup_lock: dup_num, dup_retrans
- is_timer_on_lock: is_timer_on
- timer_start_time_lock: timer_start_time
- timeout_interval_lock: timeout_interval
- sample_tuple_lock: sample_tuple

#### Ⅱ Server: tcpserver.py

The tcpserver receives data from newudpl, write the content into an output file adn send ACKs to the client. 

###### Deal with disorder

The basic reason that the TCP is more efficient is that TCP uses a buffer to store disordered segments. In real implmentaiton, I use a Hash Table to map the sequence number to the content. Actually, the Hash Table is called dictionary in Python.

Each time a segment is received, it will search in the Hash Table to check whether there are consecutive segments that have arrived at the server before. Then it will retrieve all the consecutive segments from the Hash Table and write them to the output file. 

###### Server Workflow

We are not going to implement the delayed ACK. The TCP server works like this:

- When receive a packet, check if it is corrupted first. 
  - If it is corrupted, discard the segment and send ACK with the original `expected_seq_num`.
- Check whether it is a FIN
  - If the FIN bit is 1, send the ACK with FIN = 1 and ACK = 1
- Check the sequence number `ack_num` of the segment and compared with the expected sequence number `expected_seq_num`
  - if `ack_num` < `expected_seq_num`, discard the segment and send ACK with the original `expected_seq_num`
  - if `ack_num` > `expected_seq_num`, push it to the buffer and send ACK with the original  `expected_seq_num`
  - if `ack_num` == `expected_seq_num`, write the content and all the consecutive content it has found in the buffer to the output file, update the `expected_seq_num` and send ACK with the updated `expected_seq_num`

