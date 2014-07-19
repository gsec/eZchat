#==============================================================================#
#                                  ez_database                                 #
#==============================================================================#

#============#
#  Includes  #
#============#
import dataset
import ez_message as em

#==============================================================================#
#                                class Database                                #
#==============================================================================#

class Database(object):
  """
  The Database class gives access to the sql database with user info and
  saved, encrypted messages
  """

  def __init__(self, localdb = 'sqlite:///ez.db'):
    """
    Opens a local sqlite database
        localdb = 'sqlite:///ez.db'
    which is saved to and loaded from disk automatically. To create a merely
    temporary database in memory use 'sqlite:///:memory:'
    """
    self.localdb = localdb
    self.db = dataset.connect(self.localdb)
    self.messages = self.db['messages']
    self.users = self.db['users']

  def __str__(self):
    lst = ['\n', '='*80, '\nThis is the database located in', self.localdb,
           'with the following data:\n---Messages---\n', self.msg_string(),
           '\n---Users---\nTBD']
    return ' '.join(lst)

  def msg_string (self):
    """ Return a string of all messages """
    results = self.messages.find(order_by=['time', '-msg_id'])
    lst = [str(em.Message('', '', '', _dict=d)) for d in results]
    return ('\n' + '-'*80 + '\n').join(lst)

  def in_DB (self, msg):
    """ Boolean if message or ID `msg` is in database """
    try:
      return self.messages.find_one(msg_id=msg.msg_id) != None
    except AttributeError:
      return self.messages.find_one(msg_id=msg) != None
    except :
      return 'Invalid msg, neither Message nor ID'

  def add_msg(self, msg, out = False):
    """ Add a message without creating duplicates in self.messages """
    if self.in_DB(msg):
      if out:
        return 'Already in ez_db'
    else:
      self.messages.insert(msg.__dict__)
      if out:
        return 'Added entry'

  def add_msgs(self, msgs, out = False):
    """ Add messages without creating duplicates in self.messages """
    for msg in msgs:
      self.add_msg(msg)

  def get_msg(self, msg_id):
    """ Return a message given the message ID """
    return em.Message('', '', '', _dict=self.messages.find_one(msg_id=msg_id))

  def get_msgs(self, msg_ids):
    """ Return messages given the message IDs """
    return [self.get_msg(msg_id) for msg_id in msg_ids]

  def msg_id_list (self):
    """ Return a list of all message IDs as strings """
    return [str(em.Message('', '', '', _dict=d).msg_id) for d in self.messages]

  def necessary_msgs (self, lst):
    """
    Given a list of IDs, return a list of IDs that are not in this database
    """
    return [msg for msg in lst if not self.in_DB(msg)]

#==============================================================================#
#                               Global Instance                                #
#==============================================================================#
database = Database()
