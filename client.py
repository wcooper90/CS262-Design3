import socket, threading
import sys
username = ""

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
IP_ADDRESS = '0.0.0.0'

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
            'START_CHAT': 'f'}

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP_ADDRESS, 7976))

# pretty much same as Wednesday, removed the redundant connection at the beginning which asks for login/create account.
def login_message():
    global username
    choice = None
    while choice != "L" and choice != "C":
        choice = input("Log in (L) or create an account (C): ")
    if choice == "L":
        username = input("Enter username: ")
        return VERSION_NUMBER + commands['LOGIN_NAME'] + username
    else:
        username = input("Create new username: ")
        return VERSION_NUMBER + commands['CREATE_NAME'] + username


# parse user's input text. Specifically deal with commands beginning with '/'
def parse_arg(input):
    if not input:
        return VERSION_NUMBER + commands['NOTHING'] + ''

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
        return VERSION_NUMBER + commands[command] + input_strip
    elif command == 'SHOW':
        return VERSION_NUMBER + commands[command] + input_strip
    # if the command is not CONNECT, just send whole payload
    elif command != 'CONNECT':
        return VERSION_NUMBER + commands[command] + ''
    # if the command is CONNECT, send only the part of the payload which specifies which user we are connecting to
    else:
        return VERSION_NUMBER + commands[command] + input_strip[2:]

# send_text command only used when user is engaged in a chatroom. In this case, '/E' triggers chatroom exit.
def send_text(input):
    # check to see if client is exiting chat
    if input == '/E':
        return VERSION_NUMBER + commands['EXIT_CHAT'] + 'end'
    return VERSION_NUMBER + commands['TEXT'] + input


def receive():
    global username
    while True:

        try:
            message = client.recv(1024).decode('ascii')
            # print("size of transfer buffer: " + str(sys.getsizeof(message)))
            # only for login and create names functions
            if message[1] == commands['ENTER']:
                if message[2:]:
                    print(message[2:])
                m = login_message()
                client.send(m.encode('ascii'))

            # deleting the account. Break out of while loop
            elif message[1] == commands['DELETE']:
                if message[2:]:
                    print(message[2:])
                client.close()
                return

            # poll for input
            elif message[1] == commands['DISPLAY']:
                if message[2:]: print(message[2:])
                inp = input(":")
                m = parse_arg(inp)
                client.send(m.encode('ascii'))


            # receiving text from another connection
            elif message[1] == commands['SHOW_TEXT']:
                if message[2:]: print(message[2:])


            # we know we are connected to another user/in a chat room when we receive the "START_CHAT" command
            elif message[1] == commands['START_CHAT']:
                if message[2:]: print(message[2:])
                write_thread = threading.Thread(target=write)                   # thread for sending messages
                write_thread.start()


            # I assume when receiving chats from other users, message should be directly printed here. Not sure if it will be this easy in practice.
            # a new color can be toggled for received chats by serverside.
            else:
                if message[2:]:
                    print(message[2:])
        except Exception as e:
            print("An error occured!")
            print(e)
            client.close()
            break


# write thread function. When a user is connected, they can send messages
def write():
    while True:
        inp = input()
        m = send_text(inp)
        if m[2:] == 'end':
            client.send(m.encode('ascii'))
            return
        client.send(m.encode('ascii'))


# start the client
receive_thread = threading.Thread(target=receive)
receive_thread.start()
