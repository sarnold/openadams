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

class _cFeatureModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'features')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_featureModel = _cFeatureModel()
def cFeatureModel(): return _featureModel


class cFeatureDetailsView(_naf_commons.cArtifactDetailsView):
    def __init__(self, parent, readOnly=True):
        super(cFeatureDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setItemDelegate(_naf_itemmodel.cItemDelegate(self))
        self.mapper.setModel(cFeatureModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(lbl("priority")), 3, 0)
        layout.addWidget(QtGui.QLabel(lbl("risk")), 3, 2)
        layout.addWidget(QtGui.QLabel(lbl("status")), 3, 4)
        lblDescription = self.makeEditLinkLabel("description", readOnly)
        lblDescription.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblDescription, 4, 0)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=readOnly)
        cbxKeywords = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))
        cbxPriority = QtGui.QComboBox(self, enabled=not readOnly)
        cbxPriority.setModel(self.mapper.model().getLookupModel('priorityLUT'))
        cbxStatus = QtGui.QComboBox(self, enabled=not readOnly)
        cbxStatus.setModel(self.mapper.model().getLookupModel('statusLUT'))
        cbxRisk = QtGui.QComboBox(self, enabled=not readOnly)
        cbxRisk.setModel(self.mapper.model().getLookupModel('riskLUT'))
        tedDescription = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedDescription.setImageProvider(nafdb.getImageForId)

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,          0, 1, 1, 5)
        layout.addWidget(ledTitle,       1, 1, 1, 5)
        layout.addWidget(cbxKeywords,    2, 1, 1, 5)
        layout.addWidget(cbxPriority,    3, 1, 1, 1)
        layout.addWidget(cbxRisk,        3, 3, 1, 1)
        layout.addWidget(cbxStatus,      3, 5, 1, 1)
        layout.addWidget(tedDescription, 4, 1, 1, 5)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(5, 1)
        layout.setRowStretch(4, 1)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(cbxPriority, columns.index('priority'))
        self.mapper.addMapping(cbxStatus, columns.index('status'))
        self.mapper.addMapping(cbxRisk, columns.index('risk'))
        self.mapper.addMapping(tedDescription, columns.index('description'))


class cFeatureView(QtGui.QTabWidget):
    """View/edit a requirement"""
    TYPE_ID = nafdb.TYPE_FEATURE

    def __init__(self, parent, isEditable=False):
        QtGui.QTabWidget.__init__(self, parent)
        self.defaultTitle = self.tr("New Feature")
        self.editTitle = self.tr("Edit feature")
        self.mapper = _naf_tableview.cNotifier()
        self.detailsView = cFeatureDetailsView(self, readOnly=not isEditable)
        self.addTab(self.detailsView, self.tr('Feature'))
        self.mapper.addObserver(self.detailsView)

        relationType = [_naf_tableview.NORMAL_RELATION, _naf_tableview.IGNORE_RELATION][isEditable]
        self.requirementTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('requirements', ('id', 'priority', 'status', 'complexity', 'assigned', 'effort', 'category', 'keywords' ,'title'),
            relationType=relationType,
            itemsCheckable=isEditable),
            self)
        self.addTab(self.requirementTableView, self.tr('Related Requirements'))
        self.mapper.addObserver(self.requirementTableView)

        self.usecaseTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('usecases', ('id', 'priority', 'usefrequency', 'actors', 'stakeholders', 'keywords', 'title'),
            relationType=relationType,
            itemsCheckable=isEditable),
            self)
        self.addTab(self.usecaseTableView, self.tr('Related Usecases'))
        self.mapper.addObserver(self.usecaseTableView)

    def model(self):
        return self.detailsView.mapper.model()

    def submit(self):
        self.mapper.submit()
