import urwid

class ItemWidget(urwid.WidgetWrap):
  def __init__(self, id, description):
    self.id = id+1
    self.content = "Item %s: %s ..." % (str(id), description[:20])
    self.item = [
          ('fixed', 15, urwid.Padding(urwid.AttrWrap(
            urwid.Text('item %s' % str(id)), 'body', 'focus'), left=2)),
          urwid.AttrWrap(urwid.Text('%s' % description), 'body', 'focus'),
        ]
    w = urwid.Columns(self.item)
    self.__super.__init__(w)

  def selectable(self):
    """
    Make a list selectable, not scroll in down-key.
    """
    return True

  def keypress(self, size, key):
    """
    Catches the keysstrokes => yolo vim
    """
    if key == 'j':
      key = 'down'
    if key == 'k':
      key = 'up'
    return key

def main():
  palette = [
        ('body', 'dark cyan', '', 'standout'),
        ('focus', 'dark red', '', 'standout'),
        ('head', 'light red', 'black'),
      ]

  options = ['Chat', 'Preferences', 'Users', 'Network', 'look down for help!']

  def keystroke(input):
    if input in ('q', 'Q'):
      raise urwid.ExitMainLoop()
    if input == 'h':
      focus = ''
      view.set_header(urwid.AttrWrap(urwid.Text('unselected'), 'head'))

    if input is 'l':
      focus = listbox.get_focus()[0].content
      view.set_header(urwid.AttrWrap(urwid.Text(
          'selected: %s' % str(focus)), 'head'))

  items = []
  for i,n in enumerate(options):
    items.append(ItemWidget(i, n))

  #div = urwid.Divider()
  indicator = urwid.AttrMap(urwid.Text('selected: '), 'head')
  listbox = urwid.ListBox(urwid.SimpleListWalker(items))
  info = urwid.Text(
  """Use 'h,j' to move, 'l,h' to select/deselect and 'q' to exit."""
  )
  view = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=indicator,
      footer=info)
  #pile = urwid.Pile([view, div, info ])
  #top = urwid.Filler(pile, valign='top')

  loop = urwid.MainLoop(view, palette, unhandled_input=keystroke)
  loop.run()

if __name__ == '__main__':
  main()
