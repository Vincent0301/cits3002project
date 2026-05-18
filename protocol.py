"""Layer 2、Layer 3、Layer 4 的协议数据结构。

本文件只描述 header 字段、长度字段和 checksum 等“协议格式”。
真正的发送、接收、路由、ACK 状态机放在 devices.py 中实现。
"""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    DEFAULT_TTL,
    ETHERNET_TYPE_IPV4,
    L3_HEADER_SIZE,
    L4_HEADER_SIZE,
    NETWORK_PROTOCOL_UDP,
    TRANSPORT_TYPE_ACK,
    TRANSPORT_TYPE_DATA,
)


def _ones_complement_sum(data: bytes) -> int:
    """计算 16-bit one's-complement sum。

    Week 8 UDP checksum 的核心规则是：把内容看成一串 16-bit 整数，
    相加时如果最高位产生进位，就把进位回卷到低 16 位。
    """
    if len(data) % 2 == 1:
        data += b"\x00"

    total = 0
    for index in range(0, len(data), 2):
        word = (data[index] << 8) + data[index + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)

    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)

    return total


def internet_checksum(data: bytes) -> int:
    """返回 16-bit Internet checksum。"""
    return (~_ones_complement_sum(data)) & 0xFFFF


@dataclass
class Segment:
    """Layer 4 UDP-like Segment。

    字段严格对应项目说明：
    Source Port、Destination Port、Length、Checksum、Type、Sequence Number、Data。
    """

    src_port: int
    dst_port: int
    length: int
    checksum: int
    segment_type: int
    seq_num: int
    data: bytes

    @classmethod
    def create_data(cls, src_port: int, dst_port: int, seq_num: int, data: bytes) -> "Segment":
        """创建 DATA segment；checksum 会在对象创建后单独计算。"""
        return cls(
            src_port=src_port,
            dst_port=dst_port,
            length=L4_HEADER_SIZE + len(data),
            checksum=0,
            segment_type=TRANSPORT_TYPE_DATA,
            seq_num=seq_num,
            data=data,
        )

    @classmethod
    def create_ack(cls, src_port: int, dst_port: int, seq_num: int) -> "Segment":
        """创建 ACK segment；ACK 的 data 按项目要求为空。"""
        return cls(
            src_port=src_port,
            dst_port=dst_port,
            length=L4_HEADER_SIZE,
            checksum=0,
            segment_type=TRANSPORT_TYPE_ACK,
            seq_num=seq_num,
            data=b"",
        )

    def bytes_for_checksum(self) -> bytes:
        """把 segment 编码成 bytes，并把 checksum 字段按 0 处理。

        计算 checksum 时不能把 checksum 字段自身算进去，这是 UDP
        checksum 和课堂 Lab8 练习都强调的规则。
        """
        return b"".join(
            [
                self.src_port.to_bytes(2, "big"),
                self.dst_port.to_bytes(2, "big"),
                self.length.to_bytes(2, "big"),
                (0).to_bytes(2, "big"),
                self.segment_type.to_bytes(1, "big"),
                self.seq_num.to_bytes(1, "big"),
                self.data,
            ]
        )

    def compute_checksum(self) -> int:
        """根据当前字段计算 checksum。"""
        return internet_checksum(self.bytes_for_checksum())

    def checksum_is_valid(self) -> bool:
        """验证接收端重新计算得到的 checksum 是否与 header 中一致。"""
        return self.compute_checksum() == self.checksum

    def length_is_valid(self) -> bool:
        """检查 Length 字段是否等于 header + data。"""
        return self.length == L4_HEADER_SIZE + len(self.data)

    def type_name(self) -> str:
        """把数字类型转成日志里使用的 DATA / ACK。"""
        if self.segment_type == TRANSPORT_TYPE_DATA:
            return "DATA"
        if self.segment_type == TRANSPORT_TYPE_ACK:
            return "ACK"
        return "UNKNOWN"


@dataclass
class Packet:
    """Layer 3 IP-like Packet。"""

    src_ip: str
    dst_ip: str
    ttl: int
    protocol: int
    total_length: int
    payload: Segment

    @classmethod
    def create(cls, src_ip: str, dst_ip: str, payload: Segment) -> "Packet":
        """把 Layer 4 segment 封装成 Layer 3 packet。"""
        return cls(
            src_ip=src_ip,
            dst_ip=dst_ip,
            ttl=DEFAULT_TTL,
            protocol=NETWORK_PROTOCOL_UDP,
            total_length=L3_HEADER_SIZE + payload.length,
            payload=payload,
        )

    def length_is_valid(self) -> bool:
        """检查 Total Length 字段是否等于 IP-like header + payload。"""
        return self.total_length == L3_HEADER_SIZE + self.payload.length


@dataclass
class Frame:
    """Layer 2 Ethernet-like Frame。"""

    dst_mac: str
    src_mac: str
    frame_type: int
    payload: Packet

    @classmethod
    def create(cls, src_mac: str, dst_mac: str, payload: Packet) -> "Frame":
        """把 Layer 3 packet 封装成 Layer 2 frame。"""
        return cls(
            dst_mac=dst_mac,
            src_mac=src_mac,
            frame_type=ETHERNET_TYPE_IPV4,
            payload=payload,
        )
