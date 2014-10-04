#==============================================================================#
#                               ez_user_methods                                #
#==============================================================================#

#============#
#  Includes  #
#============#

import os
#import ez_cli     as cli
import ez_pipe    as pipe
import ez_user    as eu
import ez_message as em
import cPickle as pickle
from ez_process import ez_process, p2pCommand, p2pReply

class ez_user_methods(ez_process):
  """
  ez_user_methods contains methods intended to be called directly by the user.
  the class is inherited by the client which makes the methods available for the
  UI. It also takes care of the user and message database.
  """
  def __init__(self, **kwargs):
    super(ez_user_methods, self).__init__(**kwargs)
    assert('name' in kwargs)
    self.name = kwargs['name']

    # every new client gets a fresh database in memory for now. Should be made
    # an argument to support test as well as use case
    #db_name = 'sqlite:///:' + self.name + 'memory:'
    user_db_name = 'sqlite:///' + self.name + '_contacts:'
    msg_db_name  = 'sqlite:///' + self.name + '_messages:'
    self.UserDatabase = eu.UserDatabase(localdb=user_db_name)
    self.MsgDatabase  = em.MessageDatabase(localdb=msg_db_name)

    if not self.UserDatabase.in_DB(name=self.name):
      #self.replyQueue.put(self.success("New user created"))
      #os.write(pipe.pipe, 'reply')
      self.myself = eu.User(name=self.name)
      self.UserDatabase.add_entry(self.myself)
    else:
      #self.replyQueue.put(self.success("Retrieved user"))
      #print "reply"
      #print "pipe.pipe:", pipe.pipe
      #os.write(pipe.pipe, 'reply')

      #self.replyQueue.put(self.success("test"))
      #print "reply"
      self.myself = self.UserDatabase.get_entry(name=self.name)

  def cmd_close(self):
    self.enableCLI = False
    self.commandQueue.put(p2pCommand('shutdown'))
    return

  def cmd_get_online_users(self):
    #return [(user, self.ips[user]) for user in self.ips]
    print [(user, self.ips[user]) for user in self.ips]

  def cmd_get_contact_names(self):
    UIDs = self.UserDatabase.UID_list()
    #return [entry.name for entry in self.UserDatabase.get_entries(UIDs)]
    print [entry.name for entry in self.UserDatabase.get_entries(UIDs)]

  def cmd_ping(self, user_id):
    """Ping a user given his ID."""
    try:
      cmd_dct = {'user_id': user_id}
      self.commandQueue.put(p2pCommand('ping_request', cmd_dct))
    except:
      self.replyQueue.put(self.error("Syntax error in ping"))

  def cmd_add(self, user_id, host, port):
      #try:
        cmd_dct = {'user_id': user_id, 'host': host, 'port':port}
        self.add_client(**cmd_dct)
        self.commandQueue.put(p2pCommand('ping_request', cmd_dct))
      #except:
        #self.replyQueue.put(self.error("Syntax error in user"))

  def cmd_servermode(self, host, port):
    try:
      cmd_dct = {'host': host, 'port': port}
      self.commandQueue.put(p2pCommand('servermode', cmd_dct))
    except:
      self.replyQueue.put(self.error("Syntax error in servermode"))

  def cmd_connect(self, host, port):
    #master = (host, int(port))
    cmd_dct = {'host': host, 'port':int(port)}
    try:
      self.commandQueue.put(p2pCommand('connect_server', cmd_dct))
      cmd_dct['user_id'] = 'server'
      self.add_client(**cmd_dct)
    except:
      self.replyQueue.put(self.error("Syntax error in connect"))

  def cmd_bg(self):
    """ Show background processes """
    try:
      print ("background_processes:", self.background_processes)
    except:
      self.replyQueue.put(self.error("Syntax error in bp"))

  def cmd_sync(self, user_id):
    try:
      cmd_dct = {'user_id': user_id}
      self.commandQueue.put(p2pCommand('db_sync_request_out', cmd_dct))
    except:
      self.replyQueue.put(self.error("Syntax error in ips"))

  def cmd_ips(self, user_id):
    try:
      assert(user_id in self.ips)
      cmd_dct = {'user_id': user_id}
      self.commandQueue.put(p2pCommand('ips_request', cmd_dct))
    except:
      print "user:", user
      self.replyQueue.put(self.error("Syntax error in ips"))

  def cmd_key(self, user_id):
    try:
      cmd_dct = {'user_id': user_id}
      self.commandQueue.put(p2pCommand('contact_request_out', cmd_dct))
    except:
      self.replyQueue.put(self.error("Syntax error in key"))

  def cmd_send_msg(self, user_id, msg):
    #try:
      if not self.UserDatabase.in_DB(name=user_id):
        # raise error instead
        self.replyQueue.put(self.error("User not in DB"))
        return

      # store msg in db
      # TODO: nick Sa 04 Okt 2014 15:06:36 CEST
      # apparently crypto does not allow unicode
      mx = em.Message(self.name, user_id, str(msg))
      self.MsgDatabase.add_entry(mx)

      if not user_id in self.ips:
        # Strategy: send msg to random guys
        return

      data = pickle.dumps(mx)
      cmd_data = {'user_id': user_id, 'data':data}
      self.commandQueue.put(p2pCommand('send', cmd_data))

    #except:
      #self.replyQueue.put(self.error("Syntax error in command"))

  def ping_background(self, cmd):
    process_id = ('ping_reply', 'all')

    # define the function called by the timer after the countdown
    # ping_background_func calls itself resulting in an endless ping chain.
    def ping_background_func(self_timer, queue, user_ips):
      # ping all users
      user_ids = user_ips.keys()

      # custom success_callback
      def success_ping_all():
        print "background ping successful"

      for user_id in user_ids:
        cmd_dct = {'user_id': user_id, 'success_callback': success_ping_all}
        queue.put(p2pCommand('ping_request', cmd_dct))

      # check if the process still running, i.e. that it has not been killed
      # the process might have been killed while this function called.
      if process_id in self.background_processes:
        # Reset process.
        self.reset_background_process(self, process_id)

    bgp = p2pCommand('start_background_process',
            {'process_id'    : process_id,
             'callback'      : ping_background_func,
             'interval'      : 1,
             'callback_args' : (self.commandQueue, self.ips, )})
    self.commandQueue.put(bgp)

