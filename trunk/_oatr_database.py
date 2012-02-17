#!/usr/bin/python
# -*- coding: utf-8  -*-
# $Id$

import sqlite3
import _naf_database as nafdb

def createTestRunDatabase(srcDatabaseName, destDatabaseName, srcTestsuiteId):
    """
    Create a database file for the test run. 
    srcDatabaseName is the filename of the database with the testsuite and testcases
    destDatabaseName is the filename of the database to be created
    srcTestsuiteId is the id of the testsuite in srcDatabaseName to be run 
    """
    # get the columns of testcases
    testrunTable = nafdb.getTableForTypeId(nafdb.TYPE_TESTCASE)
    testrunTable.columns.append(
        nafdb.cColumn(name='status', _type='integer', displayname='Status'))
    testrunTable.columns.append(
        nafdb.cColumn(name='user', _type='text', displayname='Tester'))
    testrunTable.columns.append(
        nafdb.cColumn(name='date', _type='text', displayname='Date'))
    testrunTable.columns.append(
        nafdb.cColumn(name='action', _type='text', displayname='Action'))
    testrunTable.columns.append(
        nafdb.cColumn(name='remark', _type='text', displayname='Remark'))
    
    srcConn = sqlite3.connect(destDatabaseName)
    srcCursor = srcConn.cursor()
    #--- create artifact tables
    command = 'create table testrun (' 
    keylist = []
    for column in testrunTable.columns:
        if column.default is None:
            keylist.append('%s %s' % (column.name, column._type))
        else:
            keylist.append('%s %s default %s' % (column.name, column._type, str(column.default)))
    command = command + ','.join(keylist) + ');'
    srcCursor.execute(command)
    
        
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    createTestRunDatabase('', 'xxx.db', 0)
