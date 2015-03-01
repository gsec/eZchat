# encoding=utf-8 ==============================================================#
#                                  ez_cli.py                                   #
#==============================================================================#

import sys
import types
import os
import signal
import subprocess
from time import sleep

from optparse import OptionParser

import urwid
from urwid.command_map import CURSOR_LEFT, CURSOR_RIGHT, CURSOR_UP, CURSOR_DOWN

from ez_process import p2pReply, p2pCommand

import ez_preferences as ep
import ez_client as cl
import ez_pipe as pipe

from ez_cli_widgets import VimMsgBox, VimEdit, VimCommandLine, VimStatusline

#==============================================================================#
#                                 ez_cli_urwid                                 #
#==============================================================================#

class ez_cli_urwid(urwid.Frame):
  """
  Main CLI Frame.
  Here we build the main frame out of the widgets.
  The base layout is as follows:
        +-------------------+
        |                   |   \
        | chatlog: xxx      |    \
        | chatlog: yyy      |    /
        |                   |   /
        +-------------------+
        |                   |  \
        | >>Input widget<<  |    body
        |                   |  /
        =====================
        | StatusLine        |  \
        +-------------------+    footer
        | CommandLine       |  /
        +-------------------+
  """

  def __init__(self, name='', logging=False, *args, **kwargs):
    self.vimedit = VimEdit(caption=('VimEdit', u'eZchat\n\n'),
                           multiline=True)
    self.commandline = VimCommandLine(self.vimedit, u'')

    if ep.cli_start_in_insertmode:
      self.vimedit.mode = VimEdit.insert_mode
      self.commandline.set_edit_text(u'insert mode')
    else:
      self.vimedit.mode = VimEdit.command_mode
      self.commandline.set_edit_text(u'command mode')

    self.vimedit_f = urwid.Filler(self.vimedit, valign='top')
    self.vimedit_b = urwid.BoxAdapter(self.vimedit_f, ep.cli_edit_height)

    self.vimmsgbox = VimMsgBox(logo_file='misc/logo.txt')

    # combine vimedit and vimmsgbox to vimbox
    self.vimmsgbox_b = urwid.BoxAdapter(self.vimmsgbox, ep.cli_msg_height)
    self.vimbox = urwid.Pile([self.vimmsgbox_b, self.vimedit])
    self.vimbox_f = urwid.Filler(self.vimbox, valign='top')

    if ep.cli_status_height > 0:
      self.statusline = VimStatusline()
      for i in range(ep.cli_status_height-1):
        self.statusline.update_content('')

      self.statusline_b = urwid.BoxAdapter(self.statusline,
                                           ep.cli_status_height)

    if hasattr(self, 'statusline'):
      self.command_and_status = urwid.Pile([self.statusline_b,
                                            self.commandline])
    else:
      self.command_and_status = self.commandline

    focus_map = {'heading': 'focus heading',
                 'options': 'focus options',
                 'line': 'focus line'}

    class HorizontalBoxes(urwid.Columns):
      def __init__(self):
        super(HorizontalBoxes, self).__init__([], dividechars=1)

      def open_box(self, box, weight):
        if self.contents:
          del self.contents[self.focus_position + 1:]

        self.contents.append((urwid.AttrMap(box, 'options', focus_map),
                             self.options('weight', weight)))
        self.focus_position = len(self.contents) - 1

      def close_box(self):
        del self.contents[1]
        self.focus_position = 0

    self.top = HorizontalBoxes()
    self.top.open_box(self.vimbox_f, 100)
    self.top_f = urwid.Filler(self.top, 'top', ep.cli_msg_height +
                              ep.cli_edit_height)

    urwid.Frame.__init__(self, self.top_f, footer=self.command_and_status)

    # vimedit signals
    urwid.connect_signal(self.vimedit, 'done', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'insert_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_mode', self.mode_notifier)
    urwid.connect_signal(self.vimedit, 'command_line', self.command_line_mode)
    urwid.connect_signal(self.vimedit, 'status_update', self.status_update)
    urwid.connect_signal(self.vimedit, 'keypress', self.vimmsgbox.keypress)
    urwid.connect_signal(self.vimedit, 'return_contacts', self.return_contacts)
    urwid.connect_signal(self.vimedit, 'evaluate_command',
                         self.evaluate_command)

    # msgbox signals
    urwid.connect_signal(self.vimmsgbox, 'exit_msgbox', self.exit_msgbox)
    urwid.connect_signal(self.vimmsgbox, 'keypress', self.vimedit.keypress)

    # commandline signals
    urwid.connect_signal(self.commandline, 'command_line_exit',
                         self.command_line_exit)
    urwid.connect_signal(self.commandline, 'status_update', self.status_update)
    urwid.connect_signal(self.commandline, 'exit_ez_chat', self.exit)
    urwid.connect_signal(self.commandline, 'close_box', self.top.close_box)
    urwid.connect_signal(self.commandline, 'open_box', self.top.open_box)
    urwid.connect_signal(self.commandline, 'clear_msgbox',
                         self.vimmsgbox.clear_msgbox)
    urwid.connect_signal(self.commandline, 'msg_update', self.msg_update)

    signal.signal(signal.SIGINT, self.__close__)

    self.name = name
    self.logging = logging
    if self.logging:
      self.logger = open(ep.join(ep.location['log'],
                                 name + '_ez_cli_session.log'), 'w')

  def evaluate_command(self, cmd):
    self.commandline.evaluate_command(cmd)

  def return_contacts(self):
    self.vimedit.cmd_send_msg(self.commandline.get_marked_contacts())

  def status_update(self, content):
    if self.logging:
      self.logger.write(content + '\n')

    if hasattr(self, 'statusline'):
      # update SimpleFocusListWalker
      self.statusline.update_content(content)
      # get the number of item
      focus = len(self.statusline.body) - 1
      # set the new foucs to the last item
      self.statusline.body.set_focus(focus)

  def msg_update(self, content):
    # update SimpleFocusListWalker
    self.vimmsgbox.update_content(content)
    # get the number of item
    focus = len(self.vimmsgbox.body) - 1
    # set the new foucs to the last item
    self.vimmsgbox.body.set_focus(focus)

  def __close__(self, *args):
    self.commandline.cmd_close()
    self.exit()

  def mode_notifier(self, edit, new_edit_text):
    self.commandline.set_edit_text(str(new_edit_text))

  def enter_msgbox(self):
    self.vimbox.set_focus(0)

  def exit_msgbox(self):
    self.vimbox.set_focus(1)

  def command_line_mode(self, edit, new_edit_text):
    if hasattr(self, 'statusline'):
      self.command_and_status.set_focus(1)
    self.commandline.set_edit_text(':')
    self.commandline.set_edit_pos(1)
    self.set_focus('footer')

  def command_line_exit(self, edit, new_edit_text):
    self.commandline.set_edit_text('command mode')
    self.set_focus('body')

  def exit(self, *args):
    cl.cl.cmd_close()
    if self.logging:
      self.logger.close()
    raise urwid.ExitMainLoop()

  def received_output(self, data):
    categories = {p2pReply.success: 'success',
                  p2pReply.error:   'error',
                  p2pReply.msg:     'msg'
                  }
    if 'status' in data.strip():
        try:
          reply = cl.cl.replyQueue.get(block=False)
        except:
          reply = None
        while reply:
          if((reply.replyType == p2pReply.success) or
             (reply.replyType == p2pReply.error)):
            status = ("success" if reply.replyType == p2pReply.success
                      else "ERROR")
            self.status_update(('Client reply %s: %s' % (status, reply.data)))
          elif reply.replyType == p2pReply.msg:
            # decrypt msg and print it on the screen
            if reply.data.recipient == cl.cl.name:
              try:
                self.msg_update((str(reply.data.clear_text())))
              except Exception, e:
                self.status_update("<p>Error: %s</p>" % str(e))

          else:
            # this case should not happen! (if theres something in the queue it
            # must be success,error or msg)
            self.status_update('Client sent unknown status.')
          try:
            reply = cl.cl.replyQueue.get(block=False)
          except:
            reply = None
    else:
      # this case should not happen! (if theres something in the queue, it
      # must be success,error or msg)
      self.status_update('Client sent unknown status.')
    return True

