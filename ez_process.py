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
  queue for execution. The msgType is the string of the function which must
  match a key in the client handler functions (see ez_process_base_meta). Data
  is must be a dictionary and has to be filled with key,value pairs as required
  by the handler function.

  - msgType: type = str
  - data   : type = dict
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
  background processes. The class is not intended to be used directly by the
  user, and measures have been taken to facilitate the use of timed operations.
  See background_processes on how to use timed operations.

  Sofar Timer is used for:
  - Aborting a ping request after a certain time
  - Aborting a connection request after a certain time

  """
  def __init__(self, *args, **kwargs):
    threading._Timer.__init__(self, *args, **kwargs)
    self.setDaemon(True)

  def run(self):
    while not self.finished.isSet():
      self.finished.wait(self.interval)
      # the time has expired and the callback function is called
      if not self.finished.isSet():
        # background processes provides methods to store args and kwargs
        if hasattr(self, 'callback_args') and hasattr(self, 'callback_kwargs'):
          self.function(self, *self.callback_args, **self.kwargs)
        elif hasattr(self, 'callback_args'):
          self.function(self, *self.callback_args)
        elif hasattr(self, 'callback_kwargs'):
          self.function(self, **self.kwargs)
        else:
          self.function(self)
        self.finished.set()

#==============================================================================#
#                         class ez_process_base(_meta)                         #
#==============================================================================#

class ez_process_base_meta(type):
  """
  The metaclass __init__ function is called after the class is created, but
  before any class instance initialization. Any class with set
  __metaclass__ attribute to ez_process_base_meta which is equivalent to
  inheriting the class ez_process_base is extended by:

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

  commandQueue = Queue.Queue()
  replyQueue   = Queue.Queue()

  background_processes    = {}
  background_process_cmds = {}
  success_callback = {}

  #def __init__(self, **kwargs):
    #self.myself = None
    #assert('name' in kwargs)
    #self.name = kwargs['name']

  def success(self, success_msg=None):
    return p2pReply(p2pReply.success, success_msg)

  def error(self, error_msg=None):
    return p2pReply(p2pReply.error, error_msg)



#==============================================================================#
#                         class ez_background_process                          #
#==============================================================================#

