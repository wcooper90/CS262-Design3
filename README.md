To run server:
- python3 run_server.py -s1 [ip:port of current server] -s2 [ip: port of primary server]
  - If you are starting the first server, the second argument is optional, s1 will be the primary server by default

To run client:
- change the SERVER_ADDRESSES variable in run_client.py to contain the three addresses (ip:port) of your servers
- python3 run_client.py
