# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui02.ui'
#
# Created: Tue Jul 08 16:50:22 2014
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
        Form.resize(1065, 698)
        self.horizontalLayout = QtGui.QHBoxLayout(Form)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.groupBox = QtGui.QGroupBox(Form)
        self.groupBox.setEnabled(True)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox.setSizeIncrement(QtCore.QSize(20, 0))
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setMinimumSize(QtCore.QSize(200, 40))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self.groupBox)
        self.pushButton_2.setMinimumSize(QtCore.QSize(0, 40))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.verticalLayout.addWidget(self.pushButton_2)
        spacerItem = QtGui.QSpacerItem(20, 648, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.pushButton_4 = QtGui.QPushButton(self.groupBox)
        self.pushButton_4.setMinimumSize(QtCore.QSize(0, 40))
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
        self.verticalLayout.addWidget(self.pushButton_4)
        self.horizontalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(Form)
        self.groupBox_2.setTitle(_fromUtf8(""))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout.setContentsMargins(0, 0, 0, -1)
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.frame_2 = QtGui.QFrame(self.groupBox_2)
        self.frame_2.setMaximumSize(QtCore.QSize(16777215, 60))
        self.frame_2.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_2.setObjectName(_fromUtf8("frame_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.textEdit = QtGui.QTextEdit(self.frame_2)
        self.textEdit.setMinimumSize(QtCore.QSize(0, 50))
        self.textEdit.setMaximumSize(QtCore.QSize(16777215, 45))
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.horizontalLayout_2.addWidget(self.textEdit)
        self.Send_Button = QtGui.QPushButton(self.frame_2)
        self.Send_Button.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Send_Button.sizePolicy().hasHeightForWidth())
        self.Send_Button.setSizePolicy(sizePolicy)
        self.Send_Button.setMinimumSize(QtCore.QSize(70, 50))
        self.Send_Button.setMaximumSize(QtCore.QSize(60, 50))
        self.Send_Button.setObjectName(_fromUtf8("Send_Button"))
        self.horizontalLayout_2.addWidget(self.Send_Button)
        self.gridLayout.addWidget(self.frame_2, 1, 0, 1, 1)
        self.listView = QtGui.QListView(self.groupBox_2)
        self.listView.setObjectName(_fromUtf8("listView"))
        self.gridLayout.addWidget(self.listView, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.groupBox_2)

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.Send_Button, QtCore.SIGNAL(_fromUtf8("released()")), self.textEdit.clear)
        QtCore.QObject.connect(self.Send_Button, QtCore.SIGNAL(_fromUtf8("released()")), self.listView.reset)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.pushButton.setText(_translate("Form", "Networks", None))
        self.pushButton_2.setText(_translate("Form", "Groups", None))
        self.pushButton_4.setText(_translate("Form", "Settings", None))
        self.Send_Button.setText(_translate("Form", "Send", None))

