#==============================================================================#
#                                 ez_dialog.py                                 #
#==============================================================================#

import urwid
from vimbutton import VimButton
from types import StringType, ListType

class DialogExit(Exception):
    pass

class DialogDisplay(urwid.Frame):

    signals = ['no', 'yes']

    def __init__(self, height, width, text):
        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        if type(text) is StringType:

          body = urwid.Filler(urwid.Pile([urwid.Text(text, 'center'),
                                         urwid.Divider()]))
        elif type(text) is urwid.Text:
          body = urwid.Filler(urwid.Pile([text, urwid.Divider()]))

        elif type(text) is ListType:
          body = urwid.Filler(urwid.Pile(text + [urwid.Divider()]))

        self.frame = urwid.Frame(body, focus_part='footer')
        w = self.frame

        yes_button = VimButton("Yes")
        urwid.connect_signal(yes_button, 'click', lambda button:
                             self._emit("yes"))
        urwid.connect_signal(yes_button, 'close', lambda:
                             self._emit("no"))
        yes_button = urwid.AttrWrap(yes_button, 'selectable', 'focus')

        no_button = VimButton("No")
        urwid.connect_signal(no_button, 'click', lambda button:
                             self._emit("no"))
        urwid.connect_signal(no_button, 'close', lambda:
                             self._emit("no"))
        no_button = urwid.AttrWrap(no_button, 'selectable', 'focus')

        buttons = urwid.Columns([no_button, yes_button])

        w.footer = buttons

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left', 2), ('fixed right', 2))
        w = urwid.Filler(w, ('fixed top', 1), ('fixed bottom', 1))
        w = urwid.AttrWrap(w, 'body')

        # "shadow" effect
        emptyline = urwid.Text(('border', '  '))
        attr = urwid.AttrWrap(urwid.Filler(emptyline, "top"), 'shadow')

        w = urwid.Columns([w, ('fixed', 2, attr)])

        attr = urwid.AttrWrap(urwid.Text(('border', ' ')), 'shadow')
        super(DialogDisplay, self).__init__(w, footer=attr)

    @staticmethod
    def button_press(button):
      if button.exitcode == 1:
        urwid.emit_signal(button.popup, 'close')
      else:
        raise DialogExit(button.exitcode)

class DialogPopUp(urwid.PopUpLauncher):

  signals = ['update']

  def __init__(self, button_text='', additional_widgets=None, pop_up_text=None,
               success_callback=lambda *args: None):
    self.pop_up_text = pop_up_text
    self.success_callback = success_callback

    button = urwid.Button(button_text)
    if additional_widgets is None:
      self.__super.__init__(button)

    elif type(additional_widgets) is urwid.Text:
      self.__super.__init__(urwid.Pile([button, additional_widgets]))

    elif type(additional_widgets) is ListType:
      self.__super.__init__(urwid.Pile([button] + additional_widgets))

    urwid.connect_signal(button, 'click',
                         lambda button: self.open_pop_up())

  def create_pop_up(self):
      height = 10
      width = 20
      DD = DialogDisplay(height, width, text=self.pop_up_text)

      # no: just close the popup
      urwid.connect_signal(DD, 'no', lambda button: self.close_pop_up())

      # yes: call callback, close popup and update list.
      urwid.connect_signal(DD, 'yes', self.success_callback)
      urwid.connect_signal(DD, 'yes', lambda button: self.close_pop_up())
      urwid.connect_signal(DD, 'yes', lambda button: self._emit('update'))

      DD = urwid.Padding(DD, 'center', width)
      DD = urwid.Filler(DD, 'middle', height)

      return DD

  def get_pop_up_parameters(self):
      return {'left': 0, 'top': 1, 'overlay_width': 32, 'overlay_height': 5}

if __name__ == "__main__":
  palette = [('body', 'black', 'light gray', 'standout'),
             ('border', 'black', 'dark blue'),
             ('shadow', 'white', 'black'),
             ('selectable', 'black', 'dark cyan'),
             ('focus', 'white', 'dark blue', 'bold'),
             ('focustext', 'light gray', 'dark blue'),
             ('popbg', 'white', 'dark blue')]

  fill = urwid.Filler(urwid.Padding(DialogPopUp('push me'), 'center', 15))
  loop = urwid.MainLoop(fill, palette, pop_ups=True)
  loop.run()
