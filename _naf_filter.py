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

import logging, sys
from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_database as nafdb
import _naf_tree
import _naf_tableview
import _naf_requirement
import _naf_usecase


class cFilterTextModel(QtCore.QAbstractListModel):
    def __init__(self, tableName):
        QtCore.QAbstractListModel.__init__(self)
        (self.columnNames, self.itemLabels) = nafdb.getTextColumnNames(tableName)
        self.rowCount = len(self.itemLabels)
        self.itemSelectionState = [False] * self.rowCount
        self.conditionLabels = [
            self.tr('contains string'), self.tr('not contains string'),
            self.tr('contains string (exact case)'), self.tr('not contains string (exact case)'),
            self.tr('contains word'), self.tr('not contains word'),
            self.tr('matches regular expression'), self.tr('not matches regular expression')]
        self.currentCondition = 0
        self.pattern = ''

    def getWhereClause(self):
        clause = []
        joinop = ''
        for i in range(self.rowCount):
            if not self.itemSelectionState[i]:
                continue
            pattern = self.pattern
            if self.currentCondition in (0, 1):
                # (not) contains the string
                pattern = '%' + self.pattern + '%'
                op = 'like'
            elif self.currentCondition in (2, 3):
                # (not) contains the string (exact case)
                pattern = '*' + self.pattern + '*'
                op = 'glob'
            elif self.currentCondition in (4, 5):
                # (not) contains the word
                pattern = r'\b' + self.pattern + r'\b'
                op = 'regexp'
            else:
                op = 'regexp'
            if self.currentCondition in (1, 3, 5, 7):
                op = 'not ' + op
                joinop = ' and '
            else:
                joinop = ' or '
            clause.append('%s %s "%s"' % (self.columnNames[i], op, pattern))
        clause = joinop.join(clause)
        if len(clause) <= 0:
            return ''
        return '(' + clause + ')'

    def rowCount(self, index):
        return self.rowCount

    def data(self, index, role):
         if role == Qt.DisplayRole:
             return QtCore.QVariant(self.itemLabels[index.row()])
         else:
             return QtCore.QVariant()

    def getConditionLabels(self):
        return self.conditionLabels

    def currentConditionChanged(self, selection):
        logging.debug("selection=%d" % selection)
        self.currentCondition = selection

    def setPattern(self, pattern):
        logging.debug("pattern=%s" % pattern)
        self.pattern = pattern

    def itemSelectionChanged(self, selected, deselected):
        for modelIndex in selected.indexes():
            self.itemSelectionState[modelIndex.row()] = True
        for modelIndex in deselected.indexes():
            self.itemSelectionState[modelIndex.row()] = False
        logging.debug(str(self.itemSelectionState))


