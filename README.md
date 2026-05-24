\# CITS3002 Mini Internet Protocol Stack Simulator



\## 1. Overview



This project is a Python-based mini Internet protocol stack simulator. It demonstrates how Layer 2, Layer 3, and Layer 4 work together to transfer application data from one host to another host through a router.



The simulator uses the following fixed topology:



```text

Host A  ——  Router R1  ——  Host B

```



Host A and Host B are located in different IP networks. Therefore, Host A cannot send data directly to Host B at Layer 2. The data must first be sent to Router R1, and Router R1 then forwards it to Host B. After Host B receives a valid DATA segment, it sends an ACK segment back to Host A through Router R1.



This project does not use real socket programming or real network communication. All transmission is simulated using Python classes, objects, and method calls.



\---



\## 2. Group Members



```text

Student 1: Your Full Name, Student ID

Student 2: Your Partner Full Name, Student ID / N/A

```



\---



\## 3. Network Topology



The simulator uses two `/24` networks.



| Network | Address |

|---|---|

| Network 1 | `10.0.1.0/24` |

| Network 2 | `10.0.2.0/24` |



The devices and addresses are configured as follows:



| Device / Interface | IP Address | MAC Address |

|---|---|---|

| Host A | `10.0.1.10` | `AA:AA:AA:AA:AA:AA` |

| Router R1 Interface 1 | `10.0.1.1` | `BB:BB:BB:BB:BB:BB` |

| Router R1 Interface 2 | `10.0.2.1` | `CC:CC:CC:CC:CC:CC` |

| Host B | `10.0.2.20` | `DD:DD:DD:DD:DD:DD` |



The transport ports are:



| Host | Port |

|---|---:|

| Host A | `5000` |

| Host B | `80` |



\---



\## 4. File Structure



The project is organised into four main Python files.



| File | Purpose |

|---|---|

| `main.py` | Program entry point. It reads the command-line message size, builds the default topology, creates application data, and starts transmission from Host A to Host B. |

| `config.py` | Stores all fixed configuration values, including IP addresses, MAC addresses, interface names, routing tables, MAC tables, ports, and protocol constants. |

| `protocol.py` | Defines the protocol data structures: `Segment`, `Packet`, and `Frame`. It also implements the 16-bit Internet checksum functions. |

| `devices.py` | Implements the network devices and protocol-layer behaviour, including `Host`, `Router`, `Interface`, `DataLinkLayer`, `NetworkLayer`, and `TransportLayer`. |



\---



\## 5. How to Run



Run the program from the project directory using:



```bash

python main.py <message\_size\_in\_bytes>

```



For example:



```bash

python main.py 10

```



This command sends 10 bytes of application data from Host A to Host B.



The program validates the command-line argument. If no size is provided, if the value is not an integer, or if the value is negative, `main.py` prints an error message and exits.



\---



\## 6. Recommended Tests



The following commands can be used to test normal transmission and segmentation behaviour:



```bash

python main.py 10

python main.py 500

python main.py 501

python main.py 1000

python main.py 1200

```



Expected results:



| Input Size | Expected DATA Segments | Expected DATA Sequence Numbers | Expected Host B Data Delivery |

|---:|---:|---|---|

| `10` | 1 | `0` | `10` bytes |

| `500` | 1 | `0` | `500` bytes |

| `501` | 2 | `0, 1` | `500` bytes, then `1` byte |

| `1000` | 2 | `0, 1` | `500` bytes, then `500` bytes |

| `1200` | 3 | `0, 1, 0` | `500` bytes, `500` bytes, then `200` bytes |



A successful run should end with an ACK received by Host A. For example, for `python main.py 10`, the final important line is:



```text

Host A: Layer 4: ACK received: seq=0

```



\---



\## 7. Layer 2 Design: Data Link Layer



Layer 2 uses an Ethernet-like frame. The frame contains:



```text

Destination MAC

Source MAC

Frame Type

Payload

```



The payload of a Layer 2 frame is a Layer 3 IP-like packet.



The data link layer performs the following tasks:



\- receives packets from the network layer;

\- looks up the destination MAC address using the next-hop IP address;

\- creates Ethernet-like frames;

\- sends frames to the connected device;

\- receives frames from another device;

\- learns the source MAC address from incoming frames;

\- delivers valid packet payloads to the network layer.



For example, when Host A sends data to Host B, Host A sends the first frame to Router R1 Interface 1:



```text

SRC\_MAC = AA:AA:AA:AA:AA:AA

DST\_MAC = BB:BB:BB:BB:BB:BB

```



Router R1 then creates a new frame and forwards the packet to Host B through Interface 2:



```text

SRC\_MAC = CC:CC:CC:CC:CC:CC

DST\_MAC = DD:DD:DD:DD:DD:DD

```



This shows that MAC addresses change at every hop, while the source and destination IP addresses stay the same end-to-end.



\---



\## 8. Layer 3 Design: Network Layer



Layer 3 uses an IP-like packet. The packet contains:



```text

Source IP

Destination IP

TTL

Protocol

Total Length

Payload

```



The payload of a Layer 3 packet is a Layer 4 UDP-like segment.



The network layer performs the following tasks:



\- receives segments from the transport layer;

\- encapsulates segments into IP-like packets;

\- reads the destination IP address;

\- performs routing table lookup;

\- determines the next-hop IP address;

\- selects the outgoing interface;

\- decrements TTL when a router forwards a packet;

\- drops packets if TTL expires;

