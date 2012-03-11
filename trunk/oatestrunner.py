#!/usr/bin/python
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

import sys
import argparse
import logging
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
from _naf_database import getUserAndDate

WINTITLE = "Test Runner"
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
        self.winTitle = WINTITLE
        self.setWindowTitle(self.winTitle)
        self.setMinimumSize(800, 600)

        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value("mainwindow/geometry").toByteArray())
        self.restoreState(settings.value("mainwindow/windowState").toByteArray())
        
        self.importFileList = []
        size = settings.beginReadArray("importfiles")
        for i in range(size):
            settings.setArrayIndex(i)
            filename = settings.value("name").toString()
            self.importFileList.append(filename)
        settings.endArray()

        self.mainView = QtGui.QSplitter(self)
        self.mainView.setChildrenCollapsible(False)
        self.mainView.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.setCentralWidget(self.mainView)
        self.setupMenu()
        self.statusBar().showMessage('')
        
        if dbName:
            self.openActionHandler(None, dbName)
            
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
        wizard = _oatr_importwizard.cTestrunnerImportWizard()
        wizard.inputFilePicker.setHistory(self.importFileList)
        wizData = wizard.show()
        if not wizData: 
            return
        wizData['source'] = wizData['srcDatabase']
        try:
            _oatr_database.createTestRunDatabase(wizData['srcDatabase'], wizData['destDatabase'],
                                                 wizData['testsuiteId'], 
                                                 wizData) 
            self._loadDatabase(wizData['destDatabase'])
            if self.importFileList.count(wizData['srcDatabase']) == 0:
                # srcDatabase is not in history
                self.importFileList.insert(0, wizData['srcDatabase'])
                if len(self.importFileList) > 5:
                    del self.importFileList[-1]
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)
        
    def _loadDatabase(self, fileName):
        # TODO: probe database for existence and correctness
        self.database = None
        self.database = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.database.setHostName("")
        self.database.setDatabaseName(fileName)
        self.database.open()
        
        self.testrunModel = _oatr_testrun.cTestrunModel(None,  self.database)
        self.testrunModel.setTable('testruns')
        self.testrunModel.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        
        self.testsuiteModel = QtSql.QSqlTableModel(None, self.database)
        self.testsuiteModel.setTable('testsuites')
        self.testsuiteModel.select()

        self.testruninfoModel = QtSql.QSqlTableModel(None, self.database)
        self.testruninfoModel.setTable('testruninfo')
        self.testruninfoModel.select()

        for i in range(self.mainView.count()):
            self.mainView.widget(i).close()
        
        self.testrunDetailView = _oatr_testrun.cTestrunDetailsView(self.mainView, self.testrunModel)
        self.testsuiteDetailView = _oatr_testsuite.cTestsuiteView(self.mainView, self.testsuiteModel)
        self.testsuiteDetailView.mapper.toFirst()
        self.testruninfoDetailView = _oatr_testrun.cTestrunInfoView(self.mainView, self.testruninfoModel)
        self.testruninfoDetailView.mapper.toFirst()

        self.tableView = _oatr_tableview.cTestrunTableView(self.mainView, self.testrunModel, self.testrunTableViewSelectionHandler)
        self.tableView.activated.connect(self.execTestcase)

        self.tabView = QtGui.QTabWidget(self.mainView)
        self.tabView.addTab(self.testrunDetailView, 'Test Details')
        self.tabView.addTab(self.testsuiteDetailView, 'Testsuite')
        self.tabView.addTab(self.testruninfoDetailView, 'Test Run Info')
                
        self.actionsRequiringDatabase.setEnabled(True)
        self.setWindowTitle(QtCore.QFileInfo(fileName).baseName() + ' - ' + WINTITLE)
        self.updateStatusBar()

    def execTestcase(self):
        tableViewIndex = self.tableView.currentIndex()
        row = self.tableView.currentIndex().row()
        index = self.tableView.model().index(row, 0)
        testrunId = self.tableView.model().data(index).toInt()[0]
        query = QtSql.QSqlQuery("SELECT status FROM testruns WHERE id==%d" % testrunId)
        query.next()
        testrunStatus , valid = query.value(0).toInt()
        if not valid:
            raise ValueError
                
        dlg = _oatr_testrun.cTestrunDialog(self.testrunModel)
        dlg.testrunEditor.mapper.setCurrentIndex(index.row())
        if testrunStatus == _oatr_database.STATUS_PENDING:
            (user, timestamp) = getUserAndDate()
            dlg.testrunEditor.setTester(user)
            dlg.testrunEditor.setDate(timestamp)
        if QtGui.QDialog.Accepted == dlg.exec_():
            dlg.updateRow(row)
            self.updateStatusBar()
        self.tableView.setCurrentIndex(tableViewIndex)
        
    def createReport(self):
        # TODO: code this method
        pass
    
    def updateStatusBar(self):
        querystr = "SELECT count(*) FROM testruns where status==%d"
        cnts = []
        for i in range(len(_oatr_database.LOOKUP_TABLES['statusLUT'])):
            query = QtSql.QSqlQuery(querystr % i)
            query.next()
            cnt, _ = query.value(0).toInt()
            cnts.append(cnt)
        s = ', '.join(["%d %s" % (cnt, lbl) for lbl, cnt in zip(_oatr_database.LOOKUP_TABLES['statusLUT'], cnts)])
        s = "%d testcases: %s" % (sum(cnts), s)
        self.statusBar().showMessage(s)

    def testrunTableViewSelectionHandler(self,  index):
        row = index.row()
        self.testrunDetailView.mapper.setCurrentIndex(row)
        
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
        
    def closeEvent(self, event):
        settings = QtCore.QSettings()
        settings.setValue("mainwindow/geometry", self.saveGeometry())
        settings.setValue("mainwindow/windowState", self.saveState())
        settings.beginWriteArray("importfiles")
        for i in range(len(self.importFileList)):
            settings.setArrayIndex(i)
            settings.setValue("name", self.importFileList[i])
        settings.endArray()

