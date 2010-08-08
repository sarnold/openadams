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

__revision__ = '$$'
__id__ = '$Id$'

import sys, getopt, os, logging, sqlite3
from PyQt4 import QtGui
import _naf_database as nafdb

class cArgs(object):
    def __init__(self):
        self.outputFileName = None
        self.databaseName1 = None
        self.databaseName2 = None


class cCommandLineProcessor(object):
    def __init__(self):
        self.args = cArgs()

    def version(self):
        print("Version " + __revision__)

    def usage(self):
        print("Usage:\n%s [-h|--help] [-V|--version] [-o <ofile>|--output=<ofile>] <file1> <file2>\n"
        "  -h, --help                    show help and exit\n"
        "  -V, --version                 show version and exit\n"
        "  -o <ofile>, --output=<ofile>  output to file <ofile>\n"
        "  <file1>                       first database file\n"
        "  <file2>                       second database file\n"
        % os.path.basename(sys.argv[0]))

    def parseOpts(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:V", ["help", "output=", "version"])
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
        for o, a in opts:
            if o in ("-V", "--version"):
                self.version()
                sys.exit()
            elif o in ("-h", "--help"):
                self.usage()
                sys.exit()
            elif o in ("-o", "--output"):
                self.args.outputFileName = a
            else:
                assert False, "unhandled option"
        if len(args) != 2:
            self.usage()
            sys.exit(1)
        if self.args.outputFileName is None:
            self.args.outputFileName =  "naf_diff.html"
        self.args.databaseName1 = args[0]
        self.args.databaseName2 = args[1]




class cReport(object):
    def __init__(self, args):
        self.args = args
        self.outputFile = open(args.outputFileName, "w")
        self.outputFile.write("""
            <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
            "http://www.w3.org/TR/html4/loose.dtd">
            <head>
            <style type="text/css">
            body {
                font-family: Verdana, Helvetica, Arial, sans-serif;
                font-size: 100.01%;
            }
            h1 {
                font-size:x-large;
                color: #4444FF;
                background: #EEEEEE;
            }
            td, th { 
                border-width:1pt;
                border-style:solid;
                padding-left:1em;
                padding-right: 1em;
                text-align:left;
                vertical-align:top;
            }
            table {
                border-collapse:collapse;
            }
            </style>
            <title>NAF Diff</title>
            </head>
            <body>
        """)
        
    def start(self, filename1, filename2):
        self.outputFile.write("""
        <h1>NAF Difference</h1>
        <dl>
        <dt>File 1</dt><dd>%s</dd>
        <dt>File 2</dt><dd>%s</dd>
        </dl>
        <table>
        <tr><th>ID</th><th>Column</th><th>File 1</th><th>File 2</th></tr>
        """ % (filename1, filename2))
        
    def nonMatchingVersions(self, v1, v2):
        self.outputFile.write("""
        <tr><td>Version mismatch</td><td>N/A</td>
        <td>%s</td><td>%s</td></tr>""" % (v1, v2))
         
    def differentTypes(self, id, typeid1, typeid2):
        table1 = nafdb.getTableForTypeId(typeid1)
        table2 = nafdb.getTableForTypeId(typeid2)
        self.outputFile.write("""
        <tr><td>%s</td><td>N/A</td>
        <td>%s</td><td>%s</td></tr>""" % (id, table1.displayname, table2.displayname))
        
    def missingItem(self, id, typeid1, typeid2):
        if typeid1 == None:
            s1 = 'missing item'
        else:
            s1 = nafdb.getTableForTypeId(typeid1).displayname
        if typeid2 == None:
            s2 = 'missing item'
        else:
            s2 = nafdb.getTableForTypeId(typeid2).displayname
        self.outputFile.write("""
        <tr><td>%s</td><td>N/A</td>
        <td>%s</td><td>%s</td></tr>""" % (id, s1, s2))
        
    def differentItem(self, id, columnname, item1, item2, printId=True):
        if printId:
            idStr = str(id)
        else:
            idStr = "&nbsp;"
        self.outputFile.write("""
        <tr><td>%s</td>
        <td>%s</td><td>%s</td><td>%s</td></tr>""" % (idStr, columnname, item1, item2))

    def __del__(self):
        self.outputFile.write("""
            </table>
            </body>
            </html>
        """)
        self.outputFile.close()


def getItemForId(connection, tableName, id, columnName):
    lookupTable = nafdb.getLookupTableName(tableName, columnName)
    d = {'lt': lookupTable, 'tn': tableName, 'cn':columnName}
    cursor = connection.cursor()
    if lookupTable is None:
        cursor.execute('select %(cn)s from %(tn)s where id=?' % d, (id,))
    else:
        cursor.execute('select %(lt)s.value from %(tn)s inner join %(lt)s on %(tn)s.%(cn)s=%(lt)s.key and %(tn)s.id=?;' % d, (id,))
    try:
        return cursor.fetchone()[0]
    except TypeError:
        logging.error('unknown type')
        return None

    
def run(args):
    report = cReport(args)
    report.start(args.databaseName1, args.databaseName2)
    connection1 = sqlite3.connect(args.databaseName1)
    connection2 = sqlite3.connect(args.databaseName2)
    cursor1 = connection1.cursor()
    cursor2 = connection2.cursor()
    version1 = cursor1.execute("select version from __info__;").fetchone()[0]
    version2 = cursor2.execute("select version from __info__;").fetchone()[0]
    if version1 != version2:
        report.nonMatchingVersions(version1, version2)
        sys.exit()
    
    command = []
    for tableName in nafdb.getTableNames():
        command.append('select id, typeid from %s' % (tableName, ))
    command = ' union '.join(command)
    command = 'create temporary view allids as ' + command + ';'
    cursor1.execute(command)
    cursor2.execute(command)
    
    # TODO: check if parents of two items have changed
    # TODO: check if viewpos of two items has changed
    # TODO: check if relations of two items has changed
    
    # look at all id present in first file 
    cursor1.execute("select * from allids;")
    for (id1, typeid1) in cursor1:
        try:
            (id2, typeid2) = cursor2.execute("select * from allids where id=?", (id1, )).fetchone()
            if typeid1 == nafdb.TYPE_ROOT and typeid2 == nafdb.TYPE_ROOT:
                pass
            elif typeid1 == typeid2:
                # same types, so compare all columns 
                logging.debug("same types (%d, %d), (%d, %d)" % (id1, typeid1, id2, typeid2))
                table = nafdb.getTableForTypeId(typeid1)
                columns = table.columns
                printId = True
                for column in columns:
                    item1 = getItemForId(connection1, table.name, id1, column.name)
                    item2 = getItemForId(connection2, table.name, id2, column.name)
                    if column._type == 'text':# and (item1.lstrip().startswith("<!DOCTYPE") or item2.lstrip().startswith("<!DOCTYPE")):
                        doc = QtGui.QTextDocument()
                        doc.setHtml(item1)
                        item1 = '<br/>'.join(unicode(doc.toPlainText()).splitlines(1))
                        doc.setHtml(item2)
                        item2 = '<br/>'.join(unicode(doc.toPlainText()).splitlines(1))
                    if item1 != item2:
                        report.differentItem(id1, column.displayname, item1, item2, printId)
                        printId = False
            else:
                # different types, nothing to compare, report only
                logging.debug("different types (%d, %d), (%d, %d)" % (id1, typeid1, id2, typeid2))
                report.differentTypes(id1, typeid1, typeid2)
        except TypeError:
            # id present in first file but not in second file
            logging.debug("item (%d, %d) not found in second file" % (id1, typeid1))
            report.missingItem(id1, typeid1, None)
            pass
            
    # finally we look for all id present in second file but not in first file
    cursor2.execute("select * from allids;")
    for (id2, typeid2) in cursor2:
        try:
            (id2, typeid2) = cursor1.execute("select * from allids where id=?", (id2, )).fetchone()
        except TypeError:
            # id present in second file but not in first file
            logging.debug("item (%d, %d) not found in first file" % (id2, typeid2))
            report.missingItem(id2, None, typeid2)
            pass
    
        
        
        
    connection1.close()
    connection2.close()
    
    
if __name__ == '__main__':
    
    logFormat = '%(module)s:%(lineno)s (%(funcName)s): %(message)s'
    ##level=logging.NOTSET
    level=logging.DEBUG
    ##level=logging.INFO,
    ##level=logging.ERROR,
    logging.basicConfig(format=logFormat, level=level,
                        ##, filemode='w', filename='myapp.log'
                        )
    clp = cCommandLineProcessor()
    clp.parseOpts()
    print clp.args.outputFileName
    run(clp.args)

        
