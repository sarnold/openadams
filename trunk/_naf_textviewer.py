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

import operator
from PyQt4 import QtCore, QtGui
import _naf_database as nafdb
import _naf_tableview


class cTextEditor(QtGui.QTextEdit):

    overwriteSignal = QtCore.pyqtSignal()

    def __init__(self, *arg, **kwarg):
        super(cTextEditor, self).__init__(*arg, **kwarg)
        self.pyqtConfigure(autoFormatting=QtGui.QTextEdit.AutoAll,
            lineWrapMode=QtGui.QTextEdit.NoWrap,
            tabStopWidth=20)
        self.defaultFontSize = 10.0
        self.defaultFontName = "Helvetica"
        self.defaultTypewriteFontName = "Courier"
        defaultFont = QtGui.QFont(self.defaultFontName, self.defaultFontSize)
        self.setFont(defaultFont)

    def keyReleaseEvent(self, e):
        if e.key() != int(QtCore.Qt.Key_Insert):
            super(cTextEditor, self).keyReleaseEvent(e)
        else:
            self.overwriteSignal.emit()

    def setImageProvider(self, imageProvider):
        self.imageProvider = imageProvider

    def loadResource(self, type_, url):
        if type_ != QtGui.QTextDocument.ImageResource:
            return super(cTextEditor, self).loadResource(type_, url)
        if url.scheme() == '':
            # No scheme, so try to read image from the database
            if self.imageProvider is not None:
                try:
                    id = int(url.fragment())
                    pm = QtGui.QPixmap()
                    pm.loadFromData(self.imageProvider(id))
                    return pm
                except ValueError:
                    pass
        elif str(url.scheme()).lower() == 'file':
            # strip scheme and leading slash from url,
            # i.e. "file:///icons/folder.png" becomes "icons/folder.png"
            url.setPath(str(url.path()).lstrip('/') )
            url.setScheme('')
            # Actually the next line should return the requested resource
            # return super(cTextViewer, self).loadResource(type_, url)
            # But for some unknown reason this didn_t work
            # So the graphics resource is loaded manually
            return QtGui.QPixmap(url.toLocalFile())
        return super(cTextEditor, self).loadResource(type_, url)


class cTableFormatDialog(QtGui.QDialog):
    def __init__(self, *args, **kwargs):
        super(cTableFormatDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr("Table properties"))
        layout = QtGui.QVBoxLayout()
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        formLayout = QtGui.QFormLayout()
        self.rowsSpinbox = QtGui.QSpinBox()
        self.rowsSpinbox.setMaximum(99)
        self.rowsSpinbox.setMinimum(1)
        formLayout.addRow(self.tr("Rows"), self.rowsSpinbox)
        self.columnsSpinbox = QtGui.QSpinBox()
        self.columnsSpinbox.setMaximum(99)
        self.columnsSpinbox.setMinimum(1)
        formLayout.addRow(self.tr("Colums"), self.columnsSpinbox)
        layout.addLayout(formLayout)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def getResult(self):
        return (self.rowsSpinbox.value(), self.columnsSpinbox.value())


class cImageInsertDialog(QtGui.QDialog):
    def __init__(self, *args, **kwargs):
        super(cImageInsertDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr("Insert Image"))
        self.setMinimumWidth(640)
        layout = QtGui.QVBoxLayout()
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.imageTableView = _naf_tableview.cItemTableView(
            _naf_tableview.cItemTableModel('images', ('id', 'title', 'keywords', 'source'),
            relationType=_naf_tableview.IGNORE_RELATION,
            itemsCheckable=True), self)
        self.imageTableView.model().setCurrentIndex(-1, False)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel(self.tr('Scale')))
        self.percentScale = QtGui.QSpinBox(self)
        self.percentScale.setSuffix('%')
        self.percentScale.setMaximum(10)
        self.percentScale.setMaximum(800)
        self.percentScale.setValue(100)
        hbox.addWidget(self.percentScale)
        hbox.addStretch(1)
        layout.addWidget(self.imageTableView)
        layout.addLayout(hbox)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def getData(self):
        return (self.imageTableView.model().relatedidmap, int(self.percentScale.cleanText()))


class cReplaceDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(cReplaceDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Replace"))
        layout = QtGui.QGridLayout()
        layout.setColumnMinimumWidth(1, 200)
        layout.addWidget(QtGui.QLabel(self.tr("Find what")), 0, 0)
        self.searchText = QtGui.QLineEdit()
        layout.addWidget(self.searchText, 0, 1)

        self.replaceLabel = QtGui.QLabel(self.tr("Replace with"))
        layout.addWidget(self.replaceLabel, 1, 0)
        self.replaceText = QtGui.QLineEdit()
        layout.addWidget(self.replaceText, 1, 1)
        self.matchWholeWord = QtGui.QCheckBox(self.tr("Match whole word"))
        layout.addWidget(self.matchWholeWord, 2, 0, 1, 2)
        self.matchCase =  QtGui.QCheckBox(self.tr("Match case"))
        layout.addWidget(self.matchCase, 3, 0, 1, 2)

        findNextButton = QtGui.QPushButton(self.tr("Find Next"))
        self.findNextSignal = findNextButton.clicked
        layout.addWidget(findNextButton, 0, 2)
        self.replaceButton = QtGui.QPushButton(self.tr("Replace"))
        self.replaceSignal = self.replaceButton.clicked
        layout.addWidget(self.replaceButton, 1, 2)
        self.replaceAllButton = QtGui.QPushButton(self.tr("Replace All"))
        self.replaceAllSignal = self.replaceAllButton.clicked
        layout.addWidget(self.replaceAllButton, 2, 2)
        self.replaceSelectionButton = QtGui.QPushButton(self.tr("Replace in Selection"))
        self.replaceSelectionSignal = self.replaceSelectionButton.clicked
        layout.addWidget(self.replaceSelectionButton, 3, 2)
        closeButton = QtGui.QPushButton(self.tr("Close"))
        layout.addWidget(closeButton, 4, 2)
        closeButton.clicked.connect(self.reject)
        self.infoLabel = QtGui.QLabel()
        layout.addWidget(self.infoLabel, 5, 0)

        self.setLayout(layout)

    def getData(self):
        replaceData = {
            'searchText': self.searchText.displayText(),
            'replaceText' : self.replaceText.displayText(),
            'matchWholeWord': self.matchWholeWord.checkState(),
            'matchCase' : self.matchCase.checkState()
            }
        return replaceData

    def setData(self, replaceData):
        self.searchText.setText(replaceData['searchText'])
        self.replaceText.setText(replaceData['replaceText'])
        self.matchWholeWord.setCheckState(replaceData['matchWholeWord'])
        self.matchCase.setCheckState(replaceData['matchCase'])

    def setItemsVisibility(self, showReplaceItems):
        self.replaceLabel.setVisible(showReplaceItems)
        self.replaceText.setVisible(showReplaceItems)
        self.replaceAllButton.setVisible(showReplaceItems)
        self.replaceButton.setVisible(showReplaceItems)
        self.replaceSelectionButton.setVisible(showReplaceItems)
        self.setWindowTitle([self.tr("Find"), self.tr("Replace")][showReplaceItems])


class cDataMapper(QtCore.QObject):
    def __init__(self, textEdit, setTitleFunc):
        super(cDataMapper, self).__init__()
        self.textEdit = textEdit
        self.setTitleFunc = setTitleFunc

    def setEditItem(self, tableName, columnName, itemId):
        ##print "setEditItem", tableName, columnName, itemId
        self.tableName = tableName
        self.columnName = columnName
        self.itemId = itemId
        title = nafdb.getItemForId(tableName, itemId, 'title')
        columnDisplayName = nafdb.getColumnDisplayName(tableName, columnName)
        self.setTitleFunc(itemId, title, columnDisplayName)
        self.textEdit.setHtml(nafdb.getItemForId(tableName, itemId, columnName) or '')

    def saveEditItem(self):
        nafdb.saveItemForId(self.tableName, self.itemId, self.columnName, unicode(self.textEdit.toHtml()))

class cTextEditWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(cTextEditWidget, self).__init__(parent)
        self.parent = parent
        self.setupActions()
        self.textEdit = cTextEditor()
        self.textEdit.copyAvailable.connect(self.cutAction.setEnabled)
        self.textEdit.copyAvailable.connect(self.copyAction.setEnabled)
        self.textEdit.redoAvailable.connect(self.redoAction.setEnabled)
        self.textEdit.undoAvailable.connect(self.undoAction.setEnabled)
        self.textEdit.overwriteSignal.connect(self.overwriteMode)
        self.textEdit.copyAvailable.connect(self.copyAvailable)
        self.textEdit.currentCharFormatChanged.connect(self.currentCharFormatChanged)
        self.textEdit.cursorPositionChanged.connect(self.cursorPositionChanged)
        self.textEdit.setImageProvider(nafdb.getImageForId)
        self.mapper = cDataMapper(self.textEdit, self._setWindowTitle)

        self.setupGui()
        self.setupMenu()
        self.setupToolbar()
        self.setWindowTitle("Text Editor")
        self.replaceDialog = None
        self.lastSearchData = {'searchText' : '',
            'replaceText' : '',
            'matchWholeWord': False,
            'matchCase': False}

        self.replaceDialog = cReplaceDialog(self)
        self.replaceDialog.setData(self.lastSearchData)
        self.replaceDialog.findNextSignal.connect(self.findString)
        self.replaceDialog.replaceSignal.connect(self.replaceString)
        self.replaceDialog.replaceAllSignal.connect(self.replaceAll)
        self.replaceDialog.replaceSelectionSignal.connect(self.replaceSelection)

    def _setWindowTitle(self, itemId, title, columnDisplayName):
        N = 30
        if len(title) > N:
            s = title[:N/2] + '...' + title[-N/2:]
        s = "%d: %s (%s)" % (itemId, columnDisplayName, title)
        self.parent.setWindowTitle(s)

    def submit(self):
        # if editing raw html, finish this edit mode
        if self.editHtmlAction.isChecked():
            self.editHtml(False)
            self.editHtmlAction.setChecked(False)
        self.mapper.saveEditItem()

    def setupActions(self):
        self.editGroup = QtGui.QActionGroup(self, enabled=True)
        self.copyAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/editcopy.png'),
                self.tr("&Copy"), self, shortcut=QtGui.QKeySequence.Copy, enabled=False,
                statusTip=self.tr("Copy the current selection's contents to the clipboard"),
                triggered=self.copy)
        self.pasteAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/editpaste.png'),
            self.tr("&Paste"), self, shortcut=QtGui.QKeySequence.Paste,
            statusTip=self.tr("Paste the clipboard's contents into the current selection"),
            triggered=self.paste)
        self.cutAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/editcut.png'),
            self.tr("Cu&t"), self, shortcut=QtGui.QKeySequence.Cut, enabled=False,
            statusTip=self.tr("Cut the current selection's contents to the clipboard"),
            triggered=self.cut)
        self.undoAction = QtGui.QAction(self.tr("&Undo"), self.editGroup, shortcut=QtGui.QKeySequence.Undo,
            enabled=False, triggered=self.undo)
        self.redoAction = QtGui.QAction(self.tr("&Redo"), self, shortcut=QtGui.QKeySequence.Redo,
            enabled=False, triggered=self.redo)
        self.deleteAction = QtGui.QAction(self.tr("Delete"), self, shortcut=QtGui.QKeySequence.Delete,
            enabled = False, triggered=self.deleteSelection)
        self.selectAllAction = QtGui.QAction(self.tr("Select All"), self, shortcut=QtGui.QKeySequence.SelectAll,
            triggered=self.selectAll)
        self.editHtmlAction = QtGui.QAction(self.tr("Edit Html"), self, enabled=True, checkable=True,
            statusTip=self.tr("Edit raw HTML"), triggered=self.editHtml)

        self.imageGroup = QtGui.QActionGroup(self, enabled=True)
        self.insertImageAction = QtGui.QAction(self.tr("Insert ..."), self.imageGroup, checkable=False,
            statusTip=self.tr("Insert image"), triggered=self.insertImage)

        self.tableGroup = QtGui.QActionGroup(self, enabled=True)
        self.insertTableAction = QtGui.QAction(self.tr("Insert ..."), self.tableGroup, checkable=False,
            statusTip=self.tr("Insert table"), triggered=self.insertTable)
        self.insertTableRowAction = QtGui.QAction(self.tr("Insert row"), self.tableGroup,
            statusTip=self.tr("Insert table row"), triggered=self.insertTableRow)
        self.insertTableColumnAction = QtGui.QAction(self.tr("Insert column"), self.tableGroup,
            statusTip=self.tr("Insert table column"), triggered=self.insertTableColumn)
        self.removeTableRowAction = QtGui.QAction(self.tr("Remove row"), self.tableGroup, enabled = False,
            statusTip=self.tr("Remove table row"), triggered=self.removeTableRow)
        self.removeTableColumnAction = QtGui.QAction(self.tr("Remove column"), self.tableGroup, enabled = False,
            statusTip=self.tr("Remove table column"), triggered=self.removeTableColumn)

        self.formatGroup = QtGui.QActionGroup(self, exclusive=False)
        self.fmtBoldAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_text_bold.png'),
            self.tr('Bold'), self.formatGroup, shortcut=QtGui.QKeySequence.Bold, checkable=True,
            statusTip=self.tr("Bold"), triggered=self.setFontBold)
        self.fmtItalicAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_text_italic.png'),
            self.tr('Italic'), self.formatGroup, shortcut=QtGui.QKeySequence.Italic, checkable=True,
            statusTip=self.tr("Italic"), triggered=self.setFontItalic)
        self.fmtUnderlineAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_text_underline.png'),
            self.tr('Underline'), self.formatGroup, shortcut=QtGui.QKeySequence.Underline, checkable=True,
            statusTip=self.tr("Underline"), triggered=self.setFontUnderline)
        self.fmtMonospaceAction = QtGui.QAction(self.tr('Monospace'), self.formatGroup,
            shortcut=self.tr('Strg-M'), checkable=True,
            statusTip=self.tr("Monospace"), triggered=self.setFontFixedPitch)
        self.fntSizeIncreaseAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/fontsizeup_koffice.png'),
            self.tr('Bigger'), self.formatGroup, shortcut=self.tr('Strg-+'), checkable=False,
            statusTip=self.tr("Increase font size"),
            triggered=self.changeFontSize)
        self.fntSizeIncreaseAction.setData(+1)
        self.fntSizeDecreaseAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/fontsizedown_koffice.png'),
            self.tr('Smaller'), self.formatGroup, shortcut=self.tr('Strg--'), checkable=False,
            statusTip=self.tr("Decrease font size"),
            triggered=self.changeFontSize)
        self.fntSizeDecreaseAction.setData(-1)
        self.fmtColorAction = QtGui.QAction( QtGui.QIcon(':/icons/textedit/package_graphics.png'),
            self.tr('Color'), self.formatGroup, statusTip=self.tr("Text color"), triggered=self.setTextColor)
        self.fmtColorAction.setData(QtCore.Qt.black)
        self.setupColorActions(self.formatGroup)

        self.listGroup = QtGui.QActionGroup(self)
        self.listGroup.triggered.connect(self.formatList)
        names = (self.tr('No list'), self.tr('Disc list'), self.tr('Circle list'),
            self.tr('Square list'), self.tr('Decimal list'), self.tr('Lower alpha list'),
            self.tr('Upper alpha list'), self.tr('Lower roman list'), self.tr('Upper roman list'), )
        self.listStyles = [None, QtGui.QTextListFormat.ListDisc, QtGui.QTextListFormat.ListCircle,
            QtGui.QTextListFormat.ListSquare, QtGui.QTextListFormat.ListDecimal, QtGui.QTextListFormat.ListLowerAlpha,
            QtGui.QTextListFormat.ListUpperAlpha, QtGui.QTextListFormat.ListLowerRoman, QtGui.QTextListFormat.ListUpperRoman]
        icons = [QtGui.QIcon(), QtGui.QIcon(':/icons/textedit/list_disc.png'), QtGui.QIcon(':/icons/textedit/list_circle.png'),
                 QtGui.QIcon(':/icons/textedit/list_square.png'), QtGui.QIcon(':/icons/textedit/list_numbered.png'), QtGui.QIcon(':/icons/textedit/list_alpha_lowcase.png'), 
                 QtGui.QIcon(':/icons/textedit/list_alpha_upcase.png'), QtGui.QIcon(':/icons/textedit/list_roman_lowcase.png'), QtGui.QIcon(':/icons/textedit/list_roman_upcase.png')]
        self.listActions = []
        for name, style, icon in zip(names, self.listStyles, icons):
            action = QtGui.QAction(icon, name, self.listGroup, checkable=True)
            action.setData(style)
            self.listActions.append(action)

        self.alignmentGroup = QtGui.QActionGroup(self)
        self.alignmentGroup.triggered.connect(self._setAlignment)
        self.justLeftAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_justify_left.png'),
            self.tr('Align left'), self.alignmentGroup, checkable=True)
        self.justCenterAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_justify_center.png'),
            self.tr('Align center'), self.alignmentGroup, checkable=True)
        self.justRightAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_justify_right.png'),
            self.tr('Align right'), self.alignmentGroup, checkable=True)
        self.indentLessAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_indent_less.png'),
            self.tr('Indent less'), self.alignmentGroup, triggered=self.indentLess)
        self.indentMoreAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/format_indent_more.png'),
            self.tr('Indent more'), self.alignmentGroup, triggered=self.indentMore)

        self.findAction = QtGui.QAction(QtGui.QIcon(':/icons/textedit/edit_find.png'), self.tr("Find ..."), self,
            statusTip=self.tr("Find"), shortcut=QtGui.QKeySequence.Find,
            triggered=self.findDialog)
        self.findNextAction = QtGui.QAction(self.tr("Find Next"), self,
            statusTip=self.tr("Find next occurence"), shortcut=QtGui.QKeySequence.FindNext,
            triggered=self.findNext)
        self.findPreviousAction = QtGui.QAction(self.tr("Find Previous"), self,
            statusTip=self.tr("Find previous occurence"), shortcut=QtGui.QKeySequence.FindPrevious,
            triggered=self.findPrevious)
        self.replaceAction = QtGui.QAction(self.tr("Replace ..."), self,
            statusTip=self.tr("Replace"), shortcut=QtGui.QKeySequence.Replace,
            triggered=self.showReplaceDialog)

        self.viewGroup = QtGui.QActionGroup(self, exclusive=False)
        self.viewWhiteSpaceAction = QtGui.QAction(self.tr('View Whitespace'), self.viewGroup, checkable=True,
            triggered=self.viewWhiteSpace)
        self.viewEndOfLineAction = QtGui.QAction(self.tr('View End of Line'), self.viewGroup, checkable=True,
            triggered=self.viewEndOfLine)


    def setupColorActions(self, actionGroup):
        colors = (QtCore.Qt.black, QtCore.Qt.red, QtCore.Qt.darkRed, QtCore.Qt.green,
            QtCore.Qt.darkGreen, QtCore.Qt.blue, QtCore.Qt.darkBlue, QtCore.Qt.cyan,
            QtCore.Qt.darkCyan, QtCore.Qt.magenta, QtCore.Qt.darkMagenta, QtCore.Qt.yellow,
            QtCore.Qt.darkYellow, QtCore.Qt.gray, QtCore.Qt.darkGray, QtCore.Qt.lightGray,
            QtCore.Qt.white)
        names = (self.tr('Black'), self.tr('Red'), self.tr('Dark red'), self.tr('Green'),
            self.tr('Dark green'), self.tr('Blue'), self.tr('Dark blue'), self.tr('Cyan'),
            self.tr('Dark cyan'), self.tr('Magenta'), self.tr('Dark magenta'), self.tr('Yellow'),
            self.tr('Dark yellow'), self.tr('Gray'), self.tr('Dark gray'), self.tr('Light gray'),
            self.tr('White'))
        self.colorActions = []
        for color, name in zip(colors, names):
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(color)
            action = QtGui.QAction(QtGui.QIcon(pixmap), name, actionGroup, triggered = self.setTextColor)
            action.setData(color)
            self.colorActions.append(action)


    def setupGui(self):
        self.setContentsMargins(0, 0, 0, 0)
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        self.toolBar = QtGui.QToolBar(self.tr('Toolbar'))
        self.toolBar.pyqtConfigure(objectName='maintoolbar')
        self.menuBar = QtGui.QMenuBar()
        mainLayout.setMenuBar(self.menuBar)
        mainLayout.addWidget(self.toolBar)
        mainLayout.addWidget(self.textEdit)
        self.setLayout(mainLayout)


    def setupMenu(self):
        editMenu = self.menuBar.addMenu(self.tr('&Edit'))
        actions = (self.undoAction, self.redoAction, '|', self.cutAction,
            self.copyAction, self.pasteAction, self.deleteAction, '|',
            self.selectAllAction, '|', self.editHtmlAction)
        self.populateMenu(editMenu, actions)

        searchMenu = self.menuBar.addMenu(self.tr('&Search'))
        actions = (self.findAction, self.findNextAction, self.findPreviousAction,
            self.replaceAction,)
        self.populateMenu(searchMenu, actions)

        tableMenu = self.menuBar.addMenu(self.tr('&Table'))
        actions = (self.insertTableAction, self.insertTableRowAction, self.insertTableColumnAction,
            self.removeTableRowAction, self.removeTableColumnAction,)
        self.populateMenu(tableMenu, actions)

        imgMenu = self.menuBar.addMenu(self.tr('&Image'))
        imgMenu.addAction(self.insertImageAction)

        listMenu = self.menuBar.addMenu(self.tr('&List'))
        self.populateMenu(listMenu, self.listActions)

        fmtMenu = self.menuBar.addMenu(self.tr('&Format'))
        actions = (self.fntSizeIncreaseAction, self.fntSizeDecreaseAction, self.fmtBoldAction,
            self.fmtItalicAction, self.fmtUnderlineAction, self.fmtMonospaceAction,)
        self.populateMenu(fmtMenu, actions)

        self.colorMenu = fmtMenu.addMenu('Color')
        self.colorMenu.setIcon(self.fmtColorAction .icon())
        for colorAction in self.colorActions:
            self.colorMenu.addAction(colorAction)
        self.fmtColorAction.setMenu(self.colorMenu)

        parMenu = self.menuBar.addMenu(self.tr('&Paragraph'))
        actions = (self.justLeftAction, self.justCenterAction, self.justRightAction,
            self.indentMoreAction, self.indentLessAction,)
        self.populateMenu(parMenu, actions)

        optMenu = self.menuBar.addMenu(self.tr('&Options'))
        optMenu.addAction(self.viewWhiteSpaceAction)
        optMenu.addAction(self.viewEndOfLineAction)


    def populateMenu(self, menu, actions):
        for action in actions:
            if action == '|':
                menu.addSeparator()
            else:
                menu.addAction(action)

    def setupToolbar(self):
        self.toolBar.addAction(self.cutAction)
        self.toolBar.addAction(self.copyAction)
        self.toolBar.addAction(self.pasteAction)
        self.toolBar.addAction(self.fntSizeIncreaseAction)
        self.toolBar.addAction(self.fntSizeDecreaseAction)
        self.toolBar.addAction(self.fmtBoldAction)
        self.toolBar.addAction(self.fmtItalicAction)
        self.toolBar.addAction(self.fmtUnderlineAction)
        self.toolBar.addAction(self.fmtColorAction)
        self.toolBar.addAction(self.justLeftAction)
        self.toolBar.addAction(self.justCenterAction)
        self.toolBar.addAction(self.justRightAction)
        self.toolBar.addAction(self.indentMoreAction)
        self.toolBar.addAction(self.indentLessAction)


    def undo(self):
        self.textEdit.undo()

    def redo(self):
        self.textEdit.redo()

    def cut(self):
        self.textEdit.cut()

    def copy(self):
        self.textEdit.copy()

    def paste(self):
        self.textEdit.paste()

    def deleteSelection(self):
        textCursor = self.textEdit.textCursor()
        if not textCursor.hasSelection():
            return
        textCursor.deleteChar()

    def selectAll(self):
        self.textEdit.selectAll()

    def editHtml(self, state):
        self.formatGroup.setEnabled(not state)
        self.tableGroup.setEnabled(not state)
        self.listGroup.setEnabled(not state)
        self.alignmentGroup.setEnabled(not state)
        self.fmtColorAction.setEnabled(not state)
        self.viewGroup.setEnabled(not state)
        self.textEdit.setAcceptRichText(not state)
        if state == True:
            # we like to edit raw HTML
            self.textEdit.setPlainText(self.textEdit.toHtml())
        else:
            # we have edited raw HTML and would like to see rich text
            self.textEdit.setHtml(self.textEdit.toPlainText())

    def findDialog(self):
        self.showReplaceDialog(None, False)

    def searchFlags(self, flags):
        if self.lastSearchData['matchWholeWord']:
            flags = flags | QtGui.QTextDocument.FindWholeWords
        if self.lastSearchData['matchCase']:
            flags = flags | QtGui.QTextDocument.FindCaseSensitively
        return flags

    def findString(self, flags=0):
        self.lastSearchData = self.replaceDialog.getData()
        flags = self.searchFlags(flags)
        found = self.textEdit.find(self.lastSearchData['searchText'], QtGui.QTextDocument.FindFlags(flags))
        self.replaceDialog.infoLabel.setText([self.tr("No match"), self.tr("Match")][found])

    def findNext(self):
        self.findString()

    def findPrevious(self):
        self.findString(QtGui.QTextDocument.FindBackward)

    def showReplaceDialog(self, unused, showReplaceItems=True):
        self.replaceDialog.setItemsVisibility(showReplaceItems)
        textCursor = self.textEdit.textCursor()
        if textCursor.hasSelection():
            self.lastSearchData['searchText'] = str(textCursor.selection().toPlainText()).strip()
            self.replaceDialog.setData(self.lastSearchData)
            self.replaceDialog.replaceText.setFocus(QtCore.Qt.OtherFocusReason)
        self.replaceDialog.infoLabel.clear()
        self.replaceDialog.show()
        self.replaceDialog.raise_()
        self.replaceDialog.activateWindow()

    def replaceString(self, flags=0):
        self.lastSearchData = self.replaceDialog.getData()
        flags = self.searchFlags(flags)
        textCursor = self.textEdit.textCursor()
        # set text cursor to start of selection if any
        textCursor.setPosition(textCursor.selectionStart())
        self.textEdit.setTextCursor(textCursor)
        found = self.textEdit.find(self.lastSearchData['searchText'], QtGui.QTextDocument.FindFlags(flags))
        if found:
            textCursor = self.textEdit.textCursor()
            textCursor.removeSelectedText()
            textCursor.insertText(self.lastSearchData['replaceText'])
            self.textEdit.find(self.lastSearchData['searchText'], QtGui.QTextDocument.FindFlags(flags))
        self.replaceDialog.infoLabel.setText(QtCore.QString(self.tr("Replacements: %1")).arg([0,1][found]))

    def replaceAll(self, flags=0):
        self.lastSearchData = self.replaceDialog.getData()
        flags = self.searchFlags(flags)
        textCursor = self.textEdit.textCursor()
        # set text cursor to start of document
        textCursor.setPosition(0)
        self.textEdit.setTextCursor(textCursor)
        cnt = 0
        self.textEdit.setUpdatesEnabled(False)
        textCursor.beginEditBlock()
        while True:
            found = self.textEdit.find(self.lastSearchData['searchText'], QtGui.QTextDocument.FindFlags(flags))
            if found:
                cnt = cnt+1
                textCursor = self.textEdit.textCursor()
                textCursor.removeSelectedText()
                textCursor.insertText(self.lastSearchData['replaceText'])
            else:
                break
        textCursor.endEditBlock()
        self.textEdit.setUpdatesEnabled(True)
        self.replaceDialog.infoLabel.setText(QtCore.QString(self.tr("Replacements: %1")).arg(cnt))

    def replaceSelection(self, flags=0):
        textCursor = self.textEdit.textCursor()
        if not textCursor.hasSelection():
            self.replaceDialog.infoLabel.setText(self.tr("No Selection"))
            return
        self.lastSearchData = self.replaceDialog.getData()
        flags = self.searchFlags(flags)
        selStart = textCursor.selectionStart()
        selEnd = textCursor.selectionEnd()
        # set text cursor to start of selection
        textCursor.setPosition(selStart)
        self.textEdit.setTextCursor(textCursor)
        # the end position of the selectetion changes if replacement text has different length
        delta = len(self.lastSearchData['replaceText']) - len(self.lastSearchData['searchText'])
        cnt = 0
        self.textEdit.setUpdatesEnabled(False)
        while True:
            found = self.textEdit.find(self.lastSearchData['searchText'], QtGui.QTextDocument.FindFlags(flags))
            if found:
                textCursor = self.textEdit.textCursor()
                if textCursor.selectionStart() > selEnd:
                    break
                cnt = cnt+1
                textCursor.removeSelectedText()
                textCursor.insertText(self.lastSearchData['replaceText'])
                selEnd = selEnd + delta
            else:
                break
        self.textEdit.setUpdatesEnabled(True)
        self.replaceDialog.infoLabel.setText(QtCore.QString(self.tr("Replacements: %1")).arg(cnt))

    def insertTable(self):
        tableDialog = cTableFormatDialog()
        if QtGui.QDialog.Rejected == tableDialog.exec_():
            return
        (rows, columns) = tableDialog.getResult()
        textCursor = self.textEdit.textCursor()
        tableFormat = QtGui.QTextTableFormat()
        tableFormat.setCellPadding(2.0)
        textCursor.insertTable(rows, columns, tableFormat)

    def overwriteMode(self):
        self.textEdit.setOverwriteMode(not self.textEdit.overwriteMode())
        if self.textEdit.overwriteMode():
            self.updateCursor()
        else:
            self.textEdit.setCursorWidth(1)

    def updateCursor(self):
        fontMetrics = QtGui.QFontMetrics(self.textEdit.currentFont())
        c = self.textEdit.document().characterAt(self.textEdit.textCursor().position())
        width = fontMetrics.width(c)
        self.textEdit.setCursorWidth(width)

    def copyAvailable(self, isCopyAvailable):
        textCursor = self.textEdit.textCursor()
        self.deleteAction.setEnabled(isCopyAvailable)

    def currentCharFormatChanged(self, textCharFormat):
        self.fmtItalicAction.setChecked(textCharFormat.fontItalic())
        self.fmtUnderlineAction.setChecked(textCharFormat.fontUnderline())
        self.fmtMonospaceAction.setChecked(textCharFormat.fontFixedPitch())
        self.fmtBoldAction.setChecked(textCharFormat.fontWeight() > QtGui.QFont.Normal)

    def cursorPositionChanged(self):
        currentAlignment = self.textEdit.alignment()
        try:
            alignmentIndex = [operator.eq(currentAlignment, a) for a in (QtCore.Qt.AlignLeft, QtCore.Qt.AlignHCenter, QtCore.Qt.AlignRight)].index(True)
            self.alignmentGroup.actions()[alignmentIndex].setChecked(True)
        except ValueError:
            #TODO: log this exception
            pass
        textCursor = self.textEdit.textCursor()
        currentTable = textCursor.currentTable()
        isCursorInTable = currentTable is not None
        self.insertTableColumnAction.setEnabled(isCursorInTable)
        self.insertTableRowAction.setEnabled(isCursorInTable)
        self.removeTableRowAction.setEnabled(isCursorInTable and currentTable.rows() > 1)
        self.removeTableColumnAction.setEnabled(isCursorInTable and currentTable.columns() > 1)

        currentList = textCursor.currentList()
        isCursorInList = currentList is not None
        if isCursorInList:
            listStyle = currentList.format().style()
            index = self.listStyles.index(listStyle)
        else:
            index = 0
        self.listActions[index].setChecked(True)

        if self.textEdit.overwriteMode():
            self.updateCursor()

    def insertTableRow(self):
        (currentTable, currentRow, currentColumn) = self._getPositionInTable()
        if currentRow+1 >= currentTable.rows():
            # cursor is in the last row
            currentTable.appendRows(1)
        else:
            # cursor not in last row
            currentTable.insertRows(currentRow+1, 1)
        self.textEdit.moveCursor(QtGui.QTextCursor.NextRow)

    def insertTableColumn(self):
        (currentTable, currentRow, currentColumn) = self._getPositionInTable()
        if currentColumn+1 >= currentTable.columns():
            # cursor is in the last column
            currentTable.appendColumns(1)
        else:
            # cursor not in last column
            currentTable.insertColumns(currentColumn+1, 1)
        self.textEdit.moveCursor(QtGui.QTextCursor.NextCell)

    def removeTableRow(self):
        (currentTable, currentRow, currentColumn) = self._getPositionInTable()
        currentTable.removeRows(currentRow, 1)

    def removeTableColumn(self):
        (currentTable, currentRow, currentColumn) = self._getPositionInTable()
        currentTable.removeColumns(currentColumn, 1)

    def _getPositionInTable(self):
        textCursor = self.textEdit.textCursor()
        currentTable = textCursor.currentTable()
        currentTextTableCell = currentTable.cellAt(textCursor)
        currentRow = currentTextTableCell.row()
        currentColumn = currentTextTableCell.column()
        return (currentTable, currentRow, currentColumn)

    def insertImage(self):
        selectImageDialog = cImageInsertDialog(self)
        if QtGui.QDialog.Rejected == selectImageDialog.exec_():
            return
        (imageIdList, percentScale) = selectImageDialog.getData()
        for imageId in imageIdList:
            pm = QtGui.QPixmap()
            pm.loadFromData(self.textEdit.imageProvider(imageId))
            width = pm.width()*percentScale/100.0;
            height = pm.height()*percentScale/100.0;
            pm = None
            textImageFormat = QtGui.QTextImageFormat()
            textImageFormat.setName("#%d" % imageId)
            textImageFormat.setWidth(width)
            textImageFormat.setHeight(height)
            self.textEdit.textCursor().insertImage(textImageFormat)

    def formatList(self):
        listStyle = self.sender().checkedAction().data().toInt()[0]
        textCursor = self.textEdit.textCursor()
        currentList = textCursor.currentList()
        if 0 == listStyle:
            # no list: list to plain text
            n = currentList.count()
            while n > 0:
                currentList.removeItem(0)
                n = n - 1
            blockFormat = textCursor.blockFormat()
            blockFormat.setIndent(0)
            textCursor.setBlockFormat(blockFormat)
        else:
            if currentList is None:
                # create a new list
                textCursor.createList(listStyle)
            else:
                # change style of current list
                currentFormat = currentList.format()
                currentFormat.setStyle(listStyle)
                currentList.setFormat(currentFormat)

    def changeFontSize(self):
        # not only change font size; resizing a selected image is also performed
        ofs = self.sender().data().toInt()[0]
        textCursor = self.textEdit.textCursor()
        if textCursor.hasSelection():
            imageFormat = textCursor.charFormat().toImageFormat()
            if imageFormat.isValid():
                h = imageFormat.height()
                w = imageFormat.width()
                scale = 1.1
                if ofs < 0:
                    scale = 1.0/scale
                imageFormat.setWidth(w*scale)
                imageFormat.setHeight(h*scale)
                textCursor.setCharFormat(imageFormat)
                return
        size = self.textEdit.fontPointSize()
        if size <= 0.0:
            size = self.textEdit.defaultFontSize
        size = min(max(size+ofs, 6), 20)
        self.textEdit.setFontPointSize(size)

    def setFontBold(self, isBold):
        self.textEdit.setFontWeight([QtGui.QFont.Normal, QtGui.QFont.Bold][isBold])

    def setFontItalic(self, isItalic):
        self.textEdit.setFontItalic(isItalic)

    def setFontUnderline(self, isUnderline):
        self.textEdit.setFontUnderline(isUnderline)

    def setFontFixedPitch(self, isFixedPitch):
        ccf = self.textEdit.currentCharFormat()
        ccf.setFontFixedPitch(isFixedPitch)
        fontFamily = [self.textEdit.defaultFontName, self.textEdit.defaultTypewriteFontName][isFixedPitch]
        ccf.setFontFamily(fontFamily)
        self.textEdit.setCurrentCharFormat(ccf)

    def setTextColor(self):
        c = self.sender().data().toInt()[0]
        self.textEdit.setTextColor(QtCore.Qt.GlobalColor(c))
        self.fmtColorAction.setData(c);

    def _setAlignment(self):
        whichAlignmentIndex = [action.isChecked() for action in self.alignmentGroup.actions()].index(True)
        self.textEdit.setAlignment((QtCore.Qt.AlignLeft, QtCore.Qt.AlignHCenter, QtCore.Qt.AlignRight)[whichAlignmentIndex])


    def indentLess(self):
        textCursor = self.textEdit.textCursor()
        blockFormat = textCursor.blockFormat()
        newIndent = max(0, blockFormat.indent()-1)
        blockFormat.setIndent(newIndent)
        textCursor.setBlockFormat(blockFormat)

    def indentMore(self):
        textCursor = self.textEdit.textCursor()
        blockFormat = textCursor.blockFormat()
        newIndent = blockFormat.indent()+1
        blockFormat.setIndent(newIndent)
        textCursor.setBlockFormat(blockFormat)

    def viewWhiteSpace(self, isOn):
        textOption = self.textEdit.document().defaultTextOption()
        flags = textOption.flags()
        if isOn:
            flags = flags | QtGui.QTextOption.ShowTabsAndSpaces
        else:
            flags = flags & ~QtGui.QTextOption.ShowTabsAndSpaces
        textOption.setFlags(flags)
        self.textEdit.document().setDefaultTextOption(textOption)

    def viewEndOfLine(self, isOn):
        textOption = self.textEdit.document().defaultTextOption()
        flags = textOption.flags()
        if isOn:
            flags = flags | QtGui.QTextOption.ShowLineAndParagraphSeparators
        else:
            flags = flags & ~QtGui.QTextOption.ShowLineAndParagraphSeparators
        textOption.setFlags(flags)
        self.textEdit.document().setDefaultTextOption(textOption)
