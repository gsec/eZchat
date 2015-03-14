#==============================================================================#
#                           ez_background_process.py                           #
#==============================================================================#

#============#
#  Includes  #
#============#

from ez_process_base import ez_process_base, p2pCommand
import Queue
import thread
import threading


#==============================================================================#
#                                 class Timer                                  #
#==============================================================================#
class Timer(threading._Timer):
  """
  Timer instances are used in the client class to start timed non-blocking
  background processes. The class is not intended to be used directly by the
  user, and measures have been taken to facilitate the use of timed operations.
  See background_processes on how to use timed operations.

  So far Timer is used for:
  - Aborting a ping request after a certain time
  - Aborting a connection request after a certain time
  - Continuously trying to connect on server

  """
  def __init__(self, *args, **kwargs):
    threading._Timer.__init__(self, *args, **kwargs)
    self.setDaemon(True)

  def run(self):
    while not self.finished.isSet():
      self.finished.wait(self.interval)
      # the time has expired and the callback function is called
      if not self.finished.isSet():
        # background processes provides methods to store args and kwargs
        if hasattr(self, 'callback_args') and hasattr(self, 'callback_kwargs'):
          self.function(self, *self.callback_args, **self.kwargs)
        elif hasattr(self, 'callback_args'):
          self.function(self, *self.callback_args)
        elif hasattr(self, 'callback_kwargs'):
          self.function(self, **self.kwargs)
        else:
          self.function(self)
        self.finished.set()

#==============================================================================#
#                         class ez_background_process                          #
#==============================================================================#

class ez_background_process(ez_process_base):
  """
  A background process is defined by bg_cmd, the background process command
  dict:

  -bg_cmd = dict()

  The whole background process information is stored in a bg_cmd. A background
  process is invoked via the commandQueue via

  - my_background_process = p2pCommand('start_background_process', bg_cmd)
  - commandQueue.put(my_background_process)

  bg_cmd must include certain keys:

  1. (mandatory) 'process_id'      : my_process_id
  2. (mandatory) 'callback'        : my_func
  3. (optional)  'interval'        : my_time
  4. (optional)  'callback_args'   : (my_arg1, my_arg2, ...}
  5. (optional)  'callback_kwargs' : (my_kwarg1, my_kwarg2, ...}

  My_process_id can be anything, for instance a number, string or tuple of
  numbers and strings. Callback is the  function which is called after a period
  of time given by interval.  Callback_args and callback_kwargs are (optional)
  arguments which can be passed to callback

  A background process ends after callback has been called. A continous call of
  a user-defined callback can be achieved by defining the callback recursively
  via the reset_background_process method.
  (See ping_background)
  """

  def __init__(self, *args, **kwargs):
    super(ez_background_process, self).__init__(*args, **kwargs)

  def start_background_process(self, process_id, callback, **kwargs):
    # construct background cmd allowing to reset the process
    bg_cmd = {}
    bg_cmd['process_id'] = process_id
    bg_cmd['callback'] = callback

    # Default value of the time period is 5 seconds
    if 'interval' in kwargs:
      interval = kwargs['interval']
    else:
      interval = 5
    bg_cmd['interval'] = interval

    # generate Timer instance
    pr = Timer(interval, callback)
    # and add possibly callback args and kwargs
    if 'callback_args' in kwargs:
      pr.callback_args = kwargs['callback_args']
      bg_cmd['callback_args'] = kwargs['callback_args']
    if 'callback_kwargs' in kwargs:
      pr.callback_kwargs = kwargs['callback_kwargs']
      bg_cmd['callback_kwargs'] = kwargs['callback_kwargs']

    # construct background process
    bgp = p2pCommand('start_background_process', bg_cmd)
    self.background_process_cmds[process_id] = bgp

    # register the process
    self.background_processes[process_id] = pr
    # start the background process
    thread.start_new_thread(pr.run, ())

  def stop_background_process(self, process_id):
    try:
      pr = self.background_processes[process_id]
    except:
      raise Exception('No process with id: ' + str(process_id) + ' running.')
    pr.finished.set()
    pr.cancel()
    del self.background_processes[process_id]
    del self.background_process_cmds[process_id]

  def stop_background_processes(self):
    for process_id in self.background_processes:
      self.stop_background_process(process_id)

  def reset_background_process(self, process_id, new_process_cmd=None):
    """
    A process can be started over again if it is found in the background
    processes.
    Optionally the former process cmd can be replaced with a new one.
    """
    if process_id in self.background_processes:
      pr = self.background_processes[process_id]
      pr.finished.set()
      pr.cancel()
      del self.background_processes[process_id]
      if new_process_cmd is not None:
        self.background_process_cmds['process_id'] = new_process_cmd
        self.commandQueue.put(new_process_cmd)
      else:
        bg_cmd = self.background_process_cmds[process_id]
        self.commandQueue.put(bg_cmd)
