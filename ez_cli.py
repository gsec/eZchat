# encoding=utf-8 ==============================================================#
#                                  ez_cli.py                                   #
#==============================================================================#
# TODO: (bcn 2014-08-10) Allow to read in commands from file or pipe with switch
# -file
# TODO: (bcn 2014-08-10) Allow to scroll in LICENSE and other files. Most likely
# we want to use a text widget that also allows to center the logo when we have
# varying width

import sys, types
import signal
import subprocess, os
from time import sleep

import urwid
from urwid.util import move_next_char, move_prev_char
from urwid.command_map import (command_map, CURSOR_LEFT, CURSOR_RIGHT,
    CURSOR_UP, CURSOR_DOWN, CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT)

from ez_process import p2pReply

import ez_preferences as ep
import ez_client as cl
import ez_pipe   as pipe

#==============================================================================#
#                                  VimMsgBox                                   #
#==============================================================================#

class VimMsgBox(urwid.ListBox):
  """Prototype for our message box"""

  signals = ['exit_msgbox', 'status_update']
  def __init__(self, content = [], file_name = None, divider = True):
    if file_name != None:
      try:
        with open(str(file_name)) as f:
          content = f.readlines()
          divider = False
          for i, con in enumerate(content):
            content[i] = con.replace('\n','')
          self.logo_displayed = True
      except IOError:
        print "File not found"
    slw = []
    for item in content[:-1]:
      if divider:
        slw.extend([urwid.Text(item),urwid.Divider()])
      else:
        slw.extend([urwid.Text(item)])
    slw.append(urwid.Text(content[-1]))
    slw = urwid.SimpleFocusListWalker([urwid.AttrMap(w,
            None, 'reveal focus') for w in slw])
    urwid.ListBox.__init__(self, slw)

    self.command_dict = {'j' : self.cmd_move_down,
                         'k' : self.cmd_move_up,
                         'down' : self.cmd_exit_msgbox,
                         'up' : self.cmd_unhandled,
                         'q': self.cmd_close_list,
                         # Blocking left & right arrow key.
                         'left' : self.cmd_unhandled,
                         'right' : self.cmd_unhandled,
                         }

  def cmd_unhandled(self, *args):
    pass

  def update_content(self, content):
    self.body.append(urwid.AttrMap(urwid.Text(content), None, 'reveal focus'))
    #slw = urwid.SimpleFocusListWalker([urwid.AttrMap(w,
            #None, 'reveal focus') for w in slw])
    #self.body = slw

  def cmd_exit_msgbox(self, *args):
    if self.logo_displayed:
      slw = urwid.SimpleFocusListWalker([])
      self.body = slw
      #self.update_content('test')
      self.logo_displayed = False

    urwid.emit_signal(self, 'exit_msgbox')

  def cmd_move_up(self, size):
    urwid.ListBox.keypress(self, size, 'up')

  def cmd_move_down(self, size):
    urwid.ListBox.keypress(self, size, 'down')

  def cmd_close_list(self, *args):
    ez_cli.top.close_box()

  def keypress(self, size, key):
    # press any key to skip logo
    if self.logo_displayed:
      self.cmd_exit_msgbox()
      return
    try:
      return self.command_dict[key](size)
    except KeyError:
      return urwid.ListBox.keypress(self, size, key)



#==============================================================================#
#                                  VimListBox                                  #
#==============================================================================#

class VimListBox(urwid.ListBox):

  def __init__(self, *args, **kwargs):
    urwid.ListBox.__init__(self, *args, **kwargs)
    self.command_dict = {'j' : self.cmd_move_down,
                         'k' : self.cmd_move_up,
                         'down' : self.cmd_move_down,
                         'up' : self.cmd_move_up,
                         'q': self.cmd_close_list,
                         # Blocking left & right arrow key.
                         'left' : self.cmd_unhandled,
                         'right' : self.cmd_unhandled,
                         }

  def cmd_unhandled(self, *args):
    pass

  def cmd_move_up(self, size):
    urwid.ListBox.keypress(self, size, 'up')

  def cmd_move_down(self, size):
    urwid.ListBox.keypress(self, size, 'down')

  def cmd_close_list(self, *args):
    ez_cli.top.close_box()

  def keypress(self, size, key):
    try:
      return self.command_dict[key](size)
    except KeyError:
      return urwid.ListBox.keypress(self, size, key)