class cFilterTextWidget(QtGui.QWidget):
    def __init__(self, tableName, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._model = cFilterTextModel(tableName)
        itemListView = QtGui.QListView(self)
        itemListView.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        itemListView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        itemListView.setModel(self._model)
        itemListView.selectionModel().selectionChanged.connect(self._model.itemSelectionChanged)
        conditionComboBox = QtGui.QComboBox(self)
        conditionComboBox.addItems(self._model.getConditionLabels())
        conditionComboBox.currentIndexChanged.connect(self._model.currentConditionChanged)
        self.patternLineEdit = QtGui.QLineEdit(self)
        self.patternLineEdit.editingFinished.connect(self.patternEditingFinished)

        hboxLayout = QtGui.QHBoxLayout()
        (left, top, right, bottom) = hboxLayout.getContentsMargins()
        hboxLayout.setContentsMargins(0, top, 0, bottom)
        vboxLayoutLeft = QtGui.QVBoxLayout()
        vboxLayoutLeft.addWidget(QtGui.QLabel(self.tr("Text field")))
        vboxLayoutLeft.addWidget(itemListView)
        vboxLayoutRight = QtGui.QVBoxLayout()
        vboxLayoutRight.addWidget(QtGui.QLabel(self.tr("Condition")))
        vboxLayoutRight.addWidget(conditionComboBox)
        vboxLayoutRight.addWidget(QtGui.QLabel(self.tr("Text or pattern")))
        vboxLayoutRight.addWidget(self.patternLineEdit)
        vboxLayoutRight.addStretch(1)
        hboxLayout.addLayout(vboxLayoutLeft, stretch=0)
        hboxLayout.addLayout(vboxLayoutRight, stretch=1)
        self.setLayout(hboxLayout)

        self.itemListView = itemListView

    def patternEditingFinished(self):
        self._model.setPattern(self.patternLineEdit.text())

    def model(self):
        return self._model

    def doReset(self):
        self.itemListView.selectionModel().clearSelection()



class cFilterIntegerModel(QtCore.QAbstractTableModel):
    def __init__(self, tableName):
        QtCore.QAbstractTableModel.__init__(self)
        self.tableName = tableName
        self.columns = [column for column in nafdb.getColumns(tableName) if column.isFilterable and column._type.find("integer") != -1]
        self.rowCount = len(self.columns)
        self.conditions = [0] * self.rowCount
        self.conditionLabels = '== > < !='.split()
        self.checkState = [0] * self.rowCount
        self.values = [0] * self.rowCount

    def getWhereClause(self):
        clause = []
        for i in range(self.rowCount):
            if not self.checkState[i]:
                continue
            clause.append("%s %s %d" % (self.columns[i].name, self.conditionLabels[self.conditions[i]], self.values[i]))
        clause = ' and '.join(clause)
        if len(clause) <= 0:
            return ''
        return '(' + clause + ')'

    def rowCount(self, index):
        return self.rowCount

    def columnCount(self, index):
        return 3

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return QtCore.QVariant(self.columns[index.row()].displayname)
            elif index.column() == 1:
                return QtCore.QVariant(self.conditionLabels[self.conditions[index.row()]])
            else:
                lookupTable = self.columns[index.row()].lookupTable
                if lookupTable is None:
                    return QtCore.QVariant(self.values[index.row()])
                else:
                    return QtCore.QVariant(self.getLookupTableRows(index)[self.values[index.row()]])
        elif role == Qt.EditRole:
            if index.column() == 1:
                return QtCore.QVariant(self.conditions[index.row()])
            else: # column 2
                return QtCore.QVariant(self.values[index.row()])
        elif role == Qt.CheckStateRole:
            if index.column() == 0:
                return QtCore.QVariant([Qt.Unchecked, Qt.Checked][self.checkState[index.row()]])
        return QtCore.QVariant()

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole: return QtCore.QVariant()
        if orientation != Qt.Horizontal: return QtCore.QVariant()
        return QtCore.QVariant([self.tr('Property'), self.tr('Condition'), self.tr('Value')][section])

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flags = QtCore.QAbstractItemModel.flags(self, index)
        if index.column() == 0:
            return flags | Qt.ItemIsUserCheckable
        return flags | Qt.ItemIsEditable

    def setData(self, index, value, role):
        if role == Qt.CheckStateRole:
            self.checkState[index.row()] = value.toInt()[0] != 0
            return True
        elif role == Qt.EditRole:
            if index.column() == 1:
                self.conditions[index.row()] = value
                return True
            else: # column 2
                self.values[index.row()] = value
                return True
        return False

    def isLookupType(self, index):
        return self.columns[index.row()].lookupTable is not None

    def _translate(self, item):
        return QtCore.QCoreApplication.translate('lookupTable', item)

    def getLookupTableRows(self, index):
        return nafdb.getLookupTableRows(self.columns[index.row()].lookupTable, translatorFunc=self._translate)

    def resetCheckState(self):
        self.checkState = [0] * self.rowCount
        self.dataChanged.emit(self.createIndex(0, 0, None), self.createIndex(self.rowCount-1, 0, None))


class cConditionSelectorDelegate(QtGui.QItemDelegate):
    """See http://doc.trolltech.com/4.6/itemviews-spinboxdelegate.html """
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        editor = QtGui.QComboBox(parent)
        editor.addItems(index.model().conditionLabels)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole).toInt()[0]
        editor.setCurrentIndex(value)

    def setModelData(self, editor, model, index):
        value = editor.currentIndex()
        model.setData(index, value, Qt.EditRole);

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class cValueSelectorDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        if index.model().isLookupType(index):
            editor = QtGui.QComboBox(parent)
            editor.addItems(index.model().getLookupTableRows(index))
        else:
            editor = QtGui.QSpinBox(parent, maximum=sys.maxint)
            editor.setValue(0)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole).toInt()[0]
        if isinstance(editor, QtGui.QSpinBox):
            editor.setValue(value)
        else:
            editor.setCurrentIndex(value)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtGui.QSpinBox):
            value = editor.value()
        else:
            value = editor.currentIndex()
        model.setData(index, value, Qt.EditRole);

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class cFilterIntegerWidget(QtGui.QTableView):
    def __init__(self, tableName, parent=None):
        QtGui.QTableView.__init__(self, parent)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.verticalHeader().setVisible(False)
        self.setItemDelegateForColumn(1, cConditionSelectorDelegate(self))
        self.setItemDelegateForColumn(2, cValueSelectorDelegate(self))
        self.setModel(cFilterIntegerModel(tableName))

    def doReset(self):
        self.model().resetCheckState()


