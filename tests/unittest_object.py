import unittest
import socket
from client_object import Client
from server_object import Server
import socket, threading
from time import sleep

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

IP_ADDRESS = '127.0.0.1'
port = 7976
VERSION_NUMBER = '1'


def start_server(server):
    server.start()

def start_client(client):
    client.start()

# server1 = Server('0.0.0.0', port, commands, bcolors, VERSION_NUMBER)
# client1 = Client(commands, bcolors, IP_ADDRESS, port, VERSION_NUMBER)
#
# server_thread = threading.Thread(target=start_server, args=(server1,))
# client_thread = threading.Thread(target=start_client, args=(client1,))
#
# server_thread.start()
# sleep(1)
# client_thread.start()
#
# print(client1.messages)
#
# username = VERSION_NUMBER + commands['CREATE_NAME'] + 'name0'
# client1.send_message(username.encode('ascii'))
#
# sleep(3)
#
# print(client1.messages)
#
# client1.send_message(client1.parse_arg('/S').encode('ascii'))
#
# sleep(3)
#
# print(server1.messages)
#
# while True:
#     sleep(3)
#     print(client1.messages)






class Test(unittest.TestCase):

    def setUp(self):

        self.server1 = Server('0.0.0.0', port, commands, bcolors, VERSION_NUMBER)
        self.client1 = Client(commands, bcolors, IP_ADDRESS, port, VERSION_NUMBER)

        self.server_thread = threading.Thread(target=start_server, args=(self.server1,))
        self.client_thread = threading.Thread(target=start_client, args=(self.client1,))





    """ SERVER SIDE """
    # Attempt login with non-existent username
    def test_client_server_connection(self):
        self.server_thread.start()
        sleep(1)
        self.client_thread.start()
        sleep(1)
        self.assertEqual(self.client1.messages, [VERSION_NUMBER + commands['ENTER']])


    def test_client_create_name(self):
        username = VERSION_NUMBER + commands['CREATE_NAME'] + 'name0'
        self.client1.send_message(username.encode('ascii'))
        self.assertEqual(self.client1.messages, [VERSION_NUMBER + commands['ENTER']])
    # #
    # # Attempt creating account with existing username
    # def test_create(self):
    #     username = VERSION_NUMBER + commands['CREATE_NAME'] + 'name1'
    #     _ = server.login_username(username, self.mock_client1)
    #     error = server.login_username(username, self.mock_client2)
    #     self.assertEqual(error, 'Username taken')
    #
    # # Attempt deleting an account
    # def test_delete(self):
    #     server.clients = {self.mock_client1:'name1'}
    #     message = server.delete_account(self.mock_client1, '')
    #     self.assertIn('Account deleted', str(message[2:]))
    #
    # # Attempt exiting from a connection
    # def test_exit(self):
    #     server.clients = {self.mock_client2:'name2'}
    #     server.connections = {'name2':'name1'}
    #     server.exit(self.mock_client2, '')
    #     self.assertEqual('', server.connections['name2'])





# if __name__ == '__main__':
#     unittest.main()
