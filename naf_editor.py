#!/usr/bin/python
# -*- coding: utf-8  -*-
# $Id$

# -------------------------------------------------------------------
# Copyright 2010 Achim Köhler
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

import sys,  os, types, logging, pprint, datetime, traceback, time, types

from _naf_version import VERSION, VERSION_STR

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QCoreApplication, QObject, QString

# ------------------------------------------------------------------------------
# Initialize application and translators here, because we have static strings
# in _naf_database which needs to be translated
# ------------------------------------------------------------------------------
app = QtGui.QApplication(sys.argv)
app.setOrganizationName("")
app.setOrganizationDomain("macht-publik.de")
app.setApplicationName("nafms")
app.setWindowIcon(QtGui.QIcon(":/icons/appicon.png"))

QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)

qtTranslator = QtCore.QTranslator()
qtTranslator.load("qt_" + QtCore.QLocale.system().name(), QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
app.installTranslator(qtTranslator)

appTranslator = QtCore.QTranslator()
appTranslator.load("nafms_" + QtCore.QLocale.system().name())
app.installTranslator(appTranslator)
# ------------------------------------------------------------------------------

import _naf_database as nafdb
from _naf_database import TYPE_FOLDER, TYPE_REQUIREMENT
import _naf_tree
import _naf_tableview
import _naf_folder
import _naf_feature
import _naf_requirement
import _naf_usecase
import _naf_image
import _naf_testcase
import _naf_testsuite
import _naf_simplesection
import _naf_component
import _naf_filter
import _naf_textviewer
import _naf_resources
import naf_exportxml

MAX_RECENT_FILES = 5

class cMainController(QtCore.QObject):
    def __init__(self, mainView, ):
        QtCore.QObject.__init__(self)
        self.mainView = mainView
        self.editDialog = mainView.editDialog
        self.editView = mainView.editDialog.editView
        self.editDialog.accepted.connect(self.editItemDone)
        self.editDialog.rejected.connect(self.editItemCanceled)
        self.treeModel = mainView.treeView.model()
        self.allItemTableModel = mainView.allItemTableView.model()
        self.modelList = [self.treeModel]
        self.modelList.append(mainView.allItemTableView.model())
        for view in mainView.views:
            self.modelList.append(view.model())
        self.modelList.append(self.editDialog.folderEdit.model()) # -- should be last
        self.treeView = mainView.treeView
        self.detailView = mainView.detailView

        self.clipBoard = QtGui.qApp.clipboard()
        self.clipBoard.dataChanged.connect(self.clipBoardChanged)
        self.isArtifactInClipboard = False

    def addFolder(self):
        self._addItem('folders', self.tr("New Folder"), self.editDialog.folderEdit.model())

    def addItem(self):
        type_id = self.sender().data().toInt()[0]
        view = [view for view in self.mainView.views if view.TYPE_ID == type_id][0]
        model = view.model()
        self._addItem(model.tableName, view.defaultTitle, model)

    def _addItem(self, tableName, itemTitle, model):
        index = self.treeView.currentIndex()
        model.beginResetModel()
        index = self.treeModel.addItem(tableName, unicode(itemTitle), index)
        model.endResetModel()
        self.treeView.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.Clear)
        self.treeView.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.SelectCurrent)
        self.treeView.setCurrentIndex(index)

    def deleteItem(self):
        index = self.treeView.currentIndex()
        typeid  = self.treeModel.getItemType(index)
        n = self.treeModel.countItemsRelatedToIndex(index)
        if typeid == TYPE_FOLDER:
            if n > 0:
                QtGui.QMessageBox.information(self.mainView, self.tr("Delete folder"), self.tr("Folder is not empty!\nOnly empty folders could be deleted."))
                return
            model = self.modelList[-1]
        else:
            m = self.treeModel.countItemsWhereIndexIsRelatedTo(index) - 1 # any item is related to a folder, but that is not of interest here
            answer = QtGui.QMessageBox.question(self.mainView, self.tr("Delete item"),
                QtCore.QString(self.tr("Item is related to %1 item(s)\nFound %2 item(s) related to this item.\n\nReally delete this item?")).arg(m).arg(n),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.No:
                return
            model = self.modelList[typeid]
        model.beginResetModel()
        self.treeModel.deleteItem(model.tableName, index)
        model.endResetModel()

    def treeSelectionChanged(self, selectedModelIndex, deselectedModelIndex):
        self.showItemView(selectedModelIndex)
        typeid = self.treeModel.getItemType(selectedModelIndex)
        self.mainView.copyArtifactAction.setEnabled(typeid is not TYPE_FOLDER)

    def showItemView(self, selectedModelIndex):
        typeid = self.treeModel.getItemType(selectedModelIndex)
        itemid = self.treeModel.getItemId(selectedModelIndex)
        logging.info("typeid=%d, itemid=%d" % (typeid, itemid))
        self.detailView.setCurrentIndex(typeid-1)
        self.detailView.currentWidget().mapper.setCurrentIndex(itemid)

    def openDatabase(self, filename):
        nafdb.openDatabase(filename)
        for model in self.modelList:
            model.beginResetModel()
            model.endResetModel()
        index = self.treeModel.index(0, 0, QtCore.QModelIndex()) # root index
        self.mainView.treeView.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.SelectCurrent)
        self.mainView.treeView.setExpanded(index, True)
        self.emit(QtCore.SIGNAL('databaseLoaded()'))
        self.clipBoardChanged()

    def newDatabase(self, filename):
        nafdb.createDefaultDatabase(filename)

    def applyFilter(self, filterWidget):
        logging.debug("tableName=%s, whereClause=%s" % (filterWidget.tableName, repr(filterWidget.model().getWhereClause())))
        self.treeView.saveView()
        pi = self.treeView.getCurrentParent()
        self.treeModel.items.setFilter(filterWidget.tableName, filterWidget.model().getWhereClause())
        self.allItemTableModel.setFilter(filterWidget.tableName, filterWidget.model().getWhereClause())
        for model in self.modelList:
            model.beginResetModel()
            model.endResetModel()
        self.treeView.restoreView(pi)
        self.mainView.filterIndicator.setEnabled(True)

    def resetFilter(self, filterWidget):
        self.applyFilter(filterWidget)
        self.mainView.filterIndicator.setEnabled(False)

    def editItem(self, index=None):
        if self.editDialog.isVisible():
            self.editDialog.raise_()
            self.editDialog.activateWindow()
            return
        if not isinstance(index, QtCore.QModelIndex):
            index = self.treeView.currentIndex()
        typeid = self.treeModel.getItemType(index)
        self.editItemId = self.treeModel.getItemId(index)
        self.editView.setCurrentIndex(typeid-1)
        self.editView.currentWidget().mapper.setCurrentIndex(self.editItemId)
        self.editDialog.show()
        if self.editDialog.lastGeometry is not None:
            self.editDialog.setGeometry(self.editDialog.lastGeometry)
        self.emit(QtCore.SIGNAL('editStarted()'))

    def editItemDone(self):
        self.treeView.saveView()
        index = self.treeView.selectionModel().currentIndex()
        for model in self.modelList:
            model.beginResetModel()
            model.endResetModel()
        self.treeView.restoreView(self.editItemId)
        self.emit(QtCore.SIGNAL('editFinished()'))

    def editItemCanceled(self):
        self.emit(QtCore.SIGNAL('editFinished()'))

    def editItemText(self, tableName, columnName, itemId):
        # Edit a single text field of an item using a full text editor
        if self.editDialog.isVisible():
            self.editDialog.raise_()
            self.editDialog.activateWindow()
            return
        self.editItemId = itemId
        # text editor is last widget
        self.editView.setCurrentIndex(self.editView.count()-1)
        self.editView.currentWidget().mapper.setEditItem(str(tableName), str(columnName), itemId)
        if self.editDialog.lastGeometry is not None:
            self.editDialog.setGeometry(self.editDialog.lastGeometry)
        self.editDialog.show()
        self.emit(QtCore.SIGNAL('editStarted()'))

    def copyItem(self):
        "Copy ID of selected tree item to clipboard"
        ##print "Copy"
        index = self.treeView.currentIndex()
        itemId = self.treeModel.getItemId(index)
        typeId =self.treeModel.getItemType(index)
        mimeData = _naf_tree.cTreeMimeData()
        #TODO: use URL scheme instead of tabs, i.e. file://<currentFileName>?itemId=<itemId>&typeId=<typeId>
        mimeData.setData(_naf_tree.ARTIFACT_MIME_TYPE, "%d\t%d\t%s" % (itemId, typeId, nafdb.currentFileName))
        self.clipBoard.setMimeData(mimeData)

    def pasteItem(self):
        ##print "Paste"
        parentIndex = self.treeView.currentIndex()
        typeId = self.treeModel.getItemType(parentIndex)
        if typeId is not TYPE_FOLDER:
            parentIndex = self.treeModel.parent(parentIndex)
        mimeData = self.clipBoard.mimeData()
        if not mimeData.hasFormat(_naf_tree.ARTIFACT_MIME_TYPE):
            return
        data = mimeData.retrieveData(_naf_tree.ARTIFACT_MIME_TYPE, QtCore.QVariant.UserType)
        if type(data) is not types.StringType:
            data = str(data.toPyObject())
        (itemId, typeId, fileName) = data.split('\t')
        itemId = int(itemId)
        typeId = int(typeId)
        index = self.treeModel.copyItem(itemId, typeId, parentIndex, fileName)
        model = self.modelList[typeId]
        model.beginResetModel()
        model.endResetModel()

        self.treeView.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.Clear)
        self.treeView.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.SelectCurrent)
        self.treeView.setCurrentIndex(index)

    def clipBoardChanged(self):
        try:
            mimeData = self.clipBoard.mimeData()
            self.isArtifactInClipboard = mimeData.hasFormat(_naf_tree.ARTIFACT_MIME_TYPE)
            self.mainView.pasteArtifactAction.setEnabled(self.isArtifactInClipboard)
        except AttributeError:
            logging.error("Attribute error, may occur when application is closed")
            return

    def getReport(self):
        def formatItemList(headline, itemlist, prefix):
            fmt = "<li>%s-%%d: %%s</li>" % prefix
            noneStr = '<li>' + str(self.tr('None')) + '</li>'
            msg = [fmt % item for item in itemlist] or [noneStr]
            return "<h1>%s: %d</h1>" % (headline, len(itemlist)) + "<ul>" + '\n'.join(msg) + '</ul>'

        statistics = nafdb.getStatistics()
        text = """
        <html><head>
        <style type="text/css">
        h1 { color:blue; font-size:large; }
        td {padding-right:15px; padding-left:15px;}
        </style>
        </head><body>
        """
        text += '<h1>%s</h1><div style="margin-left:20px;"><table border="1">' % unicode(self.tr("Number of items"))
        for table in nafdb.tables:
            text += "<tr><td>&nbsp;%s&nbsp;</td><td>&nbsp;%d&nbsp;</td></tr>" % (table.displayname, statistics.itemcount[table.name])
        text += "</table></div>\n"
        text += formatItemList(unicode(self.tr("Features w/o requirements")), statistics.features_wo_requirements, "FT")
        text += formatItemList(unicode(self.tr("Requirements w/o testcases")), statistics.requirements_wo_testcases, "RQ")
        text += formatItemList(unicode(self.tr("Requirements w/o components")), statistics.requirements_wo_components, "RQ")
        text += formatItemList(unicode(self.tr("Requirements w/o features")), statistics.requirements_wo_features, "RQ")

        text += formatItemList(unicode(self.tr("Requirements w/o components")), statistics.requirements_wo_components, "RQ")
        text += formatItemList(unicode(self.tr("Requirements w/o usecases")), statistics.requirements_wo_usecases, "RQ")

        text += formatItemList(unicode(self.tr("Usecases w/o requirements")), statistics.usecases_wo_requirements_or_features, "UC")
        text += formatItemList(unicode(self.tr("Components w/o requirements")), statistics.components_wo_requirements, "CM")
        text += formatItemList(unicode(self.tr("Testsuites w/o testcases")), statistics.testsuites_wo_testcases, "TS")
        text += formatItemList(unicode(self.tr("Testcases w/o testsuites")), statistics.testcases_wo_testsuites, "TC")

        text += "</body></html>"
        return text


