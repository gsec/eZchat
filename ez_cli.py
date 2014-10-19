# encoding=utf-8 ==============================================================#
#                                  ez_cli.py                                   #
#==============================================================================#
# TODO: (bcn 2014-08-10) Allow to scroll in LICENSE and other files. Most likely
# we want to use a text widget that also allows to center the logo when we have
# varying width
# The built-in Text widget allows for scrolling. To do so, you have to focus
# the corresponding Text widget and press Up/Down (which can be mapped to j/k).
# We can implement scrolling even without focussing the Text widget.
# Assume we press `shift-j` and we want the text widget to scoll down. We simply
# need to capture `shift-j` and forward `down` to the text widget.

import sys
import types
import os
import signal
import subprocess
from time import sleep

from optparse import OptionParser

import urwid
from urwid.util import move_next_char, move_prev_char
from urwid.command_map import command_map, CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT
from urwid.command_map import CURSOR_LEFT, CURSOR_RIGHT, CURSOR_UP, CURSOR_DOWN

from ez_process import p2pReply, p2pCommand

import ez_preferences as ep
import ez_client as cl
import ez_pipe   as pipe

#==============================================================================#
#                                  VimMsgBox                                   #
#==============================================================================#

class VimMsgBox(urwid.ListBox):
  """Prototype for our message box"""

  signals = ['exit_msgbox', 'status_update']
  def __init__(self, logo_file=None, divider=True, *args, **kwargs):
    self.display_logo(logo_file, divider)

