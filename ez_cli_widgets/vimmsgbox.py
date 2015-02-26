#==============================================================================#
#                                  VimMsgBox                                   #
#==============================================================================#

#============#
#  Includes  #
#============#

import urwid

#====================#
#  Class Definition  #
#====================#

class VimMsgBox(urwid.ListBox):
  """Prototype for our message box"""

  signals = ['exit_msgbox', 'status_update', 'close_box', 'keypress']

  def __init__(self, logo_file=None, divider=True, *args, **kwargs):
    self.display_logo(logo_file, divider)

# TODO: JNicL No Commands needed Di 14 Okt 2014 00:03:09 CEST
# VimMsgBox is max unselectable. Thus no keys will ever get captured directly
    self.command_dict = {'j': self.cmd_move_down,
                         'k': self.cmd_move_up,
                         #'down' : self.cmd_exit_msgbox,
                         #'up' : self.cmd_unhandled,
                         'q': self.cmd_close_box,
                         # Blocking left & right arrow key.
                         'left': self.cmd_unhandled,
                         'right': self.cmd_unhandled}

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
        slw.extend([urwid.Text(item), urwid.Divider()])
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

  def cmd_close_box(self, *args):
    urwid.emit_signal(self, 'close_box')

  def keypress(self, size, key):
    # press any key to skip logo
    if self.logo_displayed:
      self.cmd_exit_msgbox()

      # The idea here is that the first keypress is already processed which
      # to my opinion feels better.
      urwid.emit_signal(self, 'keypress', (size[0],), key)
      return
    try:
      return self.command_dict[key](size)
    except KeyError:
      return urwid.ListBox.keypress(self, size, key)


