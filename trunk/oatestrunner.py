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

from PyQt4 import QtGui,  QtCore,  QtSql
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QCoreApplication, QObject, QString

from _naf_version import VERSION, VERSION_STR, SVN_STR
import _oatr_testrun
import _oatr_testsuite
import _oatr_tableview
import _oatr_database
import _oatr_commons
import _naf_resources

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
        self.winTitle = self.tr('Test Runner')
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
        self.testrunModel = _oatr_testrun.cTestrunModel(None,  self.database)
        self.testrunModel.setTable('testruns')
        self.testrunModel.setRelation(self.testrunModel.fieldIndex('priority'),
                                      QtSql.QSqlRelation('priorityLUT', 'key', 'value'))
        self.testrunModel.setRelation(self.testrunModel.fieldIndex('status'),
                                      QtSql.QSqlRelation('statusLUT', 'key', 'value'))
        
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
        self.testrunDetailView = _oatr_testrun.cTestrunDetailsView(self.mainView, self.testrunModel)
        self.testsuiteDetailView = _oatr_testsuite.cTestsuiteView(self.mainView, self.testsuiteModel)
        self.testruninfoDetailView = _oatr_testrun.cTestrunInfoView(self.mainView, self.testruninfoModel)
        self.setCentralWidget(self.mainView)

        self.tabView = QtGui.QTabWidget(self.mainView)
        self.tabView.addTab(self.testrunDetailView, 'Test Details')
        self.tabView.addTab(self.testsuiteDetailView, 'Testsuite')
        self.tabView.addTab(self.testruninfoDetailView, 'Test Run Info')
        
        self.setupMenu()
        
        #TODO remove this after testing
        self.createSampleDatabase()
        self.tableView.resizeColumnsToContents() 

    def testrunTableViewSelectionHandler(self,  index):
        row = index.row()
        self.testrunDetailView.mapper.setCurrentIndex(row)
        if False:
            model = index.model()
            if not model: return
            msg = []
            for col in range(model.columnCount()):
                index = model.createIndex(row,  col)
                title = unicode(model.headerData(col, Qt.Horizontal) .toString())
                content = unicode(index.data().toString())
                msg.append(title)
                msg.append('\t' + content)
            print('\n'.join(msg))
        
    def createSampleDatabase(self):
        testFileName = 'tests/samplerun_out.db'
        if os.path.exists(testFileName):
            os.remove(testFileName)
        _oatr_database.createTestRunDatabase('tests/samplerun_in.db', testFileName, 11, 
                                             {'title': 'Info title', 'description': 'Info description', 'source': 'unknown'})
        self.database.setDatabaseName(testFileName)
        self.database.open()
        self.database.exec_('update testruns set status=1 where id=14')
        self.testrunModel.reset()
        self.testrunModel.select()
        self.testsuiteModel.reset()
        self.testsuiteModel.select()
        self.testsuiteDetailView.mapper.toFirst()
        self.testruninfoModel.reset()
        self.testruninfoModel.select()
        self.testruninfoDetailView.mapper.toFirst()
    
    def setupMenu(self):
        exitAction = QtGui.QAction(self.tr('Exit'), self, statusTip=self.tr('Exit application'),
                                   triggered=self.close, shortcut=QtGui.QKeySequence.Close)
        openAction = QtGui.QAction(QtGui.QIcon(':/icons/database_open.png'), self.tr('Open test run'), self, statusTip=self.tr('Open existing test run'),
                                   triggered = self.openDatabase,shortcut=QtGui.QKeySequence.Open)
        newAction = QtGui.QAction(QtGui.QIcon(':/icons/database_new.png'), self.tr('New test run'), self, statusTip=self.tr('Create new test run'),
                                  triggered=self.newDatabase, shortcut=QtGui.QKeySequence.New)
        self.reportAction = QtGui.QAction(self.tr('Create test run report'), self, statusTip="Create a report of the test run",
            enabled=False, triggered=self.createReport)
        self.execTestcaseAction = QtGui.QAction(self.tr('Execute test'), self, statusTip="Execute selected testcase",
            enabled=False, triggered=self.execTestcase)
        aboutAction = QtGui.QAction(self.tr('About'), self, statusTip = self.tr('About this program'),
                                    triggered=self.showAbout, shortcut=QtGui.QKeySequence.HelpContents)
        
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu(self.tr('&File'))
        map(fileMenu.addAction, (newAction, openAction, self.reportAction, exitAction))
        execMenu = menuBar.addMenu(self.tr('&Run'))
        map(execMenu.addAction, (self.execTestcaseAction, ))
        helpMenu = menuBar.addMenu(self.tr('&Help'))
        map(helpMenu.addAction, (aboutAction, ))
        
        self.toolBar = self.addToolBar(self.tr('Toolbar'))
        self.toolBar.pyqtConfigure(objectName='maintoolbar')
        map(self.toolBar.addAction, (openAction, newAction))

    def createReport(self):
        pass
    
    def openDatabase(self):
        pass
    
    def newDatabase(self):
        pass
    
    def execTestcase(self):
        pass
    
    def showAbout(self):
        pass
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
