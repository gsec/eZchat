#==============================================================================#
#                                VimStatusLine                                 #
#==============================================================================#

#============#
#  Includes  #
#============#

import urwid

#====================#
#  Class Definition  #
#====================#

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
