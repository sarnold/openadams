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

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QCoreApplication, QObject, QString

from _naf_version import VERSION, VERSION_STR, SVN_STR
import _naf_testcase

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

        self.mainView = QtGui.QSplitter(self)
        self.mainView.setFrameStyle(QtGui.QFrame.StyledPanel);
        
        self.listView = QtGui.QWidget(self.mainView)
        self.detailView = _naf_testcase.cTestcaseDetailsView(self.mainView)
        self.setCentralWidget(self.mainView)

# ------------------------------------------------------------------------------
def createTestRunDatabase(srcDatabaseName, destDatabaseName):
    
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
