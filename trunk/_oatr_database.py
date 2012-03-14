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

import sqlite3
import os.path
import copy
import re
from PyQt4 import QtCore
import _naf_database as nafdb

LOOKUP_TABLES = {
    'statusLUT': ["pending", "failed", "passed", "skipped"],
    'priorityLUT': nafdb.lookupTables['priorityLUT']
}

STATUS_PENDING = 0
STATUS_FAILED = 1
STATUS_PASSED = 2
STATUS_SKIPPED = 3

# create testruns table class
columns = copy.deepcopy(nafdb.getTableForTypeId(nafdb.TYPE_TESTCASE).columns)
columns.insert(1,
    nafdb.cColumn(name='status', _type='integer', displayname='Status', default=STATUS_PENDING))
columns.append(
    nafdb.cColumn(name='user', _type='text', displayname='Tester'))
columns.append(
    nafdb.cColumn(name='date', _type='text', displayname='Date'))
columns.append(
    nafdb.cColumn(name='action', _type='text', displayname='Action'))
columns.append(
    nafdb.cColumn(name='remark', _type='text', displayname='Remark'))
TESTRUN_TABLE = nafdb.cTable(name='testruns', isFilterable=True, displayname="Test Runs", 
                             typeid=nafdb.TYPE_TESTRUN, columns=columns)

TESTRUNINFO_TABLE = nafdb.cTable(name='testruninfo', displayname="Test Run Information",
                                 isFilterable=True, typeid = -1, columns=(
                                 nafdb.cColumn(name='title', _type='text', displayname='Title'),
                                 nafdb.cColumn(name='description', _type='text', displayname='Description'),
                                 nafdb.cColumn(name='source', _type='text', displayname='Source'),
                                 ))
QtCore.QCoreApplication.translate('cColumn', 'Source')                                 

def getDisplayNameForColumn(table, name):
    return table[name].displayname

def getColumnNames(table):
    return [column.name for column in table.columns]

def _getCreateTableStatement(tableObj):
    command = 'create table %s (' % tableObj.name 
    keylist = []
    for column in tableObj.columns:
        if column.default is None:
            keylist.append('%s %s' % (column.name, column._type))
        else:
            keylist.append('%s %s default %s' % (column.name, column._type, str(column.default)))
    command = command + ','.join(keylist) + ');'
    return command

def createTestRunTables(dbObj):
    dbObj.exec_(_getCreateTableStatement(TESTRUN_TABLE))
    #
    testsuiteTable = nafdb.getTableForTypeId(nafdb.TYPE_TESTSUITE)
    dbObj.exec_(_getCreateTableStatement(testsuiteTable))
    #
    dbObj.exec_(_getCreateTableStatement(TESTRUNINFO_TABLE))
    #
    imagesTable = nafdb.getTableForTypeId(nafdb.TYPE_IMAGE)
    dbObj.exec_(_getCreateTableStatement(imagesTable))
    
    
class CursorProxy(object):
    def __init__(self, cursor):
        self.cursor = cursor
        
    def exec_(self, s):
        self.cursor.execute(s)
        
def createTestRunDatabase(srcDatabaseName, destDatabaseName, srcTestsuiteId, infoDict):
    """
    Create a database file for the test run. 
    srcDatabaseName is the filename of the database with the testsuite and testcases
    destDatabaseName is the filename of the database to be created
    srcTestsuiteId is the id of the testsuite in srcDatabaseName to be run 
    """
    # get the columns of testcases
    columnNames = nafdb.getColumnNames('testcases')
    columnNamesList = ','.join(columnNames)
    
    #createTestRunTables(destDatabaseName)
    conn = sqlite3.connect(destDatabaseName)
    cursor = conn.cursor()
    cursorProxy = CursorProxy(cursor)
    createTestRunTables(cursorProxy)
    cursor.execute("ATTACH DATABASE ? AS srcdb", (srcDatabaseName,))
    #--- create lookup tables for enumeration types
    for name, values in LOOKUP_TABLES.iteritems():
        cursor.execute("CREATE TABLE %s (key INTEGER, value TEXT);" % name)
        for value in values:
            cursor.execute("INSERT INTO %s VALUES (?, ?);" % name, (values.index(value), value))
    #--- populate artifact tables
    command = 'INSERT INTO testruns (%s) select * from srcdb.testcases where id in (select relatedid from relations where id=?)' % columnNamesList
    cursor.execute(command, (srcTestsuiteId,))
    # copy images referenced by any testcases from src into dest
    # --- first, identifiy table columns which may reference an image
    testcaseTable = nafdb.getTableForTypeId(nafdb.TYPE_TESTCASE)
    columns = [c.name for c in testcaseTable.columns if c.view == nafdb.VIEW_MULTI_LINE]
    # --- next, read all fields containing an img tag
    imageIds = set()
    pattern = re.compile(r'<img src="#(\d+)"')
    command = """select %s from testcases where %s like '%%<img src="%%'"""
    for c in columns:
        # iterate all fields which references an image and extract the image id's
        cursor.execute(command % (c, c))
        row = cursor.fetchone()
        if row is None: continue
        result = pattern.findall(row[0])
        map(imageIds.add , [int(r) for r in result])
    cursor.execute("INSERT INTO images SELECT * FROM srcdb.images WHERE id IN %s" %  str(tuple(imageIds)))
    # copy testsuite table from src to dest
    cursor.execute('INSERT INTO testsuites SELECT * FROM srcdb.testsuites WHERE id=?', (srcTestsuiteId,))
    # populate info table
    columnNames = getColumnNames(TESTRUNINFO_TABLE)
    columnNamesList = ','.join(columnNames)
    command = 'insert into testruninfo (%s) values (%s)' % (columnNamesList, ','.join(['?']*len(columnNames)))
    values = [infoDict[k] for k in columnNames]
    cursor.execute(command, values)
    # done everything, commit and close
    conn.commit()
    conn.close()
        
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    testFileName = 'tests/samplerun_out.db'
    if os.path.exists(testFileName):
        os.remove(testFileName)
    createTestRunDatabase('tests/samplerun_in.db', testFileName, 11, {'title': 'Info title', 'description': 'Info description'})

