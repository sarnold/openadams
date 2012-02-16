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

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_commons
import _naf_database as nafdb
import _naf_itemmodel
import _naf_tableview
import _naf_textviewer

class _cComponentModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'components')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_componentModel = _cComponentModel()
def cComponentModel(): return _componentModel


class cComponentDetailsView(_naf_commons.cArtifactDetailsView):
    def __init__(self, parent, readOnly=True):
        super(cComponentDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setItemDelegate(_naf_itemmodel.cItemDelegate(self))
        self.mapper.setModel(cComponentModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(lbl("kind")), 3, 0)
        lblDescription = self.makeEditLinkLabel("description", readOnly)
        lblDescription.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblDescription, 4, 0)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=readOnly)
        cbxKeywords = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))
        cbxKind = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKind.setModel(self.mapper.model().getHistoryModel('kind_view'))
        tedDescription = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedDescription.setImageProvider(nafdb.getImageForId)

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,          0, 1)
        layout.addWidget(ledTitle,       1, 1)
        layout.addWidget(cbxKeywords,    2, 1)
        layout.addWidget(cbxKind,        3, 1)
        layout.addWidget(tedDescription, 4, 1)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(4, 1)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(cbxKind, columns.index('kind'))
        self.mapper.addMapping(tedDescription, columns.index('description'))


class cComponentView(QtGui.QTabWidget):
    """View/edit a component"""
    TYPE_ID = nafdb.TYPE_COMPONENT

    def __init__(self, parent, isEditable=False):
        QtGui.QTabWidget.__init__(self, parent)
        self.defaultTitle = self.tr("New Component")
        self.editTitle = self.tr("Edit component")
        self.mapper = _naf_tableview.cNotifier()
        self.detailsView = cComponentDetailsView(self, readOnly=not isEditable)
        self.addTab(self.detailsView, self.tr('Component'))
        self.mapper.addObserver(self.detailsView)

        relationType = [_naf_tableview.NORMAL_RELATION, _naf_tableview.IGNORE_RELATION][isEditable]
        self.requirementTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('requirements', ('id', 'priority', 'status', 'complexity', 'assigned', 'effort', 'category', 'keywords' ,'title'),
            relationType=relationType,
            itemsCheckable=isEditable),
            self)
        self.addTab(self.requirementTableView, self.tr('Related Requirements'))
        self.mapper.addObserver(self.requirementTableView)

    def model(self):
        return self.detailsView.mapper.model()

    def submit(self):
        self.mapper.submit()
