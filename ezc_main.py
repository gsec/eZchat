import sys
from PyQt4 import QtCore, QtGui
from ezc_ui.py import Ui_Form

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


if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  myapp = MyForm()
  myapp.show()
  sys.exit(app.exec_())