class cEditWin(QtGui.QDialog):
    def __init__(self, parent=0, flags=0):
        super(cEditWin, self).__init__(parent)
        self.setMinimumSize(800, 600)
        self.setSizeGripEnabled(True)
        self.dialogTitles = []
        self.editView = QtGui.QStackedWidget(self)
        self.editView.currentChanged.connect(self.updateTitle)

        self.dialogTitles.append(self.tr("Edit folder"))
        self.folderEdit = _naf_folder.cFolderView(self, isEditable=True)
        self.editView.addWidget(self.folderEdit)

        for viewclass in parent.viewclasses:
            edit = viewclass(self, isEditable=True)
            self.dialogTitles.append(edit.editTitle)
            self.editView.addWidget(edit)

        self.dialogTitles.append(self.tr("Edit field"))
        self.fieldEdit = _naf_textviewer.cTextEditWidget(self)
        self.editView.addWidget(self.fieldEdit)

        self.editButtonBox = QtGui.QDialogButtonBox()
        btnSave =  self.editButtonBox.addButton(QtGui.QDialogButtonBox.Save)
        btnSave.setShortcut(QtGui.QKeySequence.Save)
        self.editButtonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.editView)
        layout.addWidget(self.editButtonBox)
        self.setLayout(layout)
        self.editButtonBox.accepted.connect(self.accept)
        self.editButtonBox.rejected.connect(self.reject)

        self.accepted = self.editButtonBox.accepted
        self.rejected = self.editButtonBox.rejected

    def accept(self):
        self.editView.currentWidget().submit()
        self.lastGeometry = self.geometry()
        self.hide()

    def reject(self):
        try:
            self.editView.currentWidget().cancel()
        except AttributeError:
            # cancel is not implemented for all widgets, ignorable exception
            pass
        self.lastGeometry = self.geometry()
        self.hide()

    def updateTitle(self, index):
        self.setWindowTitle(self.dialogTitles[index])

    def closeEvent(self, event):
        self.rejected.emit()


class cExportToXmlDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(cExportToXmlDialog, self).__init__(parent)
        self.setMinimumWidth(640)
        self.setSizeGripEnabled(False)
        self.setWindowTitle(self.tr("Export to Xml"))

        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(QtGui.QLabel(self.tr('Stylesheet')), 0, 0)
        self.styleSheetName = QtGui.QLineEdit(self)
        self.styleSheetName.textChanged.connect(self.validateStylesheet)
        styleSheetButton = QtGui.QPushButton('...')
        gridLayout.addWidget(self.styleSheetName, 0, 1)
        gridLayout.addWidget(styleSheetButton, 0, 2)
        gridLayout.addWidget(QtGui.QLabel(self.tr('Output file')), 1, 0)
        self.outFileName = QtGui.QLineEdit(self)
        self.outFileName.textChanged.connect(self.validateFileName)
        outFileButton = QtGui.QPushButton('...')
        gridLayout.addWidget(self.outFileName, 1, 1)
        gridLayout.addWidget(outFileButton, 1, 2)
        self.plainFormat = QtGui.QCheckBox(self.tr('Plain format'))
        gridLayout.addWidget(self.plainFormat, 2, 0, 1, 3)
        buttonBox = QtGui.QDialogButtonBox(self)
        self.btnOk =  buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        self.btnCancel =  buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(gridLayout)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        outFileButton.clicked.connect(self.getOutFileName)
        styleSheetButton.clicked.connect(self.getStyleSheetName)

    def getStyleSheetName(self):
        fileName = str(QtGui.QFileDialog.getOpenFileName(self, self.tr("Use Xsl Stylesheet"), ".", self.tr("Xsl Stylesheet Files (*.xsl);;All files (*.*)")))
        if fileName == '':
            return
        self.styleSheetName.setText(fileName)

    def getOutFileName(self):
        fileName = str(QtGui.QFileDialog.getSaveFileName(self, self.tr("Save to"), ".", self.tr("Xml Files (*.xml);;All files (*.*)")))
        if fileName == '':
            return
        self.outFileName.setText(fileName)

    def validateStylesheet(self, styleSheetName):
        outFileName = self.outFileName.text()
        b = (os.path.exists(styleSheetName) or (styleSheetName == '')) and str(outFileName) != ''
        self.btnOk.setEnabled(b)

    def validateFileName(self, outFileName):
        styleSheetName = str(self.styleSheetName.text())
        b = (os.path.exists(styleSheetName) or (styleSheetName == '')) and str(outFileName) != ''
        self.btnOk.setEnabled(b)