#==============================================================================#
#                                VimStatusLine                                 #
#==============================================================================#

class VimStatusline(urwid.ListBox):
  """Prototype for our message box"""

  def __init__(self):
    slw = urwid.SimpleFocusListWalker([])
    urwid.ListBox.__init__(self, slw)

  def cmd_unhandled(self, *args):
    pass

  def update_content(self, content):
    self.body.append(urwid.AttrMap(urwid.Text(content), None, 'reveal focus'))

#class VimStatusline(urwid.Text):
    #def __init__(self):
        #"""@todo: to be defined1. """


#==============================================================================#
#                                VimCommandLine                                #
#==============================================================================#

class VimCommandLine(urwid.Edit):
  """
  Evaluates commands that are typed in command mode.
  """
  signals = ['command_line_exit', 'exit_ez_chat', 'status_update']
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
    self.command_dict = {"close" : cl.cl.cmd_close,
                         "contacts" : cl.cl.cmd_get_contact_names,
                         "users" : cl.cl.cmd_get_online_users,
                         "ping" : cl.cl.cmd_ping,
                         "add" : cl.cl.cmd_add,
                         "servermode" : cl.cl.cmd_servermode,
                         "connect" : cl.cl.cmd_connect,
                         "bg" : cl.cl.cmd_bg,
                         "sync" : cl.cl.cmd_sync,
                         "ips" : cl.cl.cmd_ips,
                         "key" : cl.cl.cmd_key,
                         #"verify" : cl.cl.cmd_verify,
                         "send" : cl.cl.cmd_send_msg,
                         "quit" : self.cmd_close,
                         "q" : self.cmd_close,
                         "show" : self.cmd_show,
                         "open" : self.cmd_open
                        }

  def cmd_show(self, file_name):
    try:
      with open(str(file_name)) as f:
        self.vimedit.set_edit_text(f.read())
      self.vimedit.initialized = True
    except IOError:
      print "File not found"

  def cmd_open(self, *args):
    # what is intended here? seems wrong
    # JNicL - Sa 04 Okt 2014 00:02:08 CEST
    # Not Wrong. The following works only for `:open contacts`. We will have to
    # introduce other scenarios as we might want to open other windows, e.g.
    # settings.
    assert(args[0] == 'contacts')
    def contact_list(user_ids):
      contacts = [urwid.Text("Contacts:")]
      for user in user_ids:
        user_id = user[0]
        on  = urwid.Text(("online", u"ON"))
        off = urwid.Text(("offline", u"OFF"))
        status = on if user[1] else off
        contacts += [urwid.Columns([urwid.CheckBox(user_id), status])]
      return VimListBox(urwid.SimpleListWalker(contacts))
    # get contact list
    UIDs = cl.cl.UserDatabase.UID_list()
    if len(UIDs) > 0:
      contacts = [str(entry.name) for entry in
                  cl.cl.UserDatabase.get_entries(UIDs) if not cl.cl.name ==
                  entry.name]
    else:
      contacts = []

    # append all users online
    if len(cl.cl.ips.keys()) > 0:
      for user in cl.cl.ips.keys():
        if not (user in contacts or user == cl.cl.name):
          contacts.append(user)
    # construct user/online list
    if len(contacts) > 0:
      contacts = [(contact, contact in cl.cl.ips) for contact in contacts]

    lst = contact_list(contacts)
    #lst_f = urwid.Filler(lst, valign = 'top')
    ez_cli.top.open_box(lst, 50)
    #ez_cli.top.open_box(contacts_f)
    return

  def cmd_close(self):
    with open(ep.command_history, 'w') as f:
      f.write('\n'.join(self.command_lines))
    #cl.cl.cmd_close()
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
      #print '\n'
      #print ' '.join(matches)

  def evaluate_command(self, cmd):
    cmd_and_args = cmd.split()
    try:
      self.command_dict[cmd_and_args[0]](*cmd_and_args[1:])
      self.save_command(cmd)
      urwid.emit_signal(self, 'command_line_exit', self, '')
    # Empty cmdline
    except IndexError:
      #urwid.emit_signal(self, 'command_line_exit', self, '')
      print (' <Esc> for normal mode')
      sleep(0.8)
    # Unkown command
    except KeyError:
      #print '\n'
      print '\nCommand not known'
      sleep(0.8)
    # Arguments have wrong type
    except TypeError as e:
      print '\n'
      print str(e)
      raw_input(self.command_dict[cmd_and_args[0]].__doc__)
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
    elif key != 'backspace' or p > 1:
      urwid.Edit.keypress(self, size, key)

