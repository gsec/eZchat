#==============================================================================#
#                                   VimEdit                                    #
#==============================================================================#

#============#
#  Includes  #
#============#

import urwid
from urwid.util import move_next_char, move_prev_char
from urwid.command_map import CURSOR_LEFT, CURSOR_RIGHT, CURSOR_UP, CURSOR_DOWN

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             os.pardir))
import ez_preferences as ep
import ez_client as cl

from ez_process import p2pReply, p2pCommand

#====================#
#  Class Definition  #
#====================#

class VimEdit(urwid.Edit):
  """
  VimEdit encapsulates all vim-like edit functionality.

  VimEdit allows for customization such as custom key bindings and modes.
  Preferences are defined in ez_peferences.py (soon .rc file) and are
  initialized by invoking :py:meth:`ez_preferences.init_cli_preferences` which
  must be done before the VimEdit instance.

  """
  signals = ['done', 'insert_mode', 'command_mode', 'visual_mode',
             'command_line', 'status_update', 'keypress', 'return_contacts',
             'evaluate_command']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, **kwargs):
    urwid.Edit.__init__(self, **kwargs)
    self.mode = VimEdit.insert_mode
    self.last_key = None
    self.double_press = False
    self.initialized = None

    commands = {'cli_enter_cmdline': self.cmd_enter_cmdline,
                'cli_delete_one': self.cmd_delete_one,
                'cli_delete': self.cmd_delete,
                'cli_insert': self.cmd_insert,
                'cli_append': self.cmd_append,
                'cli_delete': self.cmd_delete,
                'cli_newline_low': self.cmd_newline_low,
                'cli_newline_high': self.cmd_newline_high,
                'cli_move_left': self.cmd_move_left,
                'cli_move_right': self.cmd_move_right,
                'cli_move_down': self.cmd_move_down,
                'cli_move_up': self.cmd_move_up,
                'cli_scroll_msg_up': self.cmd_scroll_msg_up,
                'cli_scroll_msg_down': self.cmd_scroll_msg_down,
                'cli_evaluate_command': self.cmd_evaluate_command}

    self.command_dict = {}
    for cmd in ep.cli_define_command:
      cmd_str = ep.cli_define_command[cmd]
      commands[cmd] = lambda: self.cmd_evaluate_command(cmd_str)

    for cmd in commands:
      if cmd not in ep.cli_command_dict:
        cl.cl.enqueue('shutdown')
      if cmd in ep.cli_command_dict:
        for mapped_key in ep.cli_command_dict[cmd]:
          self.command_dict[mapped_key] = commands[cmd]

  def cmd_evaluate_command(self, cmd):
    urwid.emit_signal(self, 'evaluate_command', cmd)

  def cmd_scroll_msg_up(self):
    urwid.emit_signal(self, 'keypress', (self.maxcol, 20), 'up')

  def cmd_scroll_msg_down(self):
    urwid.emit_signal(self, 'keypress', (self.maxcol, 20), 'down')

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
    if self.p == 0:
      return pressed
    p = move_prev_char(self.edit_text, 0, self.p)
    self.set_edit_pos(p)

  def cmd_move_right(self):
    if self.p >= len(self.edit_text):
      return CURSOR_RIGHT
    p = move_next_char(self.edit_text, self.p, len(self.edit_text))
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

  def cmd_send_msg(self, contacts):
    msg = self.get_edit_text()
    for contact in contacts:
      cl.cl.cmd_send_msg(contact, msg)
      urwid.emit_signal(self, 'status_update', contact)
    self.set_edit_text('')

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
        urwid.emit_signal(self, 'return_contacts')
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
      self.cmd_move_left(pressed=key)

    elif self.mode == VimEdit.insert_mode:
      urwid.Edit.keypress(self, size, key)
