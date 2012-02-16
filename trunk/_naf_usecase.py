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

import sqlite3

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_commons
import _naf_database as nafdb
import _naf_itemmodel
import _naf_tableview
import _naf_textviewer

class _cUsecaseModel(_naf_itemmodel.cItemModel):
    def __init__(self):
        _naf_itemmodel.cItemModel.__init__(self, 'usecases')

# simple singleton pattern , see http://code.activestate.com/recipes/52558/
_usecaseModel = _cUsecaseModel()
def cUsecaseModel(): return _usecaseModel


class cUsecaseDetailsView(_naf_commons.cArtifactDetailsView):
    def __init__(self, parent, readOnly=True):
        super(cUsecaseDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setItemDelegate(_naf_itemmodel.cItemDelegate(self))
        self.mapper.setModel(cUsecaseModel())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(lbl("priority")), 3, 0)
        layout.addWidget(QtGui.QLabel(lbl("usefrequency")), 3, 2)
        layout.addWidget(QtGui.QLabel(lbl("actors")), 4, 0)
        layout.addWidget(QtGui.QLabel(lbl("stakeholders")), 5, 0)

        lblPrerequisites = self.makeEditLinkLabel("prerequisites", readOnly)
        lblPrerequisites.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblPrerequisites, 6, 0)

        lblMainscenario = self.makeEditLinkLabel("mainscenario", readOnly)
        lblMainscenario.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblMainscenario, 7, 0)

        lblAltscenario = self.makeEditLinkLabel("altscenario", readOnly)
        lblAltscenario.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblAltscenario, 8, 0)

        lblNotes = self.makeEditLinkLabel("notes", readOnly)
        lblNotes.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblNotes, 9, 0)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=readOnly)

        cbxKeywords = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))

        tedPrerequisites = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedMainscenario = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedAltscenario = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedNotes = _naf_textviewer.cTextEditor(self, readOnly=readOnly)

        #cbxPriority = QtGui.QLineEdit(self, readOnly=True)
        cbxPriority = QtGui.QComboBox(self, enabled=not readOnly)
        cbxPriority.setModel(self.mapper.model().getLookupModel('priorityLUT'))

        #cbxUsefrequency = QtGui.QLineEdit(self, readOnly=True)
        cbxUsefrequency = QtGui.QComboBox(self, enabled=not readOnly)
        cbxUsefrequency.setModel(self.mapper.model().getLookupModel('usefrequencyLUT'))

        cbxActors = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxActors.setModel(self.mapper.model().getHistoryModel('actors_view'))
        cbxStakeholders = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxStakeholders.setModel(self.mapper.model().getHistoryModel('stakeholders_view'))

        tedPrerequisites.setImageProvider(nafdb.getImageForId)
        tedMainscenario.setImageProvider(nafdb.getImageForId)
        tedAltscenario.setImageProvider(nafdb.getImageForId)
        tedNotes.setImageProvider(nafdb.getImageForId)

        layout.addWidget(ledId,            0, 1, 1, 3)
        layout.addWidget(ledTitle,         1, 1, 1, 3)
        layout.addWidget(cbxKeywords,      2, 1, 1, 3)
        layout.addWidget(cbxPriority,      3, 1, 1, 1)
        layout.addWidget(cbxUsefrequency,  3, 3, 1, 1)
        layout.addWidget(cbxActors,        4, 1, 1, 3)
        layout.addWidget(cbxStakeholders,  5, 1, 1, 3)
        layout.addWidget(tedPrerequisites, 6, 1, 1, 3)
        layout.addWidget(tedMainscenario,  7, 1, 1, 3)
        layout.addWidget(tedAltscenario,   8, 1, 1, 3)
        layout.addWidget(tedNotes,         9, 1, 1, 3)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        layout.setRowStretch(6, 1)
        layout.setRowStretch(7, 3)
        layout.setRowStretch(8, 2)
        layout.setRowStretch(9, 1)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(cbxPriority, columns.index('priority'))
        self.mapper.addMapping(cbxUsefrequency, columns.index('usefrequency'))
        self.mapper.addMapping(cbxActors, columns.index('actors'))
        self.mapper.addMapping(cbxStakeholders, columns.index('stakeholders'))
        self.mapper.addMapping(tedPrerequisites, columns.index('prerequisites'))
        self.mapper.addMapping(tedMainscenario, columns.index('mainscenario'))
        self.mapper.addMapping(tedAltscenario, columns.index('altscenario'))
        self.mapper.addMapping(tedNotes, columns.index('notes'))


class cUsecaseView(QtGui.QTabWidget):
    TYPE_ID = nafdb.TYPE_USECASE

    def __init__(self, parent, isEditable=False):
        QtGui.QTabWidget.__init__(self, parent)
        self.defaultTitle = self.tr("New Usecase")
        self.editTitle = self.tr("Edit usecase")
        self.mapper = _naf_tableview.cNotifier()
        self.detailsView = cUsecaseDetailsView(self, readOnly=not isEditable)
        self.addTab(self.detailsView, self.tr('Use case'))
        self.mapper.addObserver(self.detailsView)

        self.requirementTableView = _naf_tableview.cItemTableView(_naf_tableview.cItemTableModel('requirements', ('id', 'priority', 'status', 'complexity', 'assigned', 'effort', 'category', 'keywords', 'title'),
            relationType=_naf_tableview.REVERSE_RELATION), self)
        self.addTab(self.requirementTableView, self.tr('Related Requirements'))
        self.mapper.addObserver(self.requirementTableView)
        
        self.featureTableView = _naf_tableview.cItemTableView(_naf_tableview.cItemTableModel('features', ('id', 'priority', 'status', 'risk', 'keywords', 'title'),
            relationType=_naf_tableview.REVERSE_RELATION), self)
        self.addTab(self.featureTableView, self.tr('Related Features'))
        self.mapper.addObserver(self.featureTableView)

    def model(self):
        return self.detailsView.mapper.model()

    def submit(self):
        self.mapper.submit()
