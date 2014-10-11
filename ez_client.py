#==============================================================================#
#                                  ez_client                                   #
#==============================================================================#
# TODO: (bcn 2014-08-08) when this file only contains the client class, it
# should be renamed to ez_client.py ?!

#============#
#  Includes  #
#============#
#from __future__ import print_function

import sys, errno
import socket, select
import Queue, threading
import cPickle as pickle
import ez_message  as em

from datetime import datetime
from ez_process      import p2pCommand, p2pReply, ez_process
from ez_simple_cli   import ez_simple_cli
#from ez_user_methods import ez_user_methods
#from ez_process      import ez_process_base

CLIENT_TIMEOUT = 0.1

#==============================================================================#
#                                 class client                                 #
#==============================================================================#

class client(ez_process, ez_simple_cli, threading.Thread):
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
      self.replyQueue.put(self.error(error_msg))

    # online users are stored in the ips dict
    # ips = {user_id: (user_host, user_port)}
    self.ips = {}
    self.command_history = {}

    self.timeout = CLIENT_TIMEOUT

#===================#
#  client receive   #
#===================#

  def receive(self, cmd):
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
    sdata, user_addr = self.sockfd.recvfrom(4048)
    if sdata != None:
      try:
        data = pickle.loads(sdata)
      except:
        print "sdata:", sdata
        self.replyQueue.put(self.error("data not pickled -> rejected"))
        return

      # TODO: nick new interface here Do 07 Aug 2014 12:59:17 CEST
      # it shouldn't be possible that every user can start commands on other
      # users clients. We need some security measures here and we may connect
      # them with options like how often one can be pinged or being requested to
      # send packages etc.
      if isinstance(data, dict):
        for command in data:
          cmd_dct = data[command]
          cmd_dct.update({'host': user_addr[0], 'port': user_addr[1]})
          user_cmd = p2pCommand(command, cmd_dct)
          self.commandQueue.put(user_cmd)

      elif isinstance(data, em.Message):
        self.replyQueue.put(self.success("received msg"))
        self.MsgDatabase.add_entry(data)
        #print "bytes(data):", bytes(data)
        #print "sys.getsizeof(data):", sys.getsizeof(data)
        if self.enableCLI:
          print "data.clear_text():", data.clear_text()
        self.replyQueue.put(self.msg(data))
      else:
      # raw data
        self.replyQueue.put(self.success(data))
        return data

    else:
      self.replyQueue.put(self.error("Conflict in receive"))

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
        msg = self.handlers[cmd.msgType](self, cmd)
      except Queue.Empty:
        pass
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
          self.commandQueue.put(p2pCommand('receive'))

      # check for messages in the replyQueue
      if self.enableCLI:
        try:
          reply = self.replyQueue.get(block=False)
          status = "success" if reply.replyType == p2pReply.success else "ERROR"
          print ('Client reply %s: %s' % (status, reply.data))
        except Queue.Empty:
          pass


def init_client():
  global cl
  cl = client(name = sys.argv[1], write_to_pipe = True)
  cl.start()

if __name__ == "__main__":

  try:
    name = sys.argv[1]
  except (IndexError, ValueError):
    print ("usage: %s <id>" % sys.argv[0])
    sys.exit(65)
  init_client()
