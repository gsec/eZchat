#==============================================================================#
#                                ez_process.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

import types
import Queue, thread, threading


import cPickle   as pickle
import ez_user   as eu
import ez_packet as ep
#==============================================================================#
#                               class p2pCommand                               #
#==============================================================================#

class p2pCommand(object):
  """
  A p2pCommand encapsulates commands which are then appended to the command
  queue ready for execution.
  The msgType is determined by the process,
  e.g. ping_request cmd.data = user_id (string).
  """
  def __init__(self, msgType=None, data=None):
    self.msgType = msgType
    self.data    = data

#==============================================================================#
#                                class p2pReply                                #
#==============================================================================#

class p2pReply(object):
  """
  Encapsulate received data.
  A p2pReply instance can be appended to the reply queue.

  replyType = success:  type(data) = str
  replyType = error:    type(data) = str
  """
  error, success = range(2)

  def __init__(self, replyType=None, data=None):
    self.replyType = replyType
    self.data      = data

#==============================================================================#
#                                 class Timer                                  #
#==============================================================================#

class Timer(threading._Timer):
  """
  Timer instances are used in the client class to start timed non-blocking
  background processes.

  - Abort a ping request after a certain time
  - Abort a connection request after a certain time
  - Verify if missing packets must be requested

  For more details consider the client class
  """
  def __init__(self, *args, **kwargs):
    threading._Timer.__init__(self, *args, **kwargs)
    self.setDaemon(True)

  def run(self):
    while not self.finished.isSet():
      self.finished.wait(self.interval)
      if not self.finished.isSet():
        self.function(self, *self.args, **self.kwargs)
        self.finished.set()

#==============================================================================#
#                         class ez_process_base(_meta)                         #
#==============================================================================#

class ez_process_base_meta(type):
  """
  The metaclass __init__ function is called after the class is created, but
  before any class instance initialization. Any class with set
  __metaclass__ attribute to ez_process_base_meta (which is equivalent to
  inheriting the class ez_process_base) is extended by:

  - self.handlers: dictionary storing all user-defined functions
  - global attributes as class attributes

  self.handlers is called in the client main loop in p2pclient
  """
  def __init__(cls, name, bases, dct):
    if not hasattr(cls, 'handlers'):
      cls.handlers = {}
    for attr in [x for x in dct if not x.startswith('_')]:
      # register process functionalities and inherit them to child classes
      if isinstance(dct[attr], types.FunctionType):
        assert not attr in cls.handlers
        cls.handlers[attr] = dct[attr]

      # register global attributes and inherit them to child classes
      else:
        cls.attr = dct[attr]

    super(ez_process_base_meta, cls).__init__(name, bases, dct)

class ez_process_base(object):
  __metaclass__ = ez_process_base_meta
  def __init__(self, *args, **kwargs):
    super(ez_process_base, self).__init__(*args, **kwargs)

#==============================================================================#
#                         class ez_background_process                          #
#==============================================================================#

class ez_background_process(ez_process_base):

  background_processes = {}
  # TODO: (bcn 2014-08-09) In a class this could be deleted. Is it necessary for
  # meta classes?!
  # -What do u mean?
  # - Background_processes keeps track of all processes -> needed
  # - super initialization is necessary -> needed
  def __init__(self, *args, **kwargs):
    super(ez_background_process, self).__init__(*args, **kwargs)

  #def start_background_process(self, process_id, callback,
                               #interval, *args, **kwargs):

  def start_background_process(self, cmd):
    process_id = cmd.data[0]
    if len(cmd.data) > 1:
      callback = cmd.data[1]
    if len(cmd.data) > 2:
      interval = cmd.data[2]
    else:
      interval = 5
    if len(cmd.data) == 4:
      callback_args = cmd.data[3]
    else:
      callback_args = ()

    #pr = Timer(interval, callback, *args, **kwargs)
    pr = Timer(interval, callback, *callback_args)
    self.background_processes[process_id] = pr
    thread.start_new_thread(pr.run, ())

  def stop_background_processes(self):
    for process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

  def reset_background_process(self, process_id):
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]
      bgp = p2pCommand('start_background_process',
            (process_id, pr.function, pr.interval,
              (self.commandQueue, self.ips.keys())))
      self.commandQueue.put(bgp)
      #self.start_background_process(process_id, pr.function, pr.interval,
                                    #self.commandQueue, self.ips.keys())

