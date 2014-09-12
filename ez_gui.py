'''
ez_gui creates a simple chatdialog. To show and run the chatdialog, create an instance of QtGui.QApplication and ez_gui.ez_gui. QtGui.QApplication.exec_() will run the clientmainloop. For example:

import sys
import ez_gui
from PyQt4 import QtCore, QtGui

app = QtGui.QApplication.(sys.argv)
win = ez_gui.ez_gui()
sys.exit(app.exec_())


If you want to run eZ_chat with a graphic user interface, follow further steps:
TODO:
    -ez_p2p.Client.CLI() needs to be changed. data has to be a functionargument (watch ez_gui.ez_gui.gui_onSend())
    -delete the mainloop in ez_p2p.Client.run(). QtGui.QApplication.exec_() will do this job
    -to print statusmessages in ez_p2p.Client, use ez_gui.ez_gui.gui_printStatus() instead of print
    -if a chatmessage was recieved in the clientthread, use ez_gui.ez_gui.gui_onRecv() to print it
'''

from PyQt4 import QtCore, QtGui
#import ez_p2p

try:
  _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
  def _fromUtf8(s):
      return s

try:
  _encoding = QtGui.QApplication.UnicodeUTF8
  def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
  def _translate(context, text, disambig):
      return QtGui.QApplication.translate(context, text, disambig)

class Ui_gui_mainwindow_setup(object):
  def setupUi(self, gui_mainwindow_setup):
    gui_mainwindow_setup.setObjectName(_fromUtf8("gui_mainwindow_setup"))
    gui_mainwindow_setup.resize(667, 500)
    gui_mainwindow_setup.setMinimumSize(QtCore.QSize(667, 500))
    gui_mainwindow_setup.setMaximumSize(QtCore.QSize(667, 500))
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(_fromUtf8("thumbs_003.jpg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    gui_mainwindow_setup.setWindowIcon(icon)
    self.gridLayoutWidget = QtGui.QWidget(gui_mainwindow_setup)
    self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 9, 651, 441))
    self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
    self.layTextShow = QtGui.QGridLayout(self.gridLayoutWidget)
    self.layTextShow.setMargin(0)
    self.layTextShow.setObjectName(_fromUtf8("layTextShow"))
    self.textShow = QtGui.QTextEdit(self.gridLayoutWidget)
    self.textShow.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    self.textShow.setReadOnly(True)
    self.textShow.setObjectName(_fromUtf8("textShow"))
    self.layTextShow.addWidget(self.textShow, 0, 0, 1, 1)
    self.gridLayoutWidget_2 = QtGui.QWidget(gui_mainwindow_setup)
    self.gridLayoutWidget_2.setGeometry(QtCore.QRect(10, 460, 541, 31))
    self.gridLayoutWidget_2.setObjectName(_fromUtf8("gridLayoutWidget_2"))
    self.layTextEdit = QtGui.QGridLayout(self.gridLayoutWidget_2)
    self.layTextEdit.setMargin(0)
    self.layTextEdit.setObjectName(_fromUtf8("layTextEdit"))
    self.textEdit = QtGui.QLineEdit(self.gridLayoutWidget_2)
    self.textEdit.setObjectName(_fromUtf8("textEdit"))
    self.layTextEdit.addWidget(self.textEdit, 0, 0, 1, 1)
    self.gridLayoutWidget_3 = QtGui.QWidget(gui_mainwindow_setup)
    self.gridLayoutWidget_3.setGeometry(QtCore.QRect(560, 460, 101, 31))
    self.gridLayoutWidget_3.setObjectName(_fromUtf8("gridLayoutWidget_3"))
    self.laySendBut = QtGui.QGridLayout(self.gridLayoutWidget_3)
    self.laySendBut.setMargin(0)
    self.laySendBut.setObjectName(_fromUtf8("laySendBut"))
    self.sendBut = QtGui.QPushButton(self.gridLayoutWidget_3)
    self.sendBut.setObjectName(_fromUtf8("sendBut"))
    self.laySendBut.addWidget(self.sendBut, 0, 0, 1, 1)

    self.retranslateUi(gui_mainwindow_setup)
    QtCore.QMetaObject.connectSlotsByName(gui_mainwindow_setup)

  def retranslateUi(self, gui_mainwindow_setup):
    gui_mainwindow_setup.setWindowTitle(_translate("gui_mainwindow_setup", "eZ_Chat", None))
    self.sendBut.setText(_translate("gui_mainwindow_setup", "Send", None))

class ez_gui(Ui_gui_mainwindow_setup, QtGui.QDialog):
  def __init__(self):
    QtGui.QDialog.__init__(self)
    self.setupUi(self)
    self.setWindowFlags(QtCore.Qt.Window)
    self.show()

    self.connect(self.sendBut, QtCore.SIGNAL("clicked ()"), self.gui_onSend)
    self.connect(self.textEdit, QtCore.SIGNAL("returnPressed"), self.gui_onSend)

  def gui_onSend(self):
    self.msgcontent = 'You say: ' + self.textEdit.text() + '\n'
    self.textEdit.clear()
    self.textShow.insertPlainText(self.msgcontent)
    self.textShow.moveCursor(QtGui.QTextCursor.End)
    #ez_p2p.Client.CLI(self.msgcontent)

  def gui_onRecv(self, msgdict = {}): #msgdict is a dict with sender, recipient, etime, content
    self.msgcontent = msgdict['sender'] + ' says: ' + msgdict['content'] + '\n'
    self.textShow.insertPlainText(self.msgcontent)
    self.textShow.moveCursor(QtGui.QTextCursor.End)

  def gui_printStatus(self, *statusmsg):
    self.cnt = len(statusmsg)
    for i in range(0, self.cnt, 1):
      #if type(statusmsg[i]) == int:
        #statusmsg[i] = str(statusmsg[i])
        #self.textShow.insertPlainText(statusmsg[i] + ' ')
      #elif type(statusmsg[i]) == float:
        #statusmsg[i] = str(statusmsg[i])
        #self.textShow.insertPlainText(statusmsg[i] + ' ')
      #else:
        #self.textShow.insertPlainText(statusmsg[i] + ' ')
      self.textShow.insertPlainText(statusmsg[i] + ' ')
    self.textShow.insertPlainText('\n')
    self.textShow.moveCursor(QtGui.QTextCursor.End)