#==============================================================================#
#                                   VimEdit                                    #
#==============================================================================#

# TODO: (bcn 2014-08-10) Add visual mode
class VimEdit(urwid.Edit):
  """VimEdit encapsulates all vim-like edit functionality."""
  signals = ['done', 'insert_mode', 'command_mode',
             'visual_mode', 'command_line']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, **kwargs):
    urwid.Edit.__init__(self, **kwargs)
    self.mode = VimEdit.insert_mode
    self.last_key = None
    self.double_press = False
    self.initialized = None
    self.command_dict = {':' : self.cmd_enter_cmdline,
                         'x' : self.cmd_delete_one,
                         'd' : self.cmd_delete,
                         'i' : self.cmd_insert,
                         'a' : self.cmd_append,
                         'd' : self.cmd_delete,
                         'o' : self.cmd_newline,
                         'O' : self.cmd_newline_O,
                         'h' : self.cmd_move_left,
                         'l' : self.cmd_move_right,
                         'j' : self.cmd_move_down,
                         'k' : self.cmd_move_up,
                         'down' : self.cmd_move_down,
                         'up' : self.cmd_move_up,
                         'left' : self.cmd_move_left,
                         'right' : self.cmd_move_right,
                        }

  def cmd_enter_cmdline(self):
    urwid.emit_signal(self, 'command_line', self, ':')
    self.set_edit_text('')
    return

  def cmd_delete_one(self):
    self.pref_col_maxcol = None, None
    p = self.edit_pos
    self.set_edit_text(self.edit_text[:p] + self.edit_text[self.edit_pos + 1:])
    #self.cmd_move_left(pressed = 'x')    # cursor stay in pos -> like vim
    return

  def cmd_delete(self):
    if self.last_key is None and self.double_press:
      text = self.get_edit_text()
      x, y = self.get_cursor_coords((self.maxcol,))
      text = text.split('\n')
      text.pop(y-2)
      # tweak which beavior u want, the +1 feels better ( makes a difference
      # when deleting the whole line and the cursor is at the last character)
      x_pos = sum([len(u) for u in text[:y-2]])+1
      text = '\n'.join(text)
      self.set_edit_text(text)
      self.set_edit_pos(x_pos)

  def cmd_insert(self):
    self.mode = VimEdit.insert_mode
    urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
    return

  def cmd_append(self):
    self.cmd_insert()
    if self.p >= len(self.edit_text): return
    p = move_next_char(self.edit_text, self.p, len(self.edit_text))
    self.set_edit_pos(p)
    return

  def cmd_newline(self, shift=0):
    self.cmd_insert()
    x, y = self.get_cursor_coords((self.maxcol,))
    y = y + shift
    text = self.get_edit_text()
    text = text.split('\n')
    text.insert(y - 1, '')
    text = '\n'.join(text)
    self.set_edit_text(text)
    self.move_cursor_to_coords((self.maxcol,), 'left', y + 1)
    return

  def cmd_newline_O(self):
    self.cmd_newline(shift=-1)

  def cmd_move_left(self, pressed=CURSOR_LEFT):
    if self.p==0: return pressed
    p = move_prev_char(self.edit_text,0,self.p)
    self.set_edit_pos(p)

  def cmd_move_right(self):
    if self.p >= len(self.edit_text): return CURSOR_RIGHT
    p = move_next_char(self.edit_text,self.p,len(self.edit_text))
    self.set_edit_pos(p)

  def cmd_move_down(self, shift=1):
    self.highlight = None
    x, y = self.get_cursor_coords((self.maxcol,))
    pref_col = self.get_pref_col((self.maxcol,))
    y += shift
    if not self.move_cursor_to_coords((self.maxcol,), pref_col, y):
      if shift == 1:
        return 'down'
      else:
        return 'up'

  def cmd_move_up(self):
    self.cmd_move_down(shift=-1)

  def keypress(self, size, key):
    (self.maxcol,) = size
    self.p = self.edit_pos
    if self.initialized:
      self.set_edit_text('')
      self.initialized = False
    if key == self.last_key:
      self.last_key = None
      self.double_press = True
    else:
      self.last_key = key

    # send message
    if key == 'enter':
      if self.multiline and self.mode == VimEdit.insert_mode:
        key = "\n"
        self.insert_text(key)
      else:
        urwid.emit_signal(self, 'done', self, self.get_edit_text())
        self.set_edit_text('')
      return

    # execute commands
    elif self.mode == VimEdit.command_mode:
      try:
        self.command_dict[key]()
      except KeyError:
        pass

    # enter command mode
    # TODO: nick  Fr 26 Sep 2014 21:39:56 CEST
    # esc should behave as 'x', then go to command_mode.
    # need to check if last operation was appending out of command mode which is
    # yet not possible
    elif key == 'esc':
      self.last_key = key
      self.mode = VimEdit.command_mode
      urwid.emit_signal(self, 'command_mode', self, 'command mode')
      self.cmd_move_left(pressed = key)

    elif self.mode == VimEdit.insert_mode:
      urwid.Edit.keypress(self, size, key)

