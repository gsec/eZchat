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
             'status_update', 'open_pop_up', 'contact_mark_update']
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
                         "open": self.cmd_open,
                         'stop': cl.cl.cmd_stop_background_process}

  def cmd_show(self, file_name):
    try:
      with open(str(file_name)) as f:
        self.vimedit.set_edit_text(f.read())
      self.vimedit.initialized = True
    except IOError:
      print "File not found"

  def get_marked_contacts(self):
    if hasattr(self, 'contact_checkbox'):
      return [self.contacts[pos][0] for pos, u in
              enumerate(self.contact_checkbox)
              if u.state]
    else:
      return []

  def contact_list(self):
    shadowline = urwid.AttrMap(urwid.Text(('border', ' ')), 'shadow')
    contacts = [shadowline, urwid.Text(('bold', 'Contacts:'))]
    online_users = cl.cl.ips.values()
    self.contact_checkbox = []
    for user_fingerprint, status in self.contacts:
      user, fingerprint = user_fingerprint
      user_id = user
      on = urwid.Text(("online", u"ON"))
      off = urwid.Text(("offline", u"OFF"))

      status = on if status else off
      checkbox = urwid.CheckBox(user_id)

      self.contact_checkbox.append(checkbox)
      contacts += [urwid.Columns([checkbox, status])]
    return VimListBox(urwid.SimpleListWalker(contacts))

  def open_contacts(self):
    # get contact list

    UIDs = cl.cl.UserDatabase.UID_list()
    if len(UIDs) > 0:
      contacts = [(str(entry.name), entry.UID) for entry in
                  cl.cl.UserDatabase.get_entries(UIDs) if not cl.cl.name ==
                  entry.name]
    else:
      contacts = []

    # append all users online
    #if len(cl.cl.ips.keys()) > 0:
      #for master in cl.cl.ips:
        #username, _ = cl.cl.ips[master]
        #if not (username in contacts or username == cl.cl.name):
          #contacts.append(username)

    # construct user/online list
    if len(contacts) > 0:
      # online users identified by fingerprint not user_id
      users_online = [u[1] for u in cl.cl.ips.values()]
      contacts = [(contact, contact[1] in users_online) for contact in contacts]

    self.contacts = contacts
    c_list = self.contact_list()

    urwid.connect_signal(c_list, 'close_box', self.cmd_close_box)
    urwid.connect_signal(c_list, 'close_box', self.contact_mark_update)
    urwid.emit_signal(self, 'open_box', c_list, 50)

  def contact_mark_update(self):
    """
    Signaling that contacts may be marked.
    """
    urwid.emit_signal(self, 'contact_mark_update')

  def process_list(self, update=False):
    processes = cl.cl.background_processes
    shadowline = urwid.AttrMap(urwid.Text(('border', ' ')), 'shadow')
    prs = [shadowline, urwid.Text(('bold', 'Processes:'))]
    for process_id in processes:
      pr = processes[process_id]
      pr_on = not pr.finished.isSet()
      on = urwid.Text(("online", u"ON"))
      off = urwid.Text(("offline", u"OFF"))
      status = on if pr_on else off
      from ez_dialog import DialogPopUp

      def close_process(process_id):
        def eval_cmd(*args):
          try:
            cl.cl.cmd_stop_background_process(process_id)
          except Exception, e:
            urwid.emit_signal(self, 'status_update', "Error: %s" % str(e))
        return eval_cmd

      process_pop_up = DialogPopUp(str(process_id), additional_widgets=status,
                                   pop_up_text='End process?',
                                   success_callback=close_process(process_id))

      urwid.connect_signal(process_pop_up, 'update',
                           lambda *args: self.process_list(update=True))
      prs += [process_pop_up]
      #prs += [urwid.Columns([urwid.Text(str(process_id)), status])]
    if update:
      self.slw[:] = prs
    else:
      self.slw = urwid.SimpleListWalker(prs)
    #return VimListBox(self.slw)

  def packets_list(self, update=False):
    packets = cl.cl.stored_packets
    shadowline = urwid.AttrMap(urwid.Text(('border', ' ')), 'shadow')
    pcts = [shadowline, urwid.Text(('bold', 'Packets:'))]
    for packet_id in packets:
      from ez_dialog import DialogPopUp
      max_packets = str(packets[packet_id].max_packets)
      received_packets = str(len(packets[packet_id].packets))
      # will be replaced by progress bar
      status = urwid.Text(str(received_packets) + '/' + str(max_packets))

      def close_packets(packet_id):
        def eval_cmd(*args):
          del cl.cl.stored_packets[packet_id]
          try:
            cl.cl.cmd_stop_background_process(packet_id)
          except Exception, e:
            urwid.emit_signal(self, 'status_update', "Error: %s" % str(e))
        return eval_cmd

      process_pop_up = DialogPopUp(str(packet_id), additional_widgets=status,
                                   pop_up_text='End packet?',
                                   success_callback=close_packets(packet_id))

      urwid.connect_signal(process_pop_up, 'update',
                           lambda *args: self.process_list(update=True))
      pcts += [process_pop_up]
      #prs += [urwid.Columns([urwid.Text(str(process_id)), status])]
    if update:
      self.slw[:] = pcts
    else:
      self.slw = urwid.SimpleListWalker(pcts)

  def open_processes(self):
    self.process_list()
    vimlistbox = VimListBox(self.slw)
    urwid.connect_signal(vimlistbox, 'close_box', self.cmd_close_box)
    urwid.emit_signal(self, 'open_box', vimlistbox, 50)

  def open_packets(self):
    self.packets_list()
    vimlistbox = VimListBox(self.slw)
    urwid.connect_signal(vimlistbox, 'close_box', self.cmd_close_box)
    urwid.emit_signal(self, 'open_box', vimlistbox, 50)

  def cmd_close_box(self, *args):
    urwid.emit_signal(self, 'close_box')

  def cmd_open(self, *args):
    if args[0] == 'contacts':
      self.open_contacts()
    elif args[0] == 'processes':
      self.open_processes()
    elif args[0] == 'packets':
      self.open_packets()
    elif args[0] == 'messages':
      UIDs = cl.cl.MsgDatabase.UID_list()
      msgs = sorted(cl.cl.MsgDatabase.get_entries(UIDs), key=lambda u: u.time)

      #urwid.emit_signal(self, 'clear_msgbox')
      for msg in msgs:
        try:
          msg_dct = msg.clear_message()
          urwid.emit_signal(self, 'status_update','here')
          if (hasattr(msg, 'target') and msg.target is not None and
              msg.recipient == cl.cl.fingerprint):
            sender = msg.target
          else:
            sender = msg.sender

          sender_name = cl.cl.get_user(msg_dct['sender'])
          if not sender_name:
            sender_name = msg_dct['sender']

          sender_str = ' '.join([sender_name, "@",
                                 msg_dct['time'], ":\n"])

          msg_str = msg_dct['content']
          #urwid.emit_signal(self, 'status_update', str((sender_str, msg_str), sender))
          urwid.emit_signal(self, 'msg_update', (sender_str, msg_str), sender,
                            False)
        except Exception as e:
          urwid.emit_signal(self, 'status_update', str(e))
          pass

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
    except Exception as e:
      # close cmd
      raise

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