class cAbout(QtGui.QDialog):
    def __init__(self, parent):
        super(cAbout, self).__init__(parent)
        self.setSizeGripEnabled(False)
        self.setWindowTitle(self.tr("About"))
        self.aboutText = QtGui.QLabel(self, openExternalLinks=True)
        self.aboutText.setText(str(self.tr("""
        <div align="center" style="font-size:large;">
        <p style="font-size:x-large;"><b>openADAMS Editor %s</b></p>
        <p><small>[%s]</small><p>
        <p>Copyright (C) 2010 Achim K&ouml;hler</p>
        <p>Editor for the Open "Artifact Documentation And Management System"</p>
        <p>See <a href="https://sourceforge.net/projects/openadams/">openADAMS Homepage</a> for details.</p>
        <blockquote>This program comes with ABSOLUTELY NO WARRANTY;<br/>
        This is free software, and you are welcome to redistribute it<br/>
        under the terms of the GNU General Public License; <br/>
        see the accompanied file COPYING for details.
        </blockquote>
        </div>
        """)) % (VERSION, VERSION_STR))
        self.aboutText.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        self.buttonBox.rejected.connect(self.reject)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.aboutText)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class cReportView(QtGui.QDialog):
    def __init__(self, parent, controller):
        super(cReportView, self).__init__(parent)
        self.controller = controller
        self.setMinimumSize(640, 480)
        self.setSizeGripEnabled(True)
        self.setWindowTitle(self.tr("Report"))
        self.reportText = _naf_textviewer.cTextEditor(readOnly=True)
        self.reportText.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        self.editButtonBox = QtGui.QDialogButtonBox()
        btnUpdate = QtGui.QPushButton(self.tr("&Update"))
        btnUpdate.clicked.connect(self.updateReport)
        btnSave = QtGui.QPushButton(self.tr("&Save"))
        btnSave.clicked.connect(self.saveReport)
        self.editButtonBox.addButton(btnUpdate, QtGui.QDialogButtonBox.ActionRole)
        self.editButtonBox.addButton(btnSave, QtGui.QDialogButtonBox.ActionRole)
        self.editButtonBox.addButton(QtGui.QDialogButtonBox.Close)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.reportText)
        layout.addWidget(self.editButtonBox)
        self.setLayout(layout)
        self.editButtonBox.rejected.connect(self.hide)

    def saveReport(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
            self.tr("Save Report"), '', self.tr("Html Files (*.html *.htm)"))
        fileName = str(fileName)
        if fileName is '': return
        try:
            f = open(fileName, "w")
            f.write(self.reportText.toHtml())
            f.close()
        except:
            type_, value, tb = sys.exc_info()
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, self.tr("Error"), QtCore.QString(str(value)))
            msgBox.setDetailedText(QtCore.QString(''.join(traceback.format_exception( type_, value, tb))))
            msgBox.exec_()

    def updateReport(self):
        text = self.controller.getReport()
        self.reportText.setText(text)