class ez_background_process(ez_process_base):
  """
  A background process is defined by bg_cmd, the background process command
  dict:

  -bg_cmd = dict()

  The whole background process information is stored in a bg_cmd. A background
  process is invoked via the commandQueue via

  - my_background_process = p2pCommand('start_background_process', bg_cmd)
  - commandQueue.put(my_background_process)

  bg_cmd must include certain keys:

  1. (mandatory) 'process_id'      : my_process_id
  2. (mandatory) 'callback'        : my_func
  3. (optional)  'interval'        : my_time
  4. (optional)  'callback_args'   : (my_arg1, my_arg2, ...}
  5. (optional)  'callback_kwargs' : (my_kwarg1, my_kwarg2, ...}

  My_process_id can be anything, for instance a number, string or tuple of
  numbers and strings. Callback is the  function which is called after a period
  of time given by interval.  Callback_args and callback_kwargs are (optional)
  arguments which can be passed to callback

  A background process ends after callback has been called. A continous call of
  a user-defined callback can be achieved by defining the callback recursively
  via the reset_background_process method.
  (See ping_background)
  """

  # TODO: (bcn 2014-08-09) In a class this could be deleted. Is it necessary for
  # meta classes?!
  # -What do u mean?
  # - Background_processes keeps track of all processes -> needed
  # - super initialization is necessary -> needed
  def __init__(self, *args, **kwargs):
    super(ez_background_process, self).__init__(*args, **kwargs)

  def start_background_process(self, cmd):
    # construct background cmd allowing to reset the process
    bg_cmd = {}

    # Registering mandatory arguments
    try:
      assert('process_id' in cmd.data)
      process_id = cmd.data['process_id']
    except:
      print "no process_id given for background processes"
      return
    bg_cmd['process_id'] = process_id

    try:
      assert('callback' in cmd.data)
      callback = cmd.data['callback']
    except:
      print "no callback given for background processes"
      return
    bg_cmd['callback'] = callback

    # Default value of the time period is 5 seconds
    if 'interval' in cmd.data:
      interval = cmd.data['interval']
    else:
      interval = 5
    bg_cmd['interval'] = interval

    # generate Timer instance
    pr = Timer(interval, callback)
    # and add possibly callback args and kwargs
    if 'callback_args' in cmd.data:
      pr.callback_args        = cmd.data['callback_args']
      bg_cmd['callback_args'] = cmd.data['callback_args']
    if 'callback_kwargs' in cmd.data:
      pr.callback_kwargs        = cmd.data['callback_kwargs']
      bg_cmd['callback_kwargs'] = cmd.data['callback_kwargs']

    # construct background process
    bgp = p2pCommand('start_background_process', bg_cmd)
    self.background_process_cmds[process_id] = bgp

    # register the process
    self.background_processes[process_id] = pr
    # start the background process
    thread.start_new_thread(pr.run, ())

  def stop_background_processes(self):
    for process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]
      del self.background_process_cmds[process_id]

  def reset_background_process(self, process_id, new_process_cmd = None):
    """
    A process can be started over again if it is found in the background
    processes.
    Optionally the former process cmd can be replaced with a new one.
    """
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]
      if new_process_cmd != None:
        self.background_process_cmds['process_id'] = new_process_cmd
        self.commandQueue.put(process_cmd)
      else:
        bg_cmd = self.background_process_cmds[process_id]
        self.commandQueue.put(bg_cmd)

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
    try:
      assert('user_id' in cmd.data)
      user_id = cmd.data['user_id']
    except:
      print "no user_id in cmd.data"
      return

    process_id = ('ping_reply', user_id)
    if not process_id in self.background_processes:

      if 'success_callback' in cmd.data:
        self.success_callback[process_id] = cmd.data['success_callback']

      if 'error_callback' in cmd.data:
        error_callback = cmd.data['error_callback']
      else:
        def error_callback(self_timer):
          cmd = self.error("ping failed: " + user_id)
          self.replyQueue.put(cmd)
          del self.background_processes[process_id]

      if not user_id in self.ips:
        self.replyQueue.put(self.error("user not in client list"))
        if testing:
          return str(user_id) + " is not in client list"
      else:
        master  = self.ips[user_id]
        cmd_dct = {'user_id': user_id}
        ping    = {'ping_reply': cmd_dct}
        msg     = pickle.dumps(ping)
        try:
          self.sockfd.sendto(msg, master)
          bgp = p2pCommand('start_background_process',
                {'process_id'    : process_id,
                 'callback'      : error_callback,
                 'interval'      : 5})
          self.commandQueue.put(bgp)

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
    try:
      user_id = cmd.data['user_id']
      user_addr = (cmd.data['host'], cmd.data['port'])
    except:
      print "user_id/host/port not properly specified in ping_reply"

    self.replyQueue.put(self.success("ping request from: " + str(user_addr)))
    cmd_dct = {'user_id': user_id}
    ping    = {'ping_success': cmd_dct}
    msg     = pickle.dumps(ping)
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
    try:
      user_id = cmd.data['user_id']
      user_addr = (cmd.data['host'], cmd.data['port'])
    except:
      print "user_id/host/port not properly specified in ping_reply"

    #user_id, user_addr = cmd.data
    if user_id in self.ips:
      if self.ips[user_id] == user_addr:
        process_id = ('ping_reply', user_id)
        pr = self.background_processes[process_id]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[process_id]
        if process_id in self.success_callback:
          self.success_callback[process_id]()
          del self.success_callback[process_id]
        else:
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
    try:
      master = cmd.data['master']
    except:
      print "master not properly specified in connect"

    cmd_dct      = {'user_id': self.name}
    conn_request = {'connection_request': cmd_dct}
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
    try:
      user_id = cmd.data['user_id']
      user_addr = (cmd.data['host'], cmd.data['port'])
    except:
      print "user_id/host/port not properly specified in connection_request"
      return

    process_id = ('connection_request', user_addr)
    if not process_id in self.background_processes:
      cmd_dct = {'user_id': self.name}
      #con_holepunch = {'connection_nat_traversal': self.name}
      con_holepunch = {'connection_nat_traversal': cmd_dct}
      msg           = pickle.dumps(con_holepunch)
      try:
        self.sockfd.sendto(msg, user_addr)

        def connection_failed_func(self_timer):
          cmd = self.error("connection failed with: " + str(user_addr))
          self.replyQueue.put(cmd)
          del self.background_processes[process_id]

        bgp = p2pCommand('start_background_process',
              {'process_id'    : process_id,
               'callback'      : connection_failed_func,
               'interval'      : 5})
        self.commandQueue.put(bgp)
        cmd = self.success("connection request from user:" +
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
    #try:
      #user_id, user_addr = cmd.data
    try:
      user_id   = cmd.data['user_id']
      user_addr = (cmd.data['host'], cmd.data['port'])
    except:
      print ("user_id/host/port not properly specified in" +
             "connection_nat_traversal")
      return
    cmd_dct = {'user_id': self.name}
    con_success     = {'connection_success': cmd_dct}
    msg             = pickle.dumps(con_success)

    cmd = self.success("nat traversal succeded: " + str(user_addr))
    cmd_dct = {'user_id': user_id, 'host': user_addr[0], 'port': user_addr[1]}
    self.add_client(**cmd_dct)

    self.replyQueue.put(cmd)
    self.sockfd.sendto(msg, user_addr)


  def connection_success(self, cmd):
    """
    Not to be called by the user, but automatically invoked.

    Client B receives the news that Client A succeded and Client B adds Client A
    to the user db.

    - (user_id, (user_ip, user_port)) = cmd.data
    """
    try:
      user_id = cmd.data['user_id']
      host    = cmd.data['host']
      port    = cmd.data['port']
    except:
      print "user_id, host, port not properly specified in connection_success"

    user_addr = (host, port)
    process_id = ('connection_request', user_addr)
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]

    self.replyQueue.put(self.success("user: " + str(user_addr) +" with id: " + \
                                      user_id + " has connected"))

    cmd_dct = {'user_id': user_id, 'host': user_addr[0], 'port': user_addr[1]}
    self.add_client(**cmd_dct)


