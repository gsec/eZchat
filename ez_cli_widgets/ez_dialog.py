#==============================================================================#
#                                 ez_dialog.py                                 #
#==============================================================================#

import urwid

class DialogExit(Exception):
    pass

class DialogDisplay(urwid.Frame):

    signals = ['close']

    def __init__(self, height, width, text=None, body=None):
        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.body = body
        if body is None:
            # fill space with nothing
            body = urwid.Filler(urwid.Divider(), 'top')

        self.frame = urwid.Frame(body, focus_part='footer')
        if text is not None:
            self.frame.header = urwid.Pile([urwid.Text(text, 'center'),
                                           urwid.Divider()])
        w = self.frame

        yes_button = urwid.Button("Yes")
        urwid.connect_signal(yes_button, 'click', lambda button:
                             self._emit("close"))
        yes_button = urwid.AttrWrap(yes_button, 'selectable', 'focus')

        no_button = urwid.Button("No")
        urwid.connect_signal(no_button, 'click', lambda button:
                             self._emit("close"))
        no_button = urwid.AttrWrap(no_button, 'selectable', 'focus')

        buttons = urwid.GridFlow([yes_button, no_button], 10, 3, 1, 'center')

        w.footer = buttons
        #self.frame.footer = urwid.Pile([urwid.Divider(), no_button],
                                       #focus_item=1)

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
    def __init__(self, button_text='', text=None):
      self.text = text
      self.__super.__init__(urwid.Button(button_text))
      urwid.connect_signal(self.original_widget, 'click',
                           lambda button: self.open_pop_up())

    def create_pop_up(self):
        height = 20
        width = 20
        DD = DialogDisplay(height, width, text=self.text)
        DDP = urwid.Padding(DD, 'center', width)
        DDP = urwid.Filler(DDP, 'middle', height)
        DDP = urwid.AttrWrap(DDP, 'border')

        urwid.connect_signal(DD, 'close',
                             lambda button: self.close_pop_up())
        return DDP

    def get_pop_up_parameters(self):
        return {'left': 0, 'top': 1, 'overlay_width': 32, 'overlay_height': 7}

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
