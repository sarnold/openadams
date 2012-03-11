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
import json
import types
import argparse
import logging
import traceback

from PyQt4 import QtGui,  QtCore,  QtSql
from PyQt4.QtCore import Qt

import _naf_database as nafdb
import _naf_resources
import _naf_textviewer
import _naf_about
from _naf_version import VERSION, VERSION_STR, SVN_STR

WINTITLE = "Log Viewer"
PROGNAME = 'oalogviewer'
ABOUTMSG = u"""oaviewer %s
openADAMS Log Viewer

Copyright (C) 2012 Achim Koehler

%s
""" % (VERSION, SVN_STR)

class cChangeModel(QtSql.QSqlTableModel):
    def __init__(self, *args, **kwargs):
        super(cChangeModel, self).__init__(*args, **kwargs)
        self.setTable("changes")
        self.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        
    def origdata(self, index):
        return super(cChangeModel, self).data(index, Qt.DisplayRole)
        
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
                description = unicode(super(cChangeModel, self).data(index, Qt.DisplayRole).toString())
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
            colname = unicode(model.headerData(section, Qt.Horizontal) .toString())
            model.setHeaderData(section, Qt.Horizontal, self.getHeaderString(colname))
            
    def currentChanged(self, current, previous):
        super(cChangeTableView, self).currentChanged(current,  previous)
        if self.selectionHandler: self.selectionHandler(current)
    
class cDetailView(QtGui.QWidget):
    def __init__(self, parent):
        super(cDetailView, self).__init__(parent)
        self.setLayout(QtGui.QGridLayout())
        self.setMinimumSize(200, 200)
        
    def _isHtml(self, string):
        if type(string) in types.StringTypes:
            return string.startswith("<!")
        else:
            return False
    
    def updateView(self, data):
        try:
            itemList = json.loads(data)
        except:
            return
        for label, col in zip(['Old value', 'New value'], [1, 2]):
            lbl = QtGui.QLabel(label)
            lbl.setStyleSheet("font-weight: bold; background-color:rgba(255, 10, 10, 10%); border-style: outset; border-width:2px; border-color:#909090;")
            self.layout().addWidget(lbl, 0, col, alignment=Qt.AlignTop)
        row = 1
        for item in itemList:
            for field, col in zip(['old', 'new'], [1, 2]):
                if self._isHtml(item['old']) or self._isHtml(item['new']):
                    widget = _naf_textviewer.cTextEditor(self, readOnly=True)
                    widget.setImageProvider(_imageProvider)
                    QtGui.QTextEdit(readOnly=True)
                    widget.setHtml(item[field])
                    alignment=Qt.AlignTop 
                else:
                    widget = QtGui.QLineEdit()
                    widget.setText(unicode(item[field]))
                    alignment=Qt.AlignVCenter
                self.layout().addWidget(widget, row, col, alignment=Qt.AlignTop)
            self.layout().addWidget(QtGui.QLabel(item['column'], alignment=alignment), row, 0)
            row = row + 1
        self.layout().addItem(QtGui.QSpacerItem(1,1, 1, -1), row, 0)
    
    
