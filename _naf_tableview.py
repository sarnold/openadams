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
from _naf_database import TYPE_FOLDER, TYPE_REQUIREMENT
import _naf_filter

NORMAL_RELATION = 0
REVERSE_RELATION = 1
IGNORE_RELATION = 2

class cItemTableModel(QtCore.QAbstractTableModel):
    """Model to get items from related tableName which are related
       to a certain item identified by parentid
    """
    def __init__(self, tableName, columnNames, relationType=NORMAL_RELATION, itemsCheckable=False):
        QtCore.QAbstractTableModel.__init__(self)
        if itemsCheckable: assert(relationType==IGNORE_RELATION)
        self.parentid = -1
        self.idmap = []
        self.rowCount = -1
        self.columnCount = len(columnNames)
        self.tableName = tableName
        self.tableDisplayName = nafdb.getTableDisplayName(tableName)
        self.columnNames = columnNames
        self.columnstring = ','.join(columnNames)
        self.headerNames = nafdb.getHeaderDataForColumns(tableName, columnNames)
        self.orderClause = ""
        self.whereClause = ""
        self.relationType = relationType
        self.relatedidmap = []
        self.itemsCheckable = [Qt.NoItemFlags, Qt.ItemIsUserCheckable][itemsCheckable]

    def setCurrentIndex(self, parentid, updateRelatedIdMap=True):
        logging.info("parentid=%d" % parentid)
        self.parentid = parentid
        cur = nafdb.connection.cursor()
        if self.relationType == REVERSE_RELATION:
            query = 'select id from %(tn)s where id in (select id from relations where relatedid=?) %(wc)s %(oc)s;' % {'tn':self.tableName, 'oc':self.orderClause, 'wc':self.whereClause}
        elif self.relationType == IGNORE_RELATION:
            query = 'select id from %(tn)s where id != ? %(wc)s %(oc)s;' % {'tn':self.tableName, 'oc':self.orderClause, 'wc':self.whereClause}
        else: # NORMAL_RELATION
            query = 'select id from %(tn)s where id in (select relatedid from relations where id=?) %(wc)s %(oc)s;' % {'tn':self.tableName, 'oc':self.orderClause, 'wc':self.whereClause}
        cur.execute(query, (self.parentid,))
        self.idmap = [id[0] for id in cur.fetchall()]
        self.rowCount = len(self.idmap)
        if updateRelatedIdMap:
            # in case of sorting or filtering the relatedidmap needs not to be updated
            if self.itemsCheckable == Qt.ItemIsUserCheckable:
                query = 'select id from %(tn)s where id in (select relatedid from relations where id=?);' % {'tn':self.tableName}
                cur.execute(query, (self.parentid,))
                self.relatedidmap = [id[0] for id in cur.fetchall()]
            else:
                self.relatedidmap = []
        self.reset()

    def rowCount(self, parent):
        return self.rowCount

    def columnCount(self, parent):
        return self.columnCount

    def _translate(self, item):
        return QtCore.QCoreApplication.translate('lookupTable', item)

    def data(self, index, role):
        row = index.row()
        id = self.idmap[row]
        if role == Qt.CheckStateRole and self.itemsCheckable == Qt.ItemIsUserCheckable and index.column() == 0:
            return QtCore.QVariant([Qt.Unchecked, Qt.Checked][id in self.relatedidmap])
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return QtCore.QVariant()
        columnName = self.columnNames[index.column()]
        logging.debug("row=%s, id=%s, columnName=%s"%  (str(row), str(id), str(columnName)))
        return nafdb.getItemForId(self.tableName, id, columnName, self._translate)

    def headerData(self, section, orientation, role):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return QtCore.QVariant()
        if orientation == Qt.Horizontal:
            return QtCore.QVariant(self.headerNames[section])
        else:
            return QtCore.QVariant(section+1)

    def sort(self, column, order):
        logging.debug("sort(column=%d, order=%d)" % (column, order))
        self.layoutAboutToBeChanged.emit()
        self.orderClause = "order by %s %s" % (self.columnNames[column], ('ASC', 'DESC')[order])
        self.setCurrentIndex(self.parentid, updateRelatedIdMap=False)
        self.layoutChanged.emit()

    def setFilter(self, tableName, whereClause):
        if tableName != self.tableName:
            return
        self.layoutAboutToBeChanged.emit()
        if len(whereClause) > 0:
            self.whereClause = 'and ' + whereClause
        else:
            self.whereClause = whereClause

        self.setCurrentIndex(self.parentid, updateRelatedIdMap=False)
        self.layoutChanged.emit()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flags = QtCore.QAbstractItemModel.flags(self, index)
        if index.column() == 0:
            return flags | self.itemsCheckable
        return flags

    def setData(self, index, value, role):
        if role == Qt.CheckStateRole:
            row = index.row()
            id = self.idmap[row]
            if value.toInt()[0] != 0:
                self.relatedidmap.append(id)
            else:
                self.relatedidmap.remove(id)
            return True
        return False

    def submit(self):
        # if items are not checkable there is nothing to submit
        if not self.itemsCheckable:
            return False
        # submit assumes certain conditions
        assert(self.itemsCheckable == Qt.ItemIsUserCheckable)
        assert(self.relationType==IGNORE_RELATION)
        cur = nafdb.connection.cursor()
        cur.execute("delete from relations where id=? and relatedid in (select id from %s)" % self.tableName, (self.parentid,))
        cur.executemany("insert into relations values (?, ?);", zip([self.parentid] * len(self.relatedidmap), self.relatedidmap))
        nafdb.connection.commit()
        return True


