# -*- coding: utf-8  -*-
# $Id$

# -------------------------------------------------------------------
# Copyright 2012 Achim Köhler
#
# This file is part of openADAMS.
#
# openADAMS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License,
# or (at your option) any later version.
#
# openADAMS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with openADAMS.  If not, see <http://www.gnu.org/licenses/>.
# -------------------------------------------------------------------

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal

class cFilePicker(QtCore.QObject):
    """
    A file picker widget with a label, a combobox and a button.
    Pressing the button opens a file dialog.
    Layouting the label, line edit and button is not done by this class.
    """
    # Signal emitted when the picker filename changes
    sigValidFilename = pyqtSignal('bool')
    
    def __init__(self):
        super(cFilePicker, self).__init__()
        self.isFilenameInserted = False
        self.lblCaption = QtGui.QLabel()
        self.cbxFilename = QtGui.QComboBox()
        self.cbxFilename.setEditable(True)
        self.cbxFilename.editTextChanged.connect(self.verifyFilename)
        self.btnFileDlg = QtGui.QPushButton("...")
        self.btnFileDlg.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)        
        self.fileDialog = QtGui.QFileDialog()
        self.btnFileDlg.clicked.connect(self.showFileDialog)
    
    def getWidgets(self):
        """Return the sub widgets to be layouted externally"""
        return {'label': self.lblCaption, 'combobox': self.cbxFilename, 
                'button': self.btnFileDlg, 'dialog': self.fileDialog}
    
    def setHistory(self, fileNames):
        self.cbxFilename.addItems(fileNames)
    
    def showFileDialog(self):
        if self.fileDialog.exec_() == QtGui.QDialog.Accepted:
            if self.isFilenameInserted:
                self.setFileName(self.fileDialog.selectedFiles()[0])
            else:
                self.setFileName(self.fileDialog.selectedFiles()[0])    
                self.isFilenameInserted = True
            
    def setFileName(self, name):
        if self.cbxFilename.count() == 0:
            self.cbxFilename.addItem(name)
        else:
            self.cbxFilename.setItemText(0, name)
        self.cbxFilename.setCurrentIndex(0)
        fileInfo = QtCore.QFileInfo(name)
        self.fileDialog.setDirectory(fileInfo.dir())
        self.fileDialog.selectFile(name)
        
    def verifyFilename(self, filename):
        """Slot called whenever text in combobox changes
        if the filename not exists the combobox is highlighted
        """
        self.sigValidFilename.emit(QtCore.QFile.exists(filename))
    
    def isValidFilename(self):
        return QtCore.QFile.exists(self.cbxFilename.currentText())
    
    def getFilename(self):
        return unicode(self.cbxFilename.currentText())
