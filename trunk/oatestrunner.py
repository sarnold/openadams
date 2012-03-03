#!/usr/bin/python
# -*- coding: utf-8  -*-
# $Id$

# -------------------------------------------------------------------
# Copyright 2012 Achim K�hler
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

import sys
import argparse
import logging
import os.path
import traceback

from PyQt4 import QtGui,  QtCore,  QtSql
from PyQt4.QtCore import Qt

from _naf_version import VERSION, VERSION_STR, SVN_STR
import _oatr_testrun
import _oatr_testsuite
import _oatr_tableview
import _oatr_database
import _naf_about
import _naf_resources
import _oatr_importwizard
import _oatr_database
from _naf_database import getUserAndDate

PROGNAME = 'oatestrunner'
ABOUTMSG = u"""oatestrunner %s
openADAMS Test Runner 

Copyright (C) 2012 Achim Koehler

%s
""" % (VERSION, SVN_STR)

# ------------------------------------------------------------------------------
# Initialize application and translators here, because we have static strings
# in _naf_database which needs to be translated
# ------------------------------------------------------------------------------
app = QtGui.QApplication(sys.argv)
app.setOrganizationName("")
app.setOrganizationDomain("macht-publik.de")
app.setApplicationName("oatestrunner")
app.setWindowIcon(QtGui.QIcon(":/icons/appicon.png"))

QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)

