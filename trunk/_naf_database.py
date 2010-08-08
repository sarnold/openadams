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

import sqlite3, os, os.path, sys, logging, shutil, re

from PyQt4 import QtCore


TYPE_ROOT = 0
TYPE_FOLDER = 1
TYPE_REQUIREMENT = 2
TYPE_USECASE = 3
TYPE_IMAGE = 4
TYPE_FEATURE = 5
TYPE_TESTCASE = 6
TYPE_TESTSUITE = 7
TYPE_SIMPLESECTION = 8
TYPE_COMPONENT = 9
TYPE_CHANGE = 10

DEFAULT_VIEW_POS = sys.maxint
DATABASE_VERSION = (2,)

connection = None
currentFileName = None

class cTable(object):
    def __init__(self, name, isFilterable, displayname, typeid, columns):
        self.name = name
        self.displayname = QtCore.QCoreApplication.translate('cTable', displayname)
        self.columns = columns
        self.isFilterable = isFilterable
        self.typeid = typeid
        self.hash = {}
        for column in columns:
            self.hash[column.name] = column

    def __getitem__( self, key):
        return self.hash[key]


class cColumn(object):
    def __init__(self, name, _type, displayname, lookupTable=None, isFilterable=True, historyTable=None, default=None):
        self.name = name
        self._type = _type
        self.displayname = QtCore.QCoreApplication.translate('cColumn', displayname)
        self.lookupTable = lookupTable
        self.isFilterable = isFilterable
        self.default = default
        self.historyTable = historyTable


