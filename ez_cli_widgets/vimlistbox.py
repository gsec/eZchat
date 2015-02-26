#==============================================================================#
#                                  VimListBox                                  #
#==============================================================================#

#============#
#  Includes  #
#============#

import urwid

#====================#
#  Class Definition  #
#====================#

class VimListBox(urwid.ListBox):

  signals = ['close_box']

  def __init__(self, *args, **kwargs):
    urwid.ListBox.__init__(self, *args, **kwargs)
    self.command_dict = {'j': self.cmd_move_down,
                         'k': self.cmd_move_up,
                         'down': self.cmd_move_down,
                         'up': self.cmd_move_up,
                         'q': self.cmd_close_box,
                         # Blocking left & right arrow key.
                         'left': self.cmd_unhandled,
                         'right': self.cmd_unhandled}

  def cmd_unhandled(self, *args):
    pass

  def cmd_move_up(self, size):
    urwid.ListBox.keypress(self, size, 'up')

  def cmd_move_down(self, size):
    urwid.ListBox.keypress(self, size, 'down')

  def cmd_close_box(self, *args):
    urwid.emit_signal(self, 'close_box')

  def keypress(self, size, key):
    try:
      return self.command_dict[key](size)
    except KeyError:
      return urwid.ListBox.keypress(self, size, key)