qtTranslator = QtCore.QTranslator()
qtTranslator.load("qt_" + QtCore.QLocale.system().name(), QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
app.installTranslator(qtTranslator)

appTranslator = QtCore.QTranslator()
appTranslator.load("oatr_" + QtCore.QLocale.system().name())
app.installTranslator(appTranslator)
# ------------------------------------------------------------------------------
class cMainWin(QtGui.QMainWindow):
    def __init__(self, dbName=None):
        super(cMainWin,  self).__init__()
        self.windowTitleStr = self.tr('Test Runner')
        self.winTitle = self.windowTitleStr
        self.setWindowTitle(self.winTitle)
        self.setMinimumSize(800, 600)

        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value("mainwindow/geometry").toByteArray());
        self.restoreState(settings.value("mainwindow/windowState").toByteArray());

        self.database = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.database.setHostName("")
        # create an empty database in memory, just to setup GUI correctly
        self.database.setDatabaseName(":memory:")
        self.database.open()
        _oatr_database.createTestRunTables(self.database)
        self._createTestrunModel()
        
        self.testsuiteModel = QtSql.QSqlTableModel(None, self.database)
        self.testsuiteModel.setTable('testsuites')
        
        self.testruninfoModel = QtSql.QSqlTableModel(None, self.database)
        self.testruninfoModel.setTable('testruninfo')
        
        self.mainView = QtGui.QSplitter(self)
        self.mainView.setFrameStyle(QtGui.QFrame.StyledPanel);
        
        self.tableView = _oatr_tableview.cTestrunTableView(self.mainView, self.testrunModel, self.testrunTableViewSelectionHandler)
        hiddencols = (2,4,5,6,7,8,9,10,11,12,13,14,15, 16)
        map(self.tableView.setColumnHidden, hiddencols, [True]*len(hiddencols))
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.activated.connect(self.execTestcase)
        self.testrunDetailView = _oatr_testrun.cTestrunDetailsView(self.mainView, self.testrunModel)
        self.testsuiteDetailView = _oatr_testsuite.cTestsuiteView(self.mainView, self.testsuiteModel)
        self.testruninfoDetailView = _oatr_testrun.cTestrunInfoView(self.mainView, self.testruninfoModel)
        self.setCentralWidget(self.mainView)

        self.tabView = QtGui.QTabWidget(self.mainView)
        self.tabView.addTab(self.testrunDetailView, 'Test Details')
        self.tabView.addTab(self.testsuiteDetailView, 'Testsuite')
        self.tabView.addTab(self.testruninfoDetailView, 'Test Run Info')
        
        self.setupMenu()
        self.mainView.setEnabled(False)
        
        if dbName:
            self.openActionHandler(None, dbName)

    def _createTestrunModel(self):
        self.testrunModel = _oatr_testrun.cTestrunModel(None,  self.database)
        self.testrunModel.setTable('testruns')
        #self.testrunModel.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.testrunModel.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        
    def testrunTableViewSelectionHandler(self,  index):
        row = index.row()
        self.testrunDetailView.mapper.setCurrentIndex(row)
        
    #TODO: remove this method
    def createSampleDatabase(self):
        testFileName = 'tests/samplerun_out.dbt'
        if os.path.exists(testFileName):
            os.remove(testFileName)
        _oatr_database.createTestRunDatabase('tests/samplerun_in.db', testFileName, 11, 
                                             {'title': 'Info title', 'description': 'Info description', 'source': 'unknown'})
        self._loadDatabase(testFileName)
        self.database.exec_('update testruns set status=1 where id=14')

    def setupMenu(self):
        exitAction = QtGui.QAction(self.tr('Exit'), self, statusTip=self.tr('Exit application'),
                                   triggered=self.close, shortcut=QtGui.QKeySequence.Close)
        openAction = QtGui.QAction(QtGui.QIcon(':/icons/database_open.png'), self.tr('Open test run'), self, statusTip=self.tr('Open existing test run'),
                                   triggered = self.openActionHandler,shortcut=QtGui.QKeySequence.Open)
        newAction = QtGui.QAction(QtGui.QIcon(':/icons/database_new.png'), self.tr('New test run'), self, statusTip=self.tr('Create new test run'),
                                  triggered=self.newDatabase, shortcut=QtGui.QKeySequence.New)
        reportAction = QtGui.QAction(self.tr('Create test run report'), self, statusTip="Create a report of the test run",
            triggered=self.createReport)
        execTestcaseAction = QtGui.QAction(QtGui.QIcon(':/icons/arrow-right.png'), self.tr('Execute test'), self, statusTip="Execute selected testcase",
            triggered=self.execTestcase)
        aboutAction = QtGui.QAction(self.tr('About'), self, statusTip = self.tr('About this program'),
                                    triggered=self.showAbout, shortcut=QtGui.QKeySequence.HelpContents)
        self.actionsRequiringDatabase = QtGui.QActionGroup(self)
        self.actionsRequiringDatabase.addAction(reportAction)
        self.actionsRequiringDatabase.addAction(execTestcaseAction)
        self.actionsRequiringDatabase.setEnabled(False)
        
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu(self.tr('&File'))
        map(fileMenu.addAction, (newAction, openAction, reportAction, exitAction))
        execMenu = menuBar.addMenu(self.tr('&Run'))
        map(execMenu.addAction, (execTestcaseAction, ))
        helpMenu = menuBar.addMenu(self.tr('&Help'))
        map(helpMenu.addAction, (aboutAction, ))
        
        self.toolBar = self.addToolBar(self.tr('Toolbar'))
        self.toolBar.pyqtConfigure(objectName='maintoolbar')
        map(self.toolBar.addAction, (openAction, newAction, execTestcaseAction))
    
    def _loadDatabase(self, fileName):
        # TODO: probe database file before loading
        self.database.close()
        self.database.setDatabaseName(fileName)
        self.database.open()
        
        self.testrunModel = None
        self._createTestrunModel()
        self.tableView.setModel(self.testrunModel)
        self.testrunDetailView.setModel(self.testrunModel)
        
        self.testrunModel.reset()
        self.testrunModel.select()
        self.testsuiteModel.reset()
        self.testsuiteModel.select()
        self.testsuiteDetailView.mapper.toFirst()
        self.testruninfoModel.reset()
        self.testruninfoModel.select()
        self.testruninfoDetailView.mapper.toFirst()
        self.tableView.resizeColumnsToContents() 
        self.tableView.selectRow(0)
        self.actionsRequiringDatabase.setEnabled(True)
        self.mainView.setEnabled(True)
        self.setWindowTitle(QtCore.QFileInfo(fileName).baseName() + ' - ' + self.windowTitleStr)
        self.updateStatusBar()
        
    def updateStatusBar(self):
        # TODO: provide statistic in statusbar
        querystr = "SELECT count(*) FROM testruns where status==%d"
        cnts = []
        for i in range(len(_oatr_database.LOOKUP_TABLES['statusLUT'])):
            query = QtSql.QSqlQuery(querystr % i)
            query.next()
            cnt, _ = query.value(0).toInt()
            cnts.append(cnt)
        s = ', '.join(["%d %s" % (cnt, lbl) for lbl, cnt in zip(_oatr_database.LOOKUP_TABLES['statusLUT'], cnts)])
        self.statusBar().showMessage(s)
        
    def createReport(self):
        # TODO: code this method
        print "createReport"
        self.testrunModel.submit()
        self.testrunModel.revertAll()
        pass
    
    def openActionHandler(self, sender=None, fileName=None):
        if fileName is None:
            fileName = unicode(QtGui.QFileDialog.getOpenFileName(self, self.tr("Open testrun database"), ".", self.tr("Testrun Database Files (*.dbt);;All files (*.*)")))
        if fileName == '':
            return
        try:
            self._loadDatabase(fileName)
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)
    
    def newDatabase(self):
        # TODO: manage history settings in wizard
        wizard = _oatr_importwizard.cTestrunnerImportWizard()
        wizData = wizard.show()
        if not wizData: 
            return
        wizData['source'] = wizData['srcDatabase']
        try:
            _oatr_database.createTestRunDatabase(wizData['srcDatabase'], wizData['destDatabase'],
                                                 wizData['testsuiteId'], 
                                                 wizData) 
            self._loadDatabase(wizData['destDatabase'])
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)

    def execTestcase(self):
        index = self.tableView.model().index(self.tableView.currentIndex().row(), 0)
        testrunId = self.tableView.model().data(index).toInt()[0]
        query = QtSql.QSqlQuery("SELECT status FROM testruns WHERE id==%d" % testrunId)
        query.next()
        testrunStatus , valid = query.value(0).toInt()
        if not valid:
            raise ValueError
                
        dlg = cTestrunDialog(self.testrunModel)
        dlg.testrunEditor.mapper.setCurrentIndex(index.row())
        if testrunStatus == _oatr_database.STATUS_PENDING:
            (user, timestamp) = getUserAndDate()
            dlg.testrunEditor.setTester(user)
            dlg.testrunEditor.setDate(timestamp)
        if QtGui.QDialog.Accepted == dlg.exec_():
            dlg.testrunEditor.submit()
            #self.testrunModel.submitAll()
            print ">>" + self.testrunModel.lastError().text() + "<<"
            self.updateStatusBar()
            print self.database.databaseName()
        
    
    def showAbout(self):
        aboutText = str(self.tr("""
        <div align="center" style="font-size:large;">
        <p style="font-size:x-large;"><b>openADAMS Testrunner %s</b></p>
        <p><small>[%s]</small><p>
        <p>Copyright (C) 2012 Achim K&ouml;hler</p>
        <p>Testrunner for the Open "Artifact Documentation And Management System"</p>
        <p>See <a href="https://sourceforge.net/projects/openadams/">openADAMS Homepage</a> for details.</p>
        <blockquote>This program comes with ABSOLUTELY NO WARRANTY;<br/>
        This is free software, and you are welcome to redistribute it<br/>
        under the terms of the GNU General Public License; <br/>
        see the accompanied file COPYING for details.
        </blockquote>
        </div>
        """)) % (VERSION, VERSION_STR)
        _naf_about.cAbout(self, aboutText).exec_()
    
    
    def showExceptionMessageBox(self, type_, value, tb):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, self.tr("Error"), QtCore.QString(str(value)))
        msgBox.setDetailedText(QtCore.QString(''.join(traceback.format_exception( type_, value, tb))))
        msgBox.exec_()
        
        
