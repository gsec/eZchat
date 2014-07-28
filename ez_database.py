#==============================================================================#
#                                  ez_database                                 #
#==============================================================================#

#============#
#  Includes  #
#============#
import dataset
import ez_message as em
import ez_user as eu

#==============================================================================#
#                                class Database                                #
#==============================================================================#
class Database(object):
  """
  The Database class is a template for giving access to the SQL database. Also
  other databases like MySQL could be used.
  """
  def __init__(self, table_name, constructor, localdb = 'sqlite:///ez.db'):
    self.localdb = localdb
    self.db = dataset.connect(self.localdb)
    self.table = self.db[table_name]
    self.constructor = constructor
    self.table_name = table_name

  def __str__(self):
    lst = ['\n', '='*80, '\nThis is the database located in', self.localdb,
           'with the following data:\n---' + self.table_name + '---\n',
           self.entry_string()]
    return ' '.join(lst)

  def entry_string (self):
    """ Return a string of all entries """
    results = self.table.find(order_by=['-UID'])
    lst = [str(self.constructor(_dict=d)) for d in results]
    return ('\n' + '-'*80 + '\n').join(lst)

  def in_DB (self, entry):
    """ Boolean if entry.UID or entry is in database """
    try:
      return self.table.find_one(UID=entry.UID) != None
    except AttributeError:
      return self.table.find_one(UID=entry) != None

  def get_entry(self, UID):
    """ Return an entry given the UID """
    return self.constructor(_dict=self.table.find_one(UID=UID))

  def get_entries(self, UIDs):
    """ Return list of entries given the UIDs """
    # This could be optimized
    return [self.get_entry(UID) for UID in UIDs]

  def add_entry(self, entry, out = False):
    """
    Add an entry without creating duplicates in self.table. Objects that change
    like users should use the update_entry function.
    """
    if self.in_DB(entry):
      if out:
        return 'Already in ez_db'
    else:
      self.table.insert(entry.__dict__)
      if out:
        return 'Added entry'

  def update_entry(self, entry, out = False):
    """
    Update an entry. It is selected in the table according to entry.UID.
    """
    self.table.update(entry.__dict__, ['UID'])

  def add_entries(self, entries, **kwargs):
    """
    Performance function. Does not avoid duplicates like add_entry. Can be
    useful for syncing. You can specify `chunk_size` to optimize performance.
    """
    dicts = [e.__dict__ for e in entries]
    self.table.insert_many(dicts, **kwargs)

  def UID_list (self):
    """ Return a list of all message IDs as strings """
    return [str(self.constructor(_dict=d).UID) for d in self.table]

  def necessary_entries (self, lst):
    """
    Given a list of UIDs, return a list of UIDs that are not in this database
    """
    return [entry for entry in lst if not self.in_DB(entry)]

#==============================================================================#
#                            class MessageDatabase                             #
#==============================================================================#

class MessageDatabase(Database):
  """
  The MessageDatabase class gives access to the saved, encrypted messages in the
  SQL database
  """

  def __init__(self, **kwargs):
    """
    Opens a local sqlite database
        localdb = 'sqlite:///ez.db'
    which is saved to and loaded from disk automatically. To create a merely
    temporary database in memory use 'sqlite:///:memory:'
    """
    Database.__init__(self, 'Messages', em.Message, **kwargs)

#==============================================================================#
#                              class UserDatabase                              #
#==============================================================================#

class UserDatabase(Database):
  """
  The UserDatabase class gives access to the saved information about users in
  the SQL database
  """

  def __init__(self, **kwargs):
    """
    Opens a local sqlite database
        localdb = 'sqlite:///ez.db'
    which is saved to and loaded from disk automatically. To create a merely
    temporary database in memory use 'sqlite:///:memory:'
    """
    Database.__init__(self, 'Users', eu.User, **kwargs)

  def check_for_ip(self, ip, port):
    """
    Given IP and port, check whether the user is in DB is in DB and return UID.
    """
    user = eu.User(_dict=self.table.find_one(IP=':'.join([ip, port])))
    return user.UID

#==============================================================================#
#                               Global Instance                                #
#==============================================================================#
message_database = MessageDatabase()
user_database = UserDatabase()
