import sys,os 
from PyQt4 import QtCore, QtGui, uic 
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from ezc_ui import Ui_Form

def Nicks_first_gui():
  app = QtGui.QApplication(sys.argv)
  myapp = MyForm()
  myapp.show()
  sys.exit(app.exec_())

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
  def file_dialog(self):
    """@todo: Docstring for file_dialog.
    :returns: @todo

    """
    fd = QtGui.QFileDialog(self)
    plik = open(fd.getOpenFileName()).read()
    self.ui.textOut.setText(plik)

  def copyInToOut(self):
    """@todo: Docstring for copyInToOut.
    :returns: @todo

    """
    if self.ui.textIn.text():
      self.ui.textOut.append(self.ui.textIn.text())

    self.ui.textIn.clear()


    
def Ulis_first_gui():
    history_path = os.path.join(os.path.dirname(__file__), 'history\history_database.txt')
    gui_path= os.path.join(os.path.dirname(__file__), 'ui02.ui')
    
    def message_send():
        message=str(chatwindow.textEdit.toPlainText())
        
        f = open(history_path, 'a')   
        f.write(user+":\n"+message+"\n\n")
        f.close()
        
        chatwindow.textEdit.clear()
        newpost=[user,message]
        history_modell.datensatz.append(QtCore.QVariant(newpost))
        history_modell.emit(QtCore.SIGNAL("layoutChanged()")) 
        
    history_modell = Modell(history_path)
    group_members=["Nick","Bijan","Gui","Uli"]
    user="Ul]["    
    app = QApplication(sys.argv)
    chatwindow = loadUi(gui_path)
    show_history = View(history_modell,chatwindow.listView)    
    chatwindow.connect(chatwindow.Send_Button, SIGNAL("released()"), message_send)
    
    chatwindow.show()
    app.exec_()    

                    
class Modell(QtCore.QAbstractListModel): 
    def __init__(self, dateiname): 
        QtCore.QAbstractListModel.__init__(self) 
        self.datensatz = []

        # Lade Datensatz 
        f = open(dateiname) 
        try: 
            lst = [] 
            for zeile in f: 
                if not zeile.strip(): 
                    self.datensatz.append(QtCore.QVariant(lst)) 
                    lst = [] 
                else: 
                    lst.append(zeile.strip()) 
            if lst: 
                self.datensatz.append(QtCore.QVariant(lst)) 
        finally: 
            f.close()
            
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.datensatz)

    def data(self, index, role=QtCore.Qt.DisplayRole): 
        return QtCore.QVariant(self.datensatz[index.row()])
        
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
        datensatz = index.data().toList() 
        painter.save() 
        painter.setPen(self.rahmenStift) 
        # painter.drawRect(rahmen) 
        painter.fillRect(rahmenTitel, self.titelFarbe)

        # Titel schreiben 
        painter.setPen(self.titelTextStift) 
        painter.setFont(self.titelSchriftart) 
        painter.drawText(rahmenTitelText, 
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, 
                    datensatz[0].toString())

        # Adresse schreiben 
        painter.setPen(self.textStift) 
        painter.setFont(self.textSchriftart) 
        for i, eintrag in enumerate(datensatz[1:]): 
            painter.drawText(rahmenTitel.x() + self.abstandText, 
                   rahmenTitel.bottom() + (i+1)*self.zeilenHoehe, 
                   "%s" % eintrag.toString()) 
        painter.restore() 
        
if __name__ == "__main__":
    #Nicks_first_gui()
    Ulis_first_gui()