# TODO: JNicL No Commands needed Di 14 Okt 2014 00:03:09 CEST
# VimMsgBox is max unselectable. Thus no keys will ever get captured directly
    self.command_dict = {'j' : self.cmd_move_down,
                         'k' : self.cmd_move_up,
                         #'down' : self.cmd_exit_msgbox,
                         #'up' : self.cmd_unhandled,
                         'q': self.cmd_close_list,
                         # Blocking left & right arrow key.
                         'left' : self.cmd_unhandled,
                         'right' : self.cmd_unhandled,
                         }

  def display_logo(self, file_name, divider):
    try:
      with open(str(file_name)) as f:
        content = [lines.rstrip() for lines in f.readlines()]
        divider = False
        self.logo_displayed = True
    except IOError:
      content = ['eZ-Chat: logo file not found']
      self.logo_displayed = True

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

  def cmd_unhandled(self, *args):
    pass

  def update_content(self, content):
    if self.display_logo:
      self.cmd_exit_msgbox()

    self.body.append(urwid.AttrMap(urwid.Text(content), None, 'reveal focus'))

  def clear_msgbox(self):
    # Deleting the content of the ListWalker. Create a new Walker wouldn't
    # work unless you ListBox.__init__ again.
    # iterating over self.body and deleting elements in self.body does update
    # self.body. As a result, not all rows are deleted -> range(len(@)) does
    # not share the same memory and is fixed -> iteration deletes all elements
    # in self.body
    # for row in self.body:
    for row in range(len(self.body)):
      self.body.pop(-1)

  def cmd_exit_msgbox(self, *args):
    if self.logo_displayed:
      self.clear_msgbox()
      self.logo_displayed = False
      self._selectable = False

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
      # The idea here is that the first keypress is already processed which
      # to my opinion feels better.
      ez_cli.vimedit.keypress((size[0],), key)
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
  """
  Prints the current mode and other notifications.
  """
  def __init__(self):
    slw = urwid.SimpleFocusListWalker([])
    urwid.ListBox.__init__(self, slw)

  def cmd_unhandled(self, *args):
    pass

  def update_content(self, content):
    self.body.append(urwid.AttrMap(urwid.Text(content), None, 'reveal focus'))

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
    self.command_dict = {"close"      : cl.cl.cmd_close,
                         #"contacts"   : cl.cl.cmd_get_contact_names,
                         #"users"      : cl.cl.cmd_get_online_users,
                         "ping"       : cl.cl.cmd_ping,
                         "bgping"     : cl.cl.cmd_ping_background,
                         "add"        : cl.cl.cmd_add,
                         "servermode" : cl.cl.cmd_servermode,
                         "connect"    : cl.cl.cmd_connect,
                         "bg"         : cl.cl.cmd_bg,
                         "sync"       : cl.cl.cmd_sync,
                         "bgsync"     : cl.cl.cmd_passive_sync,
                         "ips"        : cl.cl.cmd_ips,
                         "key"        : cl.cl.cmd_key,
                         #"verify" : cl.cl.cmd_verify,
                         "send"       : cl.cl.cmd_send_msg,
                         "quit"       : self.cmd_close,
                         "q"          : self.cmd_close,
                         "show"       : self.cmd_show,
                         "open"       : self.cmd_open
                         #"clear" :
                        }

  def cmd_show(self, file_name):
    try:
      with open(str(file_name)) as f:
        self.vimedit.set_edit_text(f.read())
      self.vimedit.initialized = True
    except IOError:
      print "File not found"

  def open_contacts(self):
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
    ez_cli.top.open_box(lst, 50)

  def open_processes(self):
    def process_list(processes):
      prs = [urwid.Text("Processes:")]
      for process_id in processes:
        pr = processes[process_id]
        pr_on = not pr.finished.isSet()
        on  = urwid.Text(("online", u"ON"))
        off = urwid.Text(("offline", u"OFF"))
        status = on if pr_on else off
        prs += [urwid.Columns([urwid.Text(str(process_id)), status])]
      return VimListBox(urwid.SimpleListWalker(prs))

    processes = cl.cl.background_processes
    lst = process_list(processes)
    ez_cli.top.open_box(lst, 50)

  def cmd_open(self, *args):
    if args[0] == 'contacts':
      self.open_contacts()
    elif args[0] == 'processes':
      self.open_processes()
    elif args[0] == 'messages':
      UIDs = cl.cl.MsgDatabase.UID_list()
      msgs = cl.cl.MsgDatabase.get_entries(UIDs)
      ez_cli.vimmsgbox.clear_msgbox()
      for msg in msgs:
        if msg.recipient == cl.cl.name:
          try:
            ez_cli.msg_update((str(msg.clear_text())))
          except Exception, e:
            ez_cli.status_update("<p>Error: %s</p>" % str(e))

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
    except IndexError:
      ez_cli.status_update('<Esc> for normal mode')

    # Unkown command
    except KeyError:
      ez_cli.status_update('Command not known')

    # Arguments have wrong type
    except TypeError as e:
      ez_cli.status_update('error:' + str(e))
      ez_cli.status_update(self.command_dict[cmd_and_args[0]].__doc__)

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

#==============================================================================#
#                                   VimEdit                                    #
#==============================================================================#

