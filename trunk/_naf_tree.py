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

import sqlite3, logging, pprint

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt

from _naf_database import TYPE_FOLDER, TYPE_REQUIREMENT, TYPE_USECASE, TYPE_IMAGE, \
    TYPE_FEATURE, TYPE_TESTCASE, TYPE_TESTSUITE, TYPE_SIMPLESECTION, TYPE_COMPONENT
import _naf_database as nafdb
import _naf_filter

ARTIFACT_MIME_TYPE = 'application/nafms/treedata'

class cIconProvider(QtCore.QObject):
    def __init__(self):
        self.iconDict = {
            TYPE_FOLDER: QtGui.QIcon(':/icons/folder.png'),
            TYPE_REQUIREMENT: QtGui.QIcon(':/icons/af_requirement.png'),
            TYPE_USECASE: QtGui.QIcon(':/icons/af_usecase.png'),
            TYPE_IMAGE: QtGui.QIcon(':/icons/af_image.png'),
            TYPE_FEATURE : QtGui.QIcon(':/icons/af_feature.png'),
            TYPE_TESTCASE : QtGui.QIcon(':/icons/af_testcase.png'),
            TYPE_TESTSUITE : QtGui.QIcon(':/icons/af_testsuite.png'),
            TYPE_SIMPLESECTION : QtGui.QIcon(':/icons/af_simplesection.png'),
            TYPE_COMPONENT : QtGui.QIcon(':/icons/af_component.png'),
        }
        self.iconDict[TYPE_FOLDER].addFile(':/icons/folder_open.png', mode=QtGui.QIcon.Active, state=QtGui.QIcon.On)

    def icon(self, key):
        if self.iconDict.has_key(key):
            return self.iconDict[key]
        else:
            return QtGui.QIcon()


class cTreeData(object):
    def __init__(self):
        self.dbitems = []
        self.iconprovider = cIconProvider()
        self.filterDict = {}
        for tablename in nafdb.getTableNames():
            self.filterDict[tablename] = ''

    def childCount(self, parent_id):
        "Return the number of childs of parent with parent_id"
        items = [item for item in self.dbitems if item[1]==parent_id]
        return len(items)

    def getItem(self, parent_id, row):
        "Get the row'th item from all items with parent_id"
        items = [item for item in self.dbitems if item[1]==parent_id]
        try:
            return items[row]
        except IndexError:
            ##print self.dbitems
            lst = [item for item in self.dbitems if item[0]==parent_id]
            ##print lst
            return lst[0]

    def getItemTitle(self, item):
        return item[3]

    def getItemType(self, item):
        return item[2]

    def getItemDecoration(self, item):
        ###return self.iconprovider.icon(self.type_to_icon_mapping[item[2]])
        return self.iconprovider.icon(item[2])

    def getParentId(self, item):
        return item[1]

    def getChild(self, parent, row):
        items = [item for item in self.dbitems if item[1]==self.getItemId(parent)]
        try:
            return items[row]
        except IndexError:
            return None

    def getItemId(self, item):
        return item[0]

    def getParentRow(self, parent_id):
        "Return row index and corresponding item identified by parent_id"
        parentids = [item[1] for item in self.dbitems if item[0]==parent_id]
        parent_parent_id = parentids[0]
        items = [item for item in self.dbitems if item[1]==parent_parent_id]
        itemids = [iid[0] for iid in items]
        row = itemids.index(parent_id)
        return row, items[row]

    def getRow(self, childitem):
        items = [item for item in self.dbitems if item[1]==self.getParentId(childitem)]
        return items.index(childitem)

    def resetData(self):
        """
        create temporary view alltitles as select id, typeid, title from requirements union select id, typeid, title from usecases union select id, typeid, title from folders
        create temporary view id_and_pid as select relatedid as "id", id as "parentid" from relations where id in (select id from folders) -- return id of all folders and their childs
        select id, parentid, title from id_and_pid inner join (select id as childid, title from alltitles) on id==childid
        """
        if nafdb.connection is not None:
            self.dbitems = nafdb.getTreeData(self.filterDict)

    def setFilter(self, tableName, whereClause):
        if len(whereClause) > 0:
            self.filterDict[tableName] = 'where ' + whereClause
        else:
            self.filterDict[tableName] = whereClause

    def addItem(self, item):
        self.dbitems.append(item)

    def changeParentId(self, item, parentId):
        item = list(item)
        item[1] = parentId
        return tuple(item)


