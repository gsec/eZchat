import dataset

class Database(object):

  def __init__(self, localdb = 'sqlite:///ezchat.db'):
    # Opens a local sqlite database `ezchat.db` which is saved to and loaded
    # from disk automatically
    self.localdb = localdb
    self.db = dataset.connect(self.localdb)
    self.messages = self.db['messages']
    self.users = self.db['users']

  def __str__(self):
    return "\nI am connected to " + self.localdb + \
           " and have the following data: \n" + "TBD..."

  def add_msg(self, msg, out = False):
    """ Add a message without creating duplicates in self.messages """
    if (self.messages.find_one(msg_id = msg.msg_id) == None):
      self.messages.insert(msg.__dict__)
      if (out):
        return 'Added entry'
    else:
      if(out):
        return 'Already in ezc_db'
    return ''

# bcn: I guess this global object is necessary
database = Database()