STARTUP_CMD_OPEN = 0
STARTUP_CMD_NEW = 1
STARTUP_CMD_ABOUT = 2

class cStartupDialog(QtGui.QDialog):
    def __init__(self, *args, **kwargs):
        super(cStartupDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle(WINTITLE)
        self.setWindowFlags(Qt.Popup)
        self.setStyleSheet("background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 white, stop:1 gray)")
        self.aboutDlgFn = None
        self.retVal = None
        openAction = QtGui.QAction(QtGui.QIcon(':/icons/database_open.png'), self.tr('Open existing test run'), self,
                                   triggered = self.openTestrun,shortcut=QtGui.QKeySequence.Open)
        newAction = QtGui.QAction(QtGui.QIcon(':/icons/database_new.png'), self.tr('Create new test run'), self,
                                  triggered=self.newTestrun, shortcut=QtGui.QKeySequence.New)
        aboutAction = QtGui.QAction(QtGui.QIcon(':/icons/help-browser.png'), self.tr('About'), self,
                                  triggered=self.showAbout, shortcut=QtGui.QKeySequence.HelpContents)
        exitAction = QtGui.QAction(QtGui.QIcon(':/icons/system-log-out.png'), self.tr('Exit'), self,
                                  triggered=self.reject, shortcut=QtGui.QKeySequence('Alt+X'))
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        lbl = QtGui.QLabel()
        lbl.setPixmap(QtGui.QPixmap(':/icons/appicon.png'))
        lbl.setStyleSheet("background-color:rgba(255, 0, 0, 0%)")
        hbox.addWidget(lbl)
        lbl = QtGui.QLabel('<font size="+3"><i><b>openADAMS</b> Test Runner</i></font>')
        lbl.setStyleSheet("color: #404040; background-color:rgba(255, 0, 0, 0%);")
        hbox.addWidget(lbl)
        vbox.addLayout(hbox)
        vbox.addSpacing(30)
        btn = QtGui.QToolButton()
        btn.setStyleSheet("color:white; background-color:rgba(255, 0, 0, 0%);")
        btn.setDefaultAction(openAction)
        lbl = QtGui.QLabel('<font size="+1"><a href="new">' + openAction.text() + '</a></font>')
        lbl.setStyleSheet("background-color:rgba(255, 0, 0, 0%);")
        lbl.linkActivated.connect(self.openTestrun)
        hbox = QtGui.QHBoxLayout()
        hbox.addSpacing(20)
        hbox.addWidget(btn)
        hbox.addWidget(lbl)
        vbox.addLayout(hbox)
        btn = QtGui.QToolButton()
        btn.setStyleSheet("color:white; background-color:rgba(255, 0, 0, 0%);")
        btn.setDefaultAction(newAction)
        lbl = QtGui.QLabel('<font size="+1"><a href="new">' + newAction.text() + '</a></font>')
        lbl.setStyleSheet("background-color:rgba(255, 0, 0, 0%);")
        lbl.linkActivated.connect(self.newTestrun)
        hbox = QtGui.QHBoxLayout()
        hbox.addSpacing(20)
        hbox.addWidget(btn)
        hbox.addWidget(lbl)
        vbox.addLayout(hbox)
        vbox.addSpacing(30)
        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QToolButton()
        btn.setStyleSheet("color:white; background-color:rgba(255, 0, 0, 0%);")
        btn.setDefaultAction(aboutAction)
        hbox.addWidget(btn)
        btn = QtGui.QToolButton()
        btn.setStyleSheet("color:white; background-color:rgba(255, 0, 0, 0%);")
        btn.setDefaultAction(exitAction)
        hbox.addWidget(btn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
    def registerAboutDlgFn(self, dlgFn):
        self.aboutDlgFn = dlgFn
        
    def openTestrun(self):
        self.retVal = STARTUP_CMD_OPEN
        self.accept()
    
    def newTestrun(self):
        self.retVal = STARTUP_CMD_NEW
        self.accept()
        
    def showAbout(self):
        if self.aboutDlgFn:
            self.aboutDlgFn()
        self.retVal = STARTUP_CMD_ABOUT
        self.accept()
            
    def getResult(self):
        return self.retVal
# ------------------------------------------------------------------------------


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
    if not namespace.databasefile:
        dlg = cStartupDialog(mainwin)
        dlg.registerAboutDlgFn(mainwin.showAbout)
        if dlg.exec_() !=  QtGui.QDialog.Rejected:
            result = dlg.getResult()
            if result == STARTUP_CMD_OPEN:
                mainwin.openActionHandler(None, None)
            elif result == STARTUP_CMD_NEW:
                mainwin.newDatabase()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    start()

# TODO: fix help output on command line
# TODO: recent files functionality in importer and file menu