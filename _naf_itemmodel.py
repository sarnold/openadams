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

import sqlite3, logging

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

import _naf_database as nafdb


class cItemModel(QtCore.QAbstractTableModel):
    def __init__(self, tableName):
        QtCore.QAbstractTableModel.__init__(self)
        self.tableName = tableName
        self.resetData()
        self.modelReset.connect(self.resetData)
        self.lookupModel = {} # --
        self.historyModel = {}

    def rowCount(self, parent):
        return self.rowCount

    def columnCount(self, parent):
        return self.columnCount

    def data(self, index, role):
        if role in (Qt.DisplayRole, Qt.EditRole):
            data = self._getItem(index.row(), index.column())
            return data
        return QtCore.QVariant()

    def _translate(self, item):
        return QtCore.QCoreApplication.translate('lookupTable', item)
        
    def _getItem(self, id, columnIndex):
        logging.info("id=%d", id)
        columnName = self.columns[columnIndex]
        try:
            item = nafdb.getItemForId(self.tableName, id, columnName, self._translate)
            return item
        except TypeError:
            logging.error("id=%d, columnIndex=%d, columnName=%s" %(id, columnIndex, columnName))
            return '?'

    def resetData(self):
        self.rowCount = 0
        self.columnCount = 0
        self.columns = nafdb.getColumnNames(self.tableName)
        self.columnCount = len(self.columns)
        if nafdb.connection is not None:
            self.cur = nafdb.connection.cursor()
            # here rowCount actually means the largest requirement id, not the number of requirements
            self.cur.execute('select max(id) from %s;' % self.tableName)
            n = self.cur.fetchone()[0]
            if n is not None:
                self.rowCount =  int(n)+1
            else:
                self.rowCount = 0
            for lutTableName, lookupModel in self.lookupModel.iteritems():
                lutTableRows = [self._translate(item) for item in nafdb.getLookupTableRows(lutTableName)]
                lookupModel.setStringList(lutTableRows)
            for historyTableName, historyModel in self.historyModel.iteritems():
                historyModel.setStringList(nafdb.getHistoryTableRows(historyTableName))

    def getLabel(self, column):
        return QtCore.QString(nafdb.getHeaderDataForColumns(self.tableName, (column,))[0])

    def getColumns(self):
        return self.columns

    ##def getLookupTableRows(self, columnName):
    ##    #TODO: check if this is a dead function
    ##    lutTableName = nafdb.getLookupTableName(self.tableName, columnName)
    ##    lutTableRows = [QtCore.QCoreApplication.translate('lookupTable', item) for item in nafdb.getLookupTableRows(lutTableName)]
    ##    print lutTableRows 
    ##    return lutTableRows#nafdb.getLookupTableRows(lutTableName)

    def getLookupModel(self, lutTableName):
        if not self.lookupModel.has_key(lutTableName):
            lutTableRows = nafdb.getLookupTableRows(lutTableName)
            lutTableRows = [self._translate(item) for item in nafdb.getLookupTableRows(lutTableName)]
            self.lookupModel[lutTableName] = QtGui.QStringListModel(lutTableRows)
        return self.lookupModel[lutTableName]

    def getHistoryModel(self, historyTableName):
        if not self.historyModel.has_key(historyTableName):
            self.historyModel[historyTableName] = QtGui.QStringListModel(nafdb.getHistoryTableRows(historyTableName))
        return self.historyModel[historyTableName]

    def setData(self, index, value, role):
        if role != QtCore.Qt.EditRole:
            return
        itemid = index.row()
        columnName = self.columns[index.column()]
        if value.type() == QtCore.QVariant.Int:
            value = value.toInt()[0]
        elif value.type() ==  QtCore.QVariant.String:
            value = unicode(value.toString())
        elif value.type() ==  QtCore.QVariant.ByteArray:
            value = buffer(str(value.toPyObject()))
        else:
            raise TypeError(value.typeName())
        self.cur = nafdb.connection.cursor()
        cmd = "update %s set '%s'=? where id==?;" % (self.tableName, columnName)
        self.cur.execute(cmd, (value, itemid))
        return True

    def submit(self):
        nafdb.connection.commit()
        return True

    def revert(self):
        # revert is not required, because setData is not called when we cancel editing
        return super(cItemModel, self).revert()


class cItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)

    def setEditorData(self, editor, index):
        if isinstance(editor, QtGui.QComboBox):
            value = index.model().data(index, Qt.EditRole)
            if value is None: return
            pos = editor.findText(value)
            if pos >= 0:
                editor.setCurrentIndex(pos)
            else:
                editor.insertItem(0, value)
        else:
            super(cItemDelegate, self).setEditorData(editor, index)
        return

    def setModelData(self, editor, model, index):
        ##print "setModelData", editor, model
        if isinstance(editor, QtGui.QComboBox):
            if editor.isEditable():
                data = QtCore.QVariant(editor.currentText())
                model.setData(index, data, QtCore.Qt.EditRole)
            else:
                model.setData(index, QtCore.QVariant(editor.currentIndex()), QtCore.Qt.EditRole)
        else:
            super(cItemDelegate, self).setModelData(editor, model, index)
