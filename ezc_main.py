#==============================================================================#
#                                   ez_main                                    #
#==============================================================================#

#============#
#  Includes  #
#============#
import sys, os, time

from ez_client import *
import Queue

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

#==============================================================================#
#                                 class ez_Gui                                 #
#==============================================================================#

class ez_Gui(QtGui.QWidget):

  def __init__(self):

    #super(ez_Gui, self).__init__()
    QtGui.QMainWindow.__init__(self)

    # variables
    self.history_path = os.path.join(os.path.dirname(__file__), 'history',
                                     'history_database.txt')
    self.gui_path = os.path.join(os.path.dirname(__file__), 'ui02.ui')
    self.group_members=["Nick","Bijan","Gui","Uli"]
    self.user = "Ul]["

    #loading the GUI
    self.chatwindow = loadUi(self.gui_path, self)

    # Data are imported from the database into a Model class
    self.history_modell = Model(self.history_path)

    # Data are transfered from the modell class to the View class
    self.show_history = View(self.history_modell, self.chatwindow.listView)


    # connections and actions
    self.chatwindow.connect(self.chatwindow.Send_Button, SIGNAL("released()"),
                            self.message_send)

    self.client = client()
    # start threading process
    self.client.start()
    self.client.commandQueue.put(ClientCommand(ClientCommand.connect,
                                              ("localhost",2468)))
    self.update_timer()

    # execute application
    self.chatwindow.show()