tables = [
    cTable(name='folders', isFilterable=False, displayname="Folders", typeid=TYPE_FOLDER, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS),
        ]),
    cTable(name='requirements', isFilterable=True, displayname="Requirements", typeid=TYPE_REQUIREMENT, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='priority', _type='integer', displayname='Priority', lookupTable='priorityLUT', default=0),
            cColumn(name='status', _type= 'integer', displayname='Status', lookupTable='statusLUT', default=0),
            cColumn(name='complexity', _type= 'integer', displayname='Complexity', lookupTable='complexityLUT', default=0),
            cColumn(name='assigned', _type= 'text', displayname='Assigned'),
            cColumn(name='effort', _type= 'integer', displayname='Effort', lookupTable='effortLUT', default=0),
            cColumn(name='category', _type= 'integer', displayname='Category', lookupTable='categoryLUT', default=0),
            cColumn(name='origin', _type= 'text', displayname='Origin', default="''"),
            cColumn(name='rationale', _type= 'text', displayname='Rationale', default="''"),
            cColumn(name='description', _type= 'text', displayname='Description', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='risk', _type='integer', displayname='Risk', lookupTable='riskLUT', default=0),
            cColumn(name='testability', _type= 'text', displayname='Testability', historyTable='testability_view', default="''"),
            cColumn(name='baseline', _type= 'text', displayname='Baseline', historyTable='baseline_view', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='usecases', isFilterable=True, displayname="Usecases", typeid=TYPE_USECASE, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='priority', _type='integer', displayname='Priority', lookupTable='priorityLUT', default=0),
            cColumn(name='usefrequency', _type='integer', displayname='Use frequency', lookupTable='usefrequencyLUT', default=0),
            cColumn(name='actors', _type='text', displayname='Actors', default="''"),
            cColumn(name='stakeholders', _type='text', displayname='Stakeholders', default="''"),
            cColumn(name='prerequisites', _type='text', displayname='Prerequisites', default="''"),
            cColumn(name='mainscenario', _type='text', displayname='Main scenario', default="''"),
            cColumn(name='altscenario', _type='text', displayname='Alt scenario', default="''"),
            cColumn(name='notes', _type='text', displayname='Notes', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='testsuites', isFilterable=True,displayname="Testsuites", typeid=TYPE_TESTSUITE, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='description', _type='text', displayname='Description', default="''"),
            cColumn(name='execorder', _type='text', displayname='Execution order', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='testcases', isFilterable=True, displayname="Testcases", typeid=TYPE_TESTCASE, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='purpose', _type='text', displayname='Purpose', default="''"),
            cColumn(name='prerequisite', _type='text', displayname='Prerequisite', default="''"),
            cColumn(name='testdata', _type='text', displayname='Test data', default="''"),
            cColumn(name='steps', _type='text', displayname='Steps', default="''"),
            cColumn(name='notes', _type='text', displayname='Notes', default="''"),
            cColumn(name='scripturl', _type='text', displayname='Script URL', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='priority', _type='integer', displayname='Priority', lookupTable='priorityLUT', default=0),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='simplesections', isFilterable=True, displayname="Text sections", typeid=TYPE_SIMPLESECTION, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='content', _type='text', displayname='Content', default="''"),
            cColumn(name='level', _type='integer', displayname='Level', default=0, isFilterable=False),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='features', isFilterable=True,displayname="Features", typeid=TYPE_FEATURE, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='priority', _type='integer', displayname='Priority', lookupTable='priorityLUT', default=0),
            cColumn(name='status', _type='integer', displayname='Status', lookupTable='statusLUT', default=0),
            cColumn(name='risk', _type='integer', displayname='Risk', lookupTable='riskLUT', default=0),
            cColumn(name='description', _type='text', displayname='Description', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
    ]),
    cTable(name='images', isFilterable=True, displayname="Images", typeid=TYPE_IMAGE, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='description', _type='text', displayname='Description', default="''"),
            cColumn(name='image', _type='blob', displayname='Image'),
            cColumn(name='source', _type='text', displayname='Image source', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='format', _type= 'text', displayname='Format', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='components', isFilterable=True, displayname="Components", typeid=TYPE_COMPONENT, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID', isFilterable=False),
            cColumn(name='typeid', _type='integer', displayname='Type ID'),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='description', _type='text', displayname='Description', default="''"),
            cColumn(name='keywords', _type= 'text', displayname='Keywords', historyTable='keywords_view', default="''"),
            cColumn(name='kind', _type= 'text', displayname='Kind', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
    cTable(name='changes', isFilterable=False, displayname="Changes", typeid=TYPE_CHANGE, columns=
        [
            cColumn(name='id', _type='integer primary key', displayname='ID'),
            cColumn(name='typeid', _type='integer', displayname='Type ID', isFilterable=False),
            cColumn(name='title', _type='text', displayname='Title', default="''"),
            cColumn(name='description', _type='text', displayname='Description', default="''"),
            cColumn(name='afid', _type='integer', displayname='Artefact ID'),
            cColumn(name='changetype', _type='integer', displayname='Change type'),
            cColumn(name='date', _type='text', displayname='Date', default="''"),
            cColumn(name='user', _type='text', displayname='User', default="''"),
            cColumn(name='viewpos', _type='integer', displayname='View pos', default=DEFAULT_VIEW_POS, isFilterable=False),
        ]),
]

lookupTables = {
    'priorityLUT':     ["Essential", "Expected", "Desired", "Optional"],
    'statusLUT':       ["Submitted", "Approved", "Completed", "In discussion", "Rejected"],
    'effortLUT':       ["Months", "Weeks", "Days", "Hours"],
    'complexityLUT':   ["Low", "Medium", "High"],
    'riskLUT':         ["Dangerous", "Medium", "Safe"],
    'changetypeLUT':   ["created", "edited", "deleted", "restored"],
    'usefrequencyLUT': ["Always", "Often", "Sometimes", "Rarely", "Once"],
    'categoryLUT':     ["Functional", "Reliability", "Up-time", "Safety",
                        "Security", "Performance", "Scalability", "Maintainability",
                        "Upgradability", "Supportability", "Operability",
                        "Business life-cycle", "System hardware", "System software",
                        "API", "Data import/export", "Other"],
}

def __identity(item): 
    return item

