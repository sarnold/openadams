# -*- coding: utf-8  -*-
# $Id: _naf_testcase.py 50 2012-02-16 18:15:16Z achimk $

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


class cTestcaseView(QtGui.QWidget):

    def __init__(self, parent, readOnly=True):
        super(cTestcaseView, self).__init__(parent)

        columns = self.mapper.model().getColumns()
        lbl = self.mapper.model().getLabel
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(lbl("id")), 0, 0)
        layout.addWidget(QtGui.QLabel(lbl("title")), 1, 0)
        layout.addWidget(QtGui.QLabel(lbl("keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(lbl("priority")), 2, 2)

        lblPurpose = self.makeEditLinkLabel("purpose", readOnly)
        lblPurpose.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblPurpose, 3, 0)

        lblPrerequisite = self.makeEditLinkLabel("prerequisite", readOnly)
        lblPrerequisite.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblPrerequisite, 4, 0)

        lblTestdata = self.makeEditLinkLabel("testdata", readOnly)
        lblTestdata.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblTestdata, 5, 0)

        lblSteps = self.makeEditLinkLabel("steps", readOnly)
        lblSteps.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblSteps, 6, 0)

        lblNotes = self.makeEditLinkLabel("notes", readOnly)
        lblNotes.linkActivated.connect(self.sendEditSignal)
        layout.addWidget(lblNotes, 7, 0)

        layout.addWidget(QtGui.QLabel(lbl("scripturl")), 8, 0)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=readOnly)
        cbxKeywords = QtGui.QComboBox(self, enabled=not readOnly, editable=True)
        cbxKeywords.setModel(self.mapper.model().getHistoryModel('keywords_view'))
        tedPurpose = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedPurpose.setImageProvider(nafdb.getImageForId)
        tedPrerequisite = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedPrerequisite.setImageProvider(nafdb.getImageForId)
        tedTestdata = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedTestdata.setImageProvider(nafdb.getImageForId)
        tedSteps = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedSteps.setImageProvider(nafdb.getImageForId)
        tedNotes = _naf_textviewer.cTextEditor(self, readOnly=readOnly)
        tedNotes.setImageProvider(nafdb.getImageForId)
        ledScripturl = QtGui.QLineEdit(self, readOnly=readOnly)
        cbxPriority = QtGui.QComboBox(self, enabled=not readOnly)
        cbxPriority.setModel(self.mapper.model().getLookupModel('priorityLUT'))

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,           0, 1, 1, 3)
        layout.addWidget(ledTitle,        1, 1, 1, 3)
        layout.addWidget(cbxPriority,     2, 3, 1, 1)
        layout.addWidget(cbxKeywords,     2, 1, 1, 1)
        layout.addWidget(tedPurpose,      3, 1, 1, 3)
        layout.addWidget(tedPrerequisite, 4, 1, 1, 3)
        layout.addWidget(tedTestdata,     5, 1, 1, 3)
        layout.addWidget(tedSteps,        6, 1, 1, 3)
        layout.addWidget(tedNotes,        7, 1, 1, 3)
        layout.addWidget(ledScripturl,    8, 1, 1, 3)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(3, 2)
        layout.setRowStretch(4, 2)
        layout.setRowStretch(5, 2)
        layout.setRowStretch(6, 5)
        layout.setRowStretch(7, 2)

        self.mapper.addMapping(ledId, columns.index('id'))
        self.mapper.addMapping(ledTitle, columns.index('title'))
        self.mapper.addMapping(cbxKeywords, columns.index('keywords'))
        self.mapper.addMapping(tedPurpose, columns.index('purpose'))
        self.mapper.addMapping(tedPrerequisite, columns.index('prerequisite'))
        self.mapper.addMapping(tedTestdata, columns.index('testdata'))
        self.mapper.addMapping(tedSteps, columns.index('steps'))
        self.mapper.addMapping(tedNotes, columns.index('notes'))
        self.mapper.addMapping(ledScripturl, columns.index('scripturl'))
        self.mapper.addMapping(cbxPriority, columns.index('priority'))
