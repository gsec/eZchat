#==============================================================================#
#                                 ez_relay.py                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base
import cPickle   as pickle

#==============================================================================#
#                                class ez_relay                                #
#==============================================================================#

class ez_relay(ez_process_base):
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