#==============================================================================#
#                                  ez_contact                                  #
#==============================================================================#

class ez_contact(ez_process_base):

  def __init__(self, *args, **kwargs):
    super(ez_contact, self).__init__(*args, **kwargs)

  def add_client(self, **kwargs):
    """
    Adds a new client to the clients ip base.

    - cmd.data['user_id'] = user_id
    """
    try:
      user_id = kwargs['user_id']
      self.ips[user_id] = (kwargs['host'], int(kwargs['port']))
    except:
      print "user_id/host/port not properly specified in add_client"

  def remove_client(self, user_id):
    if user_id in self.ips:
      del self.ips[user_id]
      self.replyQueue.put(p2pReply(p2pReply.success, "removed user"))
    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "user not found/removed"))

  def contact_request_out(self, cmd):
    """
    Method for exchanging public keys.

    - cmd.data['user_id'] = user_id
    """
    try:
      assert('user_id' in cmd.data)
      user_id = cmd.data['user_id']
    except:
      print "user_id not in ip list"

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      cmd_dct = {'user': self.myself}
      contact_request = {'contact_request_in': cmd_dct}
      msg             = pickle.dumps(contact_request)
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

  def contact_request_in(self, cmd):
    """
    User asks for contact data. We might have an options here restricting the
    users being allowed to request contact data.

    - cmd.data['user'] = user (User class instance)
    - host, port automatically filled by the receive method (see ez_p2p.py)
    """
    try:
      user = cmd.data['user']
      host = cmd.data['host']
      port = cmd.data['port']
    except:
      print "user/host/port not properly specified in contact_request_in"

    cmd_dct = {'user': self.myself}
    myself = {'add_contact': cmd_dct}
    msg    = pickle.dumps(myself)
    try:
      self.sockfd.sendto(msg, (host, port))
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def add_contact(self, cmd):
    try:
      new_user = cmd.data['user']
    except:
      print "user not properly specified in add_contact"

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
      #data = (self.name, self.MsgDatabase.UID_list())
      cmd_dct = {'user_id': self.name, 'UID_list': self.MsgDatabase.UID_list()}
      db_sync_request = {'db_sync_request_in': cmd_dct}
      msg             = pickle.dumps(db_sync_request)
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

  def db_sync_request_in(self, cmd):
    try:
      user_id  = cmd.data['user_id']
      UID_list = cmd.data['UID_list']
    except:
      print "user_id/UID_list not properly specified in db_sync_request_in"
      return

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
            cmd_dct = {'user_id': user_id, 'data':data}
            self.commandQueue.put(p2pCommand('send', cmd_dct))

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
    try:
      user_id = cmd.data['user_id']
    except:
      print "user id not properly specified in ips_request"
      return

    if not user_id in self.ips:
      print "self.ips:", self.ips
    else:
      master  = self.ips[user_id]
      print "self.ips:", self.ips
      cmd_dct = {'user_id': user_id}
      ping    = {'distributeIPs': cmd_dct}
      msg     = pickle.dumps(ping)
      try:
        self.sockfd.sendto(msg, master)

      except IOError as e:
        self.replyQueue.put(self.error(str(e)))
        self.replyQueue.put(self.error("ips_request unsuccessful"))

  def distributeIPs(self, cmd):
    try:
      user_id = cmd.data['user_id']
      host    = cmd.data['host']
      port    = cmd.data['port']
    except:
      print "user_id, host, port not properly specified in distributeIPs"

    master = (host, port)
    other_users = {u_id: self.ips[u_id] for u_id in self.ips \
                   if self.ips[u_id] != master}

    for other_id in other_users:
      cmd_dct_A = {'master': other_users[other_id]}
      cmd_dct_B = {'master': master}
      relay_request  = {'connect': cmd_dct_A}
      relay_request2 = {'connect': cmd_dct_B}
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


  def __init__(self, *args, **kwargs):
    super(ez_process, self).__init__(*args, **kwargs)

  # TODO: nick sockfd? Do 07 Aug 2014 00:40:15 CEST
  # Bit of a hack here since I'm using the sockfd which does not exist for
  # ez_process, but as I'm never calling an ez_process directly only through
  # inheritance everthing is fine as long as the child class has the sockfd
  # attribute.

