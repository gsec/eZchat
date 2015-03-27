#==============================================================================#
#                                ez_contact.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

import sys
from ez_process_base import ez_process_base, p2pReply
from ez_gpg import ez_gpg
import cPickle as pickle

#==============================================================================#
#                                  ez_contact                                  #
#==============================================================================#

class ez_contact(ez_process_base):

  # online users are stored in the ips dict
  # ips = {user_id: (user_host, user_port)}
  ips = {}

  def __init__(self, *args, **kwargs):
    super(ez_contact, self).__init__(*args, **kwargs)

  def add_client(self, **kwargs):
    """
    Adds a new client to the clients ip base.
    """
    try:
      user_id = kwargs['user_id']
      fingerprint = kwargs['fingerprint']
      self.ips[(user_id, fingerprint)] = (kwargs['host'], int(kwargs['port']))
    except:
      print "user_id/host/port not properly specified in add_client"
    self.success('Client ' + user_id + 'added.')

  def remove_client(self, user_id):
    if user_id in self.ips:
      del self.ips[user_id]
      self.success('removed user: ' + user_id)
    else:
      self.error('"user not found/removed": ' + user_id)

  def contact_request_out(self, user_id):
    """
    Method for exchanging public keys.

    :param user_id: User nickname
    :type  user_id: string
    """

    cmd_dct = {'user': self.myself}
    contact_request = {'contact_request_in': cmd_dct}
    msg = pickle.dumps(contact_request)
    send_cmd = {'user_specs': user_id, 'data': msg}
    self.enqueue('send', send_cmd)

  def contact_request_in(self, user, host, port):
    """
    User asks for contact data.

    :param user: User instance
    :type user: User

    :param host: Ip of a Server/Client
    :type  host: string

    :param port: Port of a Server/Client
    :type  port: int
    """

    self.success("received contact request")
    assert(self.myself is not None)

    self.success("sent contact data: " + str(self.myself.UID))
    cmd_dct = {'user': self.myself}
    myself = {'add_contact': cmd_dct}
    msg = pickle.dumps(myself)
    send_cmd = {'user_specs': (host, port), 'data': msg}
    self.enqueue('send', send_cmd)

  def add_contact(self, user):
    """
    User admitted to the User database.

    :param user: User instance
    :type user: User
    """
    if not self.UserDatabase.in_DB(UID=user.UID):
      self.UserDatabase.add_entry(user)
      self.success("new contact registered: " + user.UID)
      ez_gpg.import_key(user.public_key)
    else:
      self.success("User already in database. Contact updated.")
      ez_gpg.import_key(user.public_key)
      self.UserDatabase.update_entry(user)

