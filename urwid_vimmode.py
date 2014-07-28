import urwid

from urwid.util import move_next_char, move_prev_char
from urwid.command_map import (command_map, CURSOR_LEFT, CURSOR_RIGHT,
    CURSOR_UP, CURSOR_DOWN, CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT)

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    txt.set_text(repr(key))

class VimEdit(urwid.Edit):
  _metaclass_ = urwid.signals.MetaSignals
  signals = ['done', 'insert_mode', 'command_mode', 'visual_mode']
  insert_mode, command_mode, visual_mode = range(3)

  def __init__(self, **kwargs):

    self.__super.__init__(**kwargs)
    self.mode = VimEdit.insert_mode
    self.last_key = None

  def keypress(self, size, key):

    (maxcol,) = size
    p = self.edit_pos
    if key == 'enter':
      if self.multiline and self.mode == VimEdit.insert_mode:
        key = "\n"
        self.insert_text(key)
      else:
        urwid.emit_signal(self, 'done', self, self.get_edit_text())
        super(VimEdit, self).set_edit_text('')
      return
# command mode
    elif key == 'esc':
      self.last_key = key
      self.mode = VimEdit.command_mode
      urwid.emit_signal(self, 'command_mode', self, 'command mode')
      if p==0: return key
      p = move_prev_char(self.edit_text,0,p)
      self.set_edit_pos(p)
    elif key == 'd' and self.mode == VimEdit.command_mode:
      if self.last_key == 'd':
        super(VimEdit, self).set_edit_text('')
      else:
        self.last_key = 'd'
      return

# insert modes
    elif key == 'i' and self.mode == VimEdit.command_mode:
      self.last_key = key
      self.mode = VimEdit.insert_mode
      urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
      return
    elif key == 'a' and self.mode == VimEdit.command_mode:
      self.last_key = key
      self.mode = VimEdit.insert_mode
      urwid.emit_signal(self, 'insert_mode', self, 'insert mode')
      if p >= len(self.edit_text): return key
      p = move_next_char(self.edit_text,p,len(self.edit_text))
      self.set_edit_pos(p)
      return

# hjkl bindings
    elif key == 'h' and self.mode == VimEdit.command_mode:
      self.last_key = key
      if p==0: return key
      p = move_prev_char(self.edit_text,0,p)
      self.set_edit_pos(p)
    elif key == 'l' and self.mode == VimEdit.command_mode:
      self.last_key = key
      if p >= len(self.edit_text): return key
      p = move_next_char(self.edit_text,p,len(self.edit_text))
      self.set_edit_pos(p)
    elif key in ('j', 'k'):
      self.last_key = key
      self.highlight = None

      x,y = self.get_cursor_coords((maxcol,))
      pref_col = self.get_pref_col((maxcol,))
      assert pref_col is not None

      if key == 'k': y -= 1
      else: y += 1

      if not self.move_cursor_to_coords((maxcol,),pref_col,y):
          return key

    elif self._command_map[key] in (CURSOR_UP, CURSOR_DOWN):
      self.last_key = key
      self.highlight = None

      x,y = self.get_cursor_coords((maxcol,))
      pref_col = self.get_pref_col((maxcol,))
      assert pref_col is not None

      if self._command_map[key] == CURSOR_UP: y -= 1
      else: y += 1

      if not self.move_cursor_to_coords((maxcol,),pref_col,y):
          return key
    elif self.mode == VimEdit.insert_mode:
      self.last_key = key
      super(VimEdit, self).keypress(size, key)



palette = [('VimEdit', 'default,bold', 'default', 'bold'),]
ask = VimEdit(caption = ('VimEdit', u"Vim Mode FTW!\n"), multiline = True)
reply = urwid.Text(u'insert_mode')
button = urwid.Button(u'Exit')
div = urwid.Divider()
pile = urwid.Pile([ask, div, reply, div, button])
top = urwid.Filler(pile, valign='top')
reply.rows

def on_ask_change(edit, new_edit_text):
    reply.set_text(('VimEdit', u"Your msg, %s" % new_edit_text))


def mode_notifier(edit, new_edit_text):
    reply.set_text(('VimEdit', u"%s" % new_edit_text))

def on_exit_clicked(button):
    raise urwid.ExitMainLoop()

urwid.connect_signal(ask, 'done', on_ask_change)
urwid.connect_signal(ask, 'insert_mode', mode_notifier)
urwid.connect_signal(ask, 'command_mode', mode_notifier)
urwid.connect_signal(button, 'click', on_exit_clicked)

urwid.MainLoop(top, palette).run()
