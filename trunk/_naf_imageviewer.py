# -*- coding: utf-8  -*-
# $Id$

# -------------------------------------------------------------------
# Copyright 2010 Achim Köhler
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

# Derived from PyQt4 imageviewer example
#############################################################################
##
## Copyright (C) 2005-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

import os.path
from PyQt4 import QtCore, QtGui

class cImageViewer(QtGui.QWidget):

    imageLoadedSignal = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent=None, isEditable=False):
        super(cImageViewer, self).__init__(parent)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.createActions()

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        layout.addWidget(self.scrollArea)

        self.toolBar = QtGui.QToolBar('View toolbar', orientation=QtCore.Qt.Vertical)
        self.toolBar.addAction(self.zoomInAct)
        self.toolBar.addAction(self.zoomOutAct)
        self.toolBar.addAction(self.normalSizeAct)
        self.toolBar.addAction(self.fitToWindowAct)
        self.toolBar.addAction(self.saveImageAct)
        self.toolBar.addAction(self.importImageAct)
        self.importImageAct.setEnabled(isEditable)
        layout.addWidget(self.toolBar)

        self.setLayout(layout)

    def setPixmap(self, image):
        self.imageLabel.setPixmap(image)
        self.scaleFactor = 1.0
        self.imageLabel.adjustSize()
        self.fitToWindowAct.setEnabled(True)
        self.fitToWindowAct.setChecked(False)
        self.fitToWindow()
        self.saveImageAct.setEnabled(True)
        self.updateActions()

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()
        self.updateActions()

    def saveImage(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Image", QtCore.QDir.currentPath(), filter=self.tr("Images (*.png *.xpm *.jpg *.bmp)"))
        if not fileName:
            return
        if not self.imageLabel.pixmap().save(fileName):
            QtGui.QMessageBox.information(self, self.tr("Image Viewer"), QtCore.QString(self.tr("Cannot save %1.")).arg(fileName))

    def importImage(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Import Image",
            QtCore.QDir.currentPath(),
            filter=self.tr("Bitmap images (*.png *.xpm *.jpg *.bmp);;SVG files (*.svg *.xml)"))
        if not fileName:
            return
        suffix = os.path.splitext(str(fileName))[1]
        ##print suffix
        if suffix in ('.xml', '.svg'):
            # TODO: implement SVG support
            pass
        else:
            pm = QtGui.QPixmap()
            if not pm.load(fileName):
                QtGui.QMessageBox.information(self, self.tr("Import image"),
                    QString(self.tr("Could not import image from file %1")).arg(fileName))
            self.setPixmap(pm)
            self.emitImageLoadedSignal('PNG')

    def createActions(self):
        self.zoomInAct = QtGui.QAction(QtGui.QIcon(':/icons/24-zoom-in.png'), self.tr("Zoom In (25%)"), self,
                shortcut=QtGui.QKeySequence.ZoomIn, enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QtGui.QAction(QtGui.QIcon(':/icons/24-zoom-out.png'), self.tr("Zoom Out (25%)"), self,
                shortcut=QtGui.QKeySequence.ZoomOut, enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QtGui.QAction(QtGui.QIcon(':/icons/24-zoom-actual.png'), self.tr("Normal Size"), self,
                shortcut=QtGui.QKeySequence.Refresh, enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QtGui.QAction(QtGui.QIcon(':/icons/24-zoom-fill.png'), self.tr("Fit to Window"), self,
                enabled=False, checkable=True,
                triggered=self.fitToWindow)

        self.saveImageAct = QtGui.QAction(QtGui.QIcon(':/icons/document-save-as.png'), self.tr("Save Image"), self,
            shortcut=QtGui.QKeySequence.SaveAs, enabled=False, triggered=self.saveImage)

        self.importImageAct = QtGui.QAction(QtGui.QIcon(':/icons/document-import.png'), self.tr("Import Image"), self,
            shortcut=QtGui.QKeySequence.Open, enabled=False, triggered=self.importImage)


    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))

    def emitImageLoadedSignal(self, imageType):
        self.imageLoadedSignal.emit(imageType)
