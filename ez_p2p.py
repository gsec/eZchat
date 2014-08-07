#==============================================================================#
#                                  ez_client                                   #
#==============================================================================#

#============#
#  Includes  #
#============#
#from __future__ import print_function
import sys, time
import socket, select
import Queue, thread, threading
import cPickle as pickle

from ez_process  import ez_process, p2pCommand, p2pReply

import ez_user     as eu
import ez_packet   as ep
import ez_message  as em


#==============================================================================#
#                                 class client                                 #
#==============================================================================#

class client(ez_process, threading.Thread):
  """
  Client class with builtin queue system, p2p via NAT traversal and reliable udp
  packet system.

  Commands are executed by appending p2pCommand instances to the client
  commandQueue.

  Most commands are not intended to be called by the user himself, but are
  usually automatically called as a consequence of connection, ping or packet
  requests.

  Queue commands are defined in ez_process. The client takes care of input
  (IO + incomming packages), the user db and pulling commands/results from the
  queues.
  """
  def __init__(self, name = "", fail_connect = False):
    super(client, self).__init__()

    self.name = name
    # used to simulate udp-holepunching where one of the clients connection
    # request is declient by the others client NAT
    self.fail_connect = fail_connect

    # As long as the client is alive queue is checked for commands and replies
    self.alive = threading.Event()
    self.alive.set()

    # internal cli enabled
    self.enableCLI = True

    try:
      self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    except socket.eror, msg:
      error_msg =  'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' +   \
                    msg[1]
      self.replyQueue.put(self.error(error_msg))
      sys.exit()

    # online users are stored in the ips dict
    # ips = {user_id: (user_host, user_port)}
    self.ips = {}
    self.command_history = {}

    # sent_packets are cached in case they need to be send again
    self.sent_packets   = {}

    # received packets are cached in case packets belonging to a group of
    # packets is missing or packets being corrupted
    self.stored_packets = {}

    self.timeout = 0.1

    db_name = 'sqlite:///:' + self.name + 'memory:'
    self.UserDatabase = eu.UserDatabase(localdb = db_name)

    if not self.UserDatabase.in_DB(name = self.name):
      print "new user created"
      self.myself  = eu.User(name = self.name)
      self.UserDatabase.add_entry(self.myself)
    else:
      print "retrieved user"
      self.myself = self.UserDatabase.get_entry(name = self.name)

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
        _, user_id = data.split()
        self.commandQueue.put(p2pCommand('ping_request', user_id))
      except:
        self.replyQueue.put(self.error("Syntax error in ping"))

#============================#
#  add user to online users  #
#============================#
    elif "add" in str(data[:-1]):
      try:
        _, user_id, host, port = data.split()
        self.add_client((str(host), int(port)), user_id)
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

    #elif "time" in str(data[:-1]):
      #try:
        #_, t = data.split()
        #def put_command(urst):
          #cmd = p2pCommand('test_func', "hi")
          #self.commandQueue.put(cmd)

        #self.start_background_process(put_command, int(t))
      #except:
        #self.replyQueue.put(self.error("Syntax error in time"))

#=====================================#
#  show running background processes  #
#=====================================#
    elif "bp" in str(data[:-1]):
      try:
        print ("background_processes:", self.background_processes)
      except:
        self.replyQueue.put(self.error("Syntax error in bp"))


#==================================================#
#  user requests connection with all online users  #
#==================================================#
    elif "ips" in str(data[:-1]):
      users = data.split()
      try:
        if len(users) > 1:
          for user_id in users[1:]:
            self.commandQueue.put(p2pCommand('ips_request', (user_id)))
        else:
          for user_id in self.ips:
            self.commandQueue.put(p2pCommand('ips_request', (user_id)))

      except:
        self.replyQueue.put(self.error("Syntax error in ips"))

#============================#
#  add user to contact list  #
#============================#
    elif "key" in str(data[:-1]):
      try:
        _, user_id = data.split()
        self.commandQueue.put(p2pCommand('contact_request_out', (user_id)))
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
                            (packets.packets_hash, packet_number, key[0]) )
            self.commandQueue.put(cmd)
        else:
          print "package:", key, " successfully reconstructed"

#======================#
#  send encrypted msg  #
#======================#
    else:
      #try:
        user_id, msg = data.split()
        if not user_id in self.ips:
          return
        if not self.UserDatabase.in_DB(name = user_id):
          return

        mx = em.Message(self.name, user_id, msg)
        packets = ep.Packets(data = mx)
        print "packets.max_packets:", packets.max_packets
        self.sent_packets[packets.packets_hash] = packets

        for packet_id in packets.packets:
          #if packet_id != 5:
          data = pickle.dumps(packets.packets[packet_id])
          if len(data) > 2048:
            self.replyQueue.put(self.error("data larger than 2048 bytes"))
          else:
            self.commandQueue.put(p2pCommand('send', (user_id, data)))
      #except:
        #self.replyQueue.put(self.error("Syntax error in command"))

#===================#
#  client receive   #
#===================#

  def receive(self, cmd):
    """
    The receive function supports 3 types of data:

    - Dictionaries with p2pCommand keys and appropriate arguments as values
    - Packet instances, see ez_packet.py. They underly further restrictions, see
      below
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
          user_cmd = p2pCommand(command, (data[command], user_addr))
          self.commandQueue.put(user_cmd)

      # packet
      elif isinstance(data, ep.Packet):

        packets_hash = data.packets_hash
        for user_id in self.ips:
          # packages are dropped if not associated to a known user_id
          if user_addr == self.ips[user_id]:
            key = (user_addr, packets_hash)
            if not key in self.stored_packets:
              self.stored_packets[key] = ep.Packets()
              self.stored_packets[key].max_packets = data.max_packets
              self.stored_packets[key].packets = {}

            packets = self.stored_packets[key]

            if data.max_packets == 1 and data.packet_number == 0:
              self.replyQueue.put(self.success(pickle.loads(data.data)))
              return

            packets.packets[data.packet_number] = data
            self.stored_packets[key]            = packets

            self.replyQueue.put(self.success("Received package"))

            pr_key = ('receive', user_id)

            # TODO: nick prebuild automatic packet request Do 07 Aug 2014
            # 13:01:49 CEST Same here, we need a new interface with options
            # which checks whether packets have been send correctly and complete
            # and in case requests missing or corrupted packets

            def update_and_reconstruct_packets(*args):
              packets = self.stored_packets[key]
              reconstructed, result = packets.reconstruct_data()
              if reconstructed:
                self.replyQueue.put(self.success(result))
                pr = self.background_processes[pr_key]
                pr.finished.set()
                pr.cancel()
                del self.background_processes[pr_key]
              else:
                pass
                #if not pr_key in self.background_processes:
                  #self.start_background_process( pr_key,
                                                 #update_and_reconstruct_packets,
                                                 #5 )

            if packets.max_packets == len(packets.packets):
              update_and_reconstruct_packets()

            else:
              #pass
              if not pr_key in self.background_processes:
                self.start_background_process( pr_key,
                                               update_and_reconstruct_packets,
                                               5 )

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
        msg = self.handlers[cmd.msgType](cmd)
      except Queue.Empty as e:
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
        # socket activated -> there is incomming data
        elif i == self.sockfd:
          self.commandQueue.put(p2pCommand('receive'))

      # check for messages in the replyQueue
      try:
        reply = self.replyQueue.get(block=False)
        status = "success" if reply.replyType == p2pReply.success else "ERROR"
        print ('Client reply %s: %s' % (status, reply.data))
      except Queue.Empty:
        pass
