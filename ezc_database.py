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
  """ The Database class gives access to the sql database """

  def __init__(self, localdb = 'sqlite:///ez.db'):
    """
    Opens a local sqlite database `ez.db` which is saved to and loaded from disk
    automatically
    """
    self.localdb = localdb
    self.db = dataset.connect(self.localdb)
    self.messages = self.db['messages']
    self.users = self.db['users']

  def __str__(self):
    lst = ['\nI am connected to', self.localdb,
           'and have the following data:\n---Messages---\n', self.msg_list(),
           '\n---Users---\nTBD']
    return ' '.join(lst)

  def add_msg(self, msg, out = False):
    """ Add a message without creating duplicates in self.messages """
    if (self.messages.find_one(msg_id = msg.msg_id) == None):
      self.messages.insert(msg.__dict__)
      if out:
        return 'Added entry'
    else:
      if out:
        return 'Already in ez_db'

  def msg_list(self):
    """ Return a string of messages to be shown by the UI"""
    lst = [str(em.Message('', '', '', _dict=d)) for d in self.messages]
    return ('\n' + '='*80 + '\n').join(lst)

#==============================================================================#
#                               Global Instance                                #
#==============================================================================#
database = Database()
