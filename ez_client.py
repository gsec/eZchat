#==============================================================================#
#                                  ez_client                                   #
#==============================================================================#

#============#
#  Includes  #
#============#

import sys
import errno
import socket
import select
import Queue
import threading
import cPickle as pickle
from ez_message import Message
from ez_packet import Packet, ez_packet

from datetime import datetime
from ez_process import p2pCommand, p2pReply, ez_process, command_args
from ez_simple_cli import ez_simple_cli

CLIENT_TIMEOUT = 0.1

#==============================================================================#
#                                 class client                                 #
#==============================================================================#

class client(ez_process, ez_packet, ez_simple_cli, threading.Thread):
  """
  Client class with builtin queue system, p2p via NAT traversal and reliable udp
  packet system.

  Commands are executed by appending p2pCommand instances to the client
  commandQueue.

  Most commands are not intended to be called by the user himself, but are
  usually automatically called as a consequence of connection, ping or packet
  requests.

  Queue commands are defined in ez_process. The client takes care of input
  (IO + incomming msges), the user db and pulling commands/results from the
  queues.
  """
  handler_rules = {}

  def __init__(self, fail_connect=False, **kwargs):
    threading.Thread.__init__(self)
    super(client, self).__init__(**kwargs)

    # used to simulate udp-holepunching where one of the clients connection
    # request is declient by the others client NAT
    self.fail_connect = fail_connect

    # As long as the client is alive queue is checked for commands and replies
    self.alive = threading.Event()
    self.alive.set()

    # internal cli enabled
    self.enableCLI = False

    try:
      self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error, msg:
      error_msg = 'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + \
                  msg[1]
      self.error(error_msg)

    self.command_history = {}

    if 'acception_rules' not in kwargs:
      acception_rules = {}
      acception_rules['global_rule'] = 'Allow'
      acception_rules = {'global_rule': 'Allow'}
      self.set_acception_rules(**acception_rules)
    else:
      acception_rules = kwargs['acception_rules']
      #acception_rules = {'global_rule': 'Allow'}
      self.set_acception_rules(**acception_rules)

    self.timeout = CLIENT_TIMEOUT

  def set_acception_rules(self, **acception_rules):
    if 'global_rule' in acception_rules:
      global_rule = acception_rules['global_rule']
      del acception_rules['global_rule']
      try:
        assert(global_rule in ['Allow', 'Deny', 'Auth'])
      except:
        print 'global rule error'
        return
    else:
      global_rule = 'Deny'

    self.handlers = ez_process.get_bases_handler()
    self.handlers.update(self.get_handler())
    packet_handlers = ez_packet.get_handler()
    self.handlers.update(packet_handlers)

    for handler in self.handlers:
      if handler in acception_rules:
        self.handler_rules[handler] = acception_rules[handler]
      else:
        self.handler_rules[handler] = global_rule

#===============#
#  client send  #
#===============#

  def send(self, user_specs, data):
    """
    Send data to a user.

    :param user_id: id specifying the username
    :type  user_id: string

    :param data: The message or pickled object to be sent.
    :type  data: string
    """
    if isinstance(user_specs, str) or isinstance(user_specs, unicode):
      if user_specs in self.ips:
        user_addr = self.ips[user_specs]
      else:
        self.error("not connected to user")
        return
    elif type(user_specs) is tuple:
      user_addr = user_specs

    if sys.getsizeof(data) > self.socket_buffsize:
      send_packet_cmd = {'user_specs': user_specs, 'data': data}
      self.enqueue('send_packet', send_packet_cmd)
      return

    try:
      self.sockfd.sendto(data, user_addr)
    except IOError as e:
      self.error(str(e))


#===================#
#  client receive   #
#===================#

  def receive(self):
    """
    The receive function supports 3 types of data:

    - Dictionaries with p2pCommand keys and appropriate arguments as values
    - Message instances
    - Raw printable data

    UDP packets must be pickled otherwise the data is rejected
    """
    try:
      readable, _, _ = select.select([self.sockfd], [], [], 0)
    except:
      readable = None

    if not readable:
      return

    sdata, user_addr = self.sockfd.recvfrom(self.socket_buffsize)
    if sdata is not None:
      try:
        data = pickle.loads(sdata)
      except Exception as e:
        self.error(str(e))
        return

      self.handle_incomming_data(data, user_addr)

    else:
      self.error("Conflict in receive")

  def handle_incomming_data(self, data, user_addr):
    if isinstance(data, dict):
      for command in data:
        try:
          assert(command in self.handler_rules)
        except:
          self.error('No acception rule set for command ' + command + '.')
          return
        if self.handler_rules[command] == 'Allow':
          execute = True
        elif self.handler_rules[command] == 'Auth':
          master = (user_addr[0], int(user_addr[1]))
          if master in self.authentications:
            execute = True
          else:
            execute = False
        else:
          execute = False
        if execute:
          cmd_dct = data[command]
          cmd_dct.update({'host': user_addr[0], 'port': user_addr[1]})
          self.enqueue(command, cmd_dct)

    elif isinstance(data, Message):
      self.success("received msg")
      self.MsgDatabase.add_entry(data)
      if self.enableCLI:
        msg = data.clear_text()
        print "msg:", msg
        msg = 'server response: \n' + msg + '\n' + 'end'
        sender = data.sender
        cmd_dct = {'user_id': sender, 'msg': msg}
        self.enqueue('cmd_send_msg', cmd_dct)
      else:
        self.msg(data)

    elif isinstance(data, Packet):
      self.handle_packet(data, user_addr, self.handle_incomming_data)
    else:
      # raw data
      self.success(data)
      return data


#====================#
#  client main loop  #
#====================#

  def run(self):
    """
    client main loop: Processes all queued commands. The timeout (0.1) is set in
    order to allow checking self.alive
    """

    while self.alive.isSet():
      try:
        cmd = self.commandQueue.get(True, self.timeout)
        msg = command_args(self.handlers[cmd.funcStr])(self, cmd)
      except Queue.Empty:
        pass
      #except Exception, e:
        #self.error('ERROR: ' + str(e))
      readable = []
      try:
        if self.enableCLI:
          readable, _, _ = select.select([0, self.sockfd], [], [], 0)
        else:
          readable, _, _ = select.select([self.sockfd], [], [], 0)
      except:
        pass
      for i in readable:
        if i == 0:
          self.CLI()
        # socket activated -> there is incoming data
        elif i == self.sockfd:
          self.enqueue('receive')

      # check for messages in the replyQueue
      if self.enableCLI:
        try:
          reply = self.replyQueue.get(block=False)
          status = "success" if reply.replyType == p2pReply.success else "ERROR"
          print ('Client reply %s: %s' % (status, reply.data))
        except Queue.Empty:
          pass

def init_client(name, **kwargs):
  global cl
  cl = client(name=name, write_to_pipe=True, **kwargs)
  cl.start()

if __name__ == "__main__":
  try:
    name = sys.argv[1]
  except (IndexError, ValueError):
    print ("usage: %s <id>" % sys.argv[0])
    sys.exit(65)
  init_client()