class cMainWin(QtGui.QMainWindow):
    def __init__(self, dbName=None):
        QtGui.QMainWindow.__init__(self)
        self.winTitle = self.tr("Artifact editor")
        self.setWindowTitle(self.winTitle)
        self.setMinimumSize(800, 600)
        self.filterIndicator = QtGui.QLabel()
        self.filterIndicator.setPixmap(QtGui.QPixmap(":/icons/filter.png"))
        self.filterIndicator.setEnabled(False)
        self.statusBar().addWidget(self.filterIndicator)

        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value("mainwindow/geometry").toByteArray());
        self.restoreState(settings.value("mainwindow/windowState").toByteArray());
        self.recentFileActs = []

        self.itemView = QtGui.QSplitter(self)
        self.itemView.setFrameStyle(QtGui.QFrame.StyledPanel);

        self.treeView = _naf_tree.cTreeView(self.itemView)

        self.detailView = QtGui.QStackedWidget(self.itemView)
        # see http://doc.trolltech.com/4.6/qframe.html#properties
        self.detailView.setFrameStyle(QtGui.QFrame.WinPanel + QtGui.QFrame.Sunken)

        self.allItemTableView = _naf_tableview.cAllItemTableView(self)
        self.detailView.addWidget(self.allItemTableView)

        self.viewclasses = [
            _naf_requirement.cRequirementView,    # TYPE_REQUIREMENT = 2
            _naf_usecase.cUsecaseView,            # TYPE_USECASE = 2
            _naf_image.cImageView,                # TYPE_IMAGE = 4
            _naf_feature.cFeatureView,            # TYPE_FEATURE = 5
            _naf_testcase.cTestcaseView,          # TYPE_TESTCASE = 6
            _naf_testsuite.cTestsuiteView,        # TYPE_TESTSUITE= 7
            _naf_simplesection.cSimplesectionView,# TYPE_SIMPLESECTION = 8
            _naf_component.cComponentView,
        ]

        self.views = [viewclass(self) for viewclass in self.viewclasses]
        map(self.detailView.addWidget, self.views)

        self.editDialog = cEditWin(self, QtCore.Qt.WindowMaximizeButtonHint)
        self.editDialog.lastGeometry = None

        self.mainController = cMainController(self)
        for view in self.views:
            view.detailsView.editSignal.connect(self.mainController.editItemText)
        self.setCentralWidget(self.itemView)

        self.filterDock = _naf_filter.cFilterDock(self.mainController)
        self.filterDock.pyqtConfigure(objectName='filterdock')

        self.filterDock.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self.filterDock)
        self.filterDockViewAction = self.filterDock.toggleViewAction()
        self.filterDockViewAction.setIcon(QtGui.QIcon(':/icons/filter.png'))
        self.filterDockViewAction.setDisabled(True)

        self.reportView = cReportView(self, self.mainController)
        self.reportViewAction = QtGui.QAction(self.tr("Report"), self, enabled=False,
            triggered = self.showReportView)

        #-- Actions, toolbars and menus
        #--
        exitAction = QtGui.QAction(self.tr('Exit'), self)
        exitAction.setShortcut('Alt+X')
        exitAction.setStatusTip(self.tr('Exit application'))
        self.connect(exitAction, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

        openAction = QtGui.QAction(QtGui.QIcon(':/icons/database_open.png'), self.tr('Open database'), self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip(self.tr('Open existing database'))
        self.connect(openAction, QtCore.SIGNAL('triggered()'), self.openDatabase)

        newAction = QtGui.QAction(QtGui.QIcon(':/icons/database_new.png'), self.tr('New database'), self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip(self.tr('Create new database'))
        self.connect(newAction, QtCore.SIGNAL('triggered()'), self.newDatabase)

        self.exportAction = QtGui.QAction(self.tr('Export database'), self, statusTip="Export database to Xml",
            enabled=False, triggered=self.exportToXml)

        aboutAction = QtGui.QAction(self.tr('About'), self)
        aboutAction.setShortcut('F1')
        aboutAction.setStatusTip(self.tr('About this program'))
        aboutAction.triggered.connect(self.showAbout)

        addActionGroup = QtGui.QActionGroup(self)
        addActionGroup.setExclusive(False)
        addActionGroup.setEnabled(False)
        self.addActionGroup = addActionGroup

        addFolderAction = QtGui.QAction(QtGui.QIcon(':/icons/folder_new.png'), self.tr('Add folder'), addActionGroup)
        addFolderAction.triggered.connect(self.mainController.addFolder)

        addSimplesectionAction = QtGui.QAction(QtGui.QIcon(':/icons/af_simplesection_add.png'), self.tr('Add text section'), addActionGroup)
        addSimplesectionAction.triggered.connect(self.mainController.addItem)
        addSimplesectionAction.setData(nafdb.TYPE_SIMPLESECTION)

        addRequirementAction = QtGui.QAction(QtGui.QIcon(':/icons/af_requirement_add.png'), self.tr('Add requirement'), addActionGroup)
        addRequirementAction.triggered.connect(self.mainController.addItem)
        addRequirementAction.setData(nafdb.TYPE_REQUIREMENT)

        addUsecaseAction = QtGui.QAction(QtGui.QIcon(':/icons/af_usecase_add.png'), self.tr('Add usecase'), addActionGroup)
        addUsecaseAction.triggered.connect(self.mainController.addItem)
        addUsecaseAction.setData(nafdb.TYPE_USECASE)

        addImageAction = QtGui.QAction(QtGui.QIcon(':/icons/af_image_add.png'), self.tr('Add image'), addActionGroup)
        addImageAction.triggered.connect(self.mainController.addItem)
        addImageAction.setData(nafdb.TYPE_IMAGE)

        addFeatureAction = QtGui.QAction(QtGui.QIcon(':/icons/af_feature_add.png'), self.tr('Add feature'), addActionGroup)
        addFeatureAction.triggered.connect(self.mainController.addItem)
        addFeatureAction.setData(nafdb.TYPE_FEATURE)

        addTestcaseAction = QtGui.QAction(QtGui.QIcon(':/icons/af_testcase_add.png'), self.tr('Add testcase'), addActionGroup)
        addTestcaseAction.triggered.connect(self.mainController.addItem)
        addTestcaseAction.setData(nafdb.TYPE_TESTCASE)

        addTestsuiteAction = QtGui.QAction(QtGui.QIcon(':/icons/af_testsuite_add.png'), self.tr('Add testsuite'), addActionGroup)
        addTestsuiteAction.triggered.connect(self.mainController.addItem)
        addTestsuiteAction.setData(nafdb.TYPE_TESTSUITE)

        addComponentAction = QtGui.QAction(QtGui.QIcon(':/icons/af_component_add.png'), self.tr('Add component'), addActionGroup)
        addComponentAction.triggered.connect(self.mainController.addItem)
        addComponentAction.setData(nafdb.TYPE_COMPONENT)

        editArtifactAction = QtGui.QAction(QtGui.QIcon(':/icons/file_edit.png'), self.tr('Edit item'), addActionGroup)
        editArtifactAction.triggered.connect(self.mainController.editItem)

        copyArtifactAction = QtGui.QAction(QtGui.QIcon(':/icons/editcopy.png'), self.tr('Copy item'), addActionGroup)
        copyArtifactAction.setShortcut(QtGui.QKeySequence.Copy)
        copyArtifactAction.triggered.connect(self.mainController.copyItem)
        self.copyArtifactAction = copyArtifactAction

        pasteArtifactAction = QtGui.QAction(QtGui.QIcon(':/icons/editpaste.png'), self.tr('Paste'), addActionGroup)
        pasteArtifactAction.setShortcut(QtGui.QKeySequence.Paste)
        pasteArtifactAction.triggered.connect(self.mainController.pasteItem)
        pasteArtifactAction.setEnabled(False)
        self.pasteArtifactAction = pasteArtifactAction

        deleteArtifactAction = QtGui.QAction(QtGui.QIcon(':/icons/file_delete.png'), self.tr('Delete item'), addActionGroup)
        deleteArtifactAction.setShortcut(QtGui.QKeySequence.Delete)
        deleteArtifactAction.triggered.connect(self.mainController.deleteItem)

        for i in range(MAX_RECENT_FILES):
            self.recentFileActs.append(QtGui.QAction(self, visible=False,
                triggered=self.openRecentFile))

        self.connect(self.mainController, QtCore.SIGNAL('databaseLoaded()'), QtCore.SLOT('databaseLoadedAction()') )
        self.connect(self.mainController, QtCore.SIGNAL('editStarted()'), QtCore.SLOT('editStartedAction()') )
        self.connect(self.mainController, QtCore.SIGNAL('editFinished()'), QtCore.SLOT('editFinishedAction()') )

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu(self.tr('&File'))
        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        self.recentMenu = fileMenu.addMenu(self.tr("Recent databases"))
        for i in range(MAX_RECENT_FILES):
            self.recentMenu.addAction(self.recentFileActs[i])
        fileMenu.addSeparator()
        self.updateRecentFileActions()
        fileMenu.addAction(self.exportAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        editMenu = menuBar.addMenu(self.tr('&Edit'))
        editMenu.addAction(editArtifactAction)
        editMenu.addAction(copyArtifactAction)
        editMenu.addAction(pasteArtifactAction)
        editMenu.addAction(deleteArtifactAction)
        editMenu.addSeparator()
        editMenu.addAction(addFolderAction)
        editMenu.addAction(addSimplesectionAction)
        editMenu.addAction(addFeatureAction)
        editMenu.addAction(addRequirementAction)
        editMenu.addAction(addUsecaseAction)
        editMenu.addAction(addComponentAction)
        editMenu.addAction(addTestcaseAction)
        editMenu.addAction(addTestsuiteAction)
        editMenu.addAction(addImageAction)

        viewMenu = menuBar.addMenu(self.tr('&View'))
        viewMenu.addAction(self.filterDockViewAction)
        viewMenu.addAction(self.reportViewAction)

        helpMenu = menuBar.addMenu(self.tr('&Help'))
        helpMenu.addAction(aboutAction)

        self.toolBar = self.addToolBar(self.tr('Toolbar'))
        self.toolBar.pyqtConfigure(objectName='maintoolbar')
        self.toolBar.addAction(openAction)
        self.toolBar.addAction(newAction)
        self.toolBar.addAction(self.filterDockViewAction)
        self.toolBar.addAction(copyArtifactAction)
        self.toolBar.addAction(pasteArtifactAction)
        self.toolBar.addAction(editArtifactAction)
        self.toolBar.addAction(deleteArtifactAction)
        self.toolBar.addAction(addFolderAction)
        self.toolBar.addAction(addSimplesectionAction)
        self.toolBar.addAction(addFeatureAction)
        self.toolBar.addAction(addRequirementAction)
        self.toolBar.addAction(addUsecaseAction)
        self.toolBar.addAction(addComponentAction)
        self.toolBar.addAction(addTestcaseAction)
        self.toolBar.addAction(addTestsuiteAction)
        self.toolBar.addAction(addImageAction)

        self.treeView.activated.connect(self.mainController.editItem)
        self.treeView.selectionModel().currentChanged.connect(self.mainController.treeSelectionChanged)

        if dbName is not None:
            self.openDatabase(dbName)

    def openRecentFile(self):
        action = self.sender()
        if action:
            self.openDatabase(unicode(action.data().toPyObject()))

    def openDatabase(self, fileName=None):
        if fileName is None:
            fileName = unicode(QtGui.QFileDialog.getOpenFileName(self, self.tr("Open database"), ".", self.tr("Database Files (*.db);;All files (*.*)")))
        if fileName == '':
            return
        try:
            self.mainController.openDatabase(fileName)
            self.setCurrentFile(fileName)
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)

    def exportToXml(self):
        args = naf_exportxml.cArgs()
        args.databaseName = nafdb.currentFileName
        args.outputFileName =  os.path.splitext(args.databaseName)[0] + ".xml"

        exportDialog = cExportToXmlDialog(self)
        exportDialog.outFileName.setText(args.outputFileName)
        exportDialog.styleSheetName.setText(naf_exportxml.DEFAULT_XSL_FILE)
        if  QtGui.QDialog.Rejected == exportDialog.exec_():
            return

        args.outputFileName = str(exportDialog.outFileName.text())
        args.plainFormat = exportDialog.plainFormat.checkState() != QtCore.Qt.Unchecked
        args.stylesheet = str(exportDialog.styleSheetName.text())
        try:
            naf_exportxml.run(args)
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)


    def newDatabase(self):
        fileName = unicode(QtGui.QFileDialog.getSaveFileName(self, self.tr("New database"), ".", self.tr("Database Files (*.db);;All files (*.*)")))
        if fileName == '':
            return
        fileName = os.path.abspath(fileName)
        try:
            self.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            self.mainController.newDatabase(fileName)
            self.mainController.openDatabase(fileName)
            self.setCurrentFile(fileName)
        except:
            (type_, value, tb) = sys.exc_info()
            self.showExceptionMessageBox(type_, value, tb)
        finally:
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def setCurrentFile(self, fileName):
        self.curFile = fileName
        self.setWindowTitle("%s - %s" % (self.strippedName(fileName), self.winTitle))
        settings = QtCore.QSettings()
        files = list(settings.value('recentFileList').toPyObject() or [])
        try:
            files.remove(fileName)
        except ValueError:
            pass
        files.insert(0, fileName)
        del files[MAX_RECENT_FILES:]
        settings.setValue('recentFileList', files)
        self.updateRecentFileActions()

    def updateRecentFileActions(self):
        settings = QtCore.QSettings()
        files = settings.value('recentFileList').toPyObject() or []
        numRecentFiles = min(len(files), MAX_RECENT_FILES)
        for i in range(numRecentFiles):
            text = "&%d %s" % (i + 1, files[i])
            self.recentFileActs[i].setText(text)
            self.recentFileActs[i].setData(files[i])
            self.recentFileActs[i].setVisible(True)
        for j in range(numRecentFiles, MAX_RECENT_FILES):
            self.recentFileActs[j].setVisible(False)
        self.recentMenu.setEnabled((numRecentFiles > 0))

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    @QtCore.pyqtSlot()
    def databaseLoadedAction(self):
        self.filterDockViewAction.setEnabled(True)
        self.reportViewAction.setEnabled(True)
        self.addActionGroup.setEnabled(True)
        self.exportAction.setEnabled(True)

    @QtCore.pyqtSlot()
    def editStartedAction(self):
        self.addActionGroup.setEnabled(False)

    @QtCore.pyqtSlot()
    def editFinishedAction(self):
        self.addActionGroup.setEnabled(True)

    def showAbout(self):
        cAbout(self).exec_()

    def showReportView(self):
        self.reportView.show()
        self.reportView.raise_()
        self.reportView.activateWindow()
        self.reportView.updateReport()

    def closeEvent(self, event):
        settings = QtCore.QSettings()
        settings.setValue("mainwindow/geometry", self.saveGeometry())
        settings.setValue("mainwindow/windowState", self.saveState())
        ##self.closeEvent(event)

    def showExceptionMessageBox(self, type_, value, tb):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, self.tr("Error"), QtCore.QString(str(value)))
        msgBox.setDetailedText(QtCore.QString(''.join(traceback.format_exception( type_, value, tb))))
        msgBox.exec_()


def start():
    dbName = None
    for i in range(1, len(sys.argv)):
        if not sys.argv[i].startswith('-'):
            dbName = sys.argv[i].decode(sys.getfilesystemencoding())
            break;
    mainwin = cMainWin(dbName)
    mainwin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    logFormat = '%(module)s:%(lineno)s (%(funcName)s): %(message)s'
    level=logging.NOTSET
    ##level=logging.DEBUG
    ##level=logging.INFO,
    ##level=logging.ERROR,
    logging.basicConfig(format=logFormat, level=level,
                        ##, filemode='w', filename='myapp.log'
                        )
    logging.debug("logging.debug is on")
    logging.info("logging.info is on")
    logging.error("logging.error is on")
    start()

# TODO: show active filters in status line
# TODO: export artifacts with backrelations
# TODO: import artifacts (till now done by copy/paste from another app instance)
# TODO: diff of databases
# TODO: localization
