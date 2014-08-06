from ez_p2p import p2pCommand, Timer
import sys, errno, time

import Queue, thread, threading
#================#
#  ping methods  #
#================#

# schematic view of the ping process
#------------------------------------------------------------------------------#
#              /----------\       ping request        /----------\             #
#              | client A |-------------------------> | client B |             #
#              `----------'              \            `----------'             #
#   start timer     |        ping failed /                  |                  #
#                   |        x-----.----'                   /                  #
#                   |               `---------------------'                    #
#   ping success    | cancel timer  /                                          #
#      <------------+--------------'                                           #
#                   \                                                          #
#                    `-> Time over -> ping failed                              #
#------------------------------------------------------------------------------#

#class ez_process(object):
  #def __init__(self, command, start_conditional = None,
                     #stop_conditional = None):

    #self.sender            = ""
    #self.recipient         = ""
    #self.command           = command
    #self.start_conditional = start_conditional
    #self.stop_conditional  = stop_conditional

  #def get_sender(self):
    #return self.sender
  #def get_recipient(self):
    #return self.recipient

#def ping_request(self, cmd):
  #"""
  #Starts a ping request. Client A must be connected to Client B, i.e. they
  #must be both in clients user database, otherwise the ping process fails. To
  #enforce the precondition the argument requires the user_id. The user_addr is
  #retrieved from the user db.

  #- user_id = cmd.data
  #"""
  #user_id = cmd.data
  #pr_key = (p2pCommand.ping_reply, user_id)
  #if not pr_key in self.background_processes:
    #if not user_id in self.ips:
      #self.replyQueue.put(self.error("user not in client list"))
    #else:
      #master  = self.ips[user_id]
      #ping    = {p2pCommand.ping_reply: user_id}
      #msg     = pickle.dumps(ping)
      #try:
        #self.sockfd.sendto(msg, master)

        #def ping_failed_func(self_timer):
          #cmd = self.error("ping failed: " + user_id)
          #self.replyQueue.put(cmd)
          #del self.background_processes[pr_key]

        #self.start_background_process(pr_key, ping_failed_func, 5)

      #except IOError as e:
        #self.replyQueue.put(self.error(str(e)))
        #self.replyQueue.put(self.error("ping unsuccessful"))
  #else:
    #self.replyQueue.put(self.error("cannot ping again, " +                   \
                                   #"still waiting for response"))




#ping = {p2pCommand.ping_reply: user_id}
#lambda x: ez_process.get_sender()
#ping_process = ez_process(ping,


class ez_process(type):
  send, proceed, stop = range(3)

  def __call__(cls, *args, **kwargs):
    print "called called"
  # use call to correctly set the calling methods
    if "stage" in kwargs:
      assert(kwargs["stage"] <= cls.stages)
      cls.stage = kwargs["stage"]
    else:
      stage = 1
    for arg in args:
      print "arg:", arg
    for key, value in kwargs.items():
      print "key:", key
      if key == 'send':
        cls.send = value
        cls.command[ez_process.send] = cls.send

    cmd_order = ["cmd", "arg"]

    processes = cls.process_definition
    for pr_num in processes:
      for cmd in cmd_order:
        if cmd in processes[pr_num]:
      #for pr_name in processes[pr_num]:
          pr = processes[pr_num][cmd]
          if pr in cls.command:
            cls.proceed[pr_num].append(cls.send)
            #pass
      #if 'cmd' in processes[pr_num]:

    return super(ez_process, cls).__call__()


  def __new__(cls, clsname, bases, dct):
    # use this to override the init method
    return super(ez_process, cls).__new__(cls, clsname, bases, dct)

  def __init__(cls, clsname, bases, dct):
    print "called init."
    # use this to set class attributes
    super(ez_process, cls).__init__(clsname, bases, dct)

    print "setting class attributes"
    cls.recipients = []
    cls.proceed    = {}
    cls.timer      = {}
    cls.command    = {}

    print "makeing sure the class structure is set up properly"
    assert("process_definition" in dct)

    processes  = dct["process_definition"]
    cls.stages = len(processes)
    cls.stage  = 0

    for stage in range(1, cls.stages):
      cls.proceed[stage] = []


    def start_timer(cls, interval, proc, *args, **kwargs):
      pr = Timer(interval, proc, args, kwargs)
      cls.timer[cls.stage] = pr
      thread.start_new_thread(pr.run, ())

    def gen_timer(cls, arg, pr_num):
      if isinstance(arg, int):
        def process_failed(self):
          print cls.process_name + " failed"
        cls.proceed[pr_num].append(lambda self: start_timer(self, arg,
                                                            process_failed))

    def gen_stop(cls, arg, pr_num):
      pass

    cmds = {'break': gen_timer, 'end': gen_stop}
    for pr_num in processes:
      print "processes[pr_num]:", processes[pr_num]
      for cmd in cmds:
        if cmd in processes[pr_num]:
          cmds[cmd](cls, processes[pr_num][cmd], pr_num)
    #sys.exit()


class ez_ping(object):
  __metaclass__ = ez_process

  def ping_success():
    print "ping success"

  # the commands are defined by ez_process commands and ez_process commands are
  # mapped back to class commands which do atm not exists.
  process_definition = {1:{'cmd': ez_process.send, "break": 1},
                        2:{'cmd': ez_process.send},
                        3:{'cmd': ez_process.stop, 'end': ping_success}}

  process_name       = "ping"
  def __init__(self):
    print "init class"
    self.process()
  def process(self):
    for f in self.proceed[self.stage]:
      f(self)
    #self.stages = 3
  def foo(self, para):
    pass

def Bar(self):
  print "bar"

t = ez_ping(2, stage = 1, send = Bar)
#print "t.d:", t.d

#print t.proceed
#t.send()
#print t.proceed
time.sleep(3)

#print type(ez_ping.ping_success)
