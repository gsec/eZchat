#==============================================================================#
#                                 ez_dialog.py                                 #
#==============================================================================#

import urwid

class DialogExit(Exception):
    pass

class DialogDisplay(urwid.Frame):

    signals = ['close']

    def __init__(self, text, height, width, body=None):
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
            self.frame.header = urwid.Pile([urwid.Text(text),
                                           urwid.Divider()])
        w = self.frame

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
        raise DialogExit(button.exitcode)

class DialogPopUp(urwid.PopUpLauncher):
    def __init__(self):
        self.__super.__init__(urwid.Text("", 'center'))
        #urwid.connect_signal(self.original_widget, 'click',
                             #lambda button: self.open_pop_up())

    def create_pop_up(self):
        text = 'accept'
        height = 20
        width = 20
        DD = DialogDisplay(text, height, width)
        #DDP = urwid.Padding(DD, 'center', width)
        #DDP = urwid.Filler(DDP, 'middle', height)
        #DDP = urwid.AttrWrap(DDP, 'border')
        buttons = [("Yes", 0), ("No", 1)]

        l = []
        for name, exitcode in buttons:
            b = urwid.Button(name, DialogDisplay.button_press)
            b.exitcode = exitcode
            b = urwid.AttrWrap(b, 'selectable', 'focus')
            l.append(b)
        DD.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        DD.frame.footer = urwid.Pile([urwid.Divider(), DD.buttons],
                                     focus_item=1)

        urwid.connect_signal(DD, 'close',
                             lambda button: self.close_pop_up())
        return DD

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

  fill = urwid.Filler(urwid.Padding(DialogPopUp(), 'center', 15))
  loop = urwid.MainLoop(fill, palette, pop_ups=True)
  loop.run()

