# encoding=utf-8 ==============================================================#
#                                  ez_database                                 #
#==============================================================================#

#============#
#  Includes  #
#============#
import dataset

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

  def in_DB (self, **kwargs):
    """
    Returns boolean given keyword argument component=value. Example:
      table.in_DB(UID='123')
    """
    return self.table.find_one(**kwargs) != None

  def get_entry(self, **kwargs):
    """
    Returns entry given keyword argument component=value. Example:
      table.get_entry(UID='123')
    """
    # TODO: (bcn 2014-08-01) What happens if he doesn't find it? I want to
    # return None
    return self.constructor(_dict=self.table.find_one(**kwargs))

  def get_entries(self, UIDs):
    """ Return list of entries given the UIDs """
    # This could be optimized
    return [self.get_entry(UID=UID) for UID in UIDs]

  def add_entry(self, entry, out=False):
    """
    Add an entry without creating duplicates in self.table. Objects that change
    like users should use the update_entry function.
    """
    if self.in_DB(UID=entry.UID):
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
    """ Return a list of the UIDs of all entries as strings """
    return [str(self.constructor(_dict=d).UID) for d in self.table]

  def necessary_entries (self, lst):
    """
    Given a list of UIDs, return a list of UIDs that are not in this database
    """
    return [entry for entry in lst if not self.in_DB(UID=entry)]

