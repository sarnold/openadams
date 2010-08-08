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

__revision__ = '$Rev$'
__id__ = '$Id$'


import os, sys, getopt, sqlite3, datetime, codecs, base64, logging, traceback
import xml.dom.minidom
from xml.dom.minidom import getDOMImplementation, XMLNS_NAMESPACE, parse, parse
import re, traceback

import _naf_database as nafdb


class cArgs(object):
    def __init__(self):
        self.inputFileName = None
        self.databaseName = None


class cCommandLineProcessor(object):
    def __init__(self):
        self.args = cArgs()

    def version(self):
        print("Version " + __revision__)

    def usage(self):
        print("Usage:\n%s [-h|--help] [-V|--version] [-o <ofile>|--output=<ofile>] <ifile>\n"
        "  -h, --help                             show help and exit\n"
        "  -V, --version                          show version and exit\n"
        "  -o <ofile>, --output=<ofile>           output to database file <ofile>\n"
        "  <ifile>                                Xml input file"
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
                self.args.databaseName = a
            else:
                assert False, "unhandled option"
        if len(args) != 1:
            self.usage()
            sys.exit(1)
        if self.args.databaseName is None:
            self.args.databaseName =  os.path.splitext(args[0])[0] + ".db"
        self.args.inputFileName = args[0]


class cImportException(Exception):
    pass

nodename = {
xml.dom.minidom.Node.ELEMENT_NODE                 :"ELEMENT_NODE",
xml.dom.minidom.Node.ATTRIBUTE_NODE               :"ATTRIBUTE_NODE",
xml.dom.minidom.Node.TEXT_NODE                    :"TEXT_NODE",
xml.dom.minidom.Node.CDATA_SECTION_NODE           :"CDATA_SECTION_NODE",
xml.dom.minidom.Node.ENTITY_NODE                  :"ENTITY_NODE",
xml.dom.minidom.Node.PROCESSING_INSTRUCTION_NODE  :"PROCESSING_INSTRUCTION_NODE",
xml.dom.minidom.Node.COMMENT_NODE                 :"COMMENT_NODE",
xml.dom.minidom.Node.DOCUMENT_NODE                :"DOCUMENT_NODE",
xml.dom.minidom.Node.DOCUMENT_TYPE_NODE           :"DOCUMENT_TYPE_NODE",
xml.dom.minidom.Node.NOTATION_NODE                :"NOTATION_NODE"
}

class cImportPlainXml(object):
    def __init__(self, args):
        self.encoding = 'UTF-8'
        self.args = args
        self.maxId = -1

    def _nop(self, x):
        return x

    def b64decode(self, data):
        return buffer(base64.b64decode(data))

    def importXmlSection(self, tableName):
        logging.debug(tableName)
        maxId = -1
        columns = nafdb.getColumns(tableName)
        conversions = []
        keys = []
        placeholders = []
        for column in columns:
            keys.append(column.name)
            placeholders.append('?')
            if column._type.startswith('text'):
                conversions.append(unicode)
            elif column._type.startswith('integer'):
                conversions.append(int)
            elif column._type.startswith('blob'):
                conversions.append(self.b64decode)
            else:
                conversions.append(self._nop)
        table = self.dom.getElementsByTagName(tableName)[0]
        items = table.getElementsByTagName('item')
        for item in items:
            values = []
            for key in keys:
                child = item.getElementsByTagName(key)[0].firstChild
                if child is None:
                    value == ''
                elif xml.dom.minidom.Node.TEXT_NODE == child.nodeType:
                    value = child.data.strip()
                else:
                    logging.error(nodename[child.nodeType])
                    value = ''
                values.append(value)
                if key == 'id':
                    self.maxId = max(self.maxId, int(value))
            values = tuple(f(x) for f, x in zip(conversions,  values))
            nafdb.connection.execute("insert into %s values (%s);" % (tableName, ','.join(placeholders)), values)
        nafdb.connection.commit()

    def run(self):
        self.dom = parse(self.args.inputFileName)
        version = self.dom.documentElement.getAttribute('dbversion')
        version = int(version)
        if version != nafdb.DATABASE_VERSION[0]:
            raise cImportException('Database version %d in Xml file does not match required version %d' % (version, nafdb.DATABASE_VERSION[0]))
        if os.path.exists(self.args.databaseName):
            raise cImportException('database already exists: %s' % self.args.databaseName)
        nafdb.createEmptyDatabase(self.args.databaseName)
        nafdb.openDatabase(self.args.databaseName)
        map(self.importXmlSection, nafdb.getTableNames())

        #-- relations
        relations = self.dom.getElementsByTagName('relations')[0]
        items = relations.getElementsByTagName('item')
        values = []
        for item in items:
            value = (int(item.getElementsByTagName('id')[0].firstChild.data.strip()), int(item.getElementsByTagName('relatedid')[0].firstChild.data.strip()))
            values.append(value)
        nafdb.connection.executemany("insert into relations values (?, ?);", values)

        # Update counter table
        nafdb.connection.execute("update counter set cnt=?", (self.maxId+1,))

        nafdb.connection.commit()


def run(args):
    cImportPlainXml(args).run()


if __name__ == '__main__':

    logFormat = '%(module)s:%(lineno)s (%(funcName)s): %(message)s'
    level=logging.NOTSET
    ##level=logging.DEBUG
    ##level=logging.INFO,
    ##level=logging.ERROR,
    logging.basicConfig(format=logFormat, level=level,
                        ##, filemode='w', filename='myapp.log'
                        )
    clp = cCommandLineProcessor()
    clp.parseOpts()
    run(clp.args)
