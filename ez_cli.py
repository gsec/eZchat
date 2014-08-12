# encoding=utf-8 ==============================================================#
#                                  ez_cli.py                                   #
#==============================================================================#

import sys, types
import urwid
from urwid.util import move_next_char, move_prev_char
from urwid.command_map import (command_map, CURSOR_LEFT, CURSOR_RIGHT,
    CURSOR_UP, CURSOR_DOWN, CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT)

import signal
import ez_p2p as ep

# imports related to the inclusion of the chat client
import ez_client as cl
import subprocess, os
run_me = os.path.join(os.path.dirname(sys.argv[0]), 'ez_client.py')

#==============================================================================#
#                                  VimButton                                   #
#==============================================================================#

class VimButton(urwid.Button):
  """TODO: Explain me..."""
  insert_mode, command_mode, visual_mode = range(3)

  def keypress(self, size, key):
    if key =='j':
      return 'down'
    elif key == 'k':
      return 'up'
    else:
      urwid.Button.keypress(size, key)

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

                         # blocking the left & right arrow key.
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
#                                VimCommandLine                                #
#==============================================================================#

class VimCommandLine(urwid.Edit):
  """Evaluates commands that are typed in the lowest line of the CLI."""
  signals = ['command_line_exit', 'exit_ez_chat']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, vimedit, *args, **kwargs):
    urwid.Edit.__init__(self, *args, **kwargs)
    self.vimedit = vimedit
    self.command_dict = {"close" : cl.cl.cmd_close,
                         "users" : cl.cl.cmd_users,
                         "ping" : cl.cl.cmd_ping,
                         "add" : cl.cl.cmd_add,
                         "servermode" : cl.cl.cmd_servermode,
                         "connect" : cl.cl.cmd_connect,
                         "bg" : cl.cl.cmd_bg,
                         "sync" : cl.cl.cmd_sync,
                         "ips" : cl.cl.cmd_ips,
                         "key" : cl.cl.cmd_key,
                         "verify" : cl.cl.cmd_verify,
                         "send" : cl.cl.cmd_send,
                         "quit" : self.cmd_close,
                         "q" : self.cmd_close,
                         "show" : self.cmd_show,
                         "open" : self.cmd_open
                        }

  def cmd_show(self, file_name):
    with open(str(file_name)) as f:
      self.vimedit.set_edit_text(f.read())
    self.vimedit.initialized = True
    return

  def cmd_open(self, *args):
    assert(args[0] == 'contacts')
    #contacts   = VimText(caption=('VimEdit', u'eZchat\n\n'))
    #contacts_f = urwid.Filler(contacts, valign = 'top')
    def contact_list(user_ids):
      contacts = [urwid.Text("contacts")]
      for user_id in user_ids:
        on  = urwid.Text(("online",u"ON"))
        off = urwid.Text(("offline", u"OFF"))
        contacts += [urwid.Columns([urwid.CheckBox(user_id), off])]
      return VimListBox(urwid.SimpleListWalker(contacts))

    lst = contact_list(["Alice", "Bob"])
    #lst_f = urwid.Filler(lst, valign = 'top')
    ez_cli.top.open_box(lst, 50)
    #ez_cli.top.open_box(contacts_f)
    return

  def cmd_close(self):
    ez_cli.top.close_box()
    #urwid.emit_signal(self, 'exit_ez_chat')
    return

  def tab_completion(self):
    cmd = self.get_edit_text()[1:]
    matches = [key for key in self.command_dict if key.startswith(cmd)]
    if len(matches) == 1:
      self.set_edit_text(':' + matches[0] + ' ')
      p = self.edit_pos
      p = move_next_char(self.edit_text, len(self.edit_text), p)
      self.set_edit_pos(p)
    else:
      print '\n'
      print ' '.join(matches)
    return

  def evaluate_command(self):
    try:
      command = self.get_edit_text()[1:]
      cmd_and_args = command.split()
      try:
        self.command_dict[cmd_and_args[0]](*cmd_and_args[1:])
        urwid.emit_signal(self, 'command_line_exit', self, '')
      except KeyError:
        print '\n'
        print 'Command not known'
      except TypeError as e:
        print '\n'
        print str(e)
        print self.command_dict[cmd_and_args[0]].__doc__
    except IndexError:
      urwid.emit_signal(self, 'command_line_exit', self, '')
      return

  def keypress(self, size, key):
    p = self.edit_pos
    if key == 'esc':
      urwid.emit_signal(self, 'command_line_exit', self, '')
      return
    elif key == 'enter':
      self.evaluate_command()
      return
    elif key == 'tab':
      self.tab_completion()
    # do not allow to delete `:`
    elif key != 'backspace' or p > 1:
      urwid.Edit.keypress(self, size, key)


