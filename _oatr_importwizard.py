from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtCore import Qt

import filepicker
import _oatr_tableview
import _oatr_commons

class cTestrunnerImportWizard(QtCore.QObject):
    def __init__(self, parent=None):
        super(cTestrunnerImportWizard, self).__init__()
        self.testsuiteWizardPage = cTestsuiteWizardPage()
        self.infoWizardPage = cInfoWizardPage()
        self.wizard = QtGui.QWizard()
        self.wizard.addPage(self.createImportDatabasePage())
        self.wizard.addPage(self.testsuiteWizardPage)
        self.wizard.addPage(self.infoWizardPage)
        self.wizard.setWindowTitle(self.tr("Create new testrun"))
        self.wizard.currentIdChanged.connect(self.idChangedHandler)
                
    def idChangedHandler(self, currentId):
        if currentId == 0:
            # on first page, disable continue button when import filename is invalid
            self.wizard.button(QtGui.QWizard.NextButton).setEnabled(self.inputFilePicker.isValidFilename())
        elif currentId == 1:
            self.testsuiteWizardPage.initTable(self.inputFilePicker.getFilename())
            self.wizard.button(QtGui.QWizard.NextButton).setDisabled(self.testsuiteWizardPage.tableIsEmpty())
        elif currentId == 2:
            self.wizard.button(QtGui.QWizard.FinishButton).setEnabled(False) # user has to enter 
            fileInfo = QtCore.QFileInfo(self.inputFilePicker.getFilename())
            fileInfo.setFile(fileInfo.dir(), fileInfo.baseName()+'.%s' % _oatr_commons.TR_FILE_SUFFIX)
            fileName = fileInfo.filePath()
            self.infoWizardPage.outputFilePicker.setFileName(fileName)
        else:
            pass
        
    def createImportDatabasePage(self):
        page = QtGui.QWizardPage()
        page.setTitle(self.tr("Select database with testsuite to run"))
        layout = QtGui.QHBoxLayout()
        self.inputFilePicker = filepicker.cFilePicker()
        self.inputFilePicker.sigValidFilename.connect(self.validImportFilename)
        widgets = self.inputFilePicker.getWidgets()
        widgets['label'].setText(self.tr("Database"))
        widgets['dialog'].setNameFilter(self.tr("Database files (*.db);;All files (*.*)"))
        widgets['dialog'].setFileMode(QtGui.QFileDialog.ExistingFile)
        #TODO: remove next line
        self.inputFilePicker.setHistory(['C:/work/openadams/trunk/tests/samplerun_in.db', 'aaa', 'bbb'])
        map(layout.addWidget, [w for w in (widgets['label'], widgets['combobox'], widgets['button'])])
        layout.setStretch(1, 10)
        page.setLayout(layout)
        return page
    
    def show(self):
        if self.wizard.exec_() == QtGui.QDialog.Accepted:
            return {'srcDatabase': self.inputFilePicker.getFilename(),
                    'destDatabase': self.infoWizardPage.outputFilePicker.getFilename(),
                    'testsuiteId': self.testsuiteWizardPage.getSelectedTestsuiteId(),
                    'title': str(self.infoWizardPage.leTitle.text()),
                    'description': str(self.infoWizardPage.teDescription.toPlainText())}
        else:
            return None
        
    def validImportFilename(self, isValid):
        self.wizard.button(QtGui.QWizard.NextButton).setEnabled(isValid)
          
class cTestsuiteWizardPage(QtGui.QWizardPage):
    def __init__(self):
        super(cTestsuiteWizardPage, self).__init__()
        self.setTitle(self.tr("Select testsuite to run"))
        layout = QtGui.QHBoxLayout()
        self.tableView = _oatr_tableview.cTestsuiteTableView(self, model=None)
        layout.addWidget(self.tableView)
        self.setLayout(layout)
        
    def initTable(self, databaseName):
        self.database = QtSql.QSqlDatabase.addDatabase("QSQLITE", 'importconnection')
        self.database.setHostName("")
        self.database.setDatabaseName(databaseName)
        self.database.open()
        model = QtSql.QSqlTableModel(self, self.database)
        model.setTable('testsuites')
        self.tableView.setModel(model)
        hiddencols = (1,3,4,5,6,7)
        map(self.tableView.setColumnHidden, hiddencols, [True]*len(hiddencols))
        self.tableView.setHeader()
        model.reset()
        model.select()
        if not self.tableIsEmpty():
            self.tableView.selectRow(0)
        
    def tableIsEmpty(self):
        return self.tableView.model().rowCount() == 0
    
    def getSelectedTestsuiteId(self):
        index = self.tableView.model().index(self.tableView.currentIndex().row(), 0)
        return self.tableView.model().data(index).toInt()[0]


class cInfoWizardPage(QtGui.QWizardPage):
    def __init__(self):
        super(cInfoWizardPage, self).__init__()
        self.setTitle(self.tr("Enter testrun information"))
        layout = QtGui.QGridLayout()
        self.outputFilePicker = filepicker.cFilePicker()
        widgets = self.outputFilePicker.getWidgets()
        widgets['label'].setText(self.tr("Testrun file"))
        widgets['dialog'].setNameFilter(self.tr("Testrun files (*.%s);;All files (*.*)" % _oatr_commons.TR_FILE_SUFFIX))
        widgets['dialog'].setFileMode(QtGui.QFileDialog.AnyFile)
        widgets['dialog'].setAcceptMode(QtGui.QFileDialog.AcceptSave)
        layout.addWidget(widgets['label'], 0, 0)
        layout.addWidget(widgets['combobox'], 0, 1)
        layout.addWidget(widgets['button'], 0, 2)
        layout.addWidget(QtGui.QLabel(self.tr("Title")), 1, 0)
        self.leTitle = QtGui.QLineEdit()
        self.registerField("title*", self.leTitle); # title is mandatory
        layout.addWidget(self.leTitle, 1, 1, 1, 2)
        layout.addWidget(QtGui.QLabel(self.tr("Description"), alignment=Qt.AlignTop), 2, 0)
        self.teDescription = QtGui.QTextEdit()
        layout.addWidget(self.teDescription, 2, 1, 1, 2)
        layout.setColumnStretch(1, 1)
        self.setLayout(layout)
        
    def validatePage(self):
        fileName = self.outputFilePicker.getFilename()
        if QtCore.QFile.exists(fileName):
            r = QtGui.QMessageBox.warning(self, self.tr("Overwrite file"),
                                              self.tr("File %s already exists. Okay to overwrite?" % fileName),
                                              QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
            if r == QtGui.QMessageBox.No:
                return False
            if not QtCore.QFile.remove(fileName):
                QtGui.QMessageBox.critical(self, self.tr("Failure"), self.tr("Failed to remove file %s" % fileName))
                return False
        return True
                