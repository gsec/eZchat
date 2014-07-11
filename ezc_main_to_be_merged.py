import sys, os, time
from PyQt4 import QtCore, QtGui
from ezc_ui import Ui_Form
from client import *
import Queue

class MyForm(QtGui.QMainWindow):

  """Docstring for MyForm. """

  def __init__(self, parent = None):
    """@todo: to be defined1.

    :parent: @todo

    """
    QtGui.QMainWindow.__init__(self, parent)
    self.ui = Ui_Form()
    self.ui.setupUi(self)
    QtCore.QObject.connect( self.ui.OpenFile, QtCore.SIGNAL("clicked()"),
                            self.file_dialog )
    QtCore.QObject.connect( self.ui.textIn, QtCore.SIGNAL("returnPressed()"),
                            self.copyInToOut )
    QtCore.QObject.connect( self.ui.close, QtCore.SIGNAL("clicked()"),
                            self.shutdown )
    self.client = client()
    # start threading process
    self.client.start()
    self.client.commandQueue.put(ClientCommand(ClientCommand.connect, ("localhost",2468)))
    #reply = self.client.replyQueue.get(True)
    #print(reply.replyType, reply.data)
    #reply = self.client.replyQueue.get(True)
    #print(reply.replyType, reply.data)
    self.update_timer()
    #client.commandQueue.put(ClientCommand(ClientCommand.close))

  def file_dialog(self):
    """@todo: Docstring for file_dialog.
    :returns: @todo

    """
    #fd = QtGui.QFileDialog(self)
    #plik = open(fd.getOpenFileName()).read()
    #self.ui.textOut.setText(plik)
    self.client.commandQueue.put(ClientCommand(ClientCommand.send, 'hello'))
    #reply = self.client.replyQueue.get(True)
    #print(reply.replyType, reply.data)
    #self.client.commandQueue.put(ClientCommand(ClientCommand.receive))


  def copyInToOut(self):
    if self.ui.textIn.text():
      # the cast into str turned out to be mandatory as the data is transformed
      # into a c struct binary data
      msg = str(self.ui.textIn.text())
      self.client.commandQueue.put(ClientCommand(ClientCommand.send, msg))

  def update_timer(self):
    self.client_reply_timer = QtCore.QTimer(self)
    self.client_reply_timer.timeout.connect(self.on_client_reply_timer)
    self.client_reply_timer.start(100)

  def on_client_reply_timer(self):
    """
    Whenever client_reply_timer timesout on_client_reply_timer is called,
    allowing to check if messages have been sent to the client
    """
    # If data has been sent to the client readable is active
    try:
      readable, _, _ = select.select([self.client.client_socket], [], [], 0)
      read = bool(readable)
    except socket.error:
      pass
    if read:
      self.client.commandQueue.put(ClientCommand(ClientCommand.receive))
    try:
      reply = self.client.replyQueue.get(block=False)
      status = "success" if reply.replyType == ClientReply.success else "ERROR"
      self.log('Client reply %s: %s' % (status, reply.data))
    except Queue.Empty:
      pass

  def log(self, msg):
    timestamp = '[%010.3f]' % time.clock()
    self.ui.textOut.append(timestamp + ' ' + str(msg))

  def shutdown(self):
    self.client.shutdown()

if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  myapp = MyForm()
  myapp.show()
  sys.exit(app.exec_())

