#==============================================================================#
#                                  ez_cli.py                                   #
#==============================================================================#

import sys, types
import urwid
from urwid.util import move_next_char, move_prev_char
from urwid.command_map import (command_map, CURSOR_LEFT, CURSOR_RIGHT,
    CURSOR_UP, CURSOR_DOWN, CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT)

import signal
import ez_p2p as ep

import Queue, threading
from thread import start_new_thread


# imports related to the inclusion of the chat client
import client as cl
import subprocess, os
run_me = os.path.join(os.path.dirname(sys.argv[0]), 'client.py')

#==============================================================================#
#                                  VimButton                                   #
#==============================================================================#

class VimButton(urwid.Button):
  insert_mode, command_mode, visual_mode = range(3)

  def keypress(self, size, key):
    if key =='j':
      return 'down'
    elif key == 'k':
      return 'up'
    else:
      super(VimButton, self).keypress(size, key)

#==============================================================================#
#                                VimCommandLine                                #
#==============================================================================#

class VimCommandLine(urwid.Edit, threading.Thread):
  signals = ['command_line_exit', 'exit_ez_chat']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, *args, **kwargs):
    urwid.Edit.__init__(self, *args, **kwargs)
    #start_new_thread(self.client.start,())
    #self.client.start()

  def keypress(self, size, key):
    p = self.edit_pos
    if key == 'esc':
      urwid.emit_signal(self, 'command_line_exit', self, '')
      return
    elif key == 'enter':
      self.evaluate_command()
      #return
    # do not allow to delete :
    elif key != 'backspace' or p > 1:
      super(VimCommandLine, self).keypress(size, key)

  def evaluate_command(self):
    command = self.get_edit_text()[1:]
    cmd_and_args = command.split()
    command_dict = {"close" : cl.cl.cmd_close,
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
                    "send" : cl.cl.cmd_send
                   }
    #self.client.cmd_connect("127.0.0.1", 1234)
    if command == 'q' or command == 'quit':
      urwid.emit_signal(self, 'exit_ez_chat')
    else:
      print "command:", command
      command_dict[cmd_and_args[0]](*cmd_and_args[1:])


#==============================================================================#
#                                   VimEdit                                    #
#==============================================================================#