\- delivers packets locally when the destination IP matches the receiving host.



When Host A sends data to Host B, the packet is created with:



```text

SRC\_IP = 10.0.1.10

DST\_IP = 10.0.2.20

TTL = 100

Protocol = 17

```



When Router R1 forwards the packet, it decrements TTL:



```text

100 → 99

```



The routing tables in `config.py` determine how packets move between the two networks. For example, Router R1 forwards packets for `10.0.2.0/24` through `Interface 2` and packets for `10.0.1.0/24` through `Interface 1`.



\---



\## 9. Layer 4 Design: Transport Layer



Layer 4 uses a UDP-like segment with ACK support. The segment contains:



```text

Source Port

Destination Port

Length

Checksum

Type

Sequence Number

Data

```



The project uses two segment types:



| Type | Meaning |

|---:|---|

| `0` | DATA |

| `1` | ACK |



The transport layer performs the following tasks:



\- receives application data;

\- splits large data into chunks;

\- creates DATA segments;

\- calculates checksum values;

\- sends segments to the network layer;

\- receives DATA and ACK segments from the network layer;

\- verifies checksum values;

\- delivers valid DATA to the application layer;

\- creates ACK segments;

\- uses alternating sequence numbers for reliable transfer.



The sequence number follows the alternating bit pattern:



```text

0, 1, 0, 1, ...

```



For each DATA segment, the receiver replies with an ACK that has the same sequence number.



Example:



```text

Host A sends DATA seq=0

Host B replies ACK seq=0

Host A sends DATA seq=1

Host B replies ACK seq=1

```



\---



\## 10. Segmentation



The maximum application data size carried by one Layer 4 segment is:



```text

500 bytes

```



If the application data is larger than 500 bytes, the transport layer splits it into multiple chunks.



Examples:



```text

10 bytes   → 1 segment

500 bytes  → 1 segment

501 bytes  → 2 segments: 500 + 1

1000 bytes → 2 segments: 500 + 500

1200 bytes → 3 segments: 500 + 500 + 200

```



Each DATA segment must be acknowledged before the next DATA segment is sent.



\---



\## 11. Checksum Design



The simulator implements a 16-bit Internet checksum in `protocol.py`.



The checksum is calculated over the transport segment fields. During checksum calculation, the checksum field itself is treated as zero. The receiver recalculates the checksum and compares it with the value stored in the segment.



If the checksum is valid, the segment can be processed. If the checksum is invalid, the segment is dropped.



Although the project assumes no frame corruption and no packet loss during normal testing, the checksum logic is implemented to demonstrate error detection.



\---



\## 12. Example End-to-End Flow



For the command:



```bash

python main.py 10

```



The simulator performs the following steps:



```text

1\. Host A receives 10 bytes of application data.

2\. Host A Layer 4 creates a DATA segment with seq=0.

3\. Host A Layer 3 encapsulates the segment into an IP-like packet.

4\. Host A Layer 2 encapsulates the packet into an Ethernet-like frame.

5\. Host A sends the frame to Router R1 Interface 1.

6\. Router R1 learns Host A's source MAC address.

7\. Router R1 reads the destination IP and decrements TTL from 100 to 99.

8\. Router R1 forwards the packet through Interface 2 to Host B.

9\. Host B receives the frame and delivers the segment to Layer 4.

10\. Host B verifies the checksum and delivers the DATA to the application layer.

11\. Host B creates an ACK segment with seq=0.

12\. The ACK travels back through Router R1 to Host A.

13\. Host A verifies the checksum and receives ACK seq=0.

```



The output logs show each layer's actions during this process.



\---



\## 13. Output and Logging



The simulator prints logs for the main actions at each layer.



Layer 2 logs include:



\- packet received from network layer;

\- destination MAC lookup;

\- frame creation;

\- frame sending or forwarding;

\- frame receiving;

\- source MAC learning;

\- packet delivery to network layer.



Layer 3 logs include:



\- segment received from transport layer;

\- packet received from data link layer;

\- destination IP reading;

\- routing table lookup;

\- next-hop IP decision;

\- outgoing interface selection;

\- TTL decrement;

\- local delivery.



Layer 4 logs include:



\- application data received;

\- checksum computation;

\- DATA segment creation;

\- ACK segment creation;

\- segment sending;

\- segment receiving;

\- checksum verification;

\- DATA delivery;

\- ACK receiving.



For a 10-byte message, the successful transmission ends with:



```text

Host A: Layer 4: ACK received: seq=0

```



\---



\## 14. Constraints and Assumptions



This simulator follows these constraints and assumptions:



\- no real socket programming is used;

\- no external networking libraries are used;

\- the topology is fixed as `Host A -- Router R1 -- Host B`;

\- Host A and Host B are in different networks;

\- Router R1 is required for communication between Host A and Host B;

\- normal tests assume no packet loss;

\- normal tests assume no frame corruption;

\- transmissions are deterministic;

\- Python object references and method calls are used to simulate network transmission.



\---



\## 15. Conclusion



This project implements a mini Internet protocol stack simulator using Python. It demonstrates how application data is encapsulated and transmitted through Layer 4, Layer 3, and Layer 2.



The simulator supports Ethernet-like frames, IP-like packets, UDP-like segments, checksum verification, TTL handling, routing through Router R1, ACK generation, and alternating-bit sequence numbers. It also supports segmentation for messages larger than 500 bytes.



Overall, the simulator shows a complete end-to-end communication process from Host A to Host B and back to Host A through an ACK.