class VimText(urwid.Edit):
  def __init__(self, *args, **kwargs):
    urwid.Edit.__init__(self, *args, **kwargs)
    self.command_dict = {'h' : self.cmd_move_left,
                         'l' : self.cmd_move_right,
                         'j' : self.cmd_move_down,
                         'k' : self.cmd_move_up,
                         'down' : self.cmd_move_down,
                         'up' : self.cmd_move_up,
                         'left' : self.cmd_move_left,
                         'right' : self.cmd_move_right,
                        }

  def cmd_move_left(self):
    p = move_prev_char(self.edit_text,0,self.p)
    self.set_edit_pos(p)

  def cmd_move_right(self):
    p = move_next_char(self.edit_text,self.p,len(self.edit_text))
    self.set_edit_pos(p)

  def cmd_move_down(self, shift=1):
    #self.highlight = None
    x, y = self.get_cursor_coords((self.maxcol,))
    pref_col = self.get_pref_col((self.maxcol,))
    y += shift
    # ?
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

    # send message
    if key == 'enter':
      return

    # execute commands
    elif key in self.command_dict:
      try:
        self.command_dict[key]()
      except KeyError:
        pass

    elif key == 'esc':
      self.set_edit_text("esc")
      ez_cli.top.close_box()
      return

    else:
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
    #if not self._delete_highlighted():
    self.set_edit_text(self.edit_text[:p] + self.edit_text[self.edit_pos + 1:])
    self.set_edit_pos(p)
    return

  def cmd_delete(self):
    if self.last_key is None and self.double_press:
      text = self.get_edit_text()
      x, y = self.get_cursor_coords((self.maxcol,))
      text = text.split('\n')
      text.pop(y-2)
      text = '\n'.join(text)
      self.set_edit_text(text)

  def cmd_insert(self):
    self.mode = VimEdit.insert_mode
    urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
    return

  def cmd_append(self):
    self.cmd_insert()
    if self.p >= self.maxcol: return
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

  def cmd_move_left(self):
    p = move_prev_char(self.edit_text,0,self.p)
    self.set_edit_pos(p)

  def cmd_move_right(self):
    p = move_next_char(self.edit_text,self.p,len(self.edit_text))
    self.set_edit_pos(p)

  def cmd_move_down(self, shift=1):
    #self.highlight = None
    x, y = self.get_cursor_coords((self.maxcol,))
    pref_col = self.get_pref_col((self.maxcol,))
    y += shift
    # ?
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
    elif key == 'esc':
      self.last_key = key
      self.mode = VimEdit.command_mode
      urwid.emit_signal(self, 'command_mode', self, 'command mode')
      p = move_prev_char(self.edit_text, 0, self.p)
      self.set_edit_pos(p)

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
    self.vimedit.mode = VimEdit.insert_mode
    self.commandline   = VimCommandLine(self.vimedit, u'')
    self.commandline.set_edit_text(u'insert mode')
    self.button        = VimButton(u'Exit')
    self.vimedit_f     = urwid.Filler(self.vimedit, valign = 'top')
    self.commandline_f = urwid.Filler(self.commandline, valign = 'bottom')

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
    self.top.open_box(self.vimedit_f, 100)
    self.top_f = urwid.Filler(self.top, 'top', 20)

    urwid.Frame.__init__(self, self.top_f, footer=self.commandline)

    urwid.connect_signal(self.vimedit, 'done', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'insert_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_line', self.command_line_mode)
    urwid.connect_signal(self.commandline, 'command_line_exit',
                         self.command_line_exit)
    urwid.connect_signal(self.commandline, 'exit_ez_chat', self.exit)
    signal.signal(signal.SIGINT, self.exit)
    self.commandline.cmd_show('logo')

  def mode_notifier(self, edit, new_edit_text):
    self.commandline.set_edit_text(str(new_edit_text))

  def command_line_mode(self, edit, new_edit_text):
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

ez_cli = ez_cli_urwid()
palette = [
    ('online', 'light green', 'dark green'),
    ('offline', 'dark red', 'light red'),
    ]
loop = urwid.MainLoop(ez_cli, palette)

def received_output(data):
  ez_cli.vimedit.set_edit_text(ez_cli.vimedit.get_edit_text() + data)

write_fd = loop.watch_pipe(received_output)
proc = subprocess.Popen(
    ['python', '-u', run_me, sys.argv[1]],
    stdout=write_fd,
    close_fds=True)

loop.run()
