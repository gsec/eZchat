#==============================================================================#
#                                ez_prozess.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

import sys, errno, time
import cPickle as pickle

import ez_user     as eu
import Queue, thread, threading

#==============================================================================#
#                               class p2pCommand                               #
#==============================================================================#

class p2pCommand(object):
  """
  A p2pCommand encapsulates commands which are then appended to the command
  queue ready for execution.
  The msgType determines the data type. See method declaration.
  """
  def __init__(self, msgType = None, data = None):
    self.msgType  = msgType
    self.data     = data

#==============================================================================#
#                              class ClientReply                               #
#==============================================================================#

class p2pReply(object):
  """
  Encapsulate received data.
  A p2pReply instance can be appended to the reply queue.

  replyType = success:  type(data) = str
  replyType = error:    type(data) = str
  """
  error, success = range(2)

  def __init__(self, replyType = None, data = None, clientID = None):
    self.clientID  = clientID
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

class ez_ping(object):

  def __init__(self, *args, **kwargs):
    self.handlers.update( {
        'ping_request'   : self.ping_request,
        'ping_reply'     : self.ping_reply,
        'ping_success'   : self.ping_success,
        'ping_background': self.ping_background
        } )
    super(ez_ping, self).__init__(*args, **kwargs)

#================#
#  ping methods  #
#================#

  def ping_request(self, cmd):
    """
    Starts a ping request. Client A must be connected to Client B, i.e. they
    must be both in clients user database, otherwise the ping process fails. To
    enforce the precondition the argument requires the user_id. The user_addr is
    retrieved from the user db.

    - user_id = cmd.data
    """
    user_id = cmd.data
    pr_key = ('ping_reply', user_id)
    if not pr_key in self.background_processes:
      if not user_id in self.ips:
        self.replyQueue.put(self.error("user not in client list"))
      else:
        master  = self.ips[user_id]
        ping    = {'ping_reply': user_id}
        msg     = pickle.dumps(ping)
        try:
          self.sockfd.sendto(msg, master)

          def ping_failed_func(self_timer):
            cmd = self.error("ping failed: " + user_id)
            self.replyQueue.put(cmd)
            del self.background_processes[pr_key]

          self.start_background_process(pr_key, ping_failed_func, 5)

        except IOError as e:
          self.replyQueue.put(self.error(str(e)))
          self.replyQueue.put(self.eror("ping unsuccessful"))
    else:
      self.replyQueue.put(self.error("cannot ping again, " +                   \
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
    #time.sleep(3)
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
        pr_key = ('ping_reply', user_id)
        pr = self.background_processes[pr_key]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[pr_key]
        self.replyQueue.put(self.success("ping success: " + user_id))
        return True

    self.replyQueue.put(self.error("ping failed: " + user_id))
    return False

  def ping_background(self, cmd):
    # the process id
    pr_key = ('ping_reply', 'all')

    # define the function called by the timer after the countdown
    # ping_background_func calls itself resulting in an endless ping chain.
    def ping_background_func(self_timer, queue, user_ids):
      pr_key = ('ping_reply', 'all')
      # ping all users
      for user_id in user_ids:
        queue.put(p2pCommand('ping_request', user_id))

      # check if the process still running, i.e. that it has not been killed
      # the process might have been killed while this function called.
      # I don't know if this case can occur, so the if case is just to make it
      # safe
      if pr_key in self.background_processes:
        # Reset process. I wanted to avoid a while true loop as a background
        # process thats why the following steps are necessary. We might
        # implement a reset method.
        pr = self.background_processes[pr_key]
        pr.finished.set()
        pr.cancel()
        del self.background_processes[pr_key]
        self.start_background_process(pr_key, ping_background_func,
                                      10, self.commandQueue, self.ips.keys())

    # start the background process
    self.start_background_process(pr_key, ping_background_func, 10,
                                  self.commandQueue, self.ips.keys())


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

class ez_connect(object):
  def __init__(self, *args, **kwargs):
    self.handlers.update( {
        'connect':                  self.connect,
        'connection_success':       self.connection_success,
        'connection_request':       self.connection_request,
        'connection_nat_traversal': self.connection_nat_traversal
        } )
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
        cmd = self.success( "start connection  with :" + str(master) )
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
    pr_key = ('connection_request', user_addr)
    if not pr_key in self.background_processes:
      con_holepunch = {'connection_nat_traversal': self.name}
      msg           = pickle.dumps(con_holepunch)
      try:
        self.sockfd.sendto(msg, user_addr)

        def connection_failed_func(self_timer):
          cmd = self.error("connection failed with: " + str(user_addr))
          self.replyQueue.put(cmd)
          del self.background_processes[pr_key]

        self.start_background_process(pr_key, connection_failed_func, 5)
        cmd = self.success( "connection request from user:" +                  \
                            str(user_addr) +  " with id: "+ user_id )

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

    cmd = self.success( "nat traversal succeded: " + str(user_addr) )
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
    pr_key = ('connection_request', user_addr)
    if pr_key in self.background_processes:
      pr = self.background_processes[pr_key]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[pr_key]

    self.replyQueue.put(self.success( "user: " + str(user_addr) +" with id: " +\
                                      user_id + " has connected"))
    self.add_client(user_id, user_addr)



#==============================================================================#
#                                  ez_contact                                  #
#==============================================================================#

class ez_contact(object):

  def __init__(self, *args, **kwargs):
    self.handlers.update( {
        'contact_request_in' : self.contact_request_in,
        'contact_request_out': self.contact_request_out,
        'add_contact'        : self.add_contact
        } )
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
    user, user_addr = cmd.data
    myself    = {'add_contact': self.myself}
    msg       = pickle.dumps(myself)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def add_contact(self, cmd):
    new_user, _  = cmd.data
    if not self.UserDatabase.in_DB(UID = new_user.UID):
      self.myself  = eu.User(name = self.name)
      self.UserDatabase.add_entry(new_user)
      print "new_user:", new_user.name
    else:
      print "user alrdy in database -> contact updated"
      self.myself = self.UserDatabase.update_entry(new_user)

#==============================================================================#
#                                  ez_packet                                   #
#==============================================================================#

class ez_packet(object):

  def __init__(self, *args, **kwargs):
    self.handlers.update( {
        'send_packet':    self.send_packet,
        'packet_request': self.packet_request
        } )
    super(ez_packet, self).__init__(*args, **kwargs)

  def send_packet(self, cmd):
    packets_hash, packet_number, user_id = cmd.data
    if packets_hash in self.sent_packets:
      if packet_id in self.sent_packets[packets_hash].packets:
        data = pickle.dumps(self.sent_packets[packets_hash].packets[packet_id])
        if len(data) > 2048:
          self.replyQueue.put(self.error("data larger than 2048 bytes"))
        else:
          self.commandQueue.put(p2pCommand('send', (user_id, data)))
      else:
        p2pReply(p2pReply.error, "packet_id not in sent_packets")
    else:
      p2pReply(p2pReply.error, "packet not in sent_packets")

  def packet_request(self, cmd):
    packet_info, user_addr = cmd.data
    print ("packet request from:", user_addr)
    packet  = {'send_packet': packet_info}
    msg    = pickle.dumps(packet)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

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

    self.handlers.update( {
        'ips_request'  : self.ips_request,
        'distributeIPs': self.distributeIPs
        } )
    super(ez_relay, self).__init__(*args, **kwargs)

  def ips_request(self, cmd):
    user_id = cmd.data
    if not user_id in self.ips:
      self.replyQueue.put(self.error("user not in client list"))
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
      other_users  = { u_id: self.ips[u_id] for u_id in self.ips               \
                       if self.ips[u_id] != master }

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

class ez_process(ez_ping, ez_contact, ez_packet, ez_relay):
  def __init__(self, *args, **kwargs):
    self.handlers = {}
    super(ez_process, self).__init__(*args, **kwargs)

    self.commandQueue = Queue.Queue()
    self.replyQueue   = Queue.Queue()
    self.background_processes = {}

    # Storing client functionalities
    self.handlers.update( {
        'connect_server': self.connect_server,
        'shutdown':       self.shutdown,
        'send':           self.send,
        'receive':        self.receive,
        'servermode':     self.servermode,
        'process':        self.process,
        'test_func':      self.test_func
        } )


  # TODO: nick sockfd? Do 07 Aug 2014 00:40:15 CEST
  # Bit of a hack here since I'm using the sockfd which does not exist for
  # ez_process, but as I'm never calling an ez_process directly only through
  # inheritance everthing is fine as long as the child class has the sockfd
  # attribute.


  def start_background_process(self, pr_key, proc, interval, *args, **kwargs):
    pr = Timer(interval, proc, args, kwargs)
    self.background_processes[pr_key] = pr
    thread.start_new_thread(pr.run, ())

  def stop_background_processes(self):
    for pr_key in self.background_processes:
      pr = self.background_processes[pr_key]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[pr_key]

  def success(self, success_msg = None):
    return p2pReply(p2pReply.success, success_msg)

  def error(self, error_msg = None):
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
    print "connect server"
    master       = cmd.data
    conn_success = {'connection_success': self.name}
    msg          = pickle.dumps(conn_success)
    try:
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def servermode(self, cmd):
    host, port = cmd.data
    self.sockfd.bind( (str(host), int(port) ) )
    self.replyQueue.put(self.success("listening socket"))



      #relay_request = {p2pCommand.relay_request: other_users}
      #msg           = pickle.dumps(relay_request)
      #try:
        #self.sockfd.sendto(msg, master)
        #self.replyQueue.put(self.success("distributed IPs"))
      #except IOError as e:
        #self.replyQueue.put(self.error(str(e)))

    #else:
      #for user_id in self.ips:
        #other_users  = { u_id: self.ips[u_id] for u_id in self.ips             \
                         #if u_id != user_id }
        #relay_request = {p2pCommand.relay_request: other_users}
        #msg           = pickle.dumps(relay_request)
        #master = self.ips[user_id]
        #try:
          #self.sockfd.sendto(msg, master)
          #self.replyQueue.put(self.success("distributed IPs"))
        #except IOError as e:
          #self.replyQueue.put(self.error(str(e)))

  def test_func(self, cmd):
    self.replyQueue.put(self.success("cmd.data:", cmd.data))

  def process(self, cmd):
    data, user_addr = cmd.data
    self.replyQueue.put(self.success("cmd.data:", cmd.data))

  def shutdown(self, cmd):
    if self.sockfd != None:
      self.sockfd.close()
    self.alive.clear()

  def send(self, cmd):
    user_id = cmd.data[0]

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      msg = cmd.data[1]
      try:
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "not connected to user"))