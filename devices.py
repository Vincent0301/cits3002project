# devices.py

from config import (
    HOST_A_CONFIG,
    HOST_B_CONFIG,
    ROUTER_R1_CONFIG,
    MAX_SEGMENT_DATA_SIZE,
    TRANSPORT_TYPE_ACK,
    TRANSPORT_TYPE_DATA,
)

from protocol import Segment, Packet, Frame


class Interface:
    def __init__(self, name, ip, mac, network=None, prefix=None):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.network = network
        self.prefix = prefix

        self.connected_device = None
        self.connected_interface_name = None

    def connect_to(self, other_device, other_interface_name):
        self.connected_device = other_device
        self.connected_interface_name = other_interface_name


class DataLinkLayer:
    def __init__(self, device, mac_table):
        self.device = device
        self.mac_table = dict(mac_table)
        self.learned_mac_table = {}

    def send_packet(self, packet, next_hop_ip, outgoing_interface_name):
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

        if frame.dst_mac != local_mac:
            return

        print(f"{self.device.name}: Layer 2: Packet delivered to Network Layer")

        self.device.network_layer.receive_packet(
            frame.payload,
            incoming_interface_name
        )


class NetworkLayer:
    def __init__(self, device, routing_table):
        self.device = device
        self.routing_table = routing_table

    def send_segment(self, segment, destination_ip):
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
        print(
            f"{self.device.name}: Layer 3: Packet received from Data Link Layer: "
            f"SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}"
        )

        print(f"{self.device.name}: Layer 3: Destination IP read: {packet.dst_ip}")

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
            return

        route = self.find_route(packet.dst_ip)

        if route is None:
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
        for route in self.routing_table:
            if destination_ip.startswith(route["prefix"]):
                return route

        return None


class TransportLayer:
    def __init__(self, device, port):
        self.device = device
        self.port = port

        self.next_data_seq = 0
        self.expected_data_seq = 0

        self.waiting_ack_seq = None
        self.ack_received = False

        self.last_ack_seq = None

    def send_application_data(self, data, destination_ip, destination_port):
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

    def receive_segment(self, segment, source_ip):
        print(f"{self.device.name}: Layer 4: Segment received from Network Layer")

        if not segment.length_is_valid():
            return

        if not segment.checksum_is_valid():
            if (
                segment.segment_type == TRANSPORT_TYPE_DATA
                and self.last_ack_seq is not None
            ):
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

    def receive_data(self, segment, source_ip):
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
            if self.last_ack_seq is not None:
                self.send_ack(
                    self.last_ack_seq,
                    source_ip,
                    segment.src_port
                )

    def send_ack(self, seq_num, destination_ip, destination_port):
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
        print(f"{self.device.name}: Layer 4: ACK received: seq={segment.seq_num}")

        if self.waiting_ack_seq == segment.seq_num:
            self.ack_received = True
        else:
            self.ack_received = False


class Host:
    def __init__(self, config):
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
        return False

    def connect_to(self, other_device, my_interface_name, other_interface_name):
        self.interfaces[my_interface_name].connect_to(
            other_device,
            other_interface_name
        )

    def get_default_interface_name(self):
        return self.interface_name

    def get_source_ip(self):
        return self.ip

    def get_interface_mac(self, interface_name):
        return self.interfaces[interface_name].mac

    def is_local_ip(self, ip):
        return ip == self.ip

    def send_frame(self, frame, outgoing_interface_name):
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
    def __init__(self, config):
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
        return True

    def connect_to(self, other_device, my_interface_name, other_interface_name):
        self.interfaces[my_interface_name].connect_to(
            other_device,
            other_interface_name
        )

    def get_source_ip(self):
        first_interface = next(iter(self.interfaces.values()))
        return first_interface.ip

    def get_interface_mac(self, interface_name):
        return self.interfaces[interface_name].mac

    def is_local_ip(self, ip):
        for interface in self.interfaces.values():
            if interface.ip == ip:
                return True

        return False

    def send_frame(self, frame, outgoing_interface_name):
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
        self.data_link_layer.receive_frame(
            frame,
            incoming_interface_name
        )


def connect_network(host_a, router_r1, host_b):
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
    host_a = Host(HOST_A_CONFIG)
    router_r1 = Router(ROUTER_R1_CONFIG)
    host_b = Host(HOST_B_CONFIG)

    connect_network(host_a, router_r1, host_b)

    return host_a, router_r1, host_b