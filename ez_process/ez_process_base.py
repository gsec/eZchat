#==============================================================================#
#                              ez_process_base.py                              #
#==============================================================================#

#============#
#  Includes  #
#============#

import os
import types
import Queue

# adding the eZchat path to search directory
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             os.pardir))
import ez_pipe as pipe

#==============================================================================#
#                               class p2pCommand                               #
#==============================================================================#

class p2pCommand(object):
  """
  A p2pCommand encapsulates commands which are then appended to the command
  queue for execution. The msgType is the string of the function which must
  match a key in the client handler functions (see ez_process_base_meta). Data
  is must be a dictionary and has to be filled with key,value pairs as required
  by the handler function.

  """
  def __init__(self, msgType=None, data=None):
    """
    param:  msgType: the command to be executed
    type :  msgType: string

    param: data: arguments passed to the command
    type : data: dict
    """
    self.msgType = msgType
    self.data    = data

#==============================================================================#
#                                class p2pReply                                #
#==============================================================================#

class p2pReply(object):
  """
  Encapsulate received data.
  A p2pReply instance can be appended to the reply queue.

  replyType = success:  type(data) = str
  replyType = error:    type(data) = str
  """
  error, success = range(2)
  msg            = 2

  def __init__(self, replyType=None, data=None):
    self.replyType = replyType
    self.data      = data

#==============================================================================#
#                         class ez_process_base(_meta)                         #
#==============================================================================#

class ez_process_base_meta(type):
  """
  The metaclass __init__ function is called after the class is created, but
  before any class instance initialization. Any class with set
  __metaclass__ attribute to ez_process_base_meta which is equivalent to
  inheriting the class ez_process_base is extended by:

  - self.handlers: dictionary storing all user-defined functions
  - global attributes as class attributes

  self.handlers is called in the client main loop in p2pclient
  """
  def __init__(cls, name, bases, dct):
    if not hasattr(cls, 'handlers'):
      cls.handlers = {}
    for attr in [x for x in dct if not x.startswith('_')]:
      # register process functionalities and inherit them to child classes
      if isinstance(dct[attr], types.FunctionType):
        assert not attr in cls.handlers
        cls.handlers[attr] = dct[attr]

      # register global attributes and inherit them to child classes
      else:
        cls.attr = dct[attr]

    super(ez_process_base_meta, cls).__init__(name, bases, dct)

class ez_process_base(object):
  __metaclass__ = ez_process_base_meta

  commandQueue = Queue.Queue()

  # storing active and/or sleeping background process
  background_processes    = {}
  # storing the cmd with which the background processes were initiated
  background_process_cmds = {}

  # storing user-defined functions for calling after a process has been
  # terminated successfully
  success_callback        = {}

  def __init__(self, **kwargs):
    if 'write_to_pipe' in kwargs:
      class RQueue(Queue.Queue):
        def __init__(self, write_to_pipe = False, *args, **kwargs):
          Queue.Queue.__init__(self, *args, **kwargs)
          self.write_to_pipe = write_to_pipe

        def put(self, cmd):
          Queue.Queue.put(self, cmd)
          if self.write_to_pipe:
            os.write(pipe.pipe, 'status')

      self.replyQueue = RQueue(write_to_pipe = kwargs['write_to_pipe'])
    else:
      self.replyQueue = Queue.Queue()

  # client related
  def success(self, success_msg=None):
    return p2pReply(p2pReply.success, success_msg)

  # client related
  def error(self, error_msg=None):
    return p2pReply(p2pReply.error, error_msg)

  # MsgDb update
  def msg(self, msg=None):
    return p2pReply(p2pReply.msg, msg)
