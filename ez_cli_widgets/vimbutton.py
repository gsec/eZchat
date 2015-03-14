#==============================================================================#
#                                  VimButton                                   #
#==============================================================================#

import urwid

class VimButton(urwid.Button):

  signals = ['close']

  def __init__(self, *args, **kwargs):
    urwid.Button.__init__(self, *args, **kwargs)
    self.command_dict = {'j': self.cmd_move_down,
                         'k': self.cmd_move_up,
                         'h': self.cmd_move_left,
                         'l': self.cmd_move_right,
                         'q': self.cmd_close}

  def cmd_move_up(self, size):
    return urwid.Button.keypress(self, size, 'up')

  def cmd_move_down(self, size):
    return urwid.Button.keypress(self, size, 'down')

  def cmd_move_left(self, size):
    return urwid.Button.keypress(self, size, 'left')

  def cmd_move_right(self, size):
    return urwid.Button.keypress(self, size, 'right')

  def cmd_close(self, *args):
    urwid.emit_signal(self, 'close')

  def keypress(self, size, key):
    try:
      return self.command_dict[key](size)
    except KeyError:
      return urwid.Button.keypress(self, size, key)
