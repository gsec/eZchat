#==============================================================================#
#                                 ez_relay.py                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base
import cPickle as pickle

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

  def ips_request(self, user_id):
    """
    Request connection with other clients.

    :param user_id: User nickname
    :type  user_id: string
    """

    if user_id not in self.ips:
      print "self.ips:", self.ips
    else:
      master = self.ips[user_id]
      cmd_dct = {'user_id': user_id}
      ping = {'distributeIPs': cmd_dct}
      msg = pickle.dumps(ping)
      try:
        self.sockfd.sendto(msg, master)

      except IOError as e:
        self.error(str(e))
        self.error("ips_request unsuccessful")

  def distributeIPs(self, user_id, host, port):
    """
    Starts the connection process between the user specified by user_id, host,
    port and all other users simultaneously.

    :param user_id: User nickname
    :type  user_id: string

    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    master = (host, port)
    other_users = {u_id: self.ips[u_id] for u_id in self.ips
                   if self.ips[u_id] != master}

    for other_id in other_users:
      cmd_dct_A = {'master': other_users[other_id]}
      cmd_dct_B = {'master': master}
      relay_request = {'connect': cmd_dct_A}
      relay_request2 = {'connect': cmd_dct_B}
      msg = pickle.dumps(relay_request)
      msg2 = pickle.dumps(relay_request2)
      try:
        self.sockfd.sendto(msg, master)
        self.sockfd.sendto(msg2, other_users[other_id])
        self.success("distributed IPs")
      except IOError as e:
        self.error(str(e))