# TODO: (bcn 2014-08-10) Add visual mode
class VimEdit(urwid.Edit):
  """
  VimEdit encapsulates all vim-like edit functionality.

  VimEdit allows for customization such as custom key bindings and modes.
  Preferences are defined in ez_peferences.py (soon .rc file) and are
  initialized by invoking :py:meth:`ez_preferences.init_cli_preferences` which
  must be done before the VimEdit instance.

  """
  signals = ['done', 'insert_mode', 'command_mode',
             'visual_mode', 'command_line']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, **kwargs):
    urwid.Edit.__init__(self, **kwargs)
    self.mode         = VimEdit.insert_mode
    self.last_key     = None
    self.double_press = False
    self.initialized  = None

    commands = {'cli_enter_cmdline'   : self.cmd_enter_cmdline,
                'cli_delete_one'      : self.cmd_delete_one,
                'cli_delete'          : self.cmd_delete,
                'cli_insert'          : self.cmd_insert,
                'cli_append'          : self.cmd_append,
                'cli_delete'          : self.cmd_delete,
                'cli_newline_low'     : self.cmd_newline_low,
                'cli_newline_high'    : self.cmd_newline_high,
                'cli_move_left'       : self.cmd_move_left,
                'cli_move_right'      : self.cmd_move_right,
                'cli_move_down'       : self.cmd_move_down,
                'cli_move_up'         : self.cmd_move_up,
                'cli_scroll_msg_up'   : self.cmd_scroll_msg_up,
                'cli_scroll_msg_down' : self.cmd_scroll_msg_down
                }

    self.command_dict = {}
    for cmd in commands:
      if not cmd in ep.cli_command_dict:
        sys.stderr.write('ERROR: Command ' + cmd + ' not mapped')
        cl.cl.commandQueue.put(p2pCommand('shutdown'))
        sys.exit()
      for mapped_key in ep.cli_command_dict[cmd]:
        self.command_dict[mapped_key] = commands[cmd]


  def cmd_scroll_msg_up(self):
    ez_cli.vimmsgbox.keypress((self.maxcol, 20), 'up')

  def cmd_scroll_msg_down(self):
    ez_cli.vimmsgbox.keypress((self.maxcol, 20), 'down')

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
    if self.p >= len(self.edit_text):
      return
    p = move_next_char(self.edit_text, self.p, len(self.edit_text))
    self.set_edit_pos(p)
    return

  def cmd_newline_low(self, shift=0):
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

  def cmd_newline_high(self):
    self.cmd_newline_low(shift=-1)

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
  """
  Main CLI Frame.
  Here we build the main frame out of the widgets.
  The base layout is as follows:
        +-------------------+
        |                   |   \
        | chatlog: xxx      |    \
        | chatlog: yyy      |    /
        |                   |   /
        +-------------------+
        |                   |  \
        | >>Input widget<<  |    body
        |                   |  /
        =====================
        | StatusLine        |  \
        +-------------------+    footer
        | CommandLine       |  /
        +-------------------+
  """

  def __init__(self, name = '', logging = False, *args, **kwargs):
    self.vimedit       = VimEdit(caption=('VimEdit', u'eZchat\n\n'),
                                 multiline = True)
    self.commandline   = VimCommandLine(self.vimedit, u'')

    if ep.cli_start_in_insertmode:
      self.vimedit.mode  = VimEdit.insert_mode
      self.commandline.set_edit_text(u'insert mode')
    else:
      self.vimedit.mode  = VimEdit.command_mode
      self.commandline.set_edit_text(u'command mode')

    self.vimedit_f     = urwid.Filler(self.vimedit, valign = 'top')
    self.vimedit_b     = urwid.BoxAdapter(self.vimedit_f, ep.cli_edit_height)

    self.vimmsgbox     = VimMsgBox(logo_file = 'misc/logo.txt')
    #self.vimmsgbox_f   = urwid.Filler(self.vimmsgbox, valign = 'bottom')

    # combine vimedit and vimmsgbox to vimbox
    self.vimmsgbox_b = urwid.BoxAdapter(self.vimmsgbox, ep.cli_msg_height)
    self.vimbox      = urwid.Pile([self.vimmsgbox_b, self.vimedit])
    #self.vimbox.set_focus(1)
    self.vimbox_f    = urwid.Filler(self.vimbox, valign = 'top')


    if ep.cli_status_height > 0:
      self.statusline    = VimStatusline()
      for i in range(ep.cli_status_height-1):
        self.statusline.update_content('')

      self.statusline_b  = urwid.BoxAdapter(self.statusline,
                                            ep.cli_status_height)

    if hasattr(self, 'statusline'):
      self.command_and_status = urwid.Pile([self.statusline_b,
                                            self.commandline])
    else:
      self.command_and_status = self.commandline

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
    self.top_f = urwid.Filler(self.top, 'top', ep.cli_msg_height +
        ep.cli_edit_height)

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

    self.name    = name
    self.logging = logging
    # TODO: (bcn 2014-10-19) This should also log errors
    if self.logging:
      self.logger = open(ep.join(ep.location['log'], name + '_ez_cli_session.log'),
                         'w')

  def status_update(self, content):
    if self.logging:
      self.logger.write(content + '\n')

    if hasattr(self, 'statusline'):
      # update SimpleFocusListWalker
      self.statusline.update_content(content)
      # get the number of item
      focus = len(self.statusline.body) - 1
      # set the new foucs to the last item
      self.statusline.body.set_focus(focus)

  def msg_update(self, content):
    # update SimpleFocusListWalker
    self.vimmsgbox.update_content(content)
    # get the number of item
    focus = len(self.vimmsgbox.body) - 1
    # set the new foucs to the last item
    self.vimmsgbox.body.set_focus(focus)

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
    if hasattr(self, 'statusline'):
      self.command_and_status.set_focus(1)
    self.commandline.set_edit_text(':')
    self.commandline.set_edit_pos(1)
    self.set_focus('footer')

  def command_line_exit(self, edit, new_edit_text):
    self.commandline.set_edit_text('command mode')
    self.set_focus('body')

  def exit(self, *args):
    cl.cl.cmd_close()
    if self.logging:
      self.logger.close()
    raise urwid.ExitMainLoop()