#==================#
#  connect_server  #
#==================#

  def connect_server(self, cmd):
    """
    Connects to an endpoint without the use of NAT traversal techniques. The
    endpoint should be a server(-like) system listening on some port.

    - (host_ip, host_port) = cmd.data
    """
    try:
      assert('host' in cmd.data)
      host = cmd.data['host']
    except:
      print "no host specified in servermode"
      return
    try:
      assert('port' in cmd.data)
      port = int(cmd.data['port'])
    except:
      print "no port specified in servermode"
      return

    master       = (host, port)
    cmd_dct      = {'user_id': self.name}
    conn_success = {'connection_success': cmd_dct}
    msg          = pickle.dumps(conn_success)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def servermode(self, cmd):
    """
    Start listening on port. Mandatory arguments:

    - cmd.data['host'] = host
    - cmd.data['port'] = port
    """
    try:
      assert('host' in cmd.data)
      host = cmd.data['host']
    except:
      print "no host specified in servermode"
      return

    try:
      assert('port' in cmd.data)
      port = cmd.data['port']
    except:
      print "no port specified in servermode"
      return

    self.sockfd.bind((str(host), int(port)))
    self.replyQueue.put(self.success("listening socket"))

  def shutdown(self, cmd):
    if self.sockfd != None:
      self.sockfd.close()
    self.alive.clear()

  def send(self, cmd):
    """
    Send data to a user. Mandatory arguments:

    - cmd.data['user_id'] = user_id
    - cmd.data['data']    = data
    """
    try:
      assert('user_id' in cmd.data)
      user_id = cmd.data['user_id']
    except:
      print "user not registered"

    try:
      assert('data' in cmd.data)
      data = cmd.data['data']
    except:
      print "No data which could be sent"

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      try:
        self.sockfd.sendto(data, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "not connected to user"))