class cArtifactFilterModel(object):
    def __init__(self):
        self.modelList = []

    def appendModel(self, model):
        self.modelList.append(model)

    def getWhereClause(self):
        clause = [self.modelList[0].getWhereClause()]
        for i in range(1, len(self.modelList)):
            clause.append(self.modelList[i].getWhereClause())
        clause = [c for c in clause if len(c) > 0]
        clause = ' and '.join(clause)
        if len(clause) <= 0:
            return ''
        return clause


class cArtifactFilter(QtGui.QWidget):
    signalApplyFilter = QtCore.pyqtSignal(QtGui.QWidget)
    signalResetFilter = QtCore.pyqtSignal(QtGui.QWidget)

    def __init__(self, tableName, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.tableName = tableName
        self._model = cArtifactFilterModel()
        vboxLayout = QtGui.QVBoxLayout()
        self.filterTextWidget = cFilterTextWidget(self.tableName, self)
        self.filterIntegerWidget = cFilterIntegerWidget(self.tableName, self)
        self._model.appendModel(self.filterTextWidget.model())
        self._model.appendModel(self.filterIntegerWidget.model())
        vboxLayout.addWidget(self.filterTextWidget)
        vboxLayout.addWidget(self.filterIntegerWidget, stretch=1)
        hboxLayout = QtGui.QHBoxLayout()
        btnApply = QtGui.QPushButton(self.tr("Apply"))
        btnReset = QtGui.QPushButton(self.tr("Reset"))
        hboxLayout.addStretch(1)
        hboxLayout.addWidget(btnApply)
        hboxLayout.addWidget(btnReset)
        vboxLayout.addLayout(hboxLayout)
        self.setLayout(vboxLayout)
        btnApply.clicked.connect(self.emitSignalApplyFilter)
        btnReset.clicked.connect(self.resetFilter)

    def emitSignalApplyFilter(self):
        self.signalApplyFilter.emit(self)

    def resetFilter(self):
        self.filterTextWidget.doReset()
        self.filterIntegerWidget.doReset()
        self.signalResetFilter.emit(self)

    def model(self):
        return self._model


class cFilterWidget(QtGui.QTabWidget):
    def __init__(self, controller):
        QtGui.QWidget.__init__(self)
        (tableNames, tableDisplayNames) = nafdb.getFilterableTableNames()
        self.filters = []
        for (tableName, tableDisplayName) in zip(tableNames, tableDisplayNames):
            theFilter = cArtifactFilter(tableName)
            self.filters.append(theFilter)
            self.addTab(theFilter, tableDisplayName)
            theFilter.signalApplyFilter.connect(controller.applyFilter)
            theFilter.signalResetFilter.connect(controller.resetFilter)

class cFilterDock(QtGui.QDockWidget):
    def __init__(self, mainController, parent=None):
        QtGui.QDockWidget.__init__(self, "", parent)
        self.setWindowTitle(self.tr("Filter"))
        self.filterWidget =cFilterWidget(mainController)
        self.setWidget(self.filterWidget)