#==============================================================================#
#                                 ez_cli_urwid                                 #
#==============================================================================#

class ez_cli_urwid(urwid.Frame):
  """Main CLI Frame."""

  def __init__(self, *args, **kwargs):
    self.vimedit       = VimEdit(caption=('VimEdit', u'eZchat\n\n'),
                                 multiline = True)
    self.vimedit.mode  = VimEdit.insert_mode
    self.vimedit_f     = urwid.Filler(self.vimedit, valign = 'top')
    self.vimedit_b     = urwid.BoxAdapter(self.vimedit_f, 10)

    #self.vimmsgbox     = VimMsgBox(['msg1: foo', 'msg2: bar'])
    self.vimmsgbox     = VimMsgBox(file_name = 'logo')
    self.vimmsgbox_f   = urwid.Filler(self.vimmsgbox, valign = 'bottom')

    # combine vimedit and vimmsgbox to vimbox
    self.vimmsgbox_b = urwid.BoxAdapter(self.vimmsgbox, 25)
    self.vimbox      = urwid.Pile([self.vimmsgbox_b, self.vimedit])
    self.vimbox_f    = urwid.Filler(self.vimbox, valign = 'top')
    #self.vimbox.set_focus(1)

    self.statusline    = VimStatusline()
    self.statusline.update_content('')
    self.statusline.update_content('')
    self.statusline.update_content('')
    #self.statusline.update_content('test')
    self.statusline_b  = urwid.BoxAdapter(self.statusline, 4)
    self.commandline   = VimCommandLine(self.vimedit, u'')
    self.commandline.set_edit_text(u'insert mode')

    #self.commandline_b = urwid.BoxAdapter(self.commandline, 1)
    #self.commandline_f = urwid.Filler(self.commandline, valign = 'bottom')


    self.command_and_status = urwid.Pile([self.statusline_b,
                                          self.commandline])

    #self.command_and_status = urwid.Pile([ self.commandline])

    focus_map = {
    'heading': 'focus heading',
    'options': 'focus options',
    'line': 'focus line'}

    class HorizontalBoxes(urwid.Columns):
      def __init__(self):
        super(HorizontalBoxes, self).__init__([], dividechars=1)

      def open_box(self, box, weight):
        if self.contents:
          del self.contents[self.focus_position + 1:]

        self.contents.append((urwid.AttrMap(box, 'options', focus_map),
            self.options('weight', weight)))
        self.focus_position = len(self.contents) - 1

      def close_box(self):
        del self.contents[1]
        self.focus_position = 0

    self.top = HorizontalBoxes()
    self.top.open_box(self.vimbox_f, 100)
    self.top_f = urwid.Filler(self.top, 'top', 20)

    urwid.Frame.__init__(self, self.top_f, footer=self.command_and_status)

    urwid.connect_signal(self.vimedit, 'done', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'insert_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_line', self.command_line_mode)
    urwid.connect_signal(self.commandline, 'command_line_exit',
                         self.command_line_exit)

    urwid.connect_signal(self.commandline, 'status_update',
                         self.status_update)
    urwid.connect_signal(self.commandline, 'exit_ez_chat', self.exit)
    urwid.connect_signal(self.vimmsgbox, 'exit_msgbox', self.exit_msgbox)
    signal.signal(signal.SIGINT, self.__close__)

  def status_update(self, content):
    self.statusline.update_content(content)
    focus = self.statusline.body.get_focus()[1]
    self.statusline.body.set_focus(focus+1)
    #self.statusline.set_focus(3)

  def __close__(self, *args):
    self.commandline.cmd_close()
    self.exit()

  def mode_notifier(self, edit, new_edit_text):
    self.commandline.set_edit_text(str(new_edit_text))
    #edit.set_edit_text(str(new_edit_text))

  def enter_msgbox(self):
    self.vimbox.set_focus(0)

  def exit_msgbox(self):
    self.vimbox.set_focus(1)

  def command_line_mode(self, edit, new_edit_text):
    self.command_and_status.set_focus(1)
    self.commandline.set_edit_text(':')
    self.commandline.set_edit_pos(1)
    self.set_focus('footer')

  def command_line_exit(self, edit, new_edit_text):
    self.commandline.set_edit_text('command mode')
    self.set_focus('body')

  def exit(self, *args):
    cl.cl.cmd_close()
    raise urwid.ExitMainLoop()

#==============================================================================#
#                               GLOBAL INSTANCES                               #
#==============================================================================#

#if __name__ == "__main__":
#cl.init_client()
client_path = os.path.join(os.path.dirname(sys.argv[0]), 'ez_client.py')
ez_cli = ez_cli_urwid()
palette = [
    ('online', 'light green', 'dark green'),
    ('offline', 'dark red', 'light red'),
    ]
loop = urwid.MainLoop(ez_cli, palette)

def received_output(data):
  if 'reply' in data.strip():
    try:
      reply = cl.cl.replyQueue.get(block=False)
      while reply:
        status = "success" if reply.replyType == p2pReply.success else "ERROR"
        ez_cli.status_update(
                ( data.strip() + 'Client reply %s: %s' % (status, reply.data)))
        reply = cl.cl.replyQueue.get(block=False)
    except:
      pass
  else:
    ez_cli.statusline.update_content(data)
  return True

pipe.pipe = loop.watch_pipe(received_output)
proc = subprocess.Popen(
    ['python', '-u', client_path, sys.argv[1]],
    stdout=pipe.pipe,
    close_fds=True)

loop.run()
