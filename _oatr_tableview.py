from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt
import _oatr_database as oadb 

class cTestrunTableView(QtGui.QTableView):
    def __init__(self, parent=None,  model=None,  selectionHandler=None):
        super(cTestrunTableView, self).__init__(parent, sortingEnabled=True)
        self.selectionHandler = selectionHandler
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.setEditTriggers(self.NoEditTriggers)
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