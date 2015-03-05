#==============================================================================#
#                                ez_process.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

import os
import types
import Queue
import thread
import threading
from ez_process_base import ez_process_base, p2pCommand

import cPickle as pickle
import ez_user as eu
import ez_pipe as pipe

#==============================================================================#
#                                  ez_connect                                  #
#==============================================================================#


# schematic view of the connection process
#------------------------------------------------------------------------------#
#                                  /--------\                                  #
#                    /------------ | server |--------------.                   #
#        connection  |             `--------'              |  connection       #
#      (ip_B, portB) |                                     | (ip_A, portA)     #
#              /----------\    connection requests    /----------\             #
#              | client A |----------.      X-------- | client B |             #
#              `----------'           \               `----------'             #
#                                      `-------------> succeded -----.         #
#                                                         |          |         #
#                           connection_nat_traversal     /  dont know yet if   #
#     connection succeded <-----------------------------'  Client A succeded   #
#     add client to db   |   connection_success                                #
#     reply Client B     `-----------------------------> connection succeded   #
#                                                         add client to db     #
#------------------------------------------------------------------------------#

class ez_connect(ez_process_base):
  def __init__(self, *args, **kwargs):
    super(ez_connect, self).__init__(*args, **kwargs)

#============================#
#  UDP-Holepunching methods  #
#============================#

  def connect(self, master):
    """
    Not to be called by the user, but automatically invoked.

    The connect method is invoked by the server on client A/B with (ip, port)
    from client B/A. Client A/B starts a connection_request, but in practice
    only one of the two 'connects' get passed the clients NAT.

    :param master: Endpoint of a Server/Client (Ip, Port)
    :type  master: (string, int)
    """

    cmd_dct = {'user_id': self.name}
    conn_request = {'connection_request': cmd_dct}
    msg = pickle.dumps(conn_request)
    try:
      if self.fail_connect:
        pass
      else:
        self.sockfd.sendto(msg, master)
        self.success("start connection with " + str(master))
    except IOError as e:
      self.error(str(e))

  def connection_request(self, user_id, user_addr):
    """
    Not to be called by the user, but automatically invoked.

    A succesful connection_request punches a hole in the client As NAT and tries
    to verify if client Bs NAT traversal succeeded. It may happen that client Bs
    NAT declines the request, that it does not support UDP-holepunching or that
    the udp package was not properly sent which is why a background verification
    process is started, informing, if necessary, client A of the failed
    connection process.

    :param user_id: User nickname
    :type  user_id: string

    :param user_addr: Endpoint of a Server/Client (Ip, Port)
    :type  user_addr: (string, int)
    """

    process_id = ('connection_request', user_addr)
    if process_id not in self.background_processes:
      cmd_dct = {'user_id': self.name}
      con_holepunch = {'connection_nat_traversal': cmd_dct}
      msg = pickle.dumps(con_holepunch)
      try:
        self.sockfd.sendto(msg, user_addr)

        def connection_failed_func(self_timer):
          self.error("connection failed with: " + str(user_addr))
          del self.background_processes[process_id]

        bgp = p2pCommand('start_background_process',
                         {'process_id': process_id,
                          'callback': connection_failed_func,
                          'interval': 5})
        self.commandQueue.put(bgp)
        self.success("connection request from user:" +
                     str(user_addr) + " with id: " + user_id)

      except IOError as e:
        self.error(str(e))
        self.error("connection unsuccessful")
    else:
      self.error("cannot connect again, still waiting for response")

  def connection_nat_traversal(self, user_id, user_addr):
    """
    Not to be called by the user, but automatically invoked.

    NAT traversal succeded for client A and the connection is established.
    Client B is added to the db and is also informed about the connection.

    :param user_id: User nickname
    :type  user_id: string

    :param user_addr: Endpoint of a Server/Client (Ip, Port)
    :type  user_addr: (string, int)
    """

    cmd_dct = {'user_id': self.name}
    con_success = {'connection_success': cmd_dct}
    msg = pickle.dumps(con_success)

    cmd = self.success("nat traversal succeded: " + str(user_addr))
    cmd_dct = {'user_id': user_id, 'host': user_addr[0], 'port': user_addr[1]}
    self.add_client(**cmd_dct)

    self.replyQueue.put(cmd)
    self.sockfd.sendto(msg, user_addr)

  def connection_success(self, user_id, host, port):
    """
    Not to be called by the user, but automatically invoked.

    Client B receives the news that Client A succeded and Client B adds Client A
    to the user db.

    :param user_id: User nickname
    :type  user_id: string

    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    user_addr = (host, port)
    process_id = ('connection_request', user_addr)
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    self.success("user: " + str(user_addr) + " with id: " +
                 user_id + " has connected")

    cmd_dct = {'user_id': user_id, 'host': user_addr[0], 'port': user_addr[1]}
    self.add_client(**cmd_dct)

    if hasattr(self, 'server'):
      con_success = {'connection_server_success': {}}
      msg = pickle.dumps(con_success)

      self.sockfd.sendto(msg, user_addr)

  def connection_server_success(self, host, port):
    """
    Not to be called by the user, but automatically invoked.

    Client B receives the news that Client A succeded and Client B adds Client A
    to the user db.

    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    user_addr = (host, port)
    process_id = 'connect_server'
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    self.success("Connection with server established")