#==============================================================================#
#                                   ez_ping                                    #
#==============================================================================#

# schematic view of the ping process
#------------------------------------------------------------------------------#
#              /----------\       ping request        /----------\             #
#              | client A |-------------------------> | client B |             #
#              `----------'              \            `----------'             #
#   start timer     |        ping failed /                  |                  #
#                   |        x-----.----'                   /                  #
#                   |               `---------------------'                    #
#   ping success    | cancel timer  /                                          #
#      <------------+--------------'                                           #
#                   \                                                          #
#                    `-> Time over -> ping failed                              #
#------------------------------------------------------------------------------#

class ez_ping(ez_background_process):

  def __init__(self, *args, **kwargs):
    super(ez_ping, self).__init__(*args, **kwargs)

#================#
#  ping methods  #
#================#

  def ping_request(self, cmd, testing=False):
    """
    Starts a ping request. Client A must be connected to Client B, i.e. they
    must be both in clients user database, otherwise the ping process fails. To
    enforce the precondition the argument requires the user_id. The user_addr is
    retrieved from the user db.

    - user_id = cmd.data
    """
    user_id = cmd.data
    process_id = ('ping_reply', user_id)
    if not process_id in self.background_processes:
      if not user_id in self.ips:
        self.replyQueue.put(self.error("user not in client list"))
        if testing:
          return str(user_id) + " is not in client list"
      else:
        master = self.ips[user_id]
        ping   = {'ping_reply': user_id}
        msg    = pickle.dumps(ping)
        try:
          self.sockfd.sendto(msg, master)

          def ping_failed_func(self_timer):
            cmd = self.error("ping failed: " + user_id)
            self.replyQueue.put(cmd)
            del self.background_processes[process_id]
          bgp = p2pCommand('start_background_process',
                            (process_id, ping_failed_func, 5))
          self.commandQueue.put(bgp)
          #self.start_background_process(process_id, ping_failed_func, 5)

        except IOError as e:
          self.replyQueue.put(self.error(str(e)))
          self.replyQueue.put(self.error("ping unsuccessful"))
    else:
      self.replyQueue.put(self.error("cannot ping again, " + \
                                     "still waiting for response"))

  def ping_reply(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    Client As ping request arrived and Client B responds with a ping_success

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    user_id, user_addr = cmd.data

    self.replyQueue.put(self.success("ping request from: " + str(user_addr)))
    ping   = {'ping_success': user_id}
    msg    = pickle.dumps(ping)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def ping_success(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    The ping process succeded and Client A cancels the timer background process.

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    user_id, user_addr = cmd.data
    if user_id in self.ips:
      if self.ips[user_id] == user_addr:
        process_id = ('ping_reply', user_id)
        pr = self.background_processes[process_id]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[process_id]
        self.replyQueue.put(self.success("ping success: " + user_id))
        return True

    self.replyQueue.put(self.error("ping failed: " + user_id))
    return False




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

class ez_connect(ez_background_process):
  def __init__(self, *args, **kwargs):
    super(ez_connect, self).__init__(*args, **kwargs)

#============================#
#  UDP-Holepunching methods  #
#============================#

  def connect(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    The connect method is invoked by the server on client A/B with (ip, port)
    from client B/A. Client A/B starts a connection_request, but in practice
    only one of the two 'connects' get passed the clients NAT.

    - (user_ip, user_port) = cmd.data
    """
    master, _    = cmd.data
    conn_request = {'connection_request': self.name}
    msg          = pickle.dumps(conn_request)
    try:
      if self.fail_connect:
        pass
      else:
        self.sockfd.sendto(msg, master)
        cmd = self.success("start connection with " + str(master))
        self.replyQueue.put(cmd)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))


  def connection_request(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    A succesful connection_request punches a hole in the client As NAT and tries
    to verify if client Bs NAT traversal succeeded. It may happen that client Bs
    NAT declines the request, that it does not support UDP-holepunching or that
    the udp package was not properly sent which is why a background verification
    process is started, informing, if necessary, client A of the failed
    connection process.

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    user_id, user_addr = cmd.data
    process_id = ('connection_request', user_addr)
    if not process_id in self.background_processes:
      con_holepunch = {'connection_nat_traversal': self.name}
      msg           = pickle.dumps(con_holepunch)
      try:
        self.sockfd.sendto(msg, user_addr)

        def connection_failed_func(self_timer):
          cmd = self.error("connection failed with: " + str(user_addr))
          self.replyQueue.put(cmd)
          del self.background_processes[process_id]
        bgp = p2pCommand('start_background_process',
                          (process_id, connection_failed_func, 5))
        self.commandQueue.put(bgp)
        #self.start_background_process(process_id, connection_failed_func, 5)
        cmd = self.success("connection request from user:" + \
                           str(user_addr) + " with id: " + user_id)

        self.replyQueue.put(cmd)

      except IOError as e:
        self.replyQueue.put(self.error(str(e)))
        self.replyQueue.put(self.error("connection unsuccessful"))
    else:
      cmd = self.error("cannot connect again, still waiting for response")
      self.replyQueue.put(cmd)

  def connection_nat_traversal(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    NAT traversal succeded for client A and the connection is established.
    Client B is added to the db and is also informed about the connection.

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    user_id, user_addr = cmd.data
    con_success     = {'connection_success': self.name}
    msg             = pickle.dumps(con_success)

    cmd = self.success("nat traversal succeded: " + str(user_addr))
    self.add_client(user_id, user_addr)

    self.replyQueue.put(cmd)
    self.sockfd.sendto(msg, user_addr)


  def connection_success(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    Client B receives the news that Client A succeded and Client B adds Client A
    to the user db.

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    user_id, user_addr = cmd.data
    process_id = ('connection_request', user_addr)
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    self.replyQueue.put(self.success("user: " + str(user_addr) +" with id: " + \
                                      user_id + " has connected"))
    self.add_client(user_id, user_addr)


#==============================================================================#
#                                  ez_contact                                  #
#==============================================================================#

class ez_contact(ez_process_base):

  def __init__(self, *args, **kwargs):
    super(ez_contact, self).__init__(*args, **kwargs)

  def add_client(self, user_id, user_addr):
    self.ips[user_id]  = user_addr
    user_ip, user_port = user_addr

  def remove_client(self, user_id):
    if user_id in self.ips:
      del self.ips[user_id]
      self.replyQueue.put(p2pReply(p2pReply.success, "removed user"))
    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "user not found/removed"))

  def contact_request_out(self, cmd):
    user_id = cmd.data
    if user_id in self.ips:
      user_addr = self.ips[user_id]
      contact_request = {'contact_request_in': self.myself}
      msg             = pickle.dumps(contact_request)
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

  def contact_request_in(self, cmd):
    # user asks for contact data. We might have an options here restricting the
    # users being allowed to request contact data.
    user, user_addr = cmd.data

    myself    = {'add_contact': self.myself}
    msg       = pickle.dumps(myself)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def add_contact(self, cmd):
    new_user, _  = cmd.data
    if not self.UserDatabase.in_DB(UID=new_user.UID):
      self.myself  = eu.User(name=self.name)
      self.UserDatabase.add_entry(new_user)
      print "new_user:", new_user.name
    else:
      print "user alrdy in database -> contact updated"
      self.myself = self.UserDatabase.update_entry(new_user)

class ez_db_sync(ez_process_base):

  def __init__(self, *args, **kwargs):
    super(ez_db_sync, self).__init__(*args, **kwargs)

  def db_sync_request_out(self, cmd):
    user_id = cmd.data
    if user_id in self.ips:
      user_addr = self.ips[user_id]
      data = (self.name, self.MsgDatabase.UID_list())
      db_sync_request = {'db_sync_request_in': data}
      msg             = pickle.dumps(db_sync_request)
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

  def db_sync_request_in(self, cmd):
    (user_id, UID_list), _ = cmd.data
    if user_id in self.ips:
      user_addr = self.ips[user_id]
      UIDs_to_sync = self.MsgDatabase.complement_entries(UID_list)
      if len(UIDs_to_sync) != 0:
        packets = ep.Packets(data = self.MsgDatabase.get_entries(UIDs_to_sync))
        self.sent_packets[packets.packets_hash] = packets
        for packet_id in packets.packets:
          data = pickle.dumps(packets.packets[packet_id])
          if len(data) > 2048:
            self.replyQueue.put(self.error("data larger than 2048 bytes"))
          else:
            self.commandQueue.put(p2pCommand('send', (user_id, data)))


#==============================================================================#
#                                class ez_relay                                #
#==============================================================================#

class ez_relay(ez_connect):
  """
  Supplies methods for initiating client client connection via NAT traversal

  - ips_request  : client starts connection request with the sever
  - distributeIPs: server relays two-clients at a time by sending a
                   relay_request
  """

  def __init__(self, *args, **kwargs):

    super(ez_relay, self).__init__(*args, **kwargs)

  def ips_request(self, cmd):
    user_id = cmd.data
    if not user_id in self.ips:
      print "self.ips:", self.ips
    else:
      master  = self.ips[user_id]
      ping    = {'distributeIPs': user_id}
      msg     = pickle.dumps(ping)
      try:
        self.sockfd.sendto(msg, master)

      except IOError as e:
        self.replyQueue.put(self.error(str(e)))
        self.replyQueue.put(self.error("ips_request unsuccessful"))

  def distributeIPs(self, cmd):
    if cmd.data != None:
      master = cmd.data[1]
      other_users = {u_id: self.ips[u_id] for u_id in self.ips \
                     if self.ips[u_id] != master}

      for other_id in other_users:
        relay_request  = {'connect': other_users[other_id]}
        relay_request2 = {'connect': master}
        msg            = pickle.dumps(relay_request)
        msg2           = pickle.dumps(relay_request2)
        try:
          self.sockfd.sendto(msg, master)
          self.sockfd.sendto(msg2, other_users[other_id])
          self.replyQueue.put(self.success("distributed IPs"))
        except IOError as e:
          self.replyQueue.put(self.error(str(e)))

#==============================================================================#
#                               class ez_process                               #
#==============================================================================#

class ez_process(ez_ping, ez_contact, ez_relay, ez_db_sync):

  commandQueue = Queue.Queue()
  replyQueue   = Queue.Queue()

  def __init__(self, *args, **kwargs):
    super(ez_process, self).__init__(*args, **kwargs)

  # TODO: nick sockfd? Do 07 Aug 2014 00:40:15 CEST
  # Bit of a hack here since I'm using the sockfd which does not exist for
  # ez_process, but as I'm never calling an ez_process directly only through
  # inheritance everthing is fine as long as the child class has the sockfd
  # attribute.

  def success(self, success_msg=None):
    return p2pReply(p2pReply.success, success_msg)

  def error(self, error_msg=None):
    return p2pReply(p2pReply.error, error_msg)

#==================#
#  connect_server  #
#==================#

  def connect_server(self, cmd):
    """
    Connects to an endpoint without the use of NAT traversal techniques. The
    endpoint should be a server(-like) system listening on some port.

    - (host_ip, host_port) = cmd.data
    """
    master       = cmd.data
    conn_success = {'connection_success': self.name}
    msg          = pickle.dumps(conn_success)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def servermode(self, cmd):
    host, port = cmd.data
    self.sockfd.bind((str(host), int(port)))
    self.replyQueue.put(self.success("listening socket"))

  def shutdown(self, cmd):
    if self.sockfd != None:
      self.sockfd.close()
    self.alive.clear()

  def send(self, cmd):
    user_id = cmd.data[0]

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      msg       = cmd.data[1]
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "not connected to user"))
