# config.py

# ============================================================
# Device Names
# ============================================================

HOST_A_NAME = "Host A"
HOST_B_NAME = "Host B"
ROUTER_R1_NAME = "Router R1"


# ============================================================
# Network Information
# ============================================================

NETWORK_1 = "10.0.1.0/24"
NETWORK_2 = "10.0.2.0/24"

NETWORK_1_PREFIX = "10.0.1."
NETWORK_2_PREFIX = "10.0.2."


# ============================================================
# IP Addresses
# ============================================================

HOST_A_IP = "10.0.1.10"
HOST_B_IP = "10.0.2.20"

ROUTER_R1_IF1_IP = "10.0.1.1"
ROUTER_R1_IF2_IP = "10.0.2.1"


# ============================================================
# MAC Addresses
# ============================================================

HOST_A_MAC = "AA:AA:AA:AA:AA:AA"
HOST_B_MAC = "DD:DD:DD:DD:DD:DD"

ROUTER_R1_IF1_MAC = "BB:BB:BB:BB:BB:BB"
ROUTER_R1_IF2_MAC = "CC:CC:CC:CC:CC:CC"


# ============================================================
# Interface Names
# ============================================================

HOST_INTERFACE = "eth0"

ROUTER_R1_INTERFACE_1 = "Interface 1"
ROUTER_R1_INTERFACE_2 = "Interface 2"


# ============================================================
# Protocol Constants
# These names are used by protocol.py
# ============================================================

ETHERNET_TYPE_IPV4 = 0x0800

NETWORK_PROTOCOL_UDP = 17

DEFAULT_TTL = 100

TRANSPORT_TYPE_DATA = 0
TRANSPORT_TYPE_ACK = 1

L4_HEADER_SIZE = 10
L3_HEADER_SIZE = 12
L2_HEADER_SIZE = 14

MAX_SEGMENT_DATA_SIZE = 500


# ============================================================
# Compatibility Constants
# These names are used by older versions of config/devices code
# ============================================================

ETH_TYPE_IPV4 = ETHERNET_TYPE_IPV4
IP_PROTOCOL_UDP = NETWORK_PROTOCOL_UDP

DATA_TYPE = TRANSPORT_TYPE_DATA
ACK_TYPE = TRANSPORT_TYPE_ACK

TRANSPORT_HEADER_SIZE = L4_HEADER_SIZE
IP_HEADER_SIZE = L3_HEADER_SIZE
ETHERNET_HEADER_SIZE = L2_HEADER_SIZE


# ============================================================
# Port Numbers
# ============================================================

HOST_A_PORT = 5000
HOST_B_PORT = 80

# main.py may use this name
HOST_B_SERVICE_PORT = HOST_B_PORT


# ============================================================
# MAC Tables
# next-hop IP -> destination MAC
# ============================================================

HOST_A_MAC_TABLE = {
    ROUTER_R1_IF1_IP: ROUTER_R1_IF1_MAC
}

HOST_B_MAC_TABLE = {
    ROUTER_R1_IF2_IP: ROUTER_R1_IF2_MAC
}

ROUTER_R1_MAC_TABLE = {
    HOST_A_IP: HOST_A_MAC,
    HOST_B_IP: HOST_B_MAC
}


# ============================================================
# Routing Tables
# ============================================================

HOST_A_ROUTING_TABLE = [
    {
        "network": NETWORK_1,
        "prefix": NETWORK_1_PREFIX,
        "interface": HOST_INTERFACE,
        "next_hop": None
    },
    {
        "network": NETWORK_2,
        "prefix": NETWORK_2_PREFIX,
        "interface": HOST_INTERFACE,
        "next_hop": ROUTER_R1_IF1_IP
    }
]

HOST_B_ROUTING_TABLE = [
    {
        "network": NETWORK_2,
        "prefix": NETWORK_2_PREFIX,
        "interface": HOST_INTERFACE,
        "next_hop": None
    },
    {
        "network": NETWORK_1,
        "prefix": NETWORK_1_PREFIX,
        "interface": HOST_INTERFACE,
        "next_hop": ROUTER_R1_IF2_IP
    }
]

ROUTER_R1_ROUTING_TABLE = [
    {
        "network": NETWORK_1,
        "prefix": NETWORK_1_PREFIX,
        "interface": ROUTER_R1_INTERFACE_1,
        "next_hop": None
    },
    {
        "network": NETWORK_2,
        "prefix": NETWORK_2_PREFIX,
        "interface": ROUTER_R1_INTERFACE_2,
        "next_hop": None
    }
]


# ============================================================
# Device Configs
# ============================================================

HOST_A_CONFIG = {
    "name": HOST_A_NAME,
    "ip": HOST_A_IP,
    "mac": HOST_A_MAC,
    "interface": HOST_INTERFACE,
    "mac_table": HOST_A_MAC_TABLE,
    "routing_table": HOST_A_ROUTING_TABLE,
    "port": HOST_A_PORT
}

HOST_B_CONFIG = {
    "name": HOST_B_NAME,
    "ip": HOST_B_IP,
    "mac": HOST_B_MAC,
    "interface": HOST_INTERFACE,
    "mac_table": HOST_B_MAC_TABLE,
    "routing_table": HOST_B_ROUTING_TABLE,
    "port": HOST_B_PORT
}

ROUTER_R1_CONFIG = {
    "name": ROUTER_R1_NAME,
    "interfaces": {
        ROUTER_R1_INTERFACE_1: {
            "ip": ROUTER_R1_IF1_IP,
            "mac": ROUTER_R1_IF1_MAC,
            "network": NETWORK_1,
            "prefix": NETWORK_1_PREFIX
        },
        ROUTER_R1_INTERFACE_2: {
            "ip": ROUTER_R1_IF2_IP,
            "mac": ROUTER_R1_IF2_MAC,
            "network": NETWORK_2,
            "prefix": NETWORK_2_PREFIX
        }
    },
    "mac_table": ROUTER_R1_MAC_TABLE,
    "routing_table": ROUTER_R1_ROUTING_TABLE
}


# ============================================================
# Default Application Settings
# ============================================================

DEFAULT_SOURCE_IP = HOST_A_IP
DEFAULT_DESTINATION_IP = HOST_B_IP

DEFAULT_SOURCE_PORT = HOST_A_PORT
DEFAULT_DESTINATION_PORT = HOST_B_PORT