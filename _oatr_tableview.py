# -*- coding: utf-8  -*-
# $Id$

# -------------------------------------------------------------------
# Copyright 2012 Achim Köhler
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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

import _oatr_database as oadb 
import _naf_database as nafdb

class cTestrunTableView(QtGui.QTableView):
    def __init__(self, parent=None,  model=None,  selectionHandler=None):
        super(cTestrunTableView, self).__init__(parent, sortingEnabled=True)
        self.selectionHandler = selectionHandler
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionBehavior(QtGui.QTableView.SelectRows)
        self.setSelectionMode(QtGui.QTableView.SingleSelection)
        self.setModel(model)
        model.reset()
        model.select()
        self.setHeader()
        hiddencols = (2,4,5,6,7,8,9,10,11,12,13,14,15, 16)
        map(self.setColumnHidden, hiddencols, [True]*len(hiddencols))
        self.horizontalHeader().setStretchLastSection(True)
        self.resizeColumnsToContents() 
        self.selectRow(0)
        
    def setHeader(self):
        model = self.model()
        for section in range(model.columnCount()):
            coltitle = str(model.headerData(section, Qt.Horizontal) .toString())
            model.setHeaderData(section, Qt.Horizontal, oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, coltitle))
            
    def currentChanged(self, current, previous):
        super(cTestrunTableView, self).currentChanged(current,  previous)
        if self.selectionHandler: self.selectionHandler(current)
        
        
class cTestsuiteTableView(QtGui.QTableView):
    def __init__(self, parent=None,  model=None):
        super(cTestsuiteTableView, self).__init__(parent, sortingEnabled=True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionBehavior(QtGui.QTableView.SelectRows)
        self.setSelectionMode(QtGui.QTableView.SingleSelection)
        self.setModel(model)

    def setHeader(self):
        self.horizontalHeader().setStretchLastSection(True)
        for section in range(self.model().columnCount()):
            coltitle = str(self.model().headerData(section, Qt.Horizontal).toString())
            self.model().setHeaderData(section, Qt.Horizontal, nafdb.getColumnDisplayName('testsuites', coltitle))
            