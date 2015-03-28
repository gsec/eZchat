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

  def ips_request(self, master):
    """
    Request connection with other clients.

    :param master:  User host and port tuple (host, port)
    :type  master: (string, int)
    """

    try:
      assert(master in self.ips)
    except:
      self.error('Master ' + str(master) + ' not in known ips')

    ping = {'distributeIPs': {}}
    msg = pickle.dumps(ping)
    try:
      self.sockfd.sendto(msg, master)

    except IOError as e:
      self.error(str(e))
      self.error("ips_request unsuccessful")

  def distributeIPs(self, host, port):
    """
    Starts the connection process between the user specified by host,
    port and all other users simultaneously.

    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    master = (host, port)
    other_users = {self.ips[u_id]: u_id for u_id in self.ips
                   if u_id != master}

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
