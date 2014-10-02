#==============================================================================#
#                                  ez_client                                   #
#==============================================================================#
# TODO: (bcn 2014-08-08) when this file only contains the client class, it
# should be renamed to ez_client.py ?!

#============#
#  Includes  #
#============#
#from __future__ import print_function
import sys, types
import socket, select
import Queue, threading
import cPickle as pickle

from ez_process      import p2pCommand, p2pReply
from ez_user_methods import ez_user_methods
import ez_message  as em

CLIENT_TIMEOUT = 0.1

#==============================================================================#
#                                 class client                                 #
#==============================================================================#

class client(ez_user_methods, threading.Thread):
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
      sys.exit()

    # online users are stored in the ips dict
    # ips = {user_id: (user_host, user_port)}
    self.ips = {}
    self.command_history = {}

    self.timeout = CLIENT_TIMEOUT

#=======================#
#  simple build-in cli  #
#=======================#

# TODO: nick separate cli Do 07 Aug 2014 00:32:46 CEST
# The commands do only require the access to the commandQueue
# allowing to separate the cli from client

# TODO: nick send command Do 07 Aug 2014 00:37:22 CEST
# The send command still uses direct access to the clients socket -> should be
# done via commandQueue

  def CLI(self):
    data = sys.stdin.readline()
    if not data:
      return

#=================#
#  close process  #
#=================#
    if str(data[:-1]) == "close":
      self.enableCLI = False
      self.commandQueue.put(p2pCommand('shutdown'))
      return

#===========================#
#  online users + contacts  #
#===========================#
    elif str(data[:-1]) == "users":
      print "online users"
      for user in self.ips:
        print "user:", user, self.ips[user]
      print "contacts"
      UIDs = self.UserDatabase.UID_list()
      for entry in self.UserDatabase.get_entries(UIDs):
        print "contact:", entry.name

#================#
#  ping process  #
#================#
    elif "ping" in str(data[:-1]):
      try:
        #_, user_id = data.split()
        bp_ping = p2pCommand('ping_background')
        self.commandQueue.put(bp_ping)
        #self.commandQueue.put(p2pCommand('ping_request', user_id))
      except:
        self.replyQueue.put(self.error("Syntax error in ping"))

#============================#
#  add user to online users  #
#============================#
    elif "add" in str(data[:-1]):
      try:
        _, user_id, host, port = data.split()
        self.add_client(user_id, (str(host), int(port)))
        self.commandQueue.put(p2pCommand('ping_request', user_id))
      except:
        self.replyQueue.put(self.error("Syntax error in user"))

#===================#
#  start listening  #
#===================#
    elif "servermode" in str(data[:-1]):
      try:
        _, host, port = data.split()
        self.commandQueue.put(p2pCommand('servermode', (host, int(port))))
      except:
        self.replyQueue.put(self.error("Syntax error in servermode"))

#=====================================#
#  show running background processes  #
#=====================================#
    elif "bp" in str(data[:-1]):
      try:
        print ("background_processes:", self.background_processes)
      except:
        self.replyQueue.put(self.error("Syntax error in bp"))

    elif "sync" in str(data[:-1]):
      try:
        _, user_id = data.split()
        self.commandQueue.put(p2pCommand('db_sync_request_out', user_id))
      except:
        self.replyQueue.put(self.error("Syntax error in ips"))


#==================================================#
#  user requests connection with all online users  #
#==================================================#
    elif "ips" in str(data[:-1]):
      users = data.split()
      try:
        if len(users) > 1:
          for user_id in users[1:]:
            cmd_dct = {'user_id': user_id}
            self.commandQueue.put(p2pCommand('ips_request', cmd_dct))
        else:
          for user_id in self.ips:
            cmd_dct = {'user_id': user_id}
            self.commandQueue.put(p2pCommand('ips_request', cmd_dct))

      except:
        self.replyQueue.put(self.error("Syntax error in ips"))

#============================#
#  add user to contact list  #
#============================#
    elif "key" in str(data[:-1]):
      try:
        _, user_id = data.split()
        cmd_dct = {'user_id': user_id}
        self.commandQueue.put(p2pCommand('contact_request_out', cmd_dct))
      except:
        self.replyQueue.put(self.error("Syntax error in key"))

#========================#
#  verify send packages  #
#========================#
    elif "verify" in str(data[:-1]):
      for key in self.stored_packets:
        packets = self.stored_packets[key]
        reconstructed, result = packets.reconstruct_data()
        if not reconstructed:
          for packet_number in result:
            cmd = p2pCommand('packet_request',
                             ((packets.packets_hash, packet_number), key[0]))
            self.commandQueue.put(cmd)
        else:
          print "package:", key, " successfully reconstructed"

#======================#
#  send encrypted msg  #
#======================#
    else:
      try:
        user_id, msg = data.split()
        if not self.UserDatabase.in_DB(name=user_id):
          return

        mx = em.Message(self.name, user_id, msg)
        # store msg in db
        self.MsgDatabase.add_entry(mx)

        if not user_id in self.ips:
          return

        data = pickle.dumps(mx)
        cmd_data = {'user_id': user_id, 'data':data}
        self.commandQueue.put(p2pCommand('send', cmd_data))

      except:
        self.replyQueue.put(self.error("Syntax error in command"))

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
    sdata, user_addr = self.sockfd.recvfrom(2048)
    if sdata != None:
      try:
        data = pickle.loads(sdata)
      except:
        self.replyQueue.put(self.error("data not pickled -> rejected"))

      # TODO: nick new interface here Do 07 Aug 2014 12:59:17 CEST
      # it shouldn't be possible that every user can start commands on other
      # users clients. We need some security measures here and we may connect
      # them with options like how often one can be pinged or being requested to
      # send packages etc.
      if isinstance(data, dict):
        for command in data:
          cmd_dct = data[command]
          print "command:", command
          print "cmd_dct:", cmd_dct
          cmd_dct.update({'host': user_addr[0], 'port': user_addr[1]})
          #user_cmd = p2pCommand(command, (data[command], user_addr))
          user_cmd = p2pCommand(command, cmd_dct)
          self.commandQueue.put(user_cmd)

      # raw data
      else:
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
      try:
        reply = self.replyQueue.get(block=False)
        status = "success" if reply.replyType == p2pReply.success else "ERROR"
        print ('Client reply %s: %s' % (status, reply.data))
      except Queue.Empty:
        pass
