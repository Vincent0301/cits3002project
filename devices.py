# devices.py

from ipaddress import ip_address, ip_network

from config import (
    HOST_A_CONFIG,
    HOST_B_CONFIG,
    ROUTER_R1_CONFIG,
    ETHERNET_TYPE_IPV4,
    NETWORK_PROTOCOL_UDP,
    L3_HEADER_SIZE,
    L4_HEADER_SIZE,
    MAX_SEGMENT_DATA_SIZE,
    TRANSPORT_TYPE_ACK,
    TRANSPORT_TYPE_DATA,
)

from protocol import Segment, Packet, Frame


class Interface:
    """Represents one network interface on a host or router."""

    def __init__(self, name, ip, mac, network=None, prefix=None):
        """Create an interface with an IP address, MAC address, and optional network information."""
        self.name = name
        self.ip = ip
        self.mac = mac
        self.network = network
        self.prefix = prefix

        self.connected_device = None
        self.connected_interface_name = None

    def connect_to(self, other_device, other_interface_name):
        """Connect this interface to another device's interface."""
        self.connected_device = other_device
        self.connected_interface_name = other_interface_name


class DataLinkLayer:
    """Implements Layer 2 frame creation, MAC lookup, MAC learning, and frame delivery."""

    def __init__(self, device, mac_table):
        """Create a data link layer for a device with a static next-hop IP to MAC table."""
        self.device = device
        self.mac_table = dict(mac_table)
        self.learned_mac_table = {}

    def send_packet(self, packet, next_hop_ip, outgoing_interface_name):
        """Encapsulate a Layer 3 packet into a Layer 2 frame and send it to the next hop."""
        print(f"{self.device.name}: Layer 2: Packet received from Network Layer")

        dst_mac = self.mac_table.get(next_hop_ip)

        if dst_mac is None:
            print(
                f"{self.device.name}: Layer 2: Destination MAC lookup failed "
                f"for next-hop IP ({next_hop_ip})"
            )
            return

        print(
            f"{self.device.name}: Layer 2: Destination MAC lookup for next-hop IP "
            f"({next_hop_ip}) → {dst_mac}"
        )

        src_mac = self.device.get_interface_mac(outgoing_interface_name)

        frame = Frame.create(
            src_mac=src_mac,
            dst_mac=dst_mac,
            payload=packet
        )

        print(
            f"{self.device.name}: Layer 2: Frame created: "
            f"SRC_MAC={src_mac}, DST_MAC={dst_mac}"
        )

        if self.device.is_router():
            print(f"{self.device.name}: Layer 2: Frame forwarded on {outgoing_interface_name}")
        else:
            print(f"{self.device.name}: Layer 2: Frame sent")

        self.device.send_frame(frame, outgoing_interface_name)

    def receive_frame(self, frame, incoming_interface_name):
        """Receive a Layer 2 frame, validate it, learn the source MAC, and deliver the packet upward."""
        if self.device.is_router():
            print(f"{self.device.name}: Layer 2: Frame received on {incoming_interface_name}")
            print(
                f"{self.device.name}: Layer 2: Source MAC learned: "
                f"{frame.src_mac} on {incoming_interface_name}"
            )
            local_mac = self.device.get_interface_mac(incoming_interface_name)

        else:
            print(f"{self.device.name}: Layer 2: Frame received")
            print(
                f"{self.device.name}: Layer 2: Source MAC learned: "
                f"{frame.src_mac}"
            )
            local_mac = self.device.get_interface_mac(
                self.device.get_default_interface_name()
            )

        self.learned_mac_table[frame.src_mac] = incoming_interface_name

        if frame.frame_type != ETHERNET_TYPE_IPV4:
            print(
                f"{self.device.name}: Layer 2: Unsupported frame type: "
                f"expected 0x{ETHERNET_TYPE_IPV4:04X}, got 0x{frame.frame_type:04X}"
            )
            print(f"{self.device.name}: Layer 2: Frame dropped due to unsupported frame type")
            return

        if frame.dst_mac != local_mac:
            print(
                f"{self.device.name}: Layer 2: Destination MAC mismatch: "
                f"expected {local_mac}, got {frame.dst_mac}"
            )
            print(
                f"{self.device.name}: Layer 2: Frame dropped because not addressed "
                f"to this interface"
            )
            return

        print(f"{self.device.name}: Layer 2: Packet delivered to Network Layer")

        self.device.network_layer.receive_packet(
            frame.payload,
            incoming_interface_name
        )


