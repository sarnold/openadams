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
import _naf_textviewer

class _cRequirementModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'requirements')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_requirementModel = _cRequirementModel()
def cRequirementModel(): return _requirementModel


class cRequirementDetailsView(_naf_commons.cArtifactDetailsView):

    def __init__(self, parent, readOnly=True):
        super(cRequirementDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setItemDelegate(_naf_itemmodel.cItemDelegate(self))
        self.mapper.setModel(cRequirementModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(lbl("priority")), 3, 0)
        layout.addWidget(QtGui.QLabel(lbl("status")), 3, 2)
        layout.addWidget(QtGui.QLabel(lbl("complexity")), 5, 0)
        layout.addWidget(QtGui.QLabel(lbl("assigned")), 5, 2)
        layout.addWidget(QtGui.QLabel(lbl("effort")), 6, 0)
        layout.addWidget(QtGui.QLabel(lbl("category")), 4, 2)
        layout.addWidget(QtGui.QLabel(lbl("origin")), 9, 0)
        layout.addWidget(QtGui.QLabel(lbl("risk")), 4, 0)
        layout.addWidget(QtGui.QLabel(lbl("baseline")), 6, 2)
        layout.addWidget(QtGui.QLabel(lbl("testability")), 8, 0)

        lblRationale = self.makeEditLinkLabel("rationale", readOnly)
        lblRationale.linkActivated.connect(self.sendEditSignal)

        lblDescription = self.makeEditLinkLabel("description", readOnly)
        lblDescription.linkActivated.connect(self.sendEditSignal)

        ledId = QtGui.QSpinBox(self, maximum=sys.maxint)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=readOnly)

        cbxKeywords = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))

        tedDescription = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        cbxAssigned = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxAssigned.setModel(self.mapper.model().getHistoryModel('assigned_view'))

        tedRationale = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedRationale.setImageProvider(nafdb.getImageForId)
        self.mapper.addMapping(tedRationale, columns.index('rationale'))

        cbxOrigin = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxOrigin.setModel(self.mapper.model().getHistoryModel('origin_view'))

        cbxPriority = QtGui.QComboBox(self, enabled=not readOnly)
        cbxPriority.setModel(self.mapper.model().getLookupModel('priorityLUT'))

        cbxStatus = QtGui.QComboBox(self, enabled=not readOnly)
        cbxStatus.setModel(self.mapper.model().getLookupModel('statusLUT'))

        cbxComplexity = QtGui.QComboBox(self, enabled=not readOnly)
        cbxComplexity.setModel(self.mapper.model().getLookupModel('complexityLUT'))

        cbxEffort = QtGui.QComboBox(self, enabled=not readOnly)
        cbxEffort.setModel(self.mapper.model().getLookupModel('effortLUT'))

        cbxCategory = QtGui.QComboBox(self, enabled=not readOnly)
        cbxCategory.setModel(self.mapper.model().getLookupModel('categoryLUT'))

        tedDescription.setImageProvider(nafdb.getImageForId)
        
        cbxRisk = QtGui.QComboBox(self, enabled=not readOnly)
        cbxRisk.setModel(self.mapper.model().getLookupModel('riskLUT'))
        
        cbxBaseline =  QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxBaseline.setModel(self.mapper.model().getHistoryModel('baseline_view'))
        
        cbxTestability =  QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxTestability.setModel(self.mapper.model().getHistoryModel('testability_view'))

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,          0, 1, 1, 3)
        layout.addWidget(ledTitle,       1, 1, 1, 3)
        layout.addWidget(cbxKeywords,    2, 1, 1, 3)
        layout.addWidget(cbxPriority,    3, 1, 1, 1)
        layout.addWidget(cbxRisk,        4, 1, 1, 1)
        layout.addWidget(cbxComplexity,  5, 1, 1, 1)
        layout.addWidget(cbxEffort,      6, 1, 1, 1)
        
        layout.addWidget(cbxStatus,      3, 3, 1, 1)
        layout.addWidget(cbxCategory,    4, 3, 1, 1)
        layout.addWidget(cbxAssigned,    5, 3, 1, 1)
        layout.addWidget(cbxBaseline,    6, 3, 1, 1)
        
        layout.addWidget(lblDescription, 7, 0)
        layout.addWidget(tedDescription, 7, 1, 1, 3)
        layout.addWidget(cbxTestability, 8, 1, 1, 3)
        layout.addWidget(cbxOrigin,      9, 1, 1, 3)
        layout.addWidget(lblRationale,   10, 0)
        layout.addWidget(tedRationale,   10, 1, 1, 3)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        layout.setRowStretch(7, 5)
        layout.setRowStretch(10, 1)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(tedDescription, columns.index('description'))
        self.mapper.addMapping(cbxAssigned, columns.index('assigned'))

        self.mapper.addMapping(cbxOrigin, columns.index('origin'))
        self.mapper.addMapping(cbxPriority, columns.index('priority'))
        self.mapper.addMapping(cbxStatus, columns.index('status'))
        self.mapper.addMapping(cbxComplexity, columns.index('complexity'))
        self.mapper.addMapping(cbxEffort, columns.index('effort'))
        self.mapper.addMapping(cbxCategory, columns.index('category'))
        
        self.mapper.addMapping(cbxRisk, columns.index('risk'))
        self.mapper.addMapping(cbxBaseline, columns.index('baseline'))
        self.mapper.addMapping(cbxTestability, columns.index('testability'))
        