if __name__ == "__main__":

#========================#
#  command line options  #
#========================#
  usage = "usage: %prog [options] name"
  parser = OptionParser(usage)

  parser.add_option("-s", "--script", dest="filename",
                    help="run eZchat with script", metavar="FILE")

  parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages")

  parser.add_option("-l", "--log",
                    action="store_true", dest="logging", default=False,
                    help="log status to .name_eZsession.log")

  (options, args) = parser.parse_args()

  try:
    ep.init_cli_preferences()
    if not len(args) == 1:
      print 'Please give your name as argument'
      sys.exit()
    cl.init_client(args[0], **ep.process_preferences)
    if not options.verbose:
      ep.cli_status_height = 0  # disable statusline
    ez_cli = ez_cli_urwid(name=args[0], logging=options.logging)
  except ValueError, err:
    sys.stderr.write('ERROR: %s\n' % str(err))
    cl.cl.commandQueue.put(p2pCommand('shutdown'))
    sys.exit()

#==============#
#  MAIN LOOPS  #
#==============#

  loop = urwid.MainLoop(ez_cli, ep.palette)
  pipe.pipe = loop.watch_pipe(ez_cli.received_output)

  # start eZchat with script
  if options.filename:
    try:
      with open(options.filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
          ez_cli.commandline.evaluate_command(line.replace('\n', ''))
    except IOError as e:
      ez_cli.status_update("Loading script failed. I/O error({0}): {1}".
                           format(e.errno, e.strerror))
    except:
      print "Unexpected error:", sys.exc_info()[0]
      raise

  loop.run()
  cl.cl.commandQueue.put(p2pCommand('shutdown'))
