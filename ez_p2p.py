#==============================================================================#
#                                  ez_client                                   #
#==============================================================================#

#============#
#  Includes  #
#============#
from __future__ import print_function
import sys, errno, time
import socket, struct, select
import Queue, threading
import cPickle as pickle

import ez_database as ed
import ez_user     as eu

#==============================================================================#
#                               class p2pCommand                               #
#==============================================================================#

class p2pCommand(object):
  """
  A p2pCommand encapsulates commands which are then appended to the command
  queue ready for execution.
  The msgType determines the data type, but yet there is no explicit type check.

  msgType = connect:  type(data) = tuple
                            data = (host, port) = (str, int)
  msgType = shutdown: type(data) = NoneType
  msgType = send:     type(data) = str
  msgType = receive:  type(data) = NoneType
  """
  connect, shutdown, send, receive                       = range(4)
  servermode, conn_request, relay_request, distributeIPs = range(4, 8)
  ping_request, ping_reply, ips_request                  = range(8,11)

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
  success, error = range(2)

  def __init__(self, replyType = None, data = None, clientID = None):
    self.clientID  = clientID
    self.replyType = replyType
    self.data      = data

#==============================================================================#
#                                 class client                                 #
#==============================================================================#

class client(threading.Thread):
  """
  Client class with queue system. Commands are executed by appending
  p2pCommand instances to the client commandQueue.
  The connect command allows to:
    1. Create a socket
    2. Connect to a remote server
  Send command:
    3. Data is send to all connected clients
  The receive commands:
    4. Receive a reply. The result is appended to the replyQueue.
  """
  def __init__(self, name = ""):
    super(client, self).__init__()
    #self.clientID = user

    self.commandQueue = Queue.Queue()
    self.replyQueue   = Queue.Queue()

    # As long as the client is alive queue is checked for commands and replies
    self.alive = threading.Event()
    self.alive.set()

    # internal cli enabled
    self.enableCLI = True

    # Storing client functionalities
    self.handlers = {
        p2pCommand.connect:       self.connect,
        p2pCommand.shutdown:      self.shutdown,
        p2pCommand.send:          self.send,
        p2pCommand.receive:       self.receive,
        p2pCommand.servermode:    self.servermode,
        p2pCommand.conn_request:  self.conn_request,
        p2pCommand.ping_request:  self.ping_request,
        p2pCommand.ping_reply:    self.ping_reply,
        p2pCommand.ips_request:   self.ips_request,
        p2pCommand.distributeIPs: self.distributeIPs,
        p2pCommand.relay_request: self.relay_request
        }
    try:
      self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    except socket.eror, msg:
      error_msg =  'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + \
                    msg[1]
      self.replyQueue.put(self.error(error_msg))
      sys.exit()

    self.ips = {}
    self.users_connected = 0
    self.timeout = 0

    db_name = 'sqlite:///:' + name + '_memory:'
    self.UserDatabase = ed.UserDatabase(localdb = db_name)


  def success(self, success_msg = None):
    return p2pReply(p2pReply.success, success_msg)

  def error(self, error_msg = None):
    return p2pReply(p2pReply.error, error_msg)

  def add_client(self, addr, user_id):
    self.users_connected += 1
    user_ip, user_port = addr
    self.ips[user_id] = (user_ip, user_port)

  def remove_client(self, user_id):
    self.UserDatabase.add_entries
    self.users_connected -= 1
    if user_id in self.ips:
      del self.ips[user_id]
      self.replyQueue.put(p2pReply(p2pReply.success, "removed user"))
    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "user not found/removed"))

  def ips_request(self, cmd):
    user_id = cmd.data
    if not user_id in self.ips:
      print ("user not in client list")
    else:
      master  = self.ips[user_id]
      ping    = {p2pCommand.distributeIPs: user_id}
      msg     = pickle.dumps(ping)
      header  = struct.pack('<L', len(msg))
      try:
        self.sockfd.sendto(header, master)
        self.sockfd.sendto(msg, master)

      except IOError as e:
        self.replyQueue.put(self.error(str(e)))
        self.replyQueue.put(self.error("ips_request unsuccessful"))


  def ping_reply(self, cmd):
    user_id, master = cmd.data
    print ("ping request from:", master)
    ping            = user_id
    msg             = pickle.dumps(ping)
    header          = struct.pack('<L', len(msg))
    try:
      self.sockfd.sendto(header, master)
      self.sockfd.sendto(msg, master)
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def ping_request(self, cmd):
    user_id = cmd.data
    print ("user_id:", user_id)
    print ("self.ips:", self.ips)
    if not user_id in self.ips:
      print ("user not in client list")
    else:
      master  = self.ips[user_id]
      ping    = {p2pCommand.ping_reply: user_id}
      msg     = pickle.dumps(ping)
      header  = struct.pack('<L', len(msg))
      try:
        self.sockfd.sendto(header, master)
        self.sockfd.sendto(msg, master)
        #self.replyQueue.put(self.success("ping"))
        self.timeout   = 2
        readable, _, _ = select.select([self.sockfd], [], [], self.timeout)
        if readable:
          response = self.receive()
          print ("ping succes")
          return True
        self.replyQueue.put(self.error("failed to receive data"))
        self.timeout = 0
        print ("ping failed removing user from clients")
        self.remove_client(user_id)
        return False

      except IOError as e:
        self.replyQueue.put(self.error(str(e)))
        self.replyQueue.put(self.error("ping unsuccessful"))
        #print ("ping unsuccessful")

  def connect(self, cmd):
    host, port, user_id = cmd.data
    master              = (host, port)
    conn_request        = {p2pCommand.conn_request: user_id}
    msg                 = pickle.dumps(conn_request)
    header              = struct.pack('<L', len(msg))
    try:
      self.sockfd.sendto(header, master)
      self.sockfd.sendto(msg, master)
      #self.replyQueue.put(self.success("send data"))
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

    #print ("send data to host")

  def conn_request(self, cmd):
    #self.sockfd.bind( cmd.data )
    data, addr = cmd.data
    print ("user:", addr, "with id:", data, " has connected")
    self.add_client(addr, data)

  def servermode(self, cmd):
    print ("cmd.data:", cmd.data)
    host, port = cmd.data
    self.sockfd.bind( (str(host), int(port) ) )
    print ("listening socket")

  def relay_request(self, cmd):
    other_users, server = cmd.data
    for other_user in other_users:
      self.ips[other_user] = other_users[other_user]
      print ("other_user:", other_user, other_users[other_user])

  def distributeIPs(self, cmd):
    if cmd.data != None:
      master = cmd.data[1]
      other_users  = { u_id: self.ips[u_id] for u_id in self.ips             \
                       if self.ips[u_id] != master }
      relay_request = {p2pCommand.relay_request: other_users}
      msg           = pickle.dumps(relay_request)
      header        = struct.pack('<L', len(msg))
      try:
        self.sockfd.sendto(header, master)
        self.sockfd.sendto(msg, master)
        self.replyQueue.put(self.success("distributed IPs"))
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

    else:
      for user_id in self.ips:
        other_users  = { u_id: self.ips[u_id] for u_id in self.ips             \
                         if u_id != user_id }
        relay_request = {p2pCommand.relay_request: other_users}
        msg           = pickle.dumps(relay_request)
        header        = struct.pack('<L', len(msg))
        master = self.ips[user_id]
        try:
          self.sockfd.sendto(header, master)
          self.sockfd.sendto(msg, master)
          self.replyQueue.put(self.success("distributed IPs"))
        except IOError as e:
          self.replyQueue.put(self.error(str(e)))

  def shutdown(self, cmd):
    if self.sockfd != None:
      self.sockfd.close()
    self.alive.clear()

  def send(self, cmd):
    """
    The struct module is used to handle binary data stored in files or from
    network connections. The first four bytes are reserved to store the size of
    the data (header).
    """
    user_id = cmd.data[0]

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      msg       = pickle.dumps(cmd.data[1])
      header    = struct.pack('<L', len(msg))
      try:
        self.sockfd.sendto(header, user_addr)
        self.sockfd.sendto(msg, user_addr)
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))

    else:
      self.replyQueue.put(p2pReply(p2pReply.error, "not connected to user"))

  def receive(self, cmd = None):
    """
    First the header_data is retrieved which holds the size to be received.
    """
    package_size = 4
    try:
      returned_bytes = self.receive_bytes(package_size)
      if returned_bytes != None:
        header_data, user_addr = returned_bytes
        if len(header_data) == package_size:
          msg_len = struct.unpack('<L', header_data)[0]
          data, _ = self.receive_bytes(msg_len)
          if len(data) == msg_len:
            sdata = pickle.loads(data)
            if isinstance(sdata, dict):
              for command in sdata:
                self.commandQueue.put(p2pCommand(command,
                                                (sdata[command], user_addr)))
            # pure data
            else:
              return sdata
            return
        self.replyQueue.put(self.error("Socket closed prematurely"))
        self.shutdown()
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def receive_bytes(self, n_bytes, user_addr = None):
    data = ''
    while len(data) < n_bytes:
      try:
        readable, _, _ = select.select([self.sockfd], [], [], self.timeout)
      except:
        self.replyQueue.put(self.error("failed to receive data"))
        return
      if readable == []:
        return
      for i in readable:
        chunk, addr = self.sockfd.recvfrom(n_bytes - len(data))
        if user_addr != None and user_addr != addr:
          self.replyQueue.put(self.error("receive conflict"))
          return

        if chunk == '':
          return
        data += chunk
    return data, addr


  def CLI(self):
    data = sys.stdin.readline()
    if not data:
      return
    # compare command without eol
    if str(data[:-1]) == "close":
      self.enableCLI = False
      self.commandQueue.put(p2pCommand(p2pCommand.shutdown))
      return
    elif str(data[:-1]) == "users":
      for user in self.ips:
        print ("user:", user, self.ips[user])
    elif str(data[:-1]) == "dist":
      self.commandQueue.put(p2pCommand(p2pCommand.distributeIPs))
    elif "ping" in str(data[:-1]):
      try:
        ping_cmd, user_id = data.split()
        self.commandQueue.put(p2pCommand(p2pCommand.ping_request,
                                         user_id))
      except:
        self.replyQueue.put(self.error("Syntax error in ping"))
    elif "add" in str(data[:-1]):
      try:
        _, user_id, host, port = data.split()
        self.add_client((str(host), int(port)), user_id)
        self.commandQueue.put(p2pCommand(p2pCommand.ping_request,
                                         user_id))
      except:
        self.replyQueue.put(self.error("Syntax error in user"))
    elif "servermode" in str(data[:-1]):
      try:
        _, host, port = data.split()
        self.commandQueue.put(p2pCommand(p2pCommand.servermode,
                                        (host, int(port))))
      except:
        self.replyQueue.put(self.error("Syntax error in servermode"))
    elif "send" in str(data[:-1]):
      try:
        _, host, port, msg = data.split()
        user_addr = (str(host), int(port))
        msg       = pickle.dumps(msg)
        header    = struct.pack('<L', len(msg))
        try:
          self.sockfd.sendto(header, user_addr)
          self.sockfd.sendto(msg, user_addr)
        except IOError as e:
          self.replyQueue.put(self.error(str(e)))
      except:
        self.replyQueue.put(self.error("Syntax error in send"))
    elif "ips" in str(data[:-1]):
      users = data.split()
      try:
        if len(users) > 1:
          for user_id in users[1:]:
            self.commandQueue.put(p2pCommand(p2pCommand.ips_request,
                                            (user_id)))
        else:
          for user_id in self.ips:
            self.commandQueue.put(p2pCommand(p2pCommand.ips_request,
                                            (user_id)))

      except:
        self.replyQueue.put(self.error("Syntax error in ips"))
    else:
      try:
        user_id, msg = data.split()
        self.commandQueue.put(p2pCommand(p2pCommand.send,
                                        (user_id, msg)))
      except:
        self.replyQueue.put(self.error("Syntax error in command"))

  def run(self):
    """
    client main loop: Processes all queued commands. The timeout (0.1) is set in
    order to allow checking self.alive
    """
    while self.alive.isSet():
      try:
        cmd = self.commandQueue.get(True, 0.1)
        msg = self.handlers[cmd.msgType](cmd)
        if isinstance(msg, str):
          print ("msg:", msg)
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
        elif i == self.sockfd:
          self.commandQueue.put(p2pCommand(p2pCommand.receive))

      try:
        # triggered if there is something to read or something has been sent
        reply = self.replyQueue.get(block=False)
        status = "success" if reply.replyType == p2pReply.success              \
                           else "ERROR"
        #self.log('Client reply %s: %s' % (status, reply.data))
        print ('Client reply %s: %s' % (status, reply.data))
      except Queue.Empty:
        pass