class cMainWin(QtGui.QMainWindow):
    def __init__(self, dbName=None):
        super(cMainWin, self).__init__()
        self.winTitle = WINTITLE
        self.setWindowTitle(self.winTitle)
        self.setMinimumSize(800, 600)
        self.setBaseSize(800, 750)                                                          
        self.dockWidget = QtGui.QDockWidget(self.tr("Details"), self)
        self.dockWidget.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        openAction = QtGui.QAction(QtGui.QIcon(':/icons/database_open.png'), self.tr('Open database'), self,
                                   triggered = self.openDatabase,shortcut=QtGui.QKeySequence.Open)
        aboutAction = QtGui.QAction(QtGui.QIcon(':/icons/help-browser.png'), self.tr('About'), self,
                                  triggered=self.showAbout, shortcut=QtGui.QKeySequence.HelpContents)
        exitAction = QtGui.QAction(QtGui.QIcon(':/icons/system-log-out.png'), self.tr('Exit'), self,
                                  triggered=self.close, shortcut=QtGui.QKeySequence('Alt+X'))

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu(self.tr('&File'))
        map(fileMenu.addAction, (openAction, exitAction))
        viewMenu = menuBar.addMenu(self.tr('&View'))
        map(viewMenu.addAction, (self.dockWidget.toggleViewAction(), ))
        helpMenu = menuBar.addMenu(self.tr('&Help'))
        map(helpMenu.addAction, (aboutAction, ))
        
        if dbName:
            self.openDatabase(None, dbName)        

    def openDatabase(self, sender=None, fileName=None):
        if fileName is None:
            fileName = unicode(QtGui.QFileDialog.getOpenFileName(self, self.tr("Open database"), ".", self.tr("Database Files (*.db);;All files (*.*)")))
        if fileName == '':
            return
        try:
            self._loadDatabase(fileName)
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)
    
    def showAbout(self):
        aboutText = unicode(self.tr("""
        <div align="center" style="font-size:large;">
        <p style="font-size:x-large;"><b>openADAMS Log Viewer %s</b></p>
        <p><small>[%s]</small><p>
        <p>Copyright (C) 2012 Achim K&ouml;hler</p>
        <p>Log viewer for the Open "Artifact Documentation And Management System"</p>
        <p>See <a href="https://sourceforge.net/projects/openadams/">openADAMS Homepage</a> for details.</p>
        <blockquote>This program comes with ABSOLUTELY NO WARRANTY;<br/>
        This is free software, and you are welcome to redistribute it<br/>
        under the terms of the GNU General Public License; <br/>
        see the accompanied file COPYING for details.
        </blockquote>
        </div>
        """)) % (VERSION, VERSION_STR)
        _naf_about.cAbout(self, aboutText).exec_()
    
    def _loadDatabase(self, fileName):
        self.database = None
        self.database = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.database.setHostName("")
        self.database.setDatabaseName(fileName)
        self.database.open()
        
        model = cChangeModel(None, self.database)
        model.select()
        self.tableView = cChangeTableView(self, model, self.tableSelectionChanged)
        self.setCentralWidget(self.tableView)
        self.detailView = cDetailView(self.dockWidget)
        self.dockWidget.setWidget(self.detailView)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockWidget)
        self.setWindowTitle(QtCore.QFileInfo(fileName).baseName() + ' - ' + WINTITLE)
        
    def tableSelectionChanged(self, index):
        row = self.tableView.currentIndex().row()
        index = self.tableView.model().index(row, 3)
        data = unicode(self.tableView.model().origdata(index).toString())
        self.updateView(data)
        
    def updateView(self, data):
        self.detailView.close()
        self.detailView = cDetailView(self.dockWidget)
        self.detailView.updateView(data)
        self.dockWidget.setWidget(self.detailView)
     
    def showExceptionMessageBox(self, type_, value, tb):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, self.tr("Error"), QtCore.QString(unicode(value)))
        msgBox.setDetailedText(QtCore.QString(''.join(traceback.format_exception( type_, value, tb))))
        msgBox.exec_()
# ------------------------------------------------------------------------------

def _imageProvider(imgId):
    query = QtSql.QSqlQuery("SELECT image FROM images WHERE id==%d" % imgId)
    query.next()
    return query.value(0).toByteArray()

# ------------------------------------------------------------------------------

app = QtGui.QApplication(sys.argv)
app.setOrganizationName("")
app.setOrganizationDomain("macht-publik.de")
app.setApplicationName("oalogviewer")
app.setWindowIcon(QtGui.QIcon(":/icons/appicon.png"))

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
    sys .exit(app.exec_())

if __name__ == "__main__":
    start()