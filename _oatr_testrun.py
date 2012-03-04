import logging
from PyQt4 import QtGui,  QtCore, QtSql
from PyQt4.QtCore import Qt

import _oatr_database as oadb
import _oatr_commons
import _oatr_database

#class cTestrunModel(QtSql.QSqlRelationalTableModel):
class cTestrunModel(QtSql.QSqlTableModel):
    # we have foreign keys but we don't use QSqlRelationalTableModel because of
    # troubles when using QDataWidgetMapper
    # Instead we implement relations by programming them
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
        if index.column() == 1:
            # status column
            (status, valid) = super(cTestrunModel, self).data(index, Qt.DisplayRole).toInt()
            if role == Qt.DisplayRole:
                return oadb.LOOKUP_TABLES['statusLUT'][status] 
            elif role == Qt.BackgroundRole:
                return self.backgroundBrushes[status]
        return super(cTestrunModel, self).data(index, role)


class cTestrunItemDelegate(QtGui.QItemDelegate):#(QtSql.QSqlRelationalDelegate):
    def setEditorData(self, editor, index ):
        if isinstance(editor, cTestrunStatusWidget):   
            statusStr = index.model().data(index)
            status = oadb.LOOKUP_TABLES['statusLUT'].index(statusStr) 
            editor.checkButton(status)
        elif editor.property('oatrname').isValid() and editor.property('oatrname').toString() == 'ledPriority':
            (priority, valid) = index.model().data(index).toInt()
            editor.setText(oadb.LOOKUP_TABLES['priorityLUT'][priority]) 
        super(cTestrunItemDelegate,self).setEditorData(editor, index )
        
    def setModelData(self, editor, model, index):
        if isinstance(editor, cTestrunStatusWidget):   
            model.setData(index, editor.getChecked(), QtCore.Qt.EditRole)
        else:
            super(cTestrunItemDelegate,self).setModelData(editor, model, index )

    
class cTestrunDetailsView(QtGui.QWidget):
    def __init__(self, parent, model, readOnly = True):
        super(cTestrunDetailsView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(model)
        self.mapper.setItemDelegate(cTestrunItemDelegate())
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)
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
        
        columns = "status user date action remark".split()
        labels = []
        for c in columns:
            lbl = QtGui.QLabel(oadb.getDisplayNameForColumn(oadb.TESTRUN_TABLE, c))
            if not readOnly:
                lbl.setStyleSheet('color:red; text-decoration:underline')
            labels.append(lbl)
        layout.addWidget(labels[0], 8, 0)
        layout.addWidget(labels[1], 9, 0)
        layout.addWidget(labels[2], 9, 4, alignment=Qt.AlignRight|Qt.AlignVCenter)
        layout.addWidget(labels[3], 10, 0, alignment=Qt.AlignTop)
        layout.addWidget(labels[4], 11, 0, alignment=Qt.AlignTop)

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
        ledPriority.setProperty('oatrname', 'ledPriority')
        self.swStatus = cTestrunStatusWidget(self, readOnly=readOnly)
        self.ledTester = QtGui.QLineEdit(self, readOnly=readOnly)
        self.ledDate = QtGui.QLineEdit(self, readOnly=readOnly)
        self.tedAction = QtGui.QTextEdit(self, readOnly=readOnly)
        self.tedAction.setWhatsThis(self.tr("Action taken when the testcase has failed"))
        self.tedRemark = QtGui.QTextEdit(self, readOnly=readOnly)
        self.tedRemark.setWhatsThis(self.tr("Remark for executed testcase"))
        
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
        
        layout.addWidget(self.swStatus, 8, 1, 1, 5)
        layout.addWidget(self.ledDate,   9, 5, 1, 1)
        layout.addWidget(self.ledTester, 9, 1, 1, 3)
        layout.addWidget(self.tedAction, 10, 1, 1, 5)
        layout.addWidget(self.tedRemark, 11, 1, 1, 5)
                         
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(5, 5)
        layout.setColumnStretch(3, 1)
        layout.setRowStretch(3, 2)
        layout.setRowStretch(4, 2)
        layout.setRowStretch(5, 2)
        layout.setRowStretch(6, 5)
        layout.setRowStretch(8, 2)
    
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

        self.mapper.addMapping(self.swStatus, model.fieldIndex('status'))
        self.mapper.addMapping(self.ledTester, model.fieldIndex('user'))
        self.mapper.addMapping(self.ledDate, model.fieldIndex('date'))
        self.mapper.addMapping(self.tedAction, model.fieldIndex('action'))
        self.mapper.addMapping(self.tedRemark, model.fieldIndex('remark'))
        
    def setTester(self, name):
        self.ledTester.setText(name)
        
    def setDate(self, datestr):
        self.ledDate.setText(datestr)

    def model(self):
        return self.mapper.model()

    def submit(self):
        self.mapper.submit()
        
    def getData(self):
        return {'status' : self.swStatus.getChecked(), 'user' : self.ledTester.text(),
         'date' : self.ledDate.text(), 'action' : self.tedAction.toPlainText(),
         'remark' : self.tedRemark.toPlainText()}
        
            
class cTestrunStatusWidget(QtGui.QWidget):
    def __init__(self, parent=None, readOnly=True):
        super(cTestrunStatusWidget, self).__init__(parent)
        self.buttons = []
        rbGroup = QtGui.QButtonGroup(self)
        rbGroup
        hBox = QtGui.QHBoxLayout()
        for label in _oatr_database.LOOKUP_TABLES['statusLUT']:
            rb = QtGui.QRadioButton(label)
            rb.setDisabled(readOnly)
            self.buttons.append(rb)
            rbGroup.addButton(rb)
            hBox.addWidget(rb)
        self.setLayout(hBox)
        
    def checkButton(self, index):
        for rb in self.buttons: rb.setChecked(False)
        self.buttons[index].setChecked(True)
        
    def getChecked(self):
        return [btn.isChecked() for btn in self.buttons].index(True)
    
    
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


class cTestrunDialog(QtGui.QDialog):
    def __init__(self, model, parent=None):
        super(cTestrunDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Execute testcase"))
        layout = QtGui.QVBoxLayout()
        testrunEditor = cTestrunDetailsView(self, model, readOnly=False)
        layout.addWidget(testrunEditor)
        self.testrunEditor = testrunEditor
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        
    def updateRow(self, row):
        model = self.testrunEditor.model()
        record = model.record(row)
        for k, v in self.testrunEditor.getData().iteritems():
            record.setValue(k, v)
        model.setRecord(row, record)