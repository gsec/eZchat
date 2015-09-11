#==============================================================================#
#                              ez_process_base.py                              #
#==============================================================================#

#============#
#  Includes  #
#============#

import os
import vim
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
#                               AmbiguousMaster                                #
#==============================================================================#

class AmbiguousMaster(Exception):
  def __init__(self, masters):
    self.masters = masters

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

  socket_buffsize = 2024

  # online users are stored in the ips dict
  # ips = {(user_host, user_port): (user_id, fingerpring)}
  ips = {}

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
    if 'write_to_pipe' in kwargs or 'event_callback' in kwargs:
      class RQueue(Queue.Queue):
        def __init__(self, write_to_pipe=False, event_callback=None,
                     *args, **kwargs):
          Queue.Queue.__init__(self, *args, **kwargs)
          self.write_to_pipe = write_to_pipe
          self.event_callback = event_callback

        def put(self, cmd):
          Queue.Queue.put(self, cmd)
          if self.write_to_pipe:
            os.write(self.write_to_pipe, 'status')
          if self.event_callback:
            self.event_callback()
            from time import sleep
            sleep(0.1)

      if 'write_to_pipe' in kwargs and 'event_callback' in kwargs:
        self.replyQueue = RQueue(write_to_pipe=kwargs['write_to_pipe'],
                                 event_callback=kwargs['event_callback'])
      elif 'write_to_pipe' in kwargs:
        self.replyQueue = RQueue(write_to_pipe=kwargs['write_to_pipe'])

      else:
        self.replyQueue = RQueue(event_callback=kwargs['event_callback'])

    else:
      self.replyQueue = Queue.Queue()

    # user defined parameters are passed to the process preferences potentiall
    # overwriting default values.
    epp.init_process_preferences(**kwargs)

  # client related
  def success(self, success_msg=None):
    cmd = p2pReply(p2pReply.success, success_msg)
    self.replyQueue.put(cmd)

  # client related
  def error(self, error_msg=None):
    cmd = p2pReply(p2pReply.error, error_msg)
    self.replyQueue.put(cmd)

  # MsgDb update
  def msg(self, msg=None):
    self.replyQueue.put(p2pReply(p2pReply.msg, msg))

  def enqueue(self, funcStr, data=None):
    self.commandQueue.put(p2pCommand(funcStr, data))

  def get_master(self, **kwargs):
    """
    Returns the master (host, port tuple) given one of the following keywords
    `user_id`, `fingerprint`, `master`.
    """
    try:
      cases = ['user_id', 'fingerprint', 'master']
      case = [u for u in cases if u in kwargs]
      if len(case) != 1:
        raise TypeError('One and only one of the kwargs:' + ','.join(cases) +
                        'must be given')
      case = case[0]
    except:
      raise

    case_val = kwargs[case]
    key = {'user_id': (u for u in self.ips if self.ips[u][0] == case_val),
           'fingerprint': (u for u in self.ips if self.ips[u][1] == case_val),
           'master': (u for u in self.ips if u == case_val)}
    key_val = [u for u in key[case]]
    if len(key_val) == 0:
      raise Exception('User not found/removed: ' + str(case_val))
    elif len(key_val) > 1:
      raise AmbiguousMaster(key_val)
    else:
      master = key_val[0]
      return master


def master_required(process_func):
  """
  Decorator for a function only accepting master as input. The decorator allows
  the function call with alternative arguments such as fingerprint, user_id.
  The function determines the master and passes the result to the function.
  Ambiguities in masters are treated pointwise.

  Example:

  We define a function only accepting master
  >>> def func(self, master): return master
  >>> args = {'master': 1234}
  >>> self = ez_process_base(); self.ips = {1234: ('Bob', '4DE5'),\
                                            4321: ('Bob', '4DE6')}

  The  normal functionality is preserved and we can pass master
  >>> master_required(func)(self, **args)
  1234

  The master can be obtained from the fingerprint
  >>> args = {'fingerprint': '4DE5'}
  >>> master_required(func)(self, **args)
  1234

  If the master is ambiguous the function is applied to all possible masters
  >>> args = {'user_id': 'Bob'}
  >>> master_required(func)(self, **args)
  (4321, 1234)
  """
  # the number of arguments the function has
  if process_func.func_defaults is not None:
    n_defaults = len(process_func.func_defaults)
  else:
    n_defaults = 0
  n_args = process_func.func_code.co_argcount - n_defaults
  args = [arg for arg in process_func.func_code.co_varnames[:n_args]
          if arg != 'self']
  if 'master' not in args:
    raise Exception('The function ' + str(process_func.__name__) +
                    ' cannot be decorated with master_required. ' +
                    'The function must have `master` as argument')

  def assign_args(self, *args, **kwargs):
    if 'master' in kwargs:
      return process_func(self, *args, **kwargs)

    cases = ['fingerprint', 'user_id']
    selected = None
    for case in cases:
      if selected is None:
        selected = case if case in kwargs else None
    if case is None:
      raise Exception('If `master` is not given, one of the following ' +
                      ', '.join(cases) + ' must be given for the function ' +
                      str(process_func.__name__))

    try:
      master = self.get_master(**{selected: kwargs[selected]})
      kwargs['master'] = master
      del kwargs[selected]
      return process_func(self, *args, **kwargs)
    except AmbiguousMaster as e:
      masters = e.masters

      del kwargs[selected]
      ret = []
      for master in masters:
        kwargs['master'] = master
        res = process_func(self, *args, **kwargs)
        ret.append(res)
      return tuple(ret)

  return assign_args


#==============================================================================#
#                                 command_args                                 #
#==============================================================================#

def command_args(process_func):
  """
  Decorator which extracts the arguments from the p2pCommand instance cmd
  (:py:class:`ez_process.ez_process_base.p2pCommand`) and passes them to the
  function.

  >>> def func(self, a, b=None): return a, b
  >>> args = {'a': 1}
  >>> cmd = p2pCommand('test', args)
  >>> command_args(func)(None, cmd)
  (1, None)
  >>> args = {'a': 1, 'b': 2}
  >>> cmd = p2pCommand('test', args)
  >>> command_args(func)(None, cmd)
  (1, 2)
  >>> args = {'b': 3}
  >>> cmd = p2pCommand('test', args)
  >>> command_args(func)(None, cmd)
  Traceback (most recent call last):
    ...
  Exception: Missing argument: a in function: func
  """
  def assign_args(self, cmd):
    try:
      assert(isinstance(cmd, p2pCommand))
    except:
      err_msg = 'Queued function needs to be called with a p2pCommand instance'
      raise TypeError(err_msg)

    # arguments passed to process_func
    fargs = {}

    # the number of arguments the function has
    if process_func.func_defaults is not None:
      n_defaults = len(process_func.func_defaults)
    else:
      n_defaults = 0

    n_args = process_func.func_code.co_argcount - n_defaults

    # co_flags bitmap: 1=optimized | 2=newlocals | 4=*arg | 8=**arg
    additional_kwargs = process_func.func_code.co_flags ^ 8

    # self is not considered as argument
    args = (arg for arg in process_func.func_code.co_varnames[:n_args]
            if arg != 'self')

    # we require that the arguments specified for the function are present in
    # cmd
    for arg in args:
      try:
        assert(arg in cmd.data)
        fargs[arg] = cmd.data[arg]
      except:
        err_msg = ('Missing argument: ' + arg + ' in function: ' +
                   process_func.__name__)
        raise Exception(err_msg)

    # add kwargs if the function accepts it
    if additional_kwargs and cmd.data is not None:
      kwargs = {u: cmd.data[u] for u in cmd.data if u not in fargs}
      fargs.update(kwargs)
    return process_func(self, **fargs)
  return assign_args


if __name__ == '__main__':
  import doctest
  doctest.testmod()