class cRequirementView(QtGui.QTabWidget):
    """View/edit a requirement"""
    TYPE_ID = nafdb.TYPE_REQUIREMENT

    def __init__(self, parent, isEditable=False):
        QtGui.QTabWidget.__init__(self, parent)
        self.defaultTitle = self.tr("New Requirement")
        self.editTitle = self.tr("Edit requirement")
        self.mapper = _naf_tableview.cNotifier()
        self.detailsView = cRequirementDetailsView(self, readOnly=not isEditable)
        self.addTab(self.detailsView, self.tr('Requirement'))
        self.mapper.addObserver(self.detailsView)
        
        self.featureTableView = _naf_tableview.cItemTableView(_naf_tableview.cItemTableModel('features', ('id', 'priority', 'status', 'risk', 'keywords', 'title'),
            relationType=_naf_tableview.REVERSE_RELATION), self)
        self.addTab(self.featureTableView, self.tr('Related Features'))
        self.mapper.addObserver(self.featureTableView)

        relationType = [_naf_tableview.NORMAL_RELATION, _naf_tableview.IGNORE_RELATION][isEditable]
        self.usecaseTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('usecases', ('id', 'priority', 'usefrequency', 'actors', 'stakeholders', 'keywords', 'title'),
            relationType=relationType,
            itemsCheckable=isEditable),
            self)
        self.addTab(self.usecaseTableView, self.tr('Related Usecases'))
        self.mapper.addObserver(self.usecaseTableView)

        relationType = [_naf_tableview.NORMAL_RELATION, _naf_tableview.IGNORE_RELATION][isEditable]
        self.testcaseTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('testcases', ('id', 'keywords', 'title'),
            relationType=relationType,
            itemsCheckable=isEditable),
            self)
        self.addTab(self.testcaseTableView, self.tr('Related Testcases'))
        self.mapper.addObserver(self.testcaseTableView)

        self.componentTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('components', ('id', 'keywords', 'kind', 'title'),
            relationType=_naf_tableview.REVERSE_RELATION,
            itemsCheckable=False),
            self)
        self.addTab(self.componentTableView, self.tr('Related Components'))
        self.mapper.addObserver(self.componentTableView)

    def model(self):
        return self.detailsView.mapper.model()

    def submit(self):
        self.mapper.submit()