class VimEdit(urwid.Edit):
  signals = ['done', 'insert_mode', 'command_mode',
             'visual_mode', 'command_line']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, **kwargs):
    urwid.Edit.__init__(self, **kwargs)
    self.mode = VimEdit.insert_mode
    self.last_key = None
    self.double_press = False

  def keypress(self, size, key):
    (maxcol,) = size
    p = self.edit_pos
    if key == self.last_key:
      self.last_key = None
      self.double_press = True
    else:
      self.last_key = key

    if key == 'enter':
      if self.multiline and self.mode == VimEdit.insert_mode:
        key = "\n"
        self.insert_text(key)
      else:
        urwid.emit_signal(self, 'done', self, self.get_edit_text())
        super(VimEdit, self).set_edit_text('')
      return
    elif key == ':' and self.mode == VimEdit.command_mode:
      if self.mode == VimEdit.command_mode:
        urwid.emit_signal(self, 'command_line', self, ':')
        super(VimEdit, self).set_edit_text('')
      return

    # command mode
    elif key == 'esc':
      self.last_key = key
      self.mode = VimEdit.command_mode
      urwid.emit_signal(self, 'command_mode', self, 'command mode')
      if p==0: return key
      p = move_prev_char(self.edit_text,0,p)
      self.set_edit_pos(p)

    # delete modes
    elif key == 'x' and self.mode == VimEdit.command_mode:
      self.pref_col_maxcol = None, None
      p = self.edit_pos
      if not self._delete_highlighted():
        if p == 0: return key
        self.set_edit_text( self.edit_text[:p] +
            self.edit_text[self.edit_pos + 1:] )
        p = move_prev_char(self.edit_text, 0, p)
        self.set_edit_pos( p )

    elif key == 'd' and self.mode == VimEdit.command_mode:
      if self.last_key == None and self.double_press:
        text = self.get_edit_text()
        x,y = self.get_cursor_coords((maxcol,))
        text = text.split('\n')
        text.pop(y-1)
        if len(text) > 0:
          text = [u + '\n' for u in text[:-1]] + [text[-1]]
        else:
          text = ['']
        text = "".join(text)
        super(VimEdit, self).set_edit_text(text)

    # insert modes
    elif key == 'i' and self.mode == VimEdit.command_mode:
      self.mode = VimEdit.insert_mode
      urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
      return

    elif key == 'a' and self.mode == VimEdit.command_mode:
      self.mode = VimEdit.insert_mode
      urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
      if p >= len(self.edit_text): return key
      p = move_next_char(self.edit_text,p,len(self.edit_text))
      self.set_edit_pos(p)
      return

    elif key == 'o' and self.mode == VimEdit.command_mode:
      self.mode = VimEdit.insert_mode
      urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
      x,y = self.get_cursor_coords((maxcol,))
      text = self.get_edit_text()
      text = text.split('\n')
      if len(text) > 1:
        text_last = ['\n'] + [u + '\n' for u in text[y:-1]] + [text[-1]]
      else:
        text_last = ['']
      text = [u + '\n' for u in text[0:y]] + [' '] + text_last

      text = "".join(text)
      super(VimEdit, self).set_edit_text(text)
      self.move_cursor_to_coords((maxcol,), 'left', y + 1)
      return

    # hjkl bindings
    elif key == 'h' and self.mode == VimEdit.command_mode:
      if p==0: return key
      p = move_prev_char(self.edit_text,0,p)
      self.set_edit_pos(p)

    elif key == 'l' and self.mode == VimEdit.command_mode:
      if p >= len(self.edit_text): return key
      p = move_next_char(self.edit_text,p,len(self.edit_text))
      self.set_edit_pos(p)

    elif key in ('j', 'k') and self.mode == VimEdit.command_mode:
      self.highlight = None

      x,y = self.get_cursor_coords((maxcol,))
      pref_col = self.get_pref_col((maxcol,))
      assert pref_col is not None

      if key == 'k': y -= 1
      else: y += 1

      if not self.move_cursor_to_coords((maxcol,),pref_col,y):
        if key =='j':
          return 'down'
        else:
          return 'up'

    elif self._command_map[key] in (CURSOR_UP, CURSOR_DOWN):
      self.highlight = None

      x,y = self.get_cursor_coords((maxcol,))
      pref_col = self.get_pref_col((maxcol,))
      assert pref_col is not None

      if self._command_map[key] == CURSOR_UP: y -= 1
      else: y += 1

      if not self.move_cursor_to_coords((maxcol,),pref_col,y):
        return key

    elif self.mode == VimEdit.insert_mode:
      super(VimEdit, self).keypress(size, key)


#==============================================================================#
#                                 ez_cli_urwid                                 #
#==============================================================================#

class ez_cli_urwid(urwid.Frame):

  def __init__(self, *args, **kwargs):

    self.vimedit      = VimEdit(caption = ('VimEdit', u"Vim Mode FTW!\n"),
                                multiline = True)
    self.vimedit.mode = VimEdit.insert_mode
    self.commandline  = VimCommandLine()

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
    cl.cl.cmd_close()
    raise urwid.ExitMainLoop()


#print "sys.argv[1]:", sys.argv[1]
ez_cli = ez_cli_urwid()
loop = urwid.MainLoop(ez_cli)

def received_output(data):
    ez_cli.vimedit.set_edit_text(ez_cli.vimedit.get_edit_text() + data)

write_fd = loop.watch_pipe(received_output)
proc = subprocess.Popen(
    ['python', '-u', run_me, sys.argv[1], sys.argv[2], sys.argv[3]],
    stdout=write_fd,
    close_fds=True)

loop.run()
