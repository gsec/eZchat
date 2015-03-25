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

class VimMsgBox(urwid.Frame):
  """
  Prototype for our message box. VimMsgBox is max unselectable. Thus no keys
  will ever get captured directly
  """

  signals = ['exit_msgbox', 'status_update', 'close_box', 'keypress']

  body_contents = {}
  selected_content = None

  def __init__(self, logo_file=None, divider=True, *args, **kwargs):
    self.display_logo(logo_file, divider)


# TODO: JNicL No Commands needed Di 14 Okt 2014 00:03:09 CEST
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

    content_id = 'default_body'
    self.slw = self.construct_walker(content, content_id=content_id,
                                     divider=divider)
    super(VimMsgBox, self).__init__(urwid.ListBox(self.slw))
    self.selected_content = content_id
    self.set_header([''])

  def construct_walker(self, content, content_id='', divider=True):
    """
    Constructs a new body for vimmsgbox where the messages are displayed as
    plain text. Different bodys are identified via the header message and can be
    changed, tabbed via change_body, tab_body respectively.

    :content: List of strings. Each line is represented as a new line in the
              message box.

    :content_id: Internal identifier for the body

    :divider: Use divider to separate items in the SimpleFocusListWalker
    """
    slw = []
    for item in content[:-1]:
      if divider:
        slw.extend([urwid.Text(item), urwid.Divider()])
      else:
        slw.extend([urwid.Text(item)])
    slw.append(urwid.Text(content[-1]))
    self.body_contents[content_id] = slw
    slw = urwid.SimpleFocusListWalker([urwid.AttrMap(w,
                                       None, 'reveal focus') for w in slw])
    return slw

  def set_active_tab(self, pos):
    if hasattr(self, 'header'):
      header = [u[0].original_widget.get_text()[0]
                for u in self.header.contents]
      self.set_header(header, active=pos)

  def append_tab(self, text, position=-1, default_pos_one=True):
    """
    Appends a new tab to the header.
    """
    # check if a specific tab is selected
    if self.selected_content:
      active = self.body_contents.keys().index(self.selected_content)
    else:
      active = -1

    header = [u[0].original_widget.get_text()[0]
              for u in self.header.contents]
    if position >= 0 and position <= len(header):
      if default_pos_one and position == 0:
        header = [header[0], text] + header[1:]
      else:
        header = header[:position] + [text] + header[position:]
    else:
      raise Exception('Tab position not in possible range. '
                      'Header length: ' + str(len(header)) + ' ' +
                      'Position: '  + str(position))
    self.set_header(header, active=active)

  def change_content(self, content_id):
    """
    `Tabs` from one content_id to another.
    """
    if content_id not in self.body_contents:
      urwid.emit_signal(self, 'status_update', 'Error: Content ' +
                        str(content_id) + ' does not exist.')
      return
    content = self.body_contents[content_id]
    self.slw[:] = content
    self.selected_content = content_id

  def tab_body(self, dir=1, default_pos_one=True):
    """
    Changes which body is currently in use and highlights the associated item
    in the header.
    """
    assert(dir == 1 or dir == -1)
    pos = self.body_contents.keys().index(self.selected_content)
    pos += 1*dir
    pos = pos % len(self.body_contents)

    # after tabbing do not land on position 0 if not allowed
    if default_pos_one is True and pos == 0:
      pos = 1
    self.change_content(self.body_contents.keys()[pos])
    self.set_active_tab(pos)

  def cmd_unhandled(self, *args):
    pass

  def set_header(self, texts, active=-1):
    """
    Sets the appearance of the header of the msgbox. Used to determine which
    usertabs are selected.

    :texts: List of strings

    :active: Displays the selected element in texts as bold
    """
    if active >= 0 and active < len(texts):
      texts[active] = ('bold', texts[active])

    texts = map(urwid.Text, texts)
    shadowed_texts = map(lambda x: urwid.AttrWrap(x, 'shadow'), texts)
    header = urwid.Columns(shadowed_texts)
    self.header = header

  def redraw(self):
    self.slw[:] = self.body_contents[self.selected_content]

  def update_content(self, content, content_id='default_body'):
    """
    Update the content of the message box.

    :content: Content should be string.

    :content_id: tab to which the content is appended
    """
    if self.display_logo:
      self.cmd_exit_msgbox()

    if content is not None:
      content_attr = urwid.AttrMap(urwid.Text(content), None, 'reveal focus')
    if content_id not in self.body_contents:
      if content is not None:
        self.body_contents[content_id] = [content_attr]
      else:
        self.body_contents[content_id] = []

      tab_position = self.body_contents.keys().index(content_id)
      if type(content_id) is tuple:
        new_content_id = '|'.join(content_id)
        self.append_tab(new_content_id, tab_position)
      elif type(content_id) is str:
        self.append_tab(content_id, tab_position)
      else:
        raise TypeError('Type: ' + type(content_id) +
                        ' not supported in update content.')
    else:
      if content is not None:
        self.body_contents[content_id].append(content_attr)

    if content_id == self.selected_content:
      self.redraw()
      self.update_focus()

  def update_focus(self):
    """
    Scrolls down to the most recent message.
    """
    # get the number of item
    focus = len(self.slw) - 1
    # set the new foucs to the last item
    self.slw.set_focus(focus)

  def clear_msgbox(self, content_id='default_body'):
    # Deleting the content of the ListWalker. Create a new Walker wouldn't
    # work unless you ListBox.__init__ again.
    # iterating over self.body and deleting elements in self.body does update
    # self.body. As a result, not all rows are deleted -> range(len(@)) does
    # not share the same memory and is fixed -> iteration deletes all elements
    # in self.body

    # select the body of the active body
    for row in range(len(self.body_contents[content_id])):
      self.body_contents[content_id].pop(-1)
    self.redraw()

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

if __name__ == "__main__":
  msgbox = VimMsgBox()

  palette = [('body', 'black', 'light gray', 'standout')]
  loop = urwid.MainLoop(msgbox, palette, pop_ups=True)
  loop.run()
