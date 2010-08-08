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

import sqlite3, logging

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_commons
import _naf_database as nafdb
import _naf_itemmodel
import _naf_tableview
import _naf_imageviewer
import _naf_textviewer


class _cImageModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'images')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_imageModel = _cImageModel()
def cImageModel(): return _imageModel

##class cImageItemDelegate(QtGui.QItemDelegate):
class cImageItemDelegate(_naf_itemmodel.cItemDelegate):
    def setEditorData(self, editor, index):
        if isinstance(editor, _naf_imageviewer.cImageViewer):
            data = index.model().data(index, Qt.DisplayRole)
            pm = QtGui.QPixmap()
            pm.loadFromData(data)
            editor.setPixmap(pm)
        else:
            super(cImageItemDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        ##print "setModelData", editor, model
        if isinstance(editor, _naf_imageviewer.cImageViewer):
            pixmap = editor.imageLabel.pixmap()
            bytes = QtCore.QByteArray()
            databuffer = QtCore.QBuffer(bytes)
            databuffer.open(QtCore.QIODevice.WriteOnly);
            pixmap.save(databuffer, "PNG") # writes pixmap into bytes in PNG format
            model.setData(index, QtCore.QVariant(bytes), QtCore.Qt.EditRole)
        else:
            super(cImageItemDelegate, self).setModelData(editor, model, index)

class cImageView(_naf_commons.cArtifactDetailsView):
    TYPE_ID = nafdb.TYPE_IMAGE

    def __init__(self, parent, isEditable=False):
        super(cImageView, self).__init__(parent)
        self.defaultTitle = self.tr("New Image")
        self.editTitle = self.tr("Edit image")
        self.detailsView = self
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(cImageModel())
        self.mapper.setItemDelegate(cImageItemDelegate())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)
        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(lbl("format")), 4, 0)
        layout.addWidget(QtGui.QLabel(lbl("source")), 4, 2)
        layout.addWidget(QtGui.QLabel(lbl("image"), alignment=Qt.AlignTop), 5, 0)

        lblDescription = self.makeEditLinkLabel("description", not isEditable)
        lblDescription.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblDescription, 3, 0)

        ledId = QtGui.QLineEdit(self, readOnly=True)
        ledTitle = QtGui.QLineEdit(self, readOnly=not isEditable)
        cbxKeywords = QtGui.QComboBox(self, enabled=isEditable, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))
        tedDescription = _naf_textviewer.cTextEditor(self, readOnly=not isEditable)
        cbxSource = QtGui.QComboBox(self, enabled=isEditable, editable=True)
        cbxSource.setModel(self.mapper.model().getHistoryModel('source_view'))
        ledFormat = QtGui.QLineEdit(self, readOnly=True)
        imgViewer = _naf_imageviewer.cImageViewer(self, isEditable=isEditable)
        imgViewer.imageLoadedSignal.connect(ledFormat.setText)

        tedDescription.setImageProvider(nafdb.getImageForId)

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,          0, 1, 1, 3)
        layout.addWidget(ledTitle,       1, 1, 1, 3)
        layout.addWidget(cbxKeywords,    2, 1, 1, 3)
        layout.addWidget(tedDescription, 3, 1, 1, 3)
        layout.addWidget(ledFormat,      4, 1, 1, 1)
        layout.addWidget(cbxSource,      4, 3, 1, 1)
        layout.addWidget(imgViewer,      5, 1, 1, 3)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 5)
        layout.setRowStretch(3, 1)
        layout.setRowStretch(5, 10)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(tedDescription, columns.index('description'))
        self.mapper.addMapping(cbxSource, columns.index('source'))
        self.mapper.addMapping(ledFormat, columns.index('format'))
        self.mapper.addMapping(imgViewer, columns.index('image'))

    def model(self):
        return self.mapper.model()

    def submit(self):
        self.mapper.submit()

