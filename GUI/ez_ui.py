# Form implementation generated from reading ui file 'editor.ui'
#
# Created: Sat Jul  5 12:52:43 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(376, 295)
        self.textOut = QtGui.QTextEdit(Form)
        self.textOut.setGeometry(QtCore.QRect(9, 63, 351, 181))
        self.textOut.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.textOut.setObjectName(_fromUtf8("textOut"))
        self.textIn = QtGui.QLineEdit(Form)
        self.textIn.setGeometry(QtCore.QRect(9, 261, 351, 25))
        self.textIn.setObjectName(_fromUtf8("textIn"))
        self.widget = QtGui.QWidget(Form)
        self.widget.setGeometry(QtCore.QRect(9, 9, 351, 41))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(5, -1, 5, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.OpenFile = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.OpenFile.sizePolicy().hasHeightForWidth())
        self.OpenFile.setSizePolicy(sizePolicy)
        self.OpenFile.setObjectName(_fromUtf8("OpenFile"))
        self.horizontalLayout.addWidget(self.OpenFile)
        self.close = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.close.sizePolicy().hasHeightForWidth())
        self.close.setSizePolicy(sizePolicy)
        self.close.setObjectName(_fromUtf8("close"))
        self.horizontalLayout.addWidget(self.close)

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.close, QtCore.SIGNAL(_fromUtf8("clicked()")), Form.close)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.OpenFile.setText(_translate("Form", "OpenFile", None))
        self.close.setText(_translate("Form", "Close", None))