#==============================================================================#
#                            client related methods                            #
#==============================================================================#

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
    # triggered if there is something to read
    if read:
      self.client.commandQueue.put(ClientCommand(ClientCommand.receive))
    try:
    # triggered if there is something to read or something has been sent
      reply = self.client.replyQueue.get(block=False)
      status = "success" if reply.replyType == ClientReply.success else "ERROR"
      self.log('Client reply %s: %s' % (status, reply.data))
    except Queue.Empty:
      pass

  def closeEvent(self, event):
    reply = QtGui.QMessageBox.question(self, 'Message',
      "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

    if reply == QtGui.QMessageBox.Yes:
      self.client.shutdown()
      event.accept()
    else:
      event.ignore()

  def log(self, message):
    timestamp = '[%010.3f]' % time.clock()
    f = open(self.history_path, 'a')
    message = timestamp + str(message)
    f.write("\n"+self.user+":\n"+message+"\n")
    f.close()

    self.history_modell.reload(self.history_path)
    self.history_modell.emit(QtCore.SIGNAL("layoutChanged()"))

#==============================================================================#
#                          non client related methods                          #
#==============================================================================#

  # functions called by the GUI
  def message_send(self):
    # retrieve message
    message = str(self.chatwindow.textEdit.toPlainText())

    # save to history
    f = open(self.history_path, 'a')
    f.write("\n"+self.user+":\n"+message+"\n")
    f.close()

    # Send message to other clients. The client class confirms if sending was
    # successful.
    self.client.commandQueue.put(ClientCommand(ClientCommand.send, message))

    # clear text entry
    self.chatwindow.textEdit.clear()

    # send signal for repainting
    self.history_modell.reload(self.history_path)
    self.history_modell.emit(QtCore.SIGNAL("layoutChanged()"))

#==============================================================================#
#                                 class Model                                  #
#==============================================================================#

class Model(QtCore.QAbstractListModel):
  def __init__(self, dateiname):
    QtCore.QAbstractListModel.__init__(self)
    self.data = []

    word_wrap_length=80     # we could define this later as a variable
    # Lade data
    f = open(dateiname)

    try:
      lst = []
      for zeile in f:
        if not zeile.strip():
          self.data.append(QtCore.QVariant(lst))
          lst = []
        else:
          if len(zeile.strip())>word_wrap_length and len(zeile.split())>1:
            sum=0
            line=""
            list_of_words=zeile.split()
            for i in range(len(list_of_words)):
              sum+=len(list_of_words[i])+1
              if sum<word_wrap_length:
                line+=list_of_words[i]+" "
              else:
                sum=len(list_of_words[i])
                lst.append(QtCore.QVariant(line))
                line=list_of_words[i]+" "
            if line:
              lst.append(QtCore.QVariant(line))
          else:
            lst.append(zeile.strip())
      if lst:
          self.data.append(QtCore.QVariant(lst))
    finally:
        f.close()

  def reload(self, dateiname):
    self.data = []

    word_wrap_length=80     # we could define this later as a variable
    f = open(dateiname)

    try:
      lst = []
      for zeile in f:
        if not zeile.strip():
          self.data.append(QtCore.QVariant(lst))
          lst = []
        else:
          if len(zeile.strip())>word_wrap_length and len(zeile.split())>1:
            sum=0
            line=""
            list_of_words=zeile.split()
            for i in range(len(list_of_words)):
              sum+=len(list_of_words[i])+1
              if sum<word_wrap_length:
                line+=list_of_words[i]+" "
              else:
                sum=len(list_of_words[i])
                lst.append(QtCore.QVariant(line))
                line=list_of_words[i]+" "
            if line:
              lst.append(QtCore.QVariant(line))
          else:
            lst.append(zeile.strip())
      if lst:
          self.data.append(QtCore.QVariant(lst))
    finally:
        f.close()

  def rowCount(self, parent=QtCore.QModelIndex()):
      return len(self.data)

  def data(self, index, role=QtCore.Qt.DisplayRole):
      return QtCore.QVariant(self.data[index.row()])

#==============================================================================#
#                                  class View                                  #
#==============================================================================#

class View(QtGui.QListView):
  def __init__(self, modell, parent=None):
    QtGui.QListView.__init__(self, parent)
    self.resize(5000, 3000)
    self.delegate = ViewDelegate()
    self.setItemDelegate(self.delegate)
    self.setModel(modell)
    self.setVerticalScrollMode(QtGui.QListView.ScrollPerPixel)

#==============================================================================#
#                              class ViewDelegate                              #
#==============================================================================#

class ViewDelegate(QtGui.QItemDelegate):
  def __init__(self):
    QtGui.QItemDelegate.__init__(self)

    self.borderColor    = QtGui.QPen(QtGui.QColor(0, 0, 0))
    self.titleTextColor = QtGui.QPen(QtGui.QColor(255, 255, 255))
    self.titleColor     = QtGui.QBrush(QtGui.QColor(120, 120, 120))
    self.textColor      = QtGui.QPen(QtGui.QColor(0, 0, 0))
    self.titleFont      = QtGui.QFont("Helvetica", 10, QtGui.QFont.Bold)
    self.textFont       = QtGui.QFont("Helvetica", 10)

    self.lineHeight  = 15
    self.titleHeight = 20
    self.dist        = 4
    self.innerDist   = 2
    self.textDist    = 4

  def sizeHint(self, option, index):
    n_lines = len(index.data().toList())
    return QtCore.QSize(170, self.lineHeight*n_lines + self.titleHeight)

  def paint(self, painter, option, index):
    border = option.rect.adjusted(self.dist, self.dist,
                                  -self.dist, -self.dist)
    borderTitle = border.adjusted(self.innerDist,
                  self.innerDist, -self.innerDist + 1, 0)
    borderTitle.setHeight(self.titleHeight)
    borderTitleText = borderTitle.adjusted(self.textDist, 0, self.textDist, 0)
    painter.save()
    painter.setPen(self.borderColor)
    # painter.drawRect(rahmen)
    painter.fillRect(borderTitle, self.titleColor)

    # Titel schreiben
    painter.setPen(self.titleTextColor)
    painter.setFont(self.titleFont)
    data = index.data().toList()
    # Do not draw if theres nothing to draw
    if len(data) > 0:
      stringData = data[0].toString()
      painter.drawText(borderTitleText,
                       QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                       data[0].toString())

    # Adresse schreiben
    painter.setPen(self.textColor)
    painter.setFont(self.textFont)
    for i, entry in enumerate(data[1:]):
        painter.drawText(borderTitle.x() + self.textDist,
                         borderTitle.bottom() + (i+1)*self.lineHeight,
                         "%s" % entry.toString())
    painter.restore()

#==============================================================================#
#                                     MAIN                                     #
#==============================================================================#

if __name__ == "__main__":
  app = QApplication(sys.argv)
  myapp = ez_Gui()
  sys.exit(app.exec_())