#==============================================================================#
#                                  FUNCTIONS                                   #
#==============================================================================#

def received_output(data):
  categories = {p2pReply.success: 'success',
                p2pReply.error:   'error',
                p2pReply.msg:     'msg'
                }
  if 'status' in data.strip():
      try:
        reply = cl.cl.replyQueue.get(block=False)
      except:
        reply = None
      while reply:
        if ((reply.replyType == p2pReply.success) or
            (reply.replyType == p2pReply.error)):
          status = "success" if reply.replyType == p2pReply.success else "ERROR"
          ez_cli.status_update(
                    ('Client reply %s: %s' % (status, reply.data)))
        elif reply.replyType == p2pReply.msg:
          # decrypt msg and print it on the screen
          if reply.data.recipient == cl.cl.name:
            try:
              ez_cli.msg_update((str(reply.data.clear_text())))
            except Exception, e:
              ez_cli.status_update("<p>Error: %s</p>" % str(e))

        else:
          # this case should not happen! (if theres something in the queue it
          # must be success,error or msg)
          ez_cli.status_update( ('Client reply: nada' ))
        try:
          reply = cl.cl.replyQueue.get(block=False)
        except:
          reply = None
  else:
    # this case should not happen! (if theres something in the queue, it
    # must be success,error or msg)
    ez_cli.statusline.update_content(data)
  return True

#==============================================================================#
#                               GLOBAL INSTANCES                               #
#==============================================================================#
#========================#
#  command line options  #
#========================#

usage = "usage: %prog [options] name"
parser = OptionParser(usage)

# parse options
parser.add_option("-s", "--script", dest="filename",
                  help="run eZchat with script", metavar="FILE")

parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages")

parser.add_option("-l", "--log",
                  action="store_true", dest="logging", default=False,
                  help="log status to .name_eZsession.log")

(options, args) = parser.parse_args()

try:
  ep.init_cli_preferences()
  if not len(args) == 1:
    print 'Please give your name as argument'
    sys.exit()
  cl.init_client(args[0], **ep.process_preferences)
  if not options.verbose:
    ep.cli_status_height = 0 # disable statusline
  ez_cli = ez_cli_urwid(name = args[0], logging = options.logging)
except ep.DomainError, err:
  sys.stderr.write('ERROR: %s\n' % str(err))
  cl.cl.commandQueue.put(p2pCommand('shutdown'))
  sys.exit()

#==============#
#  MAIN LOOPS  #
#==============#

loop = urwid.MainLoop(ez_cli, ep.palette)
pipe.pipe = loop.watch_pipe(received_output)

# start eZchat with script
if options.filename:
  try:
    with open(options.filename, 'r') as f:
      lines = f.readlines()
      for line in lines:
        ez_cli.commandline.evaluate_command(line.replace('\n',''))
  except IOError as e:
    ez_cli.status_update("Loading script failed. I/O error({0}): {1}".
                          format(e.errno, e.strerror))
  except:
    print "Unexpected error:", sys.exc_info()[0]
    raise

loop.run()

cl.cl.commandQueue.put(p2pCommand('shutdown'))
