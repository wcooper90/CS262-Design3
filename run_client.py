import socket, threading
import sys
from client_object import Client, bcolors, commands, VERSION_NUMBER


"""
Usage: python3 run_client.py
"""

# input server addresses here
SERVER_ADDRESSES = []


def start_client(client):
    client.start()


client1 = Client(commands, bcolors, SERVER_ADDRESSES, VERSION_NUMBER)

thread = threading.Thread(target=start_client, args=(client1,))
thread.start()

## python3 run_server.py -s1 127.0.0.1:7976
## python3 run_server.py -s1 127.0.0.1:7976 -s2 127.0.0.1:7977
