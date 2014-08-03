#==============================================================================#
#                                  ez_packet                                   #
#==============================================================================#

#============#
#  Includes  #
#============#

from Crypto.Hash import SHA256
import cPickle as pickle

#==============================================================================#
#                                 class Packet                                 #
#==============================================================================#

class Packet(object):
  """
  The Packet type is used to make UDP sends reliable. See Packets for
  functionality.
  """
  def __init__(self, data = "", packet_number = 1,
                     max_packets = 1, packets_hash = ""):
    self.data          = data
    self.packet_number = packet_number
    self.max_packets   = max_packets
    self.packet_hash   = SHA256.new(self.data).digest()
    self.packets_hash  = packets_hash

  def verify_hash(self):
    return self.packet_hash == SHA256.new(self.data).digest()


#==============================================================================#
#                                class Packets                                 #
#==============================================================================#

class Packets(object):
  """
  A collection of Packet instances. To make a UDP transmission reliable create a
  Packets instance of the data to-be send. The data is chunked and for each
  Packet a hash is computed allowing the recipient to check whether the sent
  package is corrupted.

  - data = arbitrary data or even python objects.
  """
  def __init__(self, data = None, chunksize = 1):

    if data == None:
      return

    self.data = pickle.dumps(data)
    self.packets_hash = SHA256.new(self.data).digest()
    if len(self.data) > chunksize:
      self.data = [u for u in self.chunks(chunksize)]
    else:
      self.data = [self.data]

    self.packets = {}
    self.max_packets = len(self.data)

    for i, data in enumerate(self.data):
      packet_args = { "data"         : data,
                      "packet_number": i,
                      "max_packets"  : self.max_packets,
                      "packets_hash" : self.packets_hash }

      self.packets[i] = Packet(**packet_args)

  def reconstruct_data(self):
    if len(self.packets) == self.max_packets:
      data = ''
      for i in self.packets:
        if self.packets[i].verify_hash():
          t = pickle.dumps(self.packets[i])
          data += pickle.loads(t).data

        else:
          return None
      if SHA256.new(data).digest() == self.packets[i].packets_hash:
        return True, pickle.loads(data)
      else:
        return False, "checksum error"
    else:
      missing = [ u for u in range(self.max_packets)                           \
                  if not u in self.packets.keys() ]
      return False, missing


  def chunks(self, step_size):
    for i in xrange(0, len(self.data), step_size):
      yield self.data[i:i + step_size]



#msg = "blabla123"
#mypacket = Packets(msg, 3)
#del mypacket.packets[1]
#print mypacket.reconstruct_data()
