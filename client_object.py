import socket, threading
import sys
username = ""
from time import sleep

# change color of terminal text
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# USER MODIFY THE FOLLOWING LINE WITH IP_ADDRESS OF SERVER
IP_ADDRESS = '127.0.0.1'
port = 7976

VERSION_NUMBER = '1'
commands = {'LOGIN': '1',
            "CREATE": '2',
            'ENTER': '3',
            'LOGIN_NAME': '4',
            "CREATE_NAME": '5',
            'DISPLAY': '6',
            'HELP': '7',
            'SHOW': '8',
            'CONNECT': '9',
            'TEXT': 'a',
            'NOTHING': 'b',
            'DELETE': 'c',
            'EXIT_CHAT': 'd',
            'SHOW_TEXT': 'e',
            'START_CHAT': 'f',
            'SERVER_TALK': 'g',
            'SERVER_DATA': 'h',
            'SERVER_SWITCH': 'i'}



class Client():
    def __init__(self, commands, colors, server_addresses, version_number):
        self.commands = commands
        self.colors = colors
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_addresses = [(addy.split(":")[0], int(addy.split(":")[1])) for addy in server_addresses]
        self.ip = self.server_addresses[0][0]
        self.port = self.server_addresses[0][1]

        self.username = ""
        self.VERSION_NUMBER = version_number
        self.receive_thread = threading.Thread(target=self.receive)
        self.write_thread = None
        self.messages = []


    def start(self):
        connected = False
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for server in self.server_addresses:
            try:
                self.client.connect((server[0], server[1]))
                print("Found an active server!")
                connected = True
                break
            except:
                continue

        if connected:
            self.receive_thread = threading.Thread(target=self.receive)
            self.receive_thread.start()
        else:
            print("Could not find an active server to connect to!")

    def send_message(self, m):
        self.client.send(m)


    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                self.messages.append(message)
                if message[1] == self.commands['ENTER']:
                    if message[2:]: print(message[2:])

                    # if user already has a name, it must mean we are switching to another primary server
                    if self.username:
                        m = self.VERSION_NUMBER + self.commands['SERVER_SWITCH'] + self.username
                    else:
                        m = self.login_message()
                    self.client.send(m.encode('ascii'))

                elif message[1] == self.commands['DELETE']:
                    if message[2:]: print(message[2:])
                    return

                elif message[1] == self.commands['DISPLAY']:
                    if message[2:]: print(message[2:])
                    inp = input(":")
                    m = self.parse_arg(inp)
                    self.client.send(m.encode('ascii'))


                elif message[1] == self.commands['SHOW_TEXT']:
                    if message[2:]: print(message[2:])


                # we know we are connected to another user/in a chat room when we receive the "TEXT" command
                elif message[1] == self.commands['START_CHAT']:
                    if message[2:]: print(message[2:])
                    self.write_thread = threading.Thread(target=self.write)
                    self.write_thread.start()

                else:
                    if message[2:]: print(message[2:])

            except Exception as e:
                print("Connection to primary server broken! Finding replica server... ")
                self.client.close()
                sleep(5)

                self.start()
                break


    def login_message(self):
        choice = None
        while choice != "L" and choice != "C":
            choice = input("Log in (L) or create an account (C): ")
        if choice == "L":
            self.username = input("Enter username: ")
            return self.VERSION_NUMBER + self.commands['LOGIN_NAME'] + self.username
        else:
            self.username = input("Create new username: ")
            return self.VERSION_NUMBER + self.commands['CREATE_NAME'] + self.username



    # parse user's input text. Specifically deal with commands beginning with '/'
    def parse_arg(self, input):
        if not input:
            return self.VERSION_NUMBER + self.commands['NOTHING'] + ''

        input_strip = "".join(input.split())

        command = 'TEXT'
        if input_strip[0] == '/':
            if input_strip[1] == 'C':
                command = 'CONNECT'
            if input_strip[1] == 'H':
                command = 'HELP'
            if input_strip[1] == 'S':
                command = 'SHOW'
            if input_strip[1] == 'D':
                command = 'DELETE'

        if command == 'TEXT':
            return self.VERSION_NUMBER + self.commands[command] + input_strip
        elif command == 'SHOW':
            return self.VERSION_NUMBER + self.commands[command] + input_strip
        # if the command is not CONNECT, just send whole payload
        elif command != 'CONNECT':
            return self.VERSION_NUMBER + self.commands[command] + ''
        # if the command is CONNECT, send only the part of the payload which specifies which user we are connecting to
        else:
            return self.VERSION_NUMBER + self.commands[command] + input_strip[2:]

    # send_text command only used when user is engaged in a chatroom. In this case, '/E' triggers chatroom exit.
    def send_text(self, input):
        if input == '/E':
            return self.VERSION_NUMBER + self.commands['EXIT_CHAT'] + 'end'
        return self.VERSION_NUMBER + self.commands['TEXT'] + input


    def write(self):
        while True:
            inp = input()
            m = self.send_text(inp)
            if m[2:] == 'end':
                self.client.send(m.encode('ascii'))
                return
            self.client.send(m.encode('ascii'))
