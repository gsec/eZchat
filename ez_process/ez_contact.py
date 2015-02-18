#==============================================================================#
#                                ez_contact.py                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

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
      self.replyQueue.put(self.error("user_id not in ip list"))
      return

    if user_id in self.ips:
      user_addr = self.ips[user_id]
      cmd_dct = {'user': self.myself}
      contact_request = {'contact_request_in': cmd_dct}
      msg = pickle.dumps(contact_request)
      try:
        self.sockfd.sendto(msg, user_addr)
        self.replyQueue.put(self.success("sent contact request: " +
                                         str(self.myself.UID)))
      except IOError as e:
        self.replyQueue.put(self.error(str(e)))


  def contact_request_in(self, cmd):
    """
    User asks for contact data.

    - cmd.data['user'] = user (User class instance)
    - host, port automatically filled by the receive method (see ez_p2p.py)
    """
    try:
      user = cmd.data['user']
      host = cmd.data['host']
      port = cmd.data['port']
    except:
      print "user/host/port not properly specified in contact_request_in"

    self.replyQueue.put(self.success("received contact request"))
    assert(self.myself is not None)

    self.replyQueue.put(self.success("sent contact data: " +
                                     str(self.myself.UID)))
    cmd_dct = {'user': self.myself}
    myself = {'add_contact': cmd_dct}
    msg = pickle.dumps(myself)
    try:
      self.sockfd.sendto(msg, (host, port))
    except IOError as e:
      self.replyQueue.put(self.error(str(e)))

  def add_contact(self, cmd):
    try:
      new_user = cmd.data['user']
    except:
      self.replyQueue.put(self.error("User not properly specified " +
                                     "in add_contact"))
    if not self.UserDatabase.in_DB(UID=new_user.UID):
      self.UserDatabase.add_entry(new_user)
      self.replyQueue.put(self.success("new contact registered: " +
                                       new_user.UID))
      ez_gpg.import_key(new_user.public_key)
    else:
      self.replyQueue.put(self.success("User already in database. " +
                                       "Contact updated."))
      ez_gpg.import_key(new_user.public_key)
      self.UserDatabase.update_entry(new_user)

