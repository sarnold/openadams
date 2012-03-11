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

import logging

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_commons
import _naf_database as nafdb
import _naf_itemmodel
import _naf_tableview
import _naf_textviewer

class _cTestsuiteModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'testsuites')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_testsuiteModel = _cTestsuiteModel()
def cTestsuiteModel(): return _testsuiteModel


class cTestsuiteDetailsView(_naf_commons.cArtifactDetailsView):

    def __init__(self, parent, readOnly=True):
        super(cTestsuiteDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setItemDelegate(_naf_itemmodel.cItemDelegate(self))
        self.mapper.setModel(cTestsuiteModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)

        lblDescription = self.makeEditLinkLabel("description", readOnly)
        lblDescription.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblDescription, 3, 0)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=readOnly)
        cbxKeywords = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))
        tedDescription = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedDescription.setImageProvider(nafdb.getImageForId)

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,           0, 1, 1, 1)
        layout.addWidget(ledTitle,        1, 1, 1, 1)
        layout.addWidget(cbxKeywords,     2, 1, 1, 1)
        layout.addWidget(tedDescription,  3, 1, 1, 1)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(3, 1)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(tedDescription, columns.index('description'))


class cTestsuiteView(QtGui.QTabWidget):
    """View/edit a testsuite"""
    TYPE_ID = nafdb.TYPE_TESTSUITE

    def __init__(self, parent, isEditable=False):
        QtGui.QTabWidget.__init__(self, parent)
        self.defaultTitle = self.tr("New Testsuite")
        self.editTitle = self.tr("Edit testsuite")
        self.mapper = _naf_tableview.cNotifier()
        self.detailsView = cTestsuiteDetailsView(self, readOnly=not isEditable)
        self.addTab(self.detailsView, self.tr('Testsuite'))
        self.mapper.addObserver(self.detailsView)

        relationType = [_naf_tableview.NORMAL_RELATION, _naf_tableview.IGNORE_RELATION][isEditable]
        self.testcaseTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('testcases', ('id', 'keywords', 'title'),
            relationType=relationType,
            itemsCheckable=isEditable),
            self)
        self.addTab(self.testcaseTableView, self.tr('Related Testcases'))
        self.mapper.addObserver(self.testcaseTableView)

    def model(self):
        return self.detailsView.mapper.model()

    def submit(self):
        self.mapper.submit()
