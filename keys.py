from collections import namedtuple
import urwid

#==============================================================================#
#                               Global Instance                                #
#==============================================================================#
VimModes = namedtuple('Mode', ['normal', 'insert', 'command'])
vim_mode = VimModes(0,1,2)
#==============================================================================#
#                                  Keymaps                                     #
#==============================================================================#

class KeyHandler(urwid.Edit):

  def __init__(self):
    #self.size = 10
    self.special_keys = {
                        'h'     :['left',   'h',      'h'],
                        'j'     :['down',   'j',      'j'],
                        'k'     :['up',     'k',      'k'],
                        'l'     :['right',  'l',      'l'],
                        'o'     :[self.o_key,    'o',      'o'],
                        'enter' :['enter',  'enter',  'enter'],
                        'esc'   :[self.esc_n,    self.esc_i,    self.esc_c]
                        }

  def keypress(self, key, mode=vim_mode.normal):
    if key in self.special_keys:
      key_func = self.special_keys[key][mode]
      if type(key_func) is type('STRING'):
        return key_func
      else:
        return key_func(self.size)
    else:
      print('undefined input: let parent handle')
      #return super(KeyHandler, self).keypress(key, self.size)

  def esc_key(mode):
    if mode == vim_mode.normal:
      print 'normalmodeesc'
    if mode == vim_mode.insert:
      print 'instertesc'
    if mode == vim_mode.command:
      print 'commandesc'

  esc_i = lambda : self.esc_key(vim_mode.insert)
  esc_n = lambda : self.esc_key(vim_mode.normal)
  esc_c = lambda : self.esc_key(vim_mode.command)



  def o_key(self, size):
    print 'onlyamock'
    return