def getItemForId(tableName, id, columnName, translatorFunc=__identity):
    lookupTable = getLookupTableName(tableName, columnName)
    d = {'lt': lookupTable, 'tn': tableName, 'cn':columnName}
    cursor = connection.cursor()
    if lookupTable is None:
        translatorFunc=__identity
        cursor.execute('select %(cn)s from %(tn)s where id=?' % d, (id,))
    else:
        cursor.execute('select %(lt)s.value from %(tn)s inner join %(lt)s on %(tn)s.%(cn)s=%(lt)s.key and %(tn)s.id=?;' % d, (id,))
    try:
        return translatorFunc(cursor.fetchone()[0])
    except TypeError:
        logging.error('unknown type, tableName=%s, id=%s, columnName=%s' % (tableName, id, columnName))
        return None
        
def getRawItemForId(tableName, id, columnName):
    "Same as getItemForId but lookup tables are ignored"
    d = {'tn': tableName, 'cn':columnName}
    cursor = connection.cursor()
    cursor.execute('select %(cn)s from %(tn)s where id=?' % d, (id,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        logging.error('unknown type')
        return None

def saveItemForId(tableName, id, columnName, item):
    cursor = connection.cursor()
    cursor.execute("update %s set %s=? where id=?" % (tableName, columnName), (item, id))
    connection.commit()

def getItemForIdAndParentId(tableName, id, parentId, columnName):
    lookupTable = getLookupTableName(tableName, columnName)
    d = {'lt': lookupTable, 'tn': tableName, 'cn':columnName}
    cursor = connection.cursor()
    if lookupTable is None:
        cursor.execute('select %(cn)s from %(tn)s where id=? and id in (select relatedid from relations where id==?);' % d, (id, parentId))
    else:
        cursor.execute('select %(lt)s.value from %(tn)s inner join %(lt)s on %(tn)s.%(cn)s=%(lt)s.key and %(tn)s.id=? and %(tn)s.id in (select relatedid from relations where id=?);' % d, (id,parentId))
    return cursor.fetchone()[0]

def getImageForId(id):
    return getItemForId('images', id, 'image')

def getTableNames():
    return [table.name for table in tables]

def getFilterableTableNames():
    tableNames = [table.name for table in tables if table.isFilterable]
    tableDisplayNames = [table.displayname for table in tables if table.isFilterable]
    return (tableNames, tableDisplayNames)

def getHeaderDataForColumns(tableName, columnNames):
    i = getTableNames().index(tableName)
    columns = tables[i].columns
    headerDict = dict(zip([column.name for column in columns], [column.displayname for column in columns]))
    headerData = [headerDict[columnName] for columnName in columnNames]
    return headerData

def getTableDisplayName(tableName):
    i = getTableNames().index(tableName)
    return tables[i].displayname

def getTableNameForTypeId(typeid):
    tableNames = [table.name for table in tables if table.typeid == typeid]
    return tableNames[0]

def getTableForTypeId(typeid):
    table = [table for table in tables if table.typeid == typeid]
    return table[0]

def getColumnNames(tableName):
    i = getTableNames().index(tableName)
    columns = tables[i].columns
    return [column.name for column in columns]

def getColumns(tableName):
    i = getTableNames().index(tableName)
    columns = tables[i].columns
    return columns

def getColumnDisplayName(tableName, columnName):
    i = getTableNames().index(tableName)
    columns = tables[i].columns
    column = [column for column in columns if column.name == columnName][0]
    return column.displayname

def getTextColumnNames(tableName):
    i = getTableNames().index(tableName)
    columns = tables[i].columns
    columnNames = [column.name for column in columns if column._type=="text"]
    columnDisplayNames = [column.displayname for column in columns if column._type=="text"]
    return (columnNames, columnDisplayNames)

def getFilterableIntegerColumnNames(tableName):
    i = getTableNames().index(tableName)
    columns = tables[i].columns
    columnNames = [column.name for column in columns if column._type.find("integer") != -1 and column.isFilterable]
    columnDisplayNames = [column.displayname for column in columns if column._type.find("integer") != -1 and column.isFilterable]
    return (columnNames, columnDisplayNames)

def getLookupTableName(tableName, columnName):
    i = getTableNames().index(tableName)
    column = tables[i][columnName]
    return column.lookupTable

def getLookupTableRows(lutTableName, limit=-1, translatorFunc=__identity):
    if connection is None:
        return []
    cursor = connection.cursor()
    cursor.execute('select value from %s limit %d;' % (lutTableName, limit))
    return [translatorFunc(item[0]) for item in cursor.fetchall() if item[0] is not None]

def getHistoryTableRows(historyTableName):
    return getLookupTableRows(historyTableName, limit=50)

def _regexp(expr, s):
    b = None != re.compile(expr).search(s)
    return b

def openDatabase(filename):
    global connection
    global currentFileName
    if connection is not None:
        connection.close()
        currentFileName = None
    rawfilename = os.path.realpath(filename)
    filename = os.path.realpath(filename.encode('utf-8'))
    connection = sqlite3.connect(filename)
    version = connection.cursor().execute("select version from __info__;").fetchone()
    if version != DATABASE_VERSION:
        raise ValueError("Invalid database version: %s" % str(version))
    currentFileName = filename
    #TODO: As long we have stability issues, i.e. with drag and drop, we make
    #      a backup of the input file
    try:
        shutil.copyfile(rawfilename, rawfilename+'~')
    except IOError:
        logging.error('Unable to create backup file for %s' % filename)
    connection.create_function("regexp", 2, _regexp)

def newItem(tableName, itemTitle, parentId):
    logging.debug("tableName=%s, itemTitle=%s, parentId=%d" % (tableName, itemTitle, parentId))
    tableObj = tables[getTableNames().index(tableName)]
    cursor = connection.cursor()
    itemId = cursor.execute("select cnt from counter").fetchone()[0]
    cursor.execute("insert into %s (id, typeid, title) values(?, ?, ?)" % tableName, (itemId, tableObj.typeid, itemTitle))
    cursor.execute("insert into relations values (?, ?)", (parentId, itemId))
    connection.commit()
    return (itemId, parentId, tableObj.typeid, itemTitle)

def deleteItem(tableName, itemId):
    cursor = connection.cursor()
    cursor.execute("delete from %s where id=?" % tableName, (itemId, ))
    cursor.execute("delete from relations where id=?", (itemId, ))
    cursor.execute("delete from relations where relatedid=?", (itemId, ))
    connection.commit()

def copyItem(srcId, typeId, parentId, fileName):
    logging.debug("srcId=%d, typeId=%d, parentId=%d" , (srcId, typeId, parentId))
    if fileName == currentFileName:
        srccursor = connection.cursor()
    else:
        srccursor = sqlite3.connect(fileName).cursor()
    tableName = getTableNameForTypeId(typeId)
    columnNames = getColumnNames(tableName)
    columnNames.remove('id')
    destcursor = connection.cursor()
    newId = destcursor.execute("select cnt from counter").fetchone()[0]
    srccursor.execute("select %s from %s where id=%d" % (','.join(columnNames), tableName, srcId))
    destcursor.execute("insert into %s values (?,%s)" % (tableName, ','.join(len(columnNames)*'?')), (newId,)+srccursor.fetchone())
    destcursor.execute("update %s set viewpos=? where id=?" % tableName, (sys.maxint, newId))
    destcursor.execute("insert into relations values (?, ?)", (parentId, newId))
    connection.commit()
    destcursor.execute("select title from %s where id=?" % tableName, (newId,))
    return (newId, parentId, typeId, destcursor.fetchone()[0])

def countItemsRelatedToId(itemId):
    cursor = connection.cursor()
    cursor.execute("select count(*) from relations where id=?", (itemId,))
    return cursor.fetchone()[0]

def countItemsWhereIdIsRelatedTo(itemId):
    cursor = connection.cursor()
    cursor.execute("select count(*) from relations where relatedid=?", (itemId,))
    return cursor.fetchone()[0]

def changeParentId(itemId, fromParentId, toParentId):
    cursor = connection.cursor()
    cursor.execute("update relations set id=? where id=? and relatedid=?;", (toParentId, fromParentId, itemId))
    connection.commit()

def updateViewPos(itemlist):
    # If order of items in a folder is changed via drag and drop (see _naf_tree.py) the new order
    # has to be saved in database
    # Parameter itemlist is list of item tuples with (id, parentid, typeid, title)
    # All items belong to the same parent
    # the viewpos of all items has to be updated according to the item position in the list
    cursor = connection.cursor()
    for i, item in zip(range(len(itemlist)), itemlist):
        tableName = getTableNameForTypeId(item[2])
        cursor.execute("update %s set viewpos=? where id=?;" % tableName, (i, item[0]))
    connection.commit()


def getTreeData(filterDict):
    cursor = connection.cursor()
    fields = {'fields' : 'id, typeid, title'}
    command = []
    for tableName in getTableNames():
        command.append('select id, typeid, title, viewpos from %s %s ' % (tableName, filterDict[tableName]))
    command = ' union '.join(command)
    command = 'create temporary view alltitles as ' + command + ';'
    cursor.execute(command)
    cursor.execute('create temporary view id_and_pid as select relatedid as "id", id as "parentid" from relations where id in (select id from folders)')
    cursor.execute('select id, parentid, typeid, title from id_and_pid inner join (select id as childid, typeid, title from alltitles order by viewpos) on id==childid')
    dbitems = cursor.fetchall()
    cursor.execute('drop view alltitles;');
    cursor.execute('drop view id_and_pid;');
    return dbitems


def createEmptyDatabase(filename, overwriteExisting=True):
    if os.path.exists(filename) and overwriteExisting:
        os.remove(filename)
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    #--- create artifact tables
    for table in tables:
        command = 'create table %s (' % table.name
        keylist = []
        for column in table.columns:
            if column.default is None:
                keylist.append('%s %s' % (column.name, column._type))
            else:
                keylist.append('%s %s default %s' % (column.name, column._type, str(column.default)))
        command = command + ','.join(keylist) + ');'
        cursor.execute(command)
        command = 'create trigger %s_autoincr before insert on %s begin update counter set cnt = cnt+1; end;' % (table.name, table.name)
        cursor.execute(command)

    #--- create unique id counter table
    cursor.execute("create table counter (cnt integer);")
    cursor.execute("insert into counter values (0);")

    #--- create lookup tables for enumeration types
    for name, values in lookupTables.iteritems():
        cursor.execute("create table %s (key integer, value text);" % name)
        for value in values:
            cursor.execute("insert into %s values (?, ?);" % name, (values.index(value), value))

    #--- create lookup views for keywords, stakeholders and so on
    keywordsTableList = []
    for table in tables:
        for column in table.columns:
            if column.name=='keywords' and column.historyTable=='keywords_view':
                keywordsTableList.append('select distinct keywords as value from %s' % table.name)
    cmd = "create view keywords_view as " + ' union '.join(keywordsTableList)
    cursor.execute(cmd)
    cursor.execute("create view actors_view as select distinct actors as value from usecases")
    cursor.execute("create view stakeholders_view as select distinct stakeholders as value from usecases")
    cursor.execute("create view assigned_view as select distinct assigned as value from requirements")
    cursor.execute("create view origin_view as select distinct origin as value from requirements")
    cursor.execute("create view source_view as select distinct source as value from images")
    cursor.execute("create view kind_view as select distinct kind as value from components")
    cursor.execute("create view testability_view as select distinct testability as value from requirements")
    cursor.execute("create view baseline_view as select distinct baseline as value from requirements")
    
    #--- create relations
    cursor.execute("create table relations (id integer, relatedid integer);")

    #--- create internal info table
    cursor.execute("create table __info__ (version);")
    cursor.execute("insert into __info__ (version) values (?)", DATABASE_VERSION)

    # TODO: add trigger and tables for wastebasket feature

    conn.commit()
    conn.close()

def createDefaultDatabase(filename):
    folders = [
        {'name': "Project",                   'parentid': 0}, # id 1
        {'name': "100 System Requirements",   'parentid': 1}, # id 2
        {'name': "200 System Architecture",   'parentid': 1}, # id 3
        {'name': "300 Software Requirements", 'parentid': 1}, # id 4
        {'name': "310 Functional",            'parentid': 4}, # id 5
        {'name': "320 Non Functional",        'parentid': 4}, # id 6
        {'name': "400 Software Architecture", 'parentid': 1}, # id 7
        {'name': "500 Software Design",       'parentid': 1}, # id 8
        {'name': "600 Software Tests",        'parentid': 1}, # id 9
        {'name': "700 System Tests",          'parentid': 1}, # id 10
    ]
    filename = filename.encode('utf-8')
    createEmptyDatabase(filename)
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    cursor.execute("insert into folders values((select cnt from counter), ?, ?, ?)", (TYPE_ROOT, "ROOT", 0))
    foldernames = [folder['name'] for folder in folders]
    types = [TYPE_FOLDER] * len(foldernames)
    parentids = [folder['parentid'] for folder in folders]
    viewpos = range(len(folders))
    cursor.executemany("insert into folders values((select cnt from counter), ?, ?, ?)", zip(types, foldernames, viewpos))
    cursor.executemany("insert into relations values (?, (select id from folders where title=?))", zip(parentids, foldernames))
    conn.commit()
    conn.close()

class cStatistics(object):
    def __init__(self):
        self.itemcount = {}
        self.features_wo_requirements = []

    def __str__(self):
        import pprint
        return "itemcount=%s\nfeatures_wo_requirements=%s\n" % \
                (pprint.pformat(self.itemcount),
                 pprint.pformat(self.features_wo_requirements))


def getStatistics():
    statistics = cStatistics()
    cursor = connection.cursor()
    itemcount = {}
    for table in tables:
        cursor.execute("select count(*) from %s" % table.name)
        itemcount[table.name] = cursor.fetchone()[0]
    statistics.itemcount = itemcount
    # features without requirements
    cursor.execute("select id, title from features where id not in (select id from relations where relatedid in (select id from requirements));")
    statistics.features_wo_requirements = cursor.fetchall()
    # features without usecases
    cursor.execute("select id, title from features where id not in (select id from relations where relatedid in (select id from usecases));")
    statistics.features_wo_usecases = cursor.fetchall()
    # requirements without testcases
    cursor.execute("select id, title from requirements where id not in (select id from relations where relatedid in (select id from testcases));")
    statistics.requirements_wo_testcases = cursor.fetchall()
    # requirements without features
    cursor.execute("select id, title from requirements where id not in (select relatedid from relations where id in (select id from features));")
    statistics.requirements_wo_features = cursor.fetchall()
    # requirements without components
    cursor.execute("select id, title from requirements where id not in (select relatedid from relations where id in (select id from components));")
    statistics.requirements_wo_components = cursor.fetchall()
    # requirements without usecases
    cursor.execute("select id, title from requirements where id not in (select id from relations where relatedid in (select id from usecases));")
    statistics.requirements_wo_usecases = cursor.fetchall()
    # usecases without features or requirements
    cursor.execute("select id, title from usecases where id not in (select relatedid from relations where id in (select id from features union select id from requirements));")
    statistics.usecases_wo_requirements_or_features = cursor.fetchall()
    # components without requirements
    cursor.execute("select id, title from components where id not in (select id from relations where relatedid in (select id from requirements));")
    statistics.components_wo_requirements = cursor.fetchall()
    # testsuites without testcases
    cursor.execute("select id, title from testsuites where id not in (select id from relations where relatedid in (select id from testcases));")
    statistics.testsuites_wo_testcases = cursor.fetchall()
    # testcases without testsuites
    cursor.execute("select id, title from testcases where id not in (select relatedid from relations where id in (select id from testsuites));")
    statistics.testcases_wo_testsuites = cursor.fetchall()
    return statistics
