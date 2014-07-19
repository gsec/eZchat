import dataset
import ez_message as em

class Database(object):
  def __init__(self, localdb = 'sqlite:///ips.db'):
    """
    Opens a local sqlite database `ez.db` which is saved to and loaded from disk
    automatically
    """
    self.localdb = localdb
    self.db = dataset.connect(self.localdb)
    self.db = self.db['ips']


  def add_msg(self, msg, out = False):
    self.db.insert(msg)

  #def add_ports(self):
    #port = 2468
    #msg = { "port": port}
    #self.add_msg(msg)
    #port = 2469
    #msg = { "port": port}
    #self.add_msg(msg)

  def add_port(self, port):
    msg = { "port": port}
    self.add_msg(msg)
  def remove_port(self, port):
    self.db.delete(port=port)


#==============================================================================#
#                               Global Instance                                #
#==============================================================================#
ips_open = Database("sqlite:///open.db")
ips_taken = Database("sqlite:///taken.db")
#ports = ips_open.db.all()
#ports = ips_taken.db.all()
#ips_taken.remove_port(2469)
#ips_taken.remove_port(2468)
#ips_open.add_port(2470)
#ips_open.add_port(2469)
#for entry in ports:
  #print entry['port']
