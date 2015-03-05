#==============================================================================#
#                                  ez_packet                                   #
#==============================================================================#

#============#
#  Includes  #
#============#

from Crypto.Hash import MD5
import cPickle as pickle

#==============================================================================#
#                                 class Packet                                 #
#==============================================================================#

class Packet(object):
  """
  The Packet type is used to make UDP sends reliable. See Packets for
  functionality.
  """
  def __init__(self, data="", packet_number=1, max_packets=1, packets_hash=""):
    self.data = data
    self.packet_number = packet_number
    self.max_packets = max_packets
    self.packet_hash = MD5.new(self.data).digest()
    self.packets_hash = packets_hash

  def verify_hash(self):
    return self.packet_hash == self.compute_hash(self.data)

  @classmethod
  def compute_hash(self, data):
    return MD5.new(data).digest()


#==============================================================================#
#                                class Packets                                 #
#==============================================================================#

class Packets(object):
  """
  A collection of Packet instances. To make a UDP transmission reliable create a
  Packets instance of the data to-be send. The data is chunked and for each
  Packet a hash is computed allowing the recipient to check whether the sent
  package is corrupted.

  :param data: data to be packed into chunks
  :type  data: anything which can be pickled



  >>> random_data = {'hi': ['there', ('how', 'are'), 'you', 2]}
  >>> packed_data = Packets(data=random_data)
  >>> status, data = packed_data.reconstruct_data()
  >>> status
  True
  >>> data
  {'hi': ['there', ('how', 'are'), 'you', 2]}
  """
  def __init__(self, data=None, chunksize=100):

    if data is None:
      return

    self.data = pickle.dumps(data)
    self.packets_hash = Packet.compute_hash(self.data)
    if len(self.data) > chunksize:
      self.data = [u for u in self.chunks(chunksize)]
    else:
      self.data = [self.data]

    self.packets = {}
    self.max_packets = len(self.data)

    for i, data in enumerate(self.data):
      packet_args = {"data": data,
                     "packet_number": i,
                     "max_packets": self.max_packets,
                     "packets_hash": self.packets_hash}

      self.packets[i] = Packet(**packet_args)

  def reconstruct_data(self):
    """
    Reconstructs the data from the Packets instance and performs checksum
    checks.

    :param return: returns a tuple where the first entry is True if the
                   reconstruction succeeded else False. The second entry is
                   either the recontructed data or the error message or the
                   packet in packets whiich is corrupted.
    :type  return: (bool, Str)
    >>> random_data = 'r4nb0m'
    >>> packed_data = Packets(data=random_data)
    >>> status, data = packed_data.reconstruct_data()
    >>> status
    True

    Reconstruction fails if the reconstructed data has not the correct hash
    which should never be the case if the indiviual packet hashs are correct

    >>> packed_data.packets[0].packets_hash = Packet.compute_hash('r3ndOM')
    >>> status, data = packed_data.reconstruct_data()
    >>> status
    False
    >>> data
    'checksum error'

    Indiviual packets can be broken

    >>> packed_data.packets[0].packet_hash = Packet.compute_hash('r3ndOM')
    >>> status, data = packed_data.reconstruct_data()
    >>> status
    False
    >>> data
    0
    """

    if len(self.packets) == self.max_packets:
      data = ''
      for i in self.packets:
        if self.packets[i].verify_hash():
          t = pickle.dumps(self.packets[i])
          data += pickle.loads(t).data

        else:
          return False, i
      if Packet.compute_hash(data) == self.packets[0].packets_hash:
        return True, pickle.loads(data)
      else:
        return False, "checksum error"
    else:
      missing = [u for u in range(self.max_packets)
                 if u not in self.packets.keys()]
      return False, missing

  @classmethod
  def chunks(self, step_size):
    for i in xrange(0, len(self.data), step_size):
      yield self.data[i:i + step_size]

if __name__ == "__main__":
  import doctest
  doctest.testmod()
