# encoding=utf-8 ==============================================================#
#                                  ez_cli.py                                   #
#==============================================================================#

import urwid
from urwid.util import move_next_char, move_prev_char
from urwid.command_map import (command_map, CURSOR_LEFT, CURSOR_RIGHT,
    CURSOR_UP, CURSOR_DOWN, CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT)

import signal
import ez_p2p as ep

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
#                                VimCommandLine                                #
#==============================================================================#

class VimCommandLine(urwid.Edit):
  """Evaluates commands that are typed in the lowest line of the CLI."""
  signals = ['command_line_exit', 'exit_ez_chat']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, *args, **kwargs):
    urwid.Edit.__init__(self, *args, **kwargs)
    self.client = ep.client('test')
    self.command_dict = {"close" : self.client.cmd_close,
                         "users" : self.client.cmd_users,
                         "ping" : self.client.cmd_ping,
                         "add" : self.client.cmd_add,
                         "servermode" : self.client.cmd_servermode,
                         "bg" : self.client.cmd_bg,
                         "sync" : self.client.cmd_sync,
                         "ips" : self.client.cmd_ips,
                         "key" : self.client.cmd_key,
                         "verify" : self.client.cmd_verify,
                         "send" : self.client.cmd_send,
                         "quit" : self.cmd_close,
                         "q" : self.cmd_close
                        }

  def cmd_close(self):
    urwid.emit_signal(self, 'exit_ez_chat')

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

  def evaluate_command(self):
    try:
      command = self.get_edit_text()[1:]
      cmd_and_args = command.split()
      try:
        self.command_dict[cmd_and_args[0]](*cmd_and_args[1:])
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
    self.vimedit       = VimEdit(caption = ('VimEdit', u"eZchat\n\n"),
                            multiline = True)
    self.vimedit.mode = VimEdit.insert_mode
    self.commandline   = VimCommandLine(u'')
    self.commandline.set_edit_text(u'insert mode')
    self.button        = VimButton(u'Exit')
    self.vimedit_f     = urwid.Filler(self.vimedit, valign = 'top')
    self.commandline_f = urwid.Filler(self.commandline, valign = 'bottom')

    urwid.Frame.__init__(self, self.vimedit_f, footer=self.commandline)

    urwid.connect_signal(self.vimedit, 'done', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'insert_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_line', self.command_line_mode)
    urwid.connect_signal(self.commandline, 'command_line_exit',
                         self.command_line_exit)
    urwid.connect_signal(self.commandline, 'exit_ez_chat', self.exit)
    signal.signal(signal.SIGINT, self.exit)

  def mode_notifier(self, edit, new_edit_text):
    self.commandline.set_edit_text(u"%s" % new_edit_text)

  def command_line_mode(self, edit, new_edit_text):
    self.commandline.set_edit_text(u":")
    self.commandline.set_edit_pos(1)
    self.set_focus('footer')

  def command_line_exit(self, edit, new_edit_text):
    self.commandline.set_edit_text(u"command mode")
    self.set_focus('body')

  def exit(self, *args):
    raise urwid.ExitMainLoop()

#==============================================================================#
#                               GLOBAL INSTANCES                               #
#==============================================================================#

ez_cli = ez_cli_urwid()
urwid.MainLoop(ez_cli).run()
