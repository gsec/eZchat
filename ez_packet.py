#==============================================================================#
#                                  ez_packet                                   #
#==============================================================================#

#============#
#  Includes  #
#============#

import sys
from Crypto.Hash import MD5
import cPickle as pickle
from ez_process.ez_process_base import ez_process_base
from types import ListType
from ez_message import Message

import os
import tempfile
from contextlib import contextmanager

# creates a temporary file object used in doctest
@contextmanager
def tempinput(data):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data)
    temp.close()
    yield temp.name
    os.unlink(temp.name)

#==============================================================================#
#                                 class Packet                                 #
#==============================================================================#

class Packet(object):
  """
  The Packet type is used to make UDP sends reliable. See Packets for
  functionality.
  """
  def __init__(self, data="", packet_number=1, max_packets=1,
               packets_hash="", **kwargs):
    self.data = data
    self.packet_number = packet_number
    self.max_packets = max_packets
    self.packet_hash = MD5.new(self.data).digest()
    self.packets_hash = packets_hash
    for kwarg in kwargs:
      setattr(self, kwarg, kwargs[kwarg])

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

  :param data: python objects or filepath
  :type  data: anything which can be pickled or filepath

  :return: (Bool, data or filepath)


  test for python object

  >>> random_data = {'hi': ['there', ('how', 'are'), 'you', 2]}
  >>> packed_data = Packets(data=random_data)
  >>> status, data = packed_data.reconstruct_data()
  >>> status
  True
  >>> data
  {'hi': ['there', ('how', 'are'), 'you', 2]}

  test for file object

  >>> with tempinput('randomtext.') as tempfilename:
  ...   packet_data = Packets(filepath=tempfilename)
  >>> fout = tempfile.NamedTemporaryFile()
  >>> status, filepath = packet_data.reconstruct_data(filepath=fout.name)
  >>> status
  True
  >>> open(filepath, 'r').read()
  'randomtext.'
  """

  def __init__(self, data=None, filepath=None, pickle_data=True,
               chunksize=ez_process_base.socket_buffsize/2):
    try:
      both_none = (data is None) and (filepath is None)
      one = (data is None) ^ (filepath is None)
      assert(one or both_none)
    except:
      raise ValueError('Data (exclusive) or filepath must be set.')

    if filepath:
      from cPickle import load
      try:
        data = open(filepath, 'rb')
        self.filename = data.name

        # file is read as a whole into memory and the hash is computed
        # -> this may take long for large files
        self.data = data.read()
      except Exception, e:
        raise Exception('Could not load data: ' + str(e))

      self.packets_hash = Packet.compute_hash(self.data)

      if len(self.data) > chunksize:
        self.data = [u for u in self.chunks(chunksize)]
      else:
        self.data = [self.data]

    else:
      if pickle_data:
        self.data = pickle.dumps(data)
      else:
        self.data = data

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
      if hasattr(self, 'filename'):
        packet_args.update({'filename': self.filename})

      self.packets[i] = Packet(**packet_args)

  def reconstruct_data(self, filepath=None):
    """
    Reconstructs the data from the Packets instance and performs checksum
    checks.

    :param return: returns a tuple where the first entry is True if the
                   reconstruction succeeded else False. The second entry is
                   either the recontructed data or the error message or the
                   packet in packets whiich is corrupted.
    :type  return: (bool, Str)
    >>> random_data = 'r4nb0m'
    >>> packed_data = Packets(data=random_data, chunksize=10)
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
    [0]

    Or packets may be missing

    >>> del packed_data.packets[1]
    >>> status, data = packed_data.reconstruct_data()
    >>> status
    False
    >>> data
    [1]
    """

    # data is not unpicked if stored to the hard disk
    if filepath is not None:
      unpickle = False
    else:
      unpickle = True

    if len(self.packets) == self.max_packets:
      data = ''
      bad_packets = None
      for i in self.packets:
        if self.packets[i].verify_hash():
          if bad_packets is None:
            data += self.packets[i].data

        else:
          if bad_packets is None:
            bad_packets = []
          bad_packets.append(i)
      if bad_packets is not None:
        return False, bad_packets
      else:
        if Packet.compute_hash(data) == self.packets[0].packets_hash:
          if unpickle:
            return True, pickle.loads(data)
          else:
            try:
              fout = open(filepath, 'w')
              fout.write(data)
            except:
              return False, 'Error when writing to filepath'

            return True, filepath
        else:
          return False, "checksum error"
    else:
      missing = [u for u in range(self.max_packets)
                 if u not in self.packets.keys()]
      return False, missing

  def chunks(self, step_size):
    for i in xrange(0, len(self.data), step_size):
      yield self.data[i:i + step_size]

#==============================================================================#
#                                  ez_packet                                   #
#==============================================================================#

class ez_packet(ez_process_base):
  """
  Provides client methods for handling packets.
  """
  def __init__(self, *args, **kwargs):
    super(ez_packet, self).__init__(*args, **kwargs)
    # packets are stored until complete
    self.stored_packets = {}
    # sent packets are stored allowing for being requested again.
    self.sent_packets = {}

  def send_packet(self, user_specs, data):
    try:
      packets = Packets(data=data, pickle_data=False)
      self.sent_packets[packets.packets_hash] = packets
      self.success('To: ' + str(user_specs))
      for packet_id in packets.packets:
        data = pickle.dumps(packets.packets[packet_id])
        if len(data) > self.socket_buffsize:
          self.error("data larger than buggersize")
        else:
          cmd_dct = {'user_specs': user_specs, 'data': data}
        self.enqueue('send', cmd_dct)
    except Exception as e:
      self.error("Syntax error in send_packet: " + str(e))

  def resend_packet(self, packet_info, user_id):
    packets_hash, packet_id = packet_info
    if packets_hash in self.sent_packets:
      if packet_id in self.sent_packets[packets_hash].packets:
        data = self.sent_packets[packets_hash].packets[packet_id].data
        data = pickle.dumps(self.sent_packets[packets_hash].packets[packet_id])
        if len(data) > self.socket_buffsize:
          self.error("data larger than buggersize")
        else:
          cmd_dct = {'user_specs': user_id, 'data': data}
          self.enqueue('send', cmd_dct)
      else:
        self.error("packet_id not in sent_packets")
    else:
      self.error("packet not in sent_packets")

  def packet_request(self, packet_info, user_addr):
    cmd_dct = {'packet_info': packet_info, 'user_id': self.name}
    packet_cmd = {'resend_packet': cmd_dct}
    msg = pickle.dumps(packet_cmd)
    try:
      self.sockfd.sendto(msg, user_addr)
    except IOError as e:
      self.error(str(e))

  def handle_packet(self, data, user_addr, handler):
    """
    Handles incoming packets. A `packet session` is started and received
    packages are stored in *stored_packets*. A background process is started
    tracking the status of the session. If packages are missing or corrupted,
    the method :py:meth:`ez_packet.ez_packet.packet_request`is invoked
    automatically. When the packet is reconstructed completely the associated
    *stored_packets* entry is deleted.


    :param data: Packed data
    :type  data: Packet

    :param user_addr: The user address tuple (host, port) from whom the packet
                      is received.
    :type  user_addr: (string, int)

    :param handler: A handler how to proceed when the packet is reconstructed.
    :type  handler: function
    """
    packets_hash = data.packets_hash
    # packages are dropped if not associated to a known user_id
    if user_addr in self.ips:
      key = (user_addr, packets_hash)
      if key not in self.stored_packets:
        self.stored_packets[key] = Packets()
        self.stored_packets[key].max_packets = data.max_packets
        self.stored_packets[key].packets = {}

      packets = self.stored_packets[key]
      packets.packets_hash = packets_hash

      if data.max_packets == 1 and data.packet_number == 0:
        handler(pickle.loads(data.data), user_addr)
        return

      packets.packets[data.packet_number] = data
      self.stored_packets[key] = packets

      self.success("Received package")

      #pr_key = ('receive', user_id)
      pr_key = key

      def update_and_reconstruct(*args):
        packets = self.stored_packets[key]
        self.success('called reconstruct')
        reconstructed, result = packets.reconstruct_data()
        if reconstructed:
          handler(result, user_addr)
          if pr_key in self.background_processes:
            pr = self.background_processes[pr_key]
            pr.finished.set()
            pr.cancel()
            del self.background_processes[pr_key]
        else:
          self.error('Packet reconstruction failed')
          for packet_number in result:
            cmd_dct = {'packet_info': (packets.packets_hash, packet_number),
                       'user_addr': user_addr}
            self.enqueue('packet_request', cmd_dct)

          self.reset_background_process(pr_key)

      if packets.max_packets == len(packets.packets):
        update_and_reconstruct()

      else:
        cmd_dct = {'process_id': pr_key,
                   'callback': update_and_reconstruct,
                   'interval': 5}
        if pr_key not in self.background_processes:
          self.enqueue('start_background_process', cmd_dct)


if __name__ == "__main__":
  import doctest
  doctest.testmod()
