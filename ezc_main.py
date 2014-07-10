import sys,os
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *


def ezc_Gui():

  # functions called by the GUI
  def message_send():
      message=str(chatwindow.textEdit.toPlainText())

      f = open(history_path, 'a')
      f.write("\n"+user+":\n"+message+"\n")
      f.close()

      chatwindow.textEdit.clear()
      newpost=[user,message]
      history_modell.data.append(QtCore.QVariant(newpost))
      history_modell.emit(QtCore.SIGNAL("layoutChanged()"))

  # variables
  history_path = os.path.join(os.path.dirname(__file__), 'history',
                              'history_database.txt')
  gui_path= os.path.join(os.path.dirname(__file__), 'ui02.ui')
  group_members=["Nick","Bijan","Gui","Uli"]
  user="Ul]["

  #loading the GUI
  app = QApplication(sys.argv)
  chatwindow = loadUi(gui_path)

  # Data are imported from the database into a Modell class
  history_modell = Modell(history_path)

  # Data are transfered from the modell class to the View class
  show_history = View(history_modell,chatwindow.listView)


  # connections and actions
  chatwindow.connect(chatwindow.Send_Button, SIGNAL("released()"),
                     message_send)

  # execute application
  chatwindow.show()
  app.exec_()


class Modell(QtCore.QAbstractListModel):
    def __init__(self, dateiname):
        QtCore.QAbstractListModel.__init__(self)
        self.data = []

        word_wrap_length=80           # we could define this later as a variable
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

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.data)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        return QtCore.QVariant(self.data[index.row()])

class View(QtGui.QListView):
   def __init__(self, modell, parent=None):
       QtGui.QListView.__init__(self, parent)
       self.resize(5000, 3000)
       self.delegate = ViewDelegate()
       self.setItemDelegate(self.delegate)
       self.setModel(modell)
       self.setVerticalScrollMode(QtGui.QListView.ScrollPerPixel)

class ViewDelegate(QtGui.QItemDelegate):
    def __init__(self):
        QtGui.QItemDelegate.__init__(self)

        self.rahmenStift = QtGui.QPen(QtGui.QColor(0,0,0))
        self.titelTextStift = QtGui.QPen(
                                       QtGui.QColor(255,255,255))
        self.titelFarbe = QtGui.QBrush(QtGui.QColor(120,120,120))
        self.textStift = QtGui.QPen(QtGui.QColor(0,0,0))
        self.titelSchriftart = QtGui.QFont("Helvetica", 10,
                                           QtGui.QFont.Bold)
        self.textSchriftart = QtGui.QFont("Helvetica", 10)

        self.zeilenHoehe = 15
        self.titelHoehe = 20
        self.abstand = 4
        self.abstandInnen = 2
        self.abstandText = 4

    def sizeHint(self, option, index):
        anz = len(index.data().toList())
        return QtCore.QSize(170,
                          self.zeilenHoehe*anz + self.titelHoehe)

    def paint(self, painter, option, index):
        rahmen = option.rect.adjusted(self.abstand, self.abstand,
                                    -self.abstand, -self.abstand)
        rahmenTitel = rahmen.adjusted(self.abstandInnen,
                      self.abstandInnen, -self.abstandInnen+1, 0)
        rahmenTitel.setHeight(self.titelHoehe)
        rahmenTitelText = rahmenTitel.adjusted(self.abstandText,
                                        0, self.abstandText, 0)
        data = index.data().toList()
        painter.save()
        painter.setPen(self.rahmenStift)
        # painter.drawRect(rahmen)
        painter.fillRect(rahmenTitel, self.titelFarbe)

        # Titel schreiben
        painter.setPen(self.titelTextStift)
        painter.setFont(self.titelSchriftart)
        painter.drawText(rahmenTitelText,
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                    data[0].toString())

        # Adresse schreiben
        painter.setPen(self.textStift)
        painter.setFont(self.textSchriftart)
        for i, eintrag in enumerate(data[1:]):
            painter.drawText(rahmenTitel.x() + self.abstandText,
                   rahmenTitel.bottom() + (i+1)*self.zeilenHoehe,
                   "%s" % eintrag.toString())
        painter.restore()

if __name__ == "__main__":
    ezc_Gui()
