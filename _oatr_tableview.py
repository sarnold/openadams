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
        model.select()
        self.setHeader()
        
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
            