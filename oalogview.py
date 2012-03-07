import sys
import json
from PyQt4 import QtGui,  QtCore,  QtSql
from PyQt4.QtCore import Qt
import _naf_database as nafdb

WINTITLE = "Log Viewer"

class cChangeModel(QtSql.QSqlTableModel):
    def __init__(self, *args, **kwargs):
        super(cChangeModel, self).__init__(*args, **kwargs)
        self.setTable("changes")
        self.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        
    def data(self, index, role = Qt.DisplayRole):
        """
        Overrides data() method to provide lookup values in cells
        """
        if role == Qt.DisplayRole:
            if index.column() == 5:
                # changetype column
                (changetype, _) = super(cChangeModel, self).data(index, Qt.DisplayRole).toInt()
                return nafdb.CHANGESTRING[changetype] 
            elif index.column() == 3:
                # description column
                description = str(super(cChangeModel, self).data(index, Qt.DisplayRole).toString())
                try:
                    descriptionList = json.loads(description)
                    value = [item['column'] for item in descriptionList]
                    return ', '.join(value)
                except:
                    return description
        return super(cChangeModel, self).data(index, role)
    
class cChangeTableView(QtGui.QTableView):
    def __init__(self, parent, model, selectionHandler=None):
        super(cChangeTableView, self).__init__(parent, sortingEnabled=True)
        self.selectionHandler = selectionHandler
        self.setModel(model)
        hiddencols = (1, 8)
        map(self.setColumnHidden, hiddencols, [True]*len(hiddencols))
        self.setHeader()
        self.resizeColumnToContents(2) 
        self.setSelectionBehavior(QtGui.QTableView.SelectRows)
        self.setSelectionMode(QtGui.QTableView.SingleSelection)

    def getHeaderString(self, name):
        return {'id': self.tr('Change ID'),
                'typeid': self.tr('Artifact Type'),
                'title': self.tr('Title'),
                'description': self.tr('Affected fields'),
                'afid': self.tr('Artifact ID'),
                'changetype': self.tr('Change type'),
                'date': self.tr('Date'),
                'user': self.tr('User'),
                'viewpos': self.tr('View pos')}[name]
    
    def setHeader(self):
        model = self.model()
        for section in range(model.columnCount()):
            colname = str(model.headerData(section, Qt.Horizontal) .toString())
            model.setHeaderData(section, Qt.Horizontal, self.getHeaderString(colname))
            
    def currentChanged(self, current, previous):
        super(cChangeTableView, self).currentChanged(current,  previous)
        if self.selectionHandler: self.selectionHandler(current)
    
    
class cMainWin(QtGui.QMainWindow):
    def __init__(self, database, *args, **kwargs):
        super(cMainWin, self).__init__(*args, **kwargs)
        self.winTitle = WINTITLE
        self.setWindowTitle(self.winTitle)
        self.setMinimumSize(800, 600)
        model = cChangeModel(None, database)
        model.select()
        self.tableView = cChangeTableView(None, model, self.tableSelectionChanged)
        self.setCentralWidget(self.tableView)
        
    def tableSelectionChanged(self, index):
        print index.row()
        pass
     
# ------------------------------------------------------------------------------
app = QtGui.QApplication(sys.argv)

database = QtSql.QSqlDatabase.addDatabase("QSQLITE")
database.setHostName("")
database.setDatabaseName("tests/samplerun_in.db")
database.open()

mainwin = cMainWin(database)
mainwin.show()
sys.exit(app.exec_())