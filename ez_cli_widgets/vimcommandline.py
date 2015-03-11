#==============================================================================#
#                                VimCommandLine                                #
#==============================================================================#

#============#
#  Includes  #
#============#

import urwid

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             os.pardir))
import ez_client as cl
import ez_preferences as ep

from vimlistbox import VimListBox

#===================#
#  Class Definiton  #
#===================#

class VimCommandLine(urwid.Edit):
  """
  Evaluates commands that are typed in command mode.
  """
  signals = ['command_line_exit', 'exit_ez_chat', 'status_update',
             'close_box', 'open_box', 'clear_msgbox', 'msg_update',
             'status_update', 'open_pop_up']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, vimedit, *args, **kwargs):
    urwid.Edit.__init__(self, *args, **kwargs)
    self.vimedit = vimedit
    try:
      with open(ep.command_history, 'r') as f:
        self.command_lines = f.read().split('\n')
    except IOError:
      self.command_lines = []
    self.command_counter = len(self.command_lines)
    self.command_dict = {"close": cl.cl.cmd_close,
                         #"contacts"   : cl.cl.cmd_get_contact_names,
                         #"users"      : cl.cl.cmd_get_online_users,
                         "ping": cl.cl.cmd_ping,
                         "bgping": cl.cl.cmd_ping_background,
                         "add": cl.cl.cmd_add,
                         "servermode": cl.cl.cmd_servermode,
                         "connect": cl.cl.cmd_connect,
                         "auth": cl.cl.cmd_authenticate,
                         "bg": cl.cl.cmd_bg,
                         "sync": cl.cl.cmd_sync,
                         "bgsync": cl.cl.cmd_passive_sync,
                         "ips": cl.cl.cmd_ips,
                         "key": cl.cl.cmd_key,
                         "send": cl.cl.cmd_send_msg,
                         "sendpacket": cl.cl.send_packet,
                         "quit": self.cmd_close,
                         "q": self.cmd_close,
                         "show": self.cmd_show,
                         "open": self.cmd_open}

  def cmd_show(self, file_name):
    try:
      with open(str(file_name)) as f:
        self.vimedit.set_edit_text(f.read())
      self.vimedit.initialized = True
    except IOError:
      print "File not found"

  def get_marked_contacts(self):
    if hasattr(self, 'contact_checkbox'):
      return [u for u in self.contact_checkbox if
              self.contact_checkbox[u].state]
    else:
      return []

  def contact_list(self):
    contacts = [urwid.Text("Contacts:")]
    self.contact_checkbox = {}
    for user in self.contacts:
      user_id = user[0]
      on = urwid.Text(("online", u"ON"))
      off = urwid.Text(("offline", u"OFF"))
      status = on if user[1] else off
      checkbox = urwid.CheckBox(user_id)

      self.contact_checkbox[user_id] = checkbox
      contacts += [urwid.Columns([checkbox, status])]
    return VimListBox(urwid.SimpleListWalker(contacts))

  def open_contacts(self):
    # get contact list

    UIDs = cl.cl.UserDatabase.UID_list()
    if len(UIDs) > 0:
      contacts = [str(entry.name) for entry in
                  cl.cl.UserDatabase.get_entries(UIDs) if not cl.cl.name ==
                  entry.name]
    else:
      contacts = []

    # append all users online
    #if len(cl.cl.ips.keys()) > 0:
      #for user in cl.cl.ips.keys():
        #if not (user in contacts or user == cl.cl.name):
          #contacts.append(user)
    # construct user/online list
    if len(contacts) > 0:
      contacts = [(contact, contact in cl.cl.ips) for contact in contacts]

    self.contacts = contacts
    c_list = self.contact_list()

    urwid.connect_signal(c_list, 'close_box', self.cmd_close_box)
    urwid.emit_signal(self, 'open_box', c_list, 50)

  def open_processes(self):
    def process_list(processes):
      prs = [urwid.Text("Processes:")]
      for process_id in processes:
        pr = processes[process_id]
        pr_on = not pr.finished.isSet()
        on = urwid.Text(("online", u"ON"))
        off = urwid.Text(("offline", u"OFF"))
        status = on if pr_on else off
        prs += [urwid.Columns([urwid.Text(str(process_id)), status])]
      return VimListBox(urwid.SimpleListWalker(prs))

    processes = cl.cl.background_processes
    lst = process_list(processes)
    urwid.connect_signal(lst, 'close_box', self.cmd_close_box)
    urwid.emit_signal(self, 'open_box', lst, 50)

  def cmd_close_box(self, *args):
    urwid.emit_signal(self, 'close_box')

  def cmd_open(self, *args):
    if args[0] == 'contacts':
      self.open_contacts()
    elif args[0] == 'processes':
      self.open_processes()
    elif args[0] == 'messages':
      UIDs = cl.cl.MsgDatabase.UID_list()
      msgs = cl.cl.MsgDatabase.get_entries(UIDs)

      urwid.emit_signal(self, 'clear_msgbox')
      for msg in msgs:
        if msg.recipient == cl.cl.name:
          try:
            urwid.emit_signal(self, 'msg_update', str(msg.clear_text()))
          except Exception, e:
            urwid.emit_signal(self, 'status_update', "Error: %s" % str(e))
    elif args[0] == 'popup':
      urwid.emit_signal(self, 'open_pop_up')

  def cmd_close(self):
    with open(ep.command_history, 'w') as f:
      f.write('\n'.join(self.command_lines))

    urwid.emit_signal(self, 'exit_ez_chat')

  def __close__(self):
    self.cmd_close()

  def tab_completion(self, cmd):
    cmd = self.get_edit_text()[1:]
    matches = [key for key in self.command_dict if key.startswith(cmd.strip())]
    if len(matches) == 1:
      line = ':' + matches[0] + ' '
      self.set_edit_text(line[:])
      self.set_edit_pos(len(line)-1)
    else:
      urwid.emit_signal(self, 'status_update', ' '.join(matches))

  def evaluate_command(self, cmd):
    cmd_and_args = cmd.split()
    try:
      self.command_dict[cmd_and_args[0]](*cmd_and_args[1:])
      self.save_command(cmd)
      urwid.emit_signal(self, 'command_line_exit', self, '')

    # Empty cmdline
    except IndexError as e:
      urwid.emit_signal(self, 'status_update', '<Esc> for normal mode')

    # Unkown command
    except KeyError:
      urwid.emit_signal(self, 'status_update', 'Command not known.')

    # Arguments have wrong type
    except TypeError as e:
      urwid.emit_signal(self, 'status_update', 'Error:' + str(e) + '.')
      cmd_dct = self.command_dict[cmd_and_args[0]].__doc__
      urwid.emit_signal(self, 'status_update', str(cmd_dct))

    self.set_edit_text(':' + cmd)

  def save_command(self, command):
    self.checkcache = True
    self.command_lines.append(command)
    self.command_counter = len(self.command_lines)

  def get_last_command(self, shift=1):
    try:
      self.command_counter -= shift
      if self.command_counter < 0:
        raise IndexError
      last_command = self.command_lines[self.command_counter]
      self.set_edit_text(':' + last_command)
      self.set_edit_pos(len(self.edit_text))
    except IndexError:
      self.command_counter = len(self.command_lines)
      self.set_edit_text(':')

  def get_next_command(self):
    self.get_last_command(shift=-1)

  def keypress(self, size, key):
    p = self.edit_pos
    cmd = self.get_edit_text()[1:]

    if key == 'esc':
      urwid.emit_signal(self, 'command_line_exit', self, '')
      return
    elif key == 'enter':
      self.evaluate_command(cmd)
      return
    elif key == 'up':
      self.get_last_command()
      return
    elif key == 'down':
      self.get_next_command()
      return
    elif key == 'tab':
      self.tab_completion(cmd)
      return
    # do not allow to delete `:`
    elif (key != 'backspace' or p > 1) and (key != 'left' or p > 1):
      urwid.Edit.keypress(self, size, key)
