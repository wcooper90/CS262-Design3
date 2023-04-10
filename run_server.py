import socket, threading
import sys
from server_object import Server, bcolors, commands, VERSION_NUMBER
import argparse
from pathlib import Path


"""
Usage: python3 run_server.py -s1 [ip:port of current server being added] -s2 [ip:port of primary server, if this one is not the primary server]
"""
parser = argparse.ArgumentParser()
parser.add_argument('-s1','--server1', help='ip address:port of this server', required=True)
parser.add_argument('-s2','--server2', help='ip address:port of primary server', required=False)


args = parser.parse_args()
current_server_info = args.server1.split(':')
server_ip = current_server_info[0]
server_port = current_server_info[1]
primary_ip = None
primary_port = None

if args.server2:
    info = args.server2.split(":")
    primary_ip, primary_port = info[0], info[1]
    print("we need to connect to another primary server")


server1 = None
if primary_ip:
    server1 = Server(server_ip, server_port, commands, bcolors, VERSION_NUMBER, [primary_ip, primary_port])
else:
    server1 = Server(server_ip, server_port, commands, bcolors, VERSION_NUMBER)


def start_server(server):
    server.start()

if not primary_ip:
    thead = threading.Thread(target=start_server, args=(server1,))
    thead.start()

## python3 run_server.py -s1 127.0.0.1:7976
## python3 run_server.py -s1 127.0.0.1:7976 -s2 127.0.0.1:7977