class cTreeMimeData(QtCore.QMimeData):
    ownMimeString = ARTIFACT_MIME_TYPE

    def hasFormat(self, mimeString):
        return mimeString == self.ownMimeString

    def formats(self):
        return [self.ownMimeString]

    def setData(self, mimeString, data):
        self._data = data

    def retrieveData(self, mimeString, type_=QtCore.QVariant.UserType):
        if not self.hasFormat(mimeString):
            return QtCore.QVariant()
        else:
            return self._data


class cTreeModel(QtCore.QAbstractItemModel):
    """The model class for the project items tree view"""
    def __init__(self):
        QtCore.QAbstractItemModel.__init__(self)
        self.items = cTreeData()
        self.modelReset.connect(self.items.resetData)

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        if not parent.isValid():
            return self.items.childCount(0)
        else:
            return self.items.childCount(self.items.getItemId(parent.internalPointer()))

    def index(self, row, column, parent):
        "Returns the index of the item in the model specified by the given row, column and parent index."
        if not parent.isValid():
            # root element
            try:
                return self.createIndex(row, column, self.items.getItem(0, row))
            except:
                logging.error("row=%d" % (row, ))
                return QtCore.QModelIndex()
        else:
            parentItem = parent.internalPointer()
            childItem = self.items.getChild(parentItem, row)
            if childItem is None:
                return QtCore.QModelIndex()
            else:
                return self.createIndex(row, column, childItem)

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        childItem = index.internalPointer()
        parentId = self.items.getParentId(childItem)
        if  parentId== 0:
            return QtCore.QModelIndex()
        # get the row index of the parent
        row, item = self.items.getParentRow(parentId)
        return self.createIndex(row, 0, item)

    def data(self, index, role):
        ##logging.debug("cTreeModel.data(index=%s, role=%d, model=%s" % (hex(id(index)), role, index.model()))
        if not index.isValid():
            return QtCore.QVariant()
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            if self.items.getItemType(item) == TYPE_FOLDER:
                #t = "%s" % (self.items.getItemTitle(item),)
                t = "%s" % (self.items.getItemTitle(item), )
            else:
                t = "%d: %s" % (self.items.getItemId(item), self.items.getItemTitle(item))
            return QtCore.QVariant(t)
        elif role == Qt.ToolTipRole:
            return QtCore.QVariant("ID=%d: %s" % (self.items.getItemId(item), self.items.getItemTitle(item)))
        elif role == Qt.DecorationRole:
            return QtCore.QVariant(self.items.getItemDecoration(item))
        else:
            return QtCore.QVariant()

    def removeRow(self, row, parent):
        logging.debug("removeRow(row=%d, parent=%s)" % (row, parent.internalPointer()))
        return self._removeRows(row, 1, parent)

    def removeRows(self, row, count, parent):
        # removeRows() is used by drag and drop support to implement the move operation.
        # This kind of implementation is not suited for nafms database operation,
        # thus move operation is implemented entirely in dropMimeData()
        # and the removeRows() function is only a dummy here.
        # Instead _removeRows() does the job.
        return True

    def _removeRows(self, row, count, parent):
        logging.debug("_removeRows(row=%d, count=%d, parent=%s)" % (row, count, parent.internalPointer()))
        self.beginRemoveRows(parent, row, row+count-1)
        for i in range(count):
            item = self.items.getChild(parent.internalPointer(), row+i)
            typeid = self.items.getItemType(item)
            tableName = nafdb.getTableNameForTypeId(typeid)
            nafdb.deleteItem(tableName, self.items.getItemId(item))
            # TODO: encapsulate removal in cTreeData class
            self.items.dbitems.remove(item)
        self.endRemoveRows()
        return True

    def getParentFolder(self, index):
        if self.items.getItemType(index.internalPointer()) is TYPE_FOLDER:
            parentIndex = index.internalPointer()
        else:
            parentIndex = index.parent().internalPointer()
        return parentIndex

    def getItemType(self, index):
        if not index.isValid():
            return None
        return self.items.getItemType(index.internalPointer())

    def getItemId(self, index):
        if not index.isValid():
            return None
        return self.items.getItemId(index.internalPointer())

    def getParentId(self, index):
        if not index.isValid():
            return None
        return self.items.getParentId(index.internalPointer())

    def getRow(self, index):
        if not index.isValid():
            return None
        return self.items.getRow(index.internalPointer())

    def insertRow(self, row, parent):
        logging.debug("insertRow(row=%d, parent=%s)" % (row, parent.internalPointer()))
        return self.insertRows(row, 1, parent)

    def insertRows(self, row, count, parent):
        logging.debug("insertRows(row=%d, count=%d, parent=%s)" % (row, count, parent.internalPointer()))
        self.beginInsertRows(parent, row, row+count-1)
        self.endInsertRows()
        return True

    def mimeTypes(self):
        return QtCore.QStringList([cTreeMimeData.ownMimeString])

    def mimeData(self, indexes):
        data = indexes
        md = cTreeMimeData()
        md.setData(md.ownMimeString, data)
        return md

    def dropMimeData(self, data, action, row, column, parent):
        #print "dropMimeData", data.retrieveData(cTreeMimeData.ownMimeString)[0].internalPointer()
        #print  action, row, column, parent.internalPointer()
        dragItemIndex = data.retrieveData(cTreeMimeData.ownMimeString)[0] # only single selection is handled
        dragItemId = self.getItemId(dragItemIndex)
        dragItemParentId = self.getParentId(dragItemIndex)
        parentId = self.getItemId(parent)
        if action == QtCore.Qt.MoveAction:
            if dragItemParentId == parentId:
                # moving an item witout changing it's parent
                if row < 0:
                    # it's up to the application where to put the item
                    # so we leave it where it is.
                    return False
                childsOfParent = [item for item in self.items.dbitems if self.items.getParentId(item)==parentId]
                dragItem = dragItemIndex.internalPointer()
                if row < len(childsOfParent) and childsOfParent[row] == dragItem:
                    # do nothing if the item is dragged to where it already is
                    return False
                self.beginRemoveRows(self.parent(dragItemIndex), dragItemIndex.row(), dragItemIndex.row())
                self.items.dbitems.remove(dragItem)
                childsOfParent.remove(dragItem)
                self.endRemoveRows()
                if row >= len(childsOfParent):
                    self.beginInsertRows(parent, row-1, row-1)
                    actualrow = self.items.dbitems.index(childsOfParent[-1])+1
                else:
                    self.beginInsertRows(parent, row, row)
                    actualrow = self.items.dbitems.index(childsOfParent[row])
                self.items.dbitems.insert(actualrow, dragItem)
                childsOfParent.insert(row, dragItem)
                self.endInsertRows()
                nafdb.updateViewPos(childsOfParent)
                return True
            else:
                # moving an item to another parent"
                if row < 0:
                    # if dropped to folder then insert item at end
                    row = self.rowCount(parent)
                dragItem = dragItemIndex.internalPointer()
                dragItem = self.items.changeParentId(dragItem, parentId)

                childsOfParent = [item for item in self.items.dbitems if self.items.getParentId(item)==parentId]
                if len(childsOfParent) == 0:
                    self.beginInsertRows(parent, row, row)
                    actualrow = 0
                elif row >= len(childsOfParent):
                    self.beginInsertRows(parent, row-1, row-1)
                    actualrow = self.items.dbitems.index(childsOfParent[-1])+1
                else:
                    self.beginInsertRows(parent, row, row)
                    actualrow = self.items.dbitems.index(childsOfParent[row])
                self.items.dbitems.insert(actualrow, dragItem)
                childsOfParent.insert(row, dragItem)
                nafdb.changeParentId(dragItemId, dragItemParentId, parentId)
                nafdb.updateViewPos(childsOfParent)
                self.endInsertRows()

                self.beginRemoveRows(self.parent(dragItemIndex), dragItemIndex.row(), dragItemIndex.row())
                self.items.dbitems.remove(dragItemIndex.internalPointer())
                self.endRemoveRows()

                return True
        elif action == QtCore.Qt.CopyAction:
            # not supported, see supportedDropActions() why
            assert(False)
        else:
            assert(False)
        return False

    def addItem(self, tableName, itemTitle, index):
        if self.getItemType(index) == TYPE_FOLDER:
            parent = index
        else:
            parent = self.parent(index)
        n = self.rowCount(parent)
        parentId = self.getItemId(parent)
        newItem = nafdb.newItem(tableName, itemTitle, parentId)
        self.items.addItem(newItem)
        self.insertRow(n, parent)
        return self.index(n, 0, parent)

    def deleteItem(self, tableName, index):
        parent = self.parent(index)
        row = self.getRow(index)
        self.removeRow(row, parent)

    def copyItem(self, itemId, typeId, parentIndex, fileName):
        parentId = self.getItemId(parentIndex)
        n = self.rowCount(parentIndex)
        self.beginInsertRows(parentIndex, n, n)
        copyItem = nafdb.copyItem(itemId, typeId, parentId, fileName)
        self.items.addItem(copyItem)
        self.endInsertRows()
        return self.index(n, 0, parentIndex)

    def countItemsRelatedToIndex(self, index):
        return nafdb.countItemsRelatedToId(self.getItemId(index))

    def countItemsWhereIndexIsRelatedTo(self, index):
        return nafdb.countItemsWhereIdIsRelatedTo(self.getItemId(index))

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction  #| QtCore.Qt.CopyAction

    def flags(self, index):
        defaultFlags = super(cTreeModel, self).flags(index)
        if not index.isValid():
            return defaultFlags
            return QtCore.Qt.ItemIsDropEnabled | defaultFlags
        if self.getItemType(index) == TYPE_FOLDER:
            ##TODO: be careful when dragging/dropping folders; hint in README/CHANGELOG required
            return QtCore.Qt.ItemIsDropEnabled | defaultFlags | QtCore.Qt.ItemIsDragEnabled
        else:
            return QtCore.Qt.ItemIsDragEnabled | defaultFlags


class cTreeView(QtGui.QTreeView):
    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent, headerHidden=True)
        self.expandedItems = []
        self.setModel(cTreeModel())

        self.pyqtConfigure(dragEnabled=True, showDropIndicator=True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)

    def saveView(self):
        "Save expanded items"
        self.expandedItems = []
        index = self.model().index(0, 0, QtCore.QModelIndex()) # root index
        while index.isValid():
            if self.isExpanded(index):
                self.expandedItems.append(self.model().getItemId(index))
            index = self.indexBelow(index)

    def restoreView(self, selectedItemId=None):
        "Restore previously saved expanded items"
        index = self.model().index(0, 0, QtCore.QModelIndex()) # root index
        while index.isValid():
            itemid = self.model().getItemId(index)
            if  itemid in self.expandedItems:
                self.setExpanded(index, True)
            if itemid == selectedItemId:
                self.setCurrentIndex(index)
            index = self.indexBelow(index)
        self.expandedItems = []

    def getSelectedItemId(self):
        index = self.selectionModel().currentIndex()
        return self.model().getItemId(index)

    def getCurrentParent(self):
        index = self.selectionModel().currentIndex()
        if not index.isValid(): return None
        return self.model().getParentFolder(index)
