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

import _naf_database as nafdb
import _naf_itemmodel
import _naf_tableview
import _naf_textviewer

class _cFolderModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'folders')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_folderModel = _cFolderModel()
def cFolderModel(): return _folderModel


class cFolderView(QtGui.QWidget):
    """View a folder, just for editing purposes"""
    TYPE_ID = nafdb.TYPE_FOLDER

    def __init__(self, parent, isEditable=False):
        super(QtGui.QWidget, self).__init__(parent)
        self.defaultTitle = self.tr("New folder")
        self.detailsView = self
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(cFolderModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QFormLayout()
        self.setLayout(layout)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=not isEditable)

        layout.addRow(QtGui.QLabel(lbl("id")), ledId)
        layout.addRow(QtGui.QLabel(lbl("title")), ledTitle)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))

    def model(self):
        return self.mapper.model()

    def submit(self):
        self.mapper.submit()
