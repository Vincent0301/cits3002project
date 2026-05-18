"""CITS3002 Mini Internet Protocol Stack Simulator 入口文件。

运行方式：
    python main.py 100

main.py 是项目说明要求的唯一执行入口。它负责解析命令行参数、
搭建固定拓扑，并让 Host A 向 Host B 发送指定大小的应用数据。
"""

import sys

from config import HOST_B_IP, HOST_B_SERVICE_PORT
from devices import build_default_network


def parse_message_size(argv):
    """解析命令行中的应用数据大小。"""
    if len(argv) != 2:
        print("Usage: python main.py <message_size_in_bytes>")
        sys.exit(1)

    try:
        message_size = int(argv[1])
    except ValueError:
        print("Error: message size must be an integer.")
        sys.exit(1)

    if message_size < 0:
        print("Error: message size must be non-negative.")
        sys.exit(1)

    return message_size


def main():
    """搭建网络并启动一次 Host A 到 Host B 的发送流程。"""
    message_size = parse_message_size(sys.argv)

    host_a, _router, _host_b = build_default_network()

    # 项目只关心数据大小，不关心具体内容；用 X 构造确定性的 bytes。
    application_data = b"X" * message_size
    host_a.send_application_data(application_data, dst_ip=HOST_B_IP, dst_port=HOST_B_SERVICE_PORT)


if __name__ == "__main__":
    main()
