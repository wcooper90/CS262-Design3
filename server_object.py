
import json
import socket, threading
import sys
from time import sleep
import os

# to change colors of terminal text
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



class Server():
    def __init__(self, host, port, commands, colors, version_number, primary_info=None):

        self.VERSION_NUMBER = version_number
        self.colors = colors
        self.commands = commands

        # set primary to true upon instatiation
        self.is_primary = True
        # if it's not actually primary, fix it
        if primary_info:
            self.is_primary = False

        self.host = host
        self.port = int(port)
        self.primary_info = primary_info
        self.receive_thread = None
        # other servers in the system and their server ordering
        self.servers = {}
        # should stay None or go back to None if this is the primary server
        self.client = None
        # only populated for non-primary servers
        self.curr_fellow_servers = []

        self.id = None
        if self.is_primary:
            self.id = 0
            self.servers['self'] = [str(self.id), self.host, str(self.port)]
        else:
            self.connect_to_primary_server(self.primary_info[0], self.primary_info[1])

        # to recognize which server id is currently primary
        # if not this server, will be set when receiving response from primary server
        self.curr_primary_server = None
        if self.is_primary:
            self.curr_primary_server = self.id

        self.hostname=socket.gethostname()
        self.IPAddr=socket.gethostbyname(self.hostname)
        print("Your Computer Name is:"+self.hostname)
        print("Your Computer IP Address is:"+self.IPAddr)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messages = []

        self.queue = {}
        self.USERNAMES = []
        self.connections = {}
        self.clients = {}
        self.LOGGED_IN = []

        # used for saving data to json file
        self.server_data = {
            "queue": self.queue,
            "USERNAMES": self.USERNAMES,
            "connections": self.connections,
            "LOGGED_IN": self.LOGGED_IN
        }


    def connect_to_primary_server(self, primary_ip, primary_port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((primary_ip, int(primary_port)))
        self.receive_thread = threading.Thread(target=self.receive_server)
        self.receive_thread.start()


    def start(self):
        print('We are now the primary server!')
        if os.path.isfile('data/server_data' + str(self.id) + '.json'):
            f = open('data/server_data' + str(self.id) + '.json')
            data = json.load(f)
            self.queue, self.USERNAMES, self.connections = data['queue'], data['USERNAMES'], data['connections']
            # NOTE: do not read the LOGGED_IN variable here, because if system is restarting no one can be logged in

        self.server.bind((self.host, self.port))
        self.server.listen()
        self.receive()


    # deletes a username from list of usernames, removes the association from the client, and sends the appropriate message
    # TODO: eventually will also have to delete undelivered messages to a deleted account
    def delete_account(self, client, message):
        out = 'Account deleted'
        self.LOGGED_IN.remove(self.clients[client])
        self.USERNAMES.remove(self.clients[client])
        self.queue.pop(self.clients[client])
        self.clients[client] = ''
        return (self.VERSION_NUMBER + self.commands['DELETE'] + out).encode('ascii')


    # displays the other users on the current server.
    def show(self, client, message):

        all_users = []

        if message[4:]:
            if '*' in message[4:]:
                key = message[4:message.index('*')]
                for user in self.USERNAMES:
                    if key in user:
                        all_users.append(user)

            elif message[4:] in self.USERNAMES:
                all_users.append(message[4:])
            else:
                return (self.VERSION_NUMBER + self.commands['DISPLAY'] + "No users match").encode('ascii')
        else:
            all_users = self.USERNAMES


        out = ""
        for user in all_users:

            # Display number of unread messages from other users
            number_unread = 0
            if self.clients[client] in self.queue:
                if user in self.queue[self.clients[client]]:
                    number_unread = len(self.queue[self.clients[client]][user])

            if number_unread > 0: out += user + ' ('+str(number_unread)+' unread messages)' + '\n'
            else: out += user + '\n'

        # I'm just using the "DISPLAY" command to display specific messages and prompt the user for another response at this point.
        return (self.VERSION_NUMBER + self.commands['DISPLAY'] + out).encode('ascii')

    # displays the list of possible commands.
    def help(self, client, message):
        out = 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)'
        client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + out).encode('ascii'))

    # prompts the user for another input (only used when the user just presses 'enter' without typing anything)
    def prompt(self, client, message):
        client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + '').encode('ascii'))


    # conditional logic for logging in / creating an account. Updates USERNAMES and clients global data as necessary.
    def login_username(self, username, client):
        error_message = ''
        if username[1] == self.commands['LOGIN_NAME']:
            if username[2:] not in self.USERNAMES:
                error_message = 'Username not found'
            elif username[2:] in self.LOGGED_IN:
                error_message = 'User currently logged in!'
            else:
                self.clients[client] = username[2:]
                self.connections[username[2:]] = ''
                self.LOGGED_IN.append(username[2:])

        if username[1] == self.commands['CREATE_NAME']:
            if username[2:] in self.USERNAMES:
                error_message = 'Username taken'
            elif ' ' in username[2:]:
                error_message = "Your username can not have spaces"
            elif '*' in username[2:]:
                error_message = "You username can not have '*'"
            else:
                self.USERNAMES.append(username[2:])
                self.clients[client] = username[2:]
                self.connections[username[2:]] = ''
                self.queue[username[2:]] = {}
                self.LOGGED_IN.append(username[2:])
        return error_message


    # called whenever user submits a "non-command". Needs to be updated when actually connecting users,
    # Also storing a client object as a dictionary key might be a bit weird, haven't totally figured it out yet.
    def text(self, client, message):

        sender = client # client code

        receiver = self.connections[self.clients[client]] # username

        if not receiver:
            client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + 'You currently are not connected to anyone. Type /H for help.  ').encode('ascii'))
            return

        receiver_address = ''
        for key, val in self.clients.items():
            if val == receiver:
                receiver_address = key
                break

        if (receiver in self.connections) and (self.connections[receiver] == self.clients[sender]): # comparing usernames
                receiver_address.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + self.colors.OKBLUE + self.clients[client] + ': ' + self.colors.ENDC+ message[2:]).encode('ascii'))

        else:
            # Tell client that reciever is not in chat anymore, but sent messages will be saved for htem
            # store the messages
            if receiver in self.queue:
                if self.clients[sender] in self.queue[receiver]:
                    self.queue[receiver][self.clients[sender]].append(message[2:])
                else: self.queue[receiver][self.clients[sender]] = [message[2:]]
            else:
                self.queue[receiver] = {self.clients[sender]:[message[2:]]}

            client.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + 'The recipient has disconnected. Your chats will be saved. ').encode('ascii'))

    # conditional logic for connecting to another user. Updates connections accordingly.
    def connect(self, client, message):
        if message[2:] not in self.USERNAMES:
            client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + 'user not found. Please try again').encode('ascii'))
        else:
            # do not allow user to connect to oneself.
            if self.clients[client] == message[2:]:
                client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + 'You cannot connect to yourself! Please try again ').encode('ascii'))
            else:
                self.connections[self.clients[client]] = message[2:]

                client.send((self.VERSION_NUMBER + self.commands['START_CHAT'] + 'You are now connected to ' + message[2:] + '! You may now begin chatting. To exit, type "/E"').encode('ascii'))

                out = ''
                if self.clients[client] in self.queue:
                    if message[2:] in self.queue[self.clients[client]]:
                        for m in self.queue[self.clients[client]][message[2:]]:
                            out += self.colors.OKBLUE + message[2:] + ': ' + self.colors.ENDC + m + '\n'

                        self.queue[self.clients[client]][message[2:]] = []

                client.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + out).encode('ascii'))


    def check_unread_messages(self, client):
        user = self.clients[client]
        out = ""
        if user not in self.queue:
            return out 
        for key, val in self.queue[user].items():
            out += 'You have unread messages from: ' + str(key) + '\n'
        return out


    # conditional logic for disconnecting from another user. Updates connections accordingly. Prompts user for new connection.
    def exit(self, client, message):
        # connections.pop(clients[client])
        self.connections[self.clients[client]] = ''
        return (self.VERSION_NUMBER + self.commands['DISPLAY'] + 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)').encode('ascii')


    def save_data(self):
        """
        Saves data to json file server_data.json using the server_data global defined at top of file
        """

        # for some reason (maybe because these variables are in an object), self.server_data doesn't automatically update, so manually update here first before saving
        self.server_data = {
            "queue": self.queue,
            "USERNAMES": self.USERNAMES,
            "connections": self.connections,
            "LOGGED_IN": self.LOGGED_IN
        }

        # save to JSON file for persistence
        with open("data/server_data" + str(self.id) + ".json", "w") as outfile:
            json.dump(self.server_data, outfile)
        print('saved data')


    def pass_data_to_replicas(self):
        server_failure = None
        for server in self.servers:
            if server != 'self':
                try:
                    server.send((self.VERSION_NUMBER + self.commands["SERVER_DATA"] + str(self.server_data) + '>' + self.server_info_string_generator()).encode('ascii'))
                # if this server doesn't exist anymore, instead update the current server list and re-update everyone
                except Exception as e:
                    print(e)
                    print('bruhbruhbruhbruhbruhbruhbruhrbuhbrruhbruh')
                    server_failure = server
                    break

        if server_failure:
            del self.servers[server_failure]
            self.pass_data_to_replicas()


    # every time a new server joins, tell all other servers about it. If a server has happened to fail, update and inform server of this as well
    def inform_servers_about_new_server(self):
        disconnected_server = None
        for server in self.servers:
            if server != 'self':
                # if server 2 fails and primary is still up, we can't send a message to them
                try:
                    server.send(self.server_info_string_generator().encode('ascii'))
                # instead update the current server list and re-update everyone
                except:
                    disconnected_server = server
                    break

        if disconnected_server:
            del self.servers[server]
            self.inform_servers_about_new_server()
            return


    def handle(self, client):
        while True:

            # for debugging purposes
            print('*'*80)
            print('clients:', self.clients)
            print('users:', self.USERNAMES)
            print('connections:', self.connections)
            print('queue:', self.queue)
            print('fellow servers:', self.servers)

            self.save_data()

            try:
                message = client.recv(1024).decode()
                self.messages.append(message)
                # print("size of transfer buffer: " + str(sys.getsizeof(message)))
                if message[1] == self.commands['CONNECT']:
                    self.connect(client, message)
                elif message[1] == self.commands['TEXT']:
                    self.text(client, message)
                elif message[1] == self.commands['SHOW']:
                    client.send(self.show(client, message))
                elif message[1] == self.commands['HELP']:
                    self.help(client, message)
                elif message[1] == self.commands['DELETE']:
                    client.send(self.delete_account(client, message))
                elif message[1] == self.commands['EXIT_CHAT']:
                    client.send(self.exit(client, message))
                else:
                    self.prompt(client, message)

            except:
                # it's possible that user deleted their account, in which case removing them from LOGGED_IN set will throw error
                if self.clients[client]:
                    self.LOGGED_IN.remove(self.clients[client])


                if client in self.connections:
                    self.connections.pop(client)
                self.clients.pop(client)
                # the first primary server will not have a client connection to another server
                if self.client:
                    self.client.close()

                # save data to local solid state drive for persistence
                self.save_data()
                # pass saved data to replicas; remind them of existing servers in the system and pass saved JSON global variables
                self.pass_data_to_replicas()

                break

            # save data to local solid state drive for persistence
            self.save_data()
            # pass saved data to replicas; remind them of existing servers in the system and pass saved JSON global variables
            self.pass_data_to_replicas()



    def receive_server(self):
        while True:
            try:
                # interpret incoming message, combination of this
                # current server's place in queue and existing JSON file
                message = self.client.recv(1024).decode('ascii')

                if message[1] == self.commands["SERVER_DATA"]:

                    m = message[2:].split(">")
                    # had to play around with this a bit for it to be recognized as json
                    json_ = str(m[0]).replace("'", '"')
                    data = json.loads(json_)
                    self.queue, self.USERNAMES, self.connections, self.LOGGED_IN = data['queue'], data['USERNAMES'], data['connections'], data['LOGGED_IN']
                    self.save_data()

                    messages = m[1].split('[')
                    self.curr_fellow_servers = []
                    for message in messages:
                        vals = message.split(',')
                        # the split for server info will always have 3 values: id, ip, port
                        if len(vals) != 3:
                            break
                        id, ip, port = vals
                        if ip == self.host and int(port) == int(self.port):
                            self.id = id
                        self.curr_fellow_servers.append([id, ip, port])

                    # update the id of the currently recognized primary server
                    # need to check that it exists just for the first welcome message
                    if self.curr_fellow_servers:
                        self.curr_primary_server = self.curr_fellow_servers[0][0]

                    print(self.curr_fellow_servers)
                    print("Just received some new data from primary server word.")


                # the message back to the primary server will always be the curret address
                outgoing_message = VERSION_NUMBER + commands['SERVER_TALK'] + self.host + ":" + str(self.port)
                self.client.send(outgoing_message.encode('ascii'))

            # broken pipe exception
            except Exception as e:
                print("Connection with primary server was broken! Who is the next server? ")
                print(e)
                # assume that next server is next id
                next_server_id = int(self.curr_primary_server) + 1
                if int(self.id) == next_server_id:
                    print('we are the next server yay!')
                    self.is_primary = True
                    self.servers = {}
                    self.servers['self'] = [str(self.id), self.host, str(self.port)]
                    # start listening as primary server, stop the receiving thread
                    self.start()
                    return
                else:
                    # give actual primary server a chance to start
                    sleep(5)
                    primary_ip, primary_port = self.find_next_primary_server_address(next_server_id)
                    try:
                        self.connect_to_primary_server(primary_ip, primary_port)
                        print('successfully connected to next primary server!')
                    # if we can't connect to the other server, then the primary server must be us
                    except:
                        print('we are the next server yay!')
                        self.is_primary = True
                        self.servers = {}
                        self.servers['self'] = [str(self.id), self.host, str(self.port)]
                        # start listening as primary server
                        self.start()
                        return
                    return

                self.client.close()
                break

    # helper function for determining next primary server
    def find_next_primary_server_address(self, next_server_id):
        for vals in self.curr_fellow_servers:
            if int(vals[0]) == int(next_server_id):
                return vals[1], vals[2]


    # helper function for telling new servers what their id is
    def find_largest_server_number(self):
        curr = -1
        for server in self.servers:
            if int(self.servers[server][0]) > curr:
                curr = int(self.servers[server][0])
        return curr


    # create string of server information to be passed to non-primary servers
    def server_info_string_generator(self):
        string_of_servers = []
        for server_values in self.servers.values():
            string_of_servers.append(",".join(server_values))
        return "[".join(string_of_servers) + "["


    # regular receive thread for primary server
    def receive(self):

        # always make sure no accounts are logged in when starting this thread, so that if a replica replaces a primary server,
        # clients can automatically log in again as themselves
        self.LOGGED_IN = []

        # main control loop
        while True:
            client, address = self.server.accept()
            error_message = ''
            username = ''
            # check if the incoming connection is another server
            client.send((self.VERSION_NUMBER + self.commands['ENTER'] + error_message).encode('ascii'))
            response = client.recv(1024).decode('ascii')

            # error catching if client terminates program before logging in
            if not response:
                continue

            # if we receive an address that is another server
            if response[1] == commands["SERVER_TALK"]:
                incoming_server_info = response[2:].split(":")

                # give the server an id
                if not self.servers:
                    self.servers[client] = [str(self.id + 1)] + incoming_server_info
                else:
                    self.servers[client] = [str(self.find_largest_server_number() + 1)] + incoming_server_info

                # save data to local solid state drive for persistence -- just for the recognition of this new user
                self.save_data()
                # pass saved data to replicas; remind them of existing servers in the system and pass saved JSON global variables
                self.pass_data_to_replicas()

                print("Connected with {}".format(str(address)) + ", server " + str(self.servers[client]))
                # if the incoming connection is a server, just register themm as a server, we don't need to start another thread
                continue

            # when we just have become the new primary server, collect all previous users and reprompt them
            elif response[1] == commands['SERVER_SWITCH']:
                self.LOGGED_IN.append(response[2:])
                self.clients[client] = response[2:]
                print("Username is {}".format(response[2:]))

                # if user is in the middle of the conversation, continue prompting them as if in chat
                if self.connections[response[2:]]:
                    out = ""
                    client.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + out).encode('ascii'))
                # otherwise bring to home interface
                else:
                    client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + \
                        'Reconnected! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)\n' + self.check_unread_messages(client)).encode('ascii'))

                # save data to local solid state drive for persistence -- just for the recognition of this new user
                self.save_data()
                # pass saved data to replicas; remind them of existing servers in the system and pass saved JSON global variables
                self.pass_data_to_replicas()

                thread = threading.Thread(target=self.handle, args=(client,))
                thread.start()
                # if the user correctly logs in or creates account on first attempt, continue to next iteration of while loop
                # else continue to prompt user
                continue

            else:
                self.clients[client] = ''
                print("Connected with {}".format(str(address)) + ", client")
                error_message = self.login_username(response, client)
                if error_message == '':
                    print("Username is {}".format(response[2:]))
                    client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + \
                        'Logged in! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)\n' + self.check_unread_messages(client)).encode('ascii'))

                    # save data to local solid state drive for persistence -- just for the recognition of this new user
                    self.save_data()
                    # pass saved data to replicas; remind them of existing servers in the system and pass saved JSON global variables
                    self.pass_data_to_replicas()

                    thread = threading.Thread(target=self.handle, args=(client,))
                    thread.start()
                    # if the user correctly logs in or creates account on first attempt, continue to next iteration of while loop
                    # else continue to prompt user
                    continue

            # while loop to continue prompting user if their login/account creation input is incorrect
            while True:
                client.send((self.VERSION_NUMBER + self.commands['ENTER'] + error_message).encode('ascii'))
                # check for SERVER_TALK
                username = client.recv(1024).decode('ascii')
                error_message = self.login_username(username, client)
                if error_message == '':
                    break

            # save data to local solid state drive for persistence -- just for the recognition of this new user
            self.save_data()
            # pass saved data to replicas; remind them of existing servers in the system and pass saved JSON global variables
            self.pass_data_to_replicas()

            print("Username is {}".format(username[2:]))
            client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + \
                'Logged in! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)\n' + self.check_unread_messages(client)).encode('ascii'))

            # start thread for regular clients
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()
