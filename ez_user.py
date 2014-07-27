#==============================================================================#
#                                   ez_user                                    #
#==============================================================================#

#============#
#  Includes  #
#============#
from Crypto.Hash import SHA # Shorter IDs than with 256
import ez_crypto as ec

#==============================================================================#
#                                  class User                                  #
#==============================================================================#

components = ['nickname', 'public_key', 'IP', 'last_IPs', 'UID']

class User(object):
  """
  - ask for username, pw
      - create db entry
      - create private/public key pair
      - store public key public
  - db-entry for groups, network
  - db-entry for with all msg-ids as recipient
  """

  def __init__(self, nickname='', current_ip='', public_key=None, _dict=None):
    """
    This method will create a new user of the network.
    IP is a string of the form 123.123.123.123:12345.
    """
    if _dict:
      for x in components:
        setattr(self, x, _dict[x])
    else:
      self.nickname = nickname
      if public_key:
        self.public_key = public_key
      else:
        er = ec.eZ_RSA()
        self.public_key = er.generate_keys_(self.nickname)
      self.IP = current_ip
      # The database doesn't like lists. We can join them with some char though
      self.last_IPs = ' '
      self.UID = SHA.new(self.nickname + self.public_key).hexdigest()

  def current_ip_and_port(self):
    lst = self.IP.split(':')
    return (lst[0], lst[1])
