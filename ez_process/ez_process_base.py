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
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             os.pardir))
import ez_pipe as pipe
import ez_process_preferences as epp

#==============================================================================#
#                               class p2pCommand                               #
#==============================================================================#

class p2pCommand(object):
  """
  A p2pCommand encapsulates ``'commandQueue'`` commands. The p2pCommand instance
  can be appended to the client's command queue for execution via:

    cmd = p2pCommand(...)
    client_class_instance.commandQueue.put(cmd)

  The funcStr is the name of the function which must match a key in the client
  handler functions (see ez_process_base_meta). Data must be a dictionary and
  has to be filled with key,value pairs as required by the handler function.
  """
  def __init__(self, funcStr=None, data=None):
    """
    :param funcStr: Storing the function name which should be called when
                    executed.
    :type  funcStr: String

    :param data: Keyword arguments (*kwargs*) passed to the called
                 function.
    :type  data: Dict
    """
    self.funcStr = funcStr
    self.data = data

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
  msg = 2

  def __init__(self, replyType=None, data=None):
    self.replyType = replyType
    self.data = data

class ez_process_base(object):
  commandQueue = Queue.Queue()

  # storing active and/or sleeping background process
  background_processes = {}
  # storing the cmd with which the background processes were initiated
  background_process_cmds = {}

  # storing user-defined functions for calling after a process has been
  # terminated successfully
  success_callback = {}

  @classmethod
  def get_handler(self):
    handler = {}
    # add class functions
    for attr in (x for x in self.__dict__ if not x.startswith('_')):
      # register process functionalities and inherit them to child classes
      if(isinstance(self.__dict__[attr], types.FunctionType) or
         type(self.__dict__[attr]) is classmethod):
        handler[attr] = self.__dict__[attr]
    return handler

  @classmethod
  def get_bases_handler(self):
    handler = {}
    # add parent class functions
    for parent in (u for u in self.__bases__ if u is not object):
      parent_handler = parent.get_handler()
      handler.update(parent_handler)
    return handler

  def __init__(self, **kwargs):
    if 'write_to_pipe' in kwargs:
      class RQueue(Queue.Queue):
        def __init__(self, write_to_pipe=False, *args, **kwargs):
          Queue.Queue.__init__(self, *args, **kwargs)
          self.write_to_pipe = write_to_pipe

        def put(self, cmd):
          Queue.Queue.put(self, cmd)
          if self.write_to_pipe:
            os.write(pipe.pipe, 'status')

      self.replyQueue = RQueue(write_to_pipe=kwargs['write_to_pipe'])
    else:
      self.replyQueue = Queue.Queue()

    # user defined parameters are passed to the process preferences potentiall
    # overwriting default values.
    epp.init_process_preferences(**kwargs)

  # client related
  def success(self, success_msg=None):
    return p2pReply(p2pReply.success, success_msg)

  # client related
  def error(self, error_msg=None):
    return p2pReply(p2pReply.error, error_msg)

  # MsgDb update
  def msg(self, msg=None):
    return p2pReply(p2pReply.msg, msg)