class NetworkLayer:
    """Implements Layer 3 IP-like packet creation, routing, forwarding, TTL handling, and delivery."""

    def __init__(self, device, routing_table):
        """Create a network layer for a device with a routing table."""
        self.device = device
        self.routing_table = routing_table

    def send_segment(self, segment, destination_ip):
        """Encapsulate a Layer 4 segment into a Layer 3 packet and send it to Layer 2."""
        source_ip = self.device.get_source_ip()

        packet = Packet.create(
            src_ip=source_ip,
            dst_ip=destination_ip,
            payload=segment
        )

        print(
            f"{self.device.name}: Layer 3: Segment received from Transport Layer: "
            f"SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}"
        )

        print(f"{self.device.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        route = self.find_route(packet.dst_ip)

        if route is None:
            print(f"{self.device.name}: Layer 3: No route found. Packet dropped")
            return

        print(f"{self.device.name}: Layer 3: Routing table lookup performed")

        if route["next_hop"] is None:
            next_hop_ip = packet.dst_ip
        else:
            next_hop_ip = route["next_hop"]

        outgoing_interface_name = route["interface"]

        print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop_ip}")

        if self.device.is_router():
            print(
                f"{self.device.name}: Layer 3: Outgoing interface selected "
                f"({outgoing_interface_name})"
            )
        else:
            print(f"{self.device.name}: Layer 3: Outgoing interface selected")

        print(f"{self.device.name}: Layer 3: Packet forwarded to Data Link Layer")

        self.device.data_link_layer.send_packet(
            packet,
            next_hop_ip,
            outgoing_interface_name
        )

    def receive_packet(self, packet, incoming_interface_name):
        """Receive a Layer 3 packet, validate it, forward it, or deliver it to Layer 4."""
        print(
            f"{self.device.name}: Layer 3: Packet received from Data Link Layer: "
            f"SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}"
        )

        print(f"{self.device.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        if not packet.length_is_valid():
            expected_length = L3_HEADER_SIZE + packet.payload.length
            print(
                f"{self.device.name}: Layer 3: Invalid packet total length: "
                f"header field={packet.total_length}, actual length={expected_length}"
            )
            print(f"{self.device.name}: Layer 3: Packet dropped due to invalid total length")
            return

        if packet.protocol != NETWORK_PROTOCOL_UDP:
            print(
                f"{self.device.name}: Layer 3: Unsupported protocol: "
                f"expected {NETWORK_PROTOCOL_UDP}, got {packet.protocol}"
            )
            print(f"{self.device.name}: Layer 3: Packet dropped due to unsupported protocol")
            return

        if self.device.is_local_ip(packet.dst_ip):
            print(f"{self.device.name}: Layer 3: Packet identified as local delivery")
            print(f"{self.device.name}: Layer 3: Segment delivered to Transport Layer")

            if self.device.transport_layer is not None:
                self.device.transport_layer.receive_segment(
                    packet.payload,
                    packet.src_ip
                )

            return

        old_ttl = packet.ttl
        packet.ttl -= 1

        print(f"{self.device.name}: Layer 3: TTL decremented: {old_ttl} → {packet.ttl}")

        if packet.ttl <= 0:
            print(f"{self.device.name}: Layer 3: Packet dropped due to TTL expiry")
            return

        route = self.find_route(packet.dst_ip)

        if route is None:
            print(f"{self.device.name}: Layer 3: No route found. Packet dropped")
            return

        print(f"{self.device.name}: Layer 3: Routing table lookup performed")

        if route["next_hop"] is None:
            next_hop_ip = packet.dst_ip
        else:
            next_hop_ip = route["next_hop"]

        outgoing_interface_name = route["interface"]

        print(f"{self.device.name}: Layer 3: Next-hop IP determined: {next_hop_ip}")

        if self.device.is_router():
            print(
                f"{self.device.name}: Layer 3: Outgoing interface selected "
                f"({outgoing_interface_name})"
            )
        else:
            print(f"{self.device.name}: Layer 3: Outgoing interface selected")

        print(f"{self.device.name}: Layer 3: Packet forwarded to Data Link Layer")

        self.device.data_link_layer.send_packet(
            packet,
            next_hop_ip,
            outgoing_interface_name
        )

    def find_route(self, destination_ip):
        """Find the longest-prefix matching route for a destination IP address."""
        destination = ip_address(destination_ip)
        best_route = None
        best_prefix_length = -1

        for route in self.routing_table:
            network = ip_network(route["network"], strict=False)

            if destination in network and network.prefixlen > best_prefix_length:
                best_route = route
                best_prefix_length = network.prefixlen

        return best_route


class TransportLayer:
    """Implements Layer 4 UDP-like DATA/ACK communication with alternating-bit reliability."""

    def __init__(self, device, port):
        """Create a transport layer with a local application port and sequence-number state."""
        self.device = device
        self.port = port

        self.next_data_seq = 0
        self.expected_data_seq = 0

        self.waiting_ack_seq = None
        self.ack_received = False

        self.last_ack_seq = None

    def send_application_data(self, data, destination_ip, destination_port):
        """Split application data into chunks and send each chunk as a DATA segment."""
        if isinstance(data, str):
            data = data.encode("utf-8")

        print(
            f"{self.device.name}: Layer 4: Data received from Application Layer. "
            f"Data size={len(data)}"
        )

        chunks = []

        if len(data) == 0:
            chunks.append(b"")
        else:
            for start in range(0, len(data), MAX_SEGMENT_DATA_SIZE):
                chunk = data[start:start + MAX_SEGMENT_DATA_SIZE]
                chunks.append(chunk)

        for chunk in chunks:
            self.send_data_chunk(
                chunk,
                destination_ip,
                destination_port
            )

    def send_data_chunk(self, chunk, destination_ip, destination_port):
        """Send one DATA segment and retransmit it if the ACK is incorrect."""
        seq_num = self.next_data_seq

        while True:
            segment = Segment.create_data(
                src_port=self.port,
                dst_port=destination_port,
                seq_num=seq_num,
                data=chunk
            )

            segment.checksum = segment.compute_checksum()

            print(f"{self.device.name}: Layer 4: Checksum computed")

            print(
                f"{self.device.name}: Layer 4: Segment created by adding "
                f"transport layer header (DATA, seq={seq_num}) (encapsulation)"
            )

            print(f"{self.device.name}: Layer 4: Segment sent to Network Layer")

            self.waiting_ack_seq = seq_num
            self.ack_received = False

            self.device.network_layer.send_segment(
                segment,
                destination_ip
            )

            if self.ack_received:
                self.next_data_seq = 1 - self.next_data_seq
                self.waiting_ack_seq = None
                return

            print(
                f"{self.device.name}: Layer 4: Retransmitting current DATA "
                f"segment due to incorrect ACK"
            )

    def receive_segment(self, segment, source_ip):
        """Receive a Layer 4 segment, validate port, length, checksum, and handle DATA or ACK."""
        print(f"{self.device.name}: Layer 4: Segment received from Network Layer")

        if segment.dst_port != self.port:
            print(
                f"{self.device.name}: Layer 4: Destination port mismatch: "
                f"expected {self.port}, got {segment.dst_port}"
            )
            print(f"{self.device.name}: Layer 4: Segment discarded due to wrong destination port")
            return

        if not segment.length_is_valid():
            actual_length = L4_HEADER_SIZE + len(segment.data)
            print(
                f"{self.device.name}: Layer 4: Invalid segment length: "
                f"header field={segment.length}, actual length={actual_length}"
            )
            print(f"{self.device.name}: Layer 4: Segment discarded due to invalid length")
            return

        if not segment.checksum_is_valid():
            print(f"{self.device.name}: Layer 4: Checksum verification failed")
            print(f"{self.device.name}: Layer 4: Segment discarded due to checksum error")

            if (
                segment.segment_type == TRANSPORT_TYPE_DATA
                and self.last_ack_seq is not None
            ):
                print(
                    f"{self.device.name}: Layer 4: Re-sending last ACK: "
                    f"seq={self.last_ack_seq}"
                )
                self.send_ack(
                    self.last_ack_seq,
                    source_ip,
                    segment.src_port
                )

            return

        print(f"{self.device.name}: Layer 4: Checksum verified")

        if segment.segment_type == TRANSPORT_TYPE_DATA:
            self.receive_data(segment, source_ip)

        elif segment.segment_type == TRANSPORT_TYPE_ACK:
            self.receive_ack(segment)

        else:
            print(
                f"{self.device.name}: Layer 4: Unknown segment type: "
                f"{segment.segment_type}"
            )
            print(f"{self.device.name}: Layer 4: Segment discarded due to unknown type")

    def receive_data(self, segment, source_ip):
        """Handle an incoming DATA segment and send the correct ACK."""
        if segment.seq_num == self.expected_data_seq:
            print(
                f"{self.device.name}: Layer 4: DATA segment delivered to "
                f"Application Layer. Data size={len(segment.data)}"
            )

            self.last_ack_seq = segment.seq_num

            self.send_ack(
                segment.seq_num,
                source_ip,
                segment.src_port
            )

            self.expected_data_seq = 1 - self.expected_data_seq

        else:
            print(
                f"{self.device.name}: Layer 4: Duplicate DATA segment received: "
                f"expected seq={self.expected_data_seq}, got seq={segment.seq_num}"
            )

            if self.last_ack_seq is not None:
                print(
                    f"{self.device.name}: Layer 4: Re-sending last ACK: "
                    f"seq={self.last_ack_seq}"
                )
                self.send_ack(
                    self.last_ack_seq,
                    source_ip,
                    segment.src_port
                )

    def send_ack(self, seq_num, destination_ip, destination_port):
        """Create and send an ACK segment for a received DATA segment."""
        ack_segment = Segment.create_ack(
            src_port=self.port,
            dst_port=destination_port,
            seq_num=seq_num
        )

        ack_segment.checksum = ack_segment.compute_checksum()

        print(
            f"{self.device.name}: Layer 4: Segment created by adding "
            f"transport layer header (ACK, seq={seq_num})"
        )

        print(f"{self.device.name}: Layer 4: Segment sent to Network Layer")

        self.device.network_layer.send_segment(
            ack_segment,
            destination_ip
        )

    def receive_ack(self, segment):
        """Handle an incoming ACK segment and verify that it matches the expected sequence number."""
        print(f"{self.device.name}: Layer 4: ACK received: seq={segment.seq_num}")

        if self.waiting_ack_seq == segment.seq_num:
            self.ack_received = True
        else:
            print(
                f"{self.device.name}: Layer 4: Incorrect ACK: "
                f"expected seq={self.waiting_ack_seq}, got seq={segment.seq_num}"
            )
            self.ack_received = False


class Host:
    """Represents Host A or Host B with one interface and three protocol layers."""

    def __init__(self, config):
        """Create a host using its configuration dictionary."""
        self.name = config["name"]
        self.ip = config["ip"]
        self.mac = config["mac"]
        self.port = config["port"]

        self.mac_table = config["mac_table"]
        self.routing_table = config["routing_table"]

        self.interface_name = config["interface"]

        self.interfaces = {
            self.interface_name: Interface(
                self.interface_name,
                self.ip,
                self.mac
            )
        }

        self.data_link_layer = DataLinkLayer(
            self,
            self.mac_table
        )

        self.network_layer = NetworkLayer(
            self,
            self.routing_table
        )

        self.transport_layer = TransportLayer(
            self,
            self.port
        )

    def is_router(self):
        """Return False because this device is a host."""
        return False

    def connect_to(self, other_device, my_interface_name, other_interface_name):
        """Connect this host's interface to another device."""
        self.interfaces[my_interface_name].connect_to(
            other_device,
            other_interface_name
        )

    def get_default_interface_name(self):
        """Return the host's single interface name."""
        return self.interface_name

    def get_source_ip(self):
        """Return the host IP address used as the source IP."""
        return self.ip

    def get_interface_mac(self, interface_name):
        """Return the MAC address for the selected interface."""
        return self.interfaces[interface_name].mac

    def is_local_ip(self, ip):
        """Check whether an IP address belongs to this host."""
        return ip == self.ip

    def send_frame(self, frame, outgoing_interface_name):
        """Send a frame to the device connected to the outgoing interface."""
        interface = self.interfaces[outgoing_interface_name]

        if interface.connected_device is None:
            return

        receiver = interface.connected_device
        receiver_interface_name = interface.connected_interface_name

        receiver.receive_frame(
            frame,
            receiver_interface_name
        )

    def receive_frame(self, frame, incoming_interface_name=None):
        """Receive a frame from a connected device."""
        if incoming_interface_name is None:
            incoming_interface_name = self.interface_name

        self.data_link_layer.receive_frame(
            frame,
            incoming_interface_name
        )

    def send_application_data(
        self,
        data,
        destination_ip=None,
        destination_port=None,
        dst_ip=None,
        dst_port=None
    ):
        """Send application data from this host to a destination IP and port."""
        if destination_ip is None:
            destination_ip = dst_ip

        if destination_port is None:
            destination_port = dst_port

        self.transport_layer.send_application_data(
            data,
            destination_ip,
            destination_port
        )


class Router:
    """Represents Router R1 with two interfaces and Layer 2/Layer 3 forwarding logic."""

    def __init__(self, config):
        """Create a router using its configuration dictionary."""
        self.name = config["name"]

        self.mac_table = config["mac_table"]
        self.routing_table = config["routing_table"]

        self.interfaces = {}

        for interface_name, interface_config in config["interfaces"].items():
            self.interfaces[interface_name] = Interface(
                interface_name,
                interface_config["ip"],
                interface_config["mac"],
                interface_config.get("network"),
                interface_config.get("prefix")
            )

        self.data_link_layer = DataLinkLayer(
            self,
            self.mac_table
        )

        self.network_layer = NetworkLayer(
            self,
            self.routing_table
        )

        self.transport_layer = None

    def is_router(self):
        """Return True because this device is a router."""
        return True

    def connect_to(self, other_device, my_interface_name, other_interface_name):
        """Connect one router interface to another device."""
        self.interfaces[my_interface_name].connect_to(
            other_device,
            other_interface_name
        )

    def get_source_ip(self):
        """Return a router interface IP address when the router needs to originate a packet."""
        first_interface = next(iter(self.interfaces.values()))
        return first_interface.ip

    def get_interface_mac(self, interface_name):
        """Return the MAC address of a router interface."""
        return self.interfaces[interface_name].mac

    def is_local_ip(self, ip):
        """Check whether an IP address belongs to one of the router interfaces."""
        for interface in self.interfaces.values():
            if interface.ip == ip:
                return True

        return False

    def send_frame(self, frame, outgoing_interface_name):
        """Forward a frame through the selected outgoing interface."""
        interface = self.interfaces[outgoing_interface_name]

        if interface.connected_device is None:
            return

        receiver = interface.connected_device
        receiver_interface_name = interface.connected_interface_name

        receiver.receive_frame(
            frame,
            receiver_interface_name
        )

    def receive_frame(self, frame, incoming_interface_name):
        """Receive a frame on one router interface."""
        self.data_link_layer.receive_frame(
            frame,
            incoming_interface_name
        )


def connect_network(host_a, router_r1, host_b):
    """Connect Host A, Router R1, and Host B into the fixed project topology."""
    host_a.connect_to(
        router_r1,
        host_a.get_default_interface_name(),
        "Interface 1"
    )

    router_r1.connect_to(
        host_a,
        "Interface 1",
        host_a.get_default_interface_name()
    )

    host_b.connect_to(
        router_r1,
        host_b.get_default_interface_name(),
        "Interface 2"
    )

    router_r1.connect_to(
        host_b,
        "Interface 2",
        host_b.get_default_interface_name()
    )


def build_default_network():
    """Build and return the default Host A -- Router R1 -- Host B network."""
    host_a = Host(HOST_A_CONFIG)
    router_r1 = Router(ROUTER_R1_CONFIG)
    host_b = Host(HOST_B_CONFIG)

    connect_network(host_a, router_r1, host_b)

    return host_a, router_r1, host_b