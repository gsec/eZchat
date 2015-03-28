#==============================================================================#
#                               ez_simple_cli.py                               #
#==============================================================================#

#============#
#  Includes  #
#============#

import sys
import cPickle as pickle
from ez_process import p2pCommand

#==============================================================================#
#                               class simple_cli                               #
#==============================================================================#

class ez_simple_cli(object):

  def __init__(self, *args, **kwargs):
    super(ez_simple_cli, self).__init__(*args, **kwargs)

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
        print "user:", self.ips[user], user
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
      except:
        self.error("Syntax error in ping")

#============================#
#  add user to online users  #
#============================#
    elif "add" in str(data[:-1]):
      try:
        _, user_id, host, port = data.split()
        self.handlers['add_client'](user_id, (str(host), int(port)))
        self.commandQueue.put(p2pCommand('ping_request', user_id))
      except:
        self.error("Syntax error in user")

#===================#
#  start listening  #
#===================#
    elif "servermode" in str(data[:-1]):
      try:
        _, host, port = data.split()
        self.commandQueue.put(p2pCommand('servermode', (host, int(port))))
      except:
        self.error("Syntax error in servermode")

#=====================================#
#  show running background processes  #
#=====================================#
    elif "bp" in str(data[:-1]):
      try:
        print ("background_processes:", self.background_processes)
      except:
        self.error("Syntax error in bp")

    elif "sync" in str(data[:-1]):
      try:
        _, user_id = data.split()
        self.commandQueue.put(p2pCommand('db_sync_request_out', user_id))
      except:
        self.error("Syntax error in ips")


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
          for master in self.ips:
            user_id = self.ips[master][0]
            cmd_dct = {'user_id': user_id}
            self.commandQueue.put(p2pCommand('ips_request', cmd_dct))

      except:
        self.error("Syntax error in ips")

#============================#
#  add user to contact list  #
#============================#
    elif "key" in str(data[:-1]):
      try:
        _, user_id = data.split()
        cmd_dct = {'user_id': user_id}
        self.commandQueue.put(p2pCommand('contact_request_out', cmd_dct))
      except:
        self.error("Syntax error in key")

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

        import ez_message as em
        mx = em.Message(self.name, user_id, msg)
        self.MsgDatabase.add_entry(mx)

        if user_id not in self.ips:
          return

        data = pickle.dumps(mx)
        cmd_data = {'user_specs': user_id, 'data': data}
        self.enqueue('send', cmd_data)

      except Exception as e:
        self.error("Syntax error in command: " + str(e))