class cNotifier(object):
    def __init__(self):
        self.observer = []

    def addObserver(self, observer):
        self.observer.append(observer)

    def setCurrentIndex(self, itemid):
        for observer in self.observer:
            observer.mapper.setCurrentIndex(itemid)

    def beginResetModel(self):
        for observer in self.observer:
            observer.mapper.beginResetModel()

    def endResetModel(self):
        for observer in self.observer:
            observer.mapper.endResetModel()

    def setFilter(self, tableName, whereClause):
        for observer in self.observer:
            observer.mapper.setFilter(tableName, whereClause)

    def submit(self):
        for observer in self.observer:
            observer.mapper.submit()

    def revert(self):
        for observer in self.observer:
            observer.mapper.revert()


class cItemTableView(QtGui.QTableView):
    def __init__(self, model, parent=None):
        QtGui.QTableView.__init__(self, parent, sortingEnabled=True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.setModel(model)
        self.mapper = self.model()


class cAllItemTableView(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        views = []
        featureTableView = cItemTableView(cItemTableModel('features', ('id', 'title', 'priority', 'risk', 'status', 'keywords')), self)
        views.append(featureTableView)
        requirementTableView = cItemTableView(cItemTableModel('requirements', ('id', 'title', 'priority', 'risk', 'status', 'complexity', 'assigned', 'effort', 'category', 'testability', 'baseline', 'keywords')), self)
        views.append(requirementTableView)
        usecaseTableView = cItemTableView(cItemTableModel('usecases', ('id', 'title', 'priority', 'usefrequency', 'actors', 'stakeholders', 'keywords')), self)
        views.append(usecaseTableView)
        testcaseTableView = cItemTableView(cItemTableModel('testcases', ('id', 'title', 'priority', 'keywords')), self)
        views.append(testcaseTableView)
        testsuiteTableView = cItemTableView(cItemTableModel('testsuites', ('id', 'title', 'keywords')), self)
        views.append(testsuiteTableView)
        componentTableView = cItemTableView(cItemTableModel('components', ('id', 'title', 'keywords', 'kind')), self)
        views.append(componentTableView)
        self.mapper = cNotifier()
        map(self.mapper.addObserver, views)
        tabBar = QtGui.QTabBar(self)
        for view in views:
            tabBar.addTab(view.model().tableDisplayName)
        tabBar.currentChanged.connect(self.showTabPage)
        vboxLayout = QtGui.QVBoxLayout()
        vboxLayout.setContentsMargins(0, 0, 0, 0)
        vboxLayout.setSpacing(0)
        vboxLayout.addWidget(tabBar)
        stackLayout = QtGui.QStackedLayout()
        stackLayout.setContentsMargins(0, 0, 0, 0)
        vboxLayout.addLayout(stackLayout)
        map(stackLayout.addWidget, views)
        self.setLayout(vboxLayout)
        self.stackLayout = stackLayout

    def showTabPage(self, index):
        self.stackLayout.setCurrentIndex(index)

    def model(self):
        return self.mapper