class cTestrunDialog(QtGui.QDialog):
    def __init__(self, model, parent=None):
        super(cTestrunDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Execute testcase"))
        layout = QtGui.QVBoxLayout()
        testrunEditor = _oatr_testrun.cTestrunDetailsView(self, model, readOnly=False)
        layout.addWidget(testrunEditor)
        self.testrunEditor = testrunEditor
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

# ------------------------------------------------------------------------------
def start():
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description=ABOUTMSG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version='%s %s\n%s' % (PROGNAME,  VERSION, SVN_STR))
    parser.add_argument('-l',  '--log',  action='store',  nargs=1, default=['critical'],  type=str,
                        help='log level, either debug, info, error',  metavar='lvl',  dest='loglevel',
                        choices=['debug',  'info', 'error'])
    parser.add_argument('databasefile',  action='store',  type=str, nargs='?',
                        help='Database file')
    namespace=parser.parse_args()
    level = {'critical':logging.CRITICAL, 'debug': logging.DEBUG,
                'info': logging.INFO, 'error': logging.ERROR}[namespace.loglevel[0]]
    logFormat = '%(module)s:%(lineno)s (%(funcName)s): %(message)s'
    logging.basicConfig(format=logFormat, level=level,
                        ##, filemode='w', filename='myapp.log'
                        )
    mainwin = cMainWin(namespace.databasefile)
    mainwin.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    start()

# TODO: fix help output on command line
# TODO: deal with images in testcase fields
