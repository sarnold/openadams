from PyQt4 import QtGui,  QtCore, QtSql
from PyQt4.QtCore import Qt

import _oatr_database as oadb
import _oatr_commons
import _oatr_database

class cTestrunModel(QtSql.QSqlRelationalTableModel):
    def __init__(self, *arg, **kwarg):
        super(cTestrunModel, self).__init__(*arg, **kwarg)
        self.backgroundBrushes = (
                                  QtGui.QBrush(QtGui.QColor(255,255,25)), # pending
                                  QtGui.QBrush(QtGui.QColor(255,48,48)), # failed
                                  QtGui.QBrush(QtGui.QColor(64,255,64)), # passed
                                  QtGui.QBrush(QtGui.QColor(96,96,255)), # skipped
                                  )
    def data(self, index, role = Qt.DisplayRole):
        """
        Overrides data() method to provide background coloring of the status cell 
        in the view
        """
        if role == Qt.BackgroundRole and index.column() == 1:
            status = super(cTestrunModel, self).data(index, Qt.DisplayRole)
            status = oadb.LOOKUP_TABLES['statusLUT'].index(str(status.toString()))            
            return self.backgroundBrushes[status]
        return super(cTestrunModel, self).data(index, role)

class cTestrunItemDelegate(QtSql.QSqlRelationalDelegate):
    def setEditorData(self, editor, index ):
        if isinstance(editor, cTestrunStatusWidget):
            s = index.model().data(index)
            #TODO: status should immediately be read from the database 
            status = _oatr_database.LOOKUP_TABLES['statusLUT'].index(s)
            editor.checkButton(status)
        return super(cTestrunItemDelegate,self).setEditorData(editor, index )
        
    def setModelData(self, editor, model, index):
        return super(cTestrunItemDelegate,self).setModelData(editor, model, index )

    

class cTestrunDetailsView(QtGui.QWidget):
    def __init__(self, parent, model, readOnly = True):
        super(cTestrunDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(model)
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "id")), 1, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "title")), 0, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "keywords"), alignment=Qt.AlignRight|Qt.AlignVCenter), 1, 4)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "priority"), alignment=Qt.AlignRight|Qt.AlignVCenter), 1, 2)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "purpose"), alignment=Qt.AlignTop), 2, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "prerequisite"), alignment=Qt.AlignTop), 3, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "testdata"), alignment=Qt.AlignTop), 4, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "steps"), alignment=Qt.AlignTop),5, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "notes"), alignment=Qt.AlignTop), 6, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "scripturl")), 7, 0)
        
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "status")), 8, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "user"), alignment=Qt.AlignRight|Qt.AlignVCenter), 8, 2)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "date"), alignment=Qt.AlignRight|Qt.AlignVCenter), 8, 4)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "action"), alignment=Qt.AlignTop), 9, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, "remark"), alignment=Qt.AlignTop), 10, 0)

        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=True)
        ledKeywords = QtGui.QLineEdit(self, readOnly=True)
        tedPurpose = _oatr_commons.getTextViewer(self)
        tedPrerequisite = _oatr_commons.getTextViewer(self)
        tedTestdata = _oatr_commons.getTextViewer(self)
        tedSteps = _oatr_commons.getTextViewer(self)
        tedNotes = _oatr_commons.getTextViewer(self)
        ledScripturl = QtGui.QLineEdit(self, readOnly=True)
        ledPriority = QtGui.QLineEdit(self, readOnly=True)
        
        self.ledStatus = QtGui.QLineEdit(self, readOnly=True)
        self.ledTester = QtGui.QLineEdit(self, readOnly=readOnly)
        self.ledDate = QtGui.QLineEdit(self, readOnly=readOnly)
        self.tedAction = QtGui.QTextEdit(self, readOnly=readOnly)
        self.tedRemark = QtGui.QTextEdit(self, readOnly=readOnly)
        
        self.swStatus = cTestrunStatusWidget()
        layout.addWidget(self.swStatus, 11, 1, 1, 5)
        self.mapper.addMapping(self.swStatus, model.fieldIndex('status'))
        self.mapper.setItemDelegate(cTestrunItemDelegate())
        
        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledId,           1, 1, 1, 1)
        layout.addWidget(ledTitle,        0, 1, 1, 5)
        layout.addWidget(ledPriority,     1, 3, 1, 1)
        layout.addWidget(ledKeywords,     1, 5, 1, 1)
        layout.addWidget(tedPurpose,      2, 1, 1, 5)
        layout.addWidget(tedPrerequisite, 3, 1, 1, 5)
        layout.addWidget(tedTestdata,     4, 1, 1, 5)
        layout.addWidget(tedSteps,        5, 1, 1, 5)
        layout.addWidget(tedNotes,        6, 1, 1, 5)
        layout.addWidget(ledScripturl,    7, 1, 1, 5)
        
        layout.addWidget(self.ledStatus, 8, 1, 1, 1)
        layout.addWidget(self.ledDate,   8, 5, 1, 1)
        layout.addWidget(self.ledTester, 8, 3, 1, 1)
        layout.addWidget(self.tedAction, 9, 1, 1, 5)
        layout.addWidget(self.tedRemark, 10, 1, 1, 5)
                         
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(5, 5)
        layout.setColumnStretch(3, 1)
        layout.setRowStretch(3, 2)
        layout.setRowStretch(4, 2)
        layout.setRowStretch(5, 2)
        layout.setRowStretch(6, 5)
        layout.setRowStretch(7, 2)
    
        self.mapper.addMapping(ledId, model.fieldIndex('id'))
        self.mapper.addMapping(ledTitle, model.fieldIndex('title'))
        self.mapper.addMapping(ledKeywords, model.fieldIndex('keywords'))
        self.mapper.addMapping(tedPurpose, model.fieldIndex('purpose'))
        self.mapper.addMapping(tedPrerequisite, model.fieldIndex('prerequisite'))
        self.mapper.addMapping(tedTestdata, model.fieldIndex('testdata'))
        self.mapper.addMapping(tedSteps, model.fieldIndex('steps'))
        self.mapper.addMapping(tedNotes, model.fieldIndex('notes'))
        self.mapper.addMapping(ledScripturl, model.fieldIndex('scripturl'))
        self.mapper.addMapping(ledPriority, model.fieldIndex('priority'))

        self.mapper.addMapping(self.ledStatus, model.fieldIndex('status'))
        self.mapper.addMapping(self.ledTester, model.fieldIndex('user'))
        self.mapper.addMapping(self.ledDate, model.fieldIndex('date'))
        self.mapper.addMapping(self.tedAction, model.fieldIndex('action'))
        self.mapper.addMapping(self.tedRemark, model.fieldIndex('remark'))
        
    def setTester(self, name):
        self.ledTester.setText(name)
        
    def setDate(self, datestr):
        self.ledDate.setText(datestr)
        
            
class cTestrunStatusWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(cTestrunStatusWidget, self).__init__(parent)
        self.buttons = []
        rbGroup = QtGui.QButtonGroup(self)
        hBox = QtGui.QHBoxLayout()
        for label in _oatr_database.LOOKUP_TABLES['statusLUT']:
            rb = QtGui.QRadioButton(label)
            self.buttons.append(rb)
            rbGroup.addButton(rb)
            hBox.addWidget(rb)
        self.setLayout(hBox)
        
    def checkButton(self, index):
        for rb in self.buttons: rb.setChecked(False)
        self.buttons[index].setChecked(True)
    
class cTestrunInfoView(QtGui.QWidget):
    def __init__(self, parent, model):
        super(cTestrunInfoView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(model)
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUNINFO_TABLE, "title")), 0, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUNINFO_TABLE, "description"), alignment=Qt.AlignTop), 1, 0)
        layout.addWidget(QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUNINFO_TABLE, "source")), 2, 0)
        
        ledTitle = QtGui.QLineEdit(self, readOnly=True)
        tedDescription = QtGui.QTextEdit(self, readOnly=True)
        ledSource = QtGui.QLineEdit(self, readOnly=True)

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledTitle,       0, 1, 1, 1)
        layout.addWidget(tedDescription, 1, 1, 1, 1)
        layout.addWidget(ledSource,      2, 1, 1, 1)
                         
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 2)
    
        self.mapper.addMapping(ledTitle, model.fieldIndex('title'))
        self.mapper.addMapping(tedDescription, model.fieldIndex('description'))
        self.mapper.addMapping(ledSource, model.fieldIndex('source'))
        