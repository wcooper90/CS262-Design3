import unittest
import socket
from server_object import Server
from unittest.mock import Mock, patch
import threading
import json
import os



class TestServer(unittest.TestCase):
    def setUp(self):
        self.host = "127.0.0.1"
        self.port = 5000
        self.commands = {
            'LOGIN_NAME': '1',
            'CREATE_NAME': '2',
            'DISPLAY': '3',
            'DELETE': '4',
            'SHOW': '5',
            'HELP': '6',
            'PROMPT': '7',
            'MESSAGE': '8'
        }
        self.colors = {'red': 'R', 'blue': 'B'}
        self.version_number = "V1"
        self.primary_info = None

        self.server = Server(self.host, self.port, self.commands, self.colors, self.version_number, self.primary_info)

    def test_server_initialization(self):
        self.assertEqual(self.server.VERSION_NUMBER, self.version_number)
        self.assertEqual(self.server.commands, self.commands)
        self.assertEqual(self.server.colors, self.colors)
        self.assertEqual(self.server.is_primary, True)
        self.assertEqual(self.server.host, self.host)
        self.assertEqual(self.server.port, self.port)
        self.assertEqual(self.server.primary_info, self.primary_info)
        self.assertEqual(self.server.receive_thread, None)
        self.assertEqual(self.server.servers, {'self': ['0', self.host, str(self.port)]})
        self.assertEqual(self.server.curr_primary_server, 0)

    def test_show(self):
        self.server.USERNAMES = ['user1', 'user2', 'user3']
        self.server.queue = {
            'user1': {'user2': ['message1', 'message2']},
            'user2': {},
            'user3': {}
        }
        client = "client"
        self.server.clients = {client: 'user1'}

        # Test show all users
        message = "    "
        result = self.server.show(client, message)
        expected = "V13user1\nuser2 (2 unread messages)\nuser3\n".encode('ascii')
        self.assertEqual(result, expected)


    @patch('socket.gethostbyname')
    @patch('socket.gethostname')
    def setUp(self, mock_gethostname, mock_gethostbyname):
        mock_gethostname.return_value = 'test_hostname'
        mock_gethostbyname.return_value = '192.168.0.1'
        self.host = 'localhost'
        self.port = 5000
        self.commands = {'LOGIN_NAME': 'L', 'CREATE_NAME': 'C', 'SERVER_DATA': 'D', 'SERVER_TALK': 'T'}
        self.colors = {}
        self.version_number = "1"
        self.primary_info = None
        self.server = Server(self.host, self.port, self.commands, self.colors, self.version_number, self.primary_info)

    def test_find_largest_server_number(self):
        self.server.servers = {
            'server_1': ['1', '192.168.0.2', '5001'],
            'server_2': ['2', '192.168.0.3', '5002'],
            'server_3': ['3', '192.168.0.4', '5003']
        }
        largest_server_number = self.server.find_largest_server_number()
        self.assertEqual(largest_server_number, 3)

    def test_server_info_string_generator(self):
        self.server.servers = {
            'self': ['0', '192.168.0.1', '5000'],
            'server_1': ['1', '192.168.0.2', '5001'],
            'server_2': ['2', '192.168.0.3', '5002']
        }
        server_info_string = self.server.server_info_string_generator()
        expected_string = '0,192.168.0.1,5000[1,192.168.0.2,5001[2,192.168.0.3,5002['
        self.assertEqual(server_info_string, expected_string)

    @patch('socket.socket.connect')
    @patch('threading.Thread.start')
    def test_connect_to_primary_server(self, mock_thread_start, mock_connect):
        primary_ip = '192.168.0.2'
        primary_port = 5001
        self.server.connect_to_primary_server(primary_ip, primary_port)
        mock_connect.assert_called_once_with((primary_ip, primary_port))
        mock_thread_start.assert_called_once()

    @patch('json.loads')
    @patch('os.path.isfile')
    def test_start_loads_data(self, mock_isfile, mock_loads):
        mock_isfile.return_value = True
        data = {
            'queue': {},
            'USERNAMES': [],
            'connections': {},
            'LOGGED_IN': []
        }
        mock_loads.return_value = data
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(data))):
            self.server.start()
        self.assertEqual(self.server.queue, data['queue'])
        self.assertEqual(self.server.USERNAMES, data['USERNAMES'])
        self.assertEqual(self.server.connections, data['connections'])

    @patch('socket.socket.send')
    def test_receive_server_connect_to_primary_server(self, mock_send):
        primary_ip = '192.168.0.2'
        primary_port = 5001
        self.server.connect_to_primary_server(primary_ip, primary_port)
        self.server.receive_server()
        outgoing_message = self.version_number + self.commands['SERVER_TALK'] + self.host + ":"


if __name__ == '__main__':
    unittest.main()
