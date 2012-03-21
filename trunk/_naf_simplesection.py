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

import sqlite3, logging, sys

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_commons
import _naf_database as nafdb
import _naf_itemmodel
import _naf_tableview
import _naf_imageviewer
import _naf_textviewer


class _cSimplesectionModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'simplesections')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_simplesectionModel = _cSimplesectionModel()
def cSimplesectionModel(): return _simplesectionModel

class cSimplesectionView(_naf_commons.cArtifactDetailsView):
    TYPE_ID = nafdb.TYPE_SIMPLESECTION

    def __init__(self, parent, isEditable=False):
        super(cSimplesectionView, self).__init__(parent)
        self.defaultTitle = self.tr("New Text Section")
        self.editTitle = self.tr("Edit text section")
        self.detailsView = self
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setItemDelegate(_naf_itemmodel.cItemDelegate(self))
        self.mapper.setModel(cSimplesectionModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)
        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)

        lblContent = self.makeEditLinkLabel("content", not isEditable)
        lblContent.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblContent, 3, 0)

        ledId = QtGui.QSpinBox(self, maximum=sys.maxint)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=not isEditable)
        cbxKeywords = QtGui.QComboBox(self, enabled=isEditable, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))
        tedContent = _naf_textviewer.cTextEditor(self, readOnly=not isEditable)
        tedContent.setImageProvider(nafdb.getImageForId)

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,          0, 1, 1, 3)
        layout.addWidget(ledTitle,       1, 1, 1, 3)
        layout.addWidget(cbxKeywords,    2, 1, 1, 3)
        layout.addWidget(tedContent,     3, 1, 1, 3)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(tedContent, columns.index('content'))

    def model(self):
        return self.mapper.model()

    def submit(self):
        self.mapper.submit()

