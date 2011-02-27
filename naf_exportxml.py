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
from xml.dom.minidom import getDOMImplementation, XMLNS_NAMESPACE, parseString, parse
from xml.parsers.expat import ExpatError 
import re, traceback

import _naf_database as nafdb

DEFAULT_XSL_FILE = 'oareport.xsl'

BROKEN_IMAGE_DATA = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdB"\
"TUEAAK/INwWK6QAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAANrSURBVHjaYqyq"\
"qjrt4eFhzMDA8B8IQAQDIyMjAwwgs0GAiYmJgY2NjfHAgQPfW1paCgACiGHHjh0//uMBf//+/f/33z84"\
"++evX2D25UuX/svLyx8CCCAWoNQ/kMkg4vubNwxf7t9j4NPRZWBkYWb4/f0HAxMbG8NfoNyrK1cYuKWl"\
"GTj5+Bj+//vHADQU7FqAAGL59+cP2GnfXjxneDWjjeHnlbMMb+2CGeQy8hjYeXkZfgDl786bx/DvwAGG"\
"Nzo6DJIxMQw8cnIMQNeA/QwQQExAX4MNeDm1iUGI4yuDZt9iBvZLpxlutjQyvP/4keFGaysD99mzDMZA"\
"Wp6FheEW0LCfQNuBgQN2AUAAMf3/BzGAy9ab4eO9Jwy/j+1nUE4uZBC8d4fhoqMDg/D9+wxqiYkMv06d"\
"YngCZPOamDAwAdX/+f0bbABAALGA/AICQm4+DK84uBnuTGlkUNCzZFB092WQkFFk4NLSYviyZzfD+StX"\
"GdhTUxlUrK0Z/v/8CdYMAgABxAJmAPGfr18ZxO0cGb58+sZwoyKVQU3PgoFNVo3h+/ZtDOcvXWL419HB"\
"oOniwvD12TOGf8Cw+Qe1GCCAwAaAzeLhYXh9/SbDvxX9DPy/njM8276e4ecHBgZ2oLiUqCjDi/XrGR7I"\
"yzOIKSiA1f+HxgJAADH9gwbIhxNHGX7URzBI3N7LwMvGwPCFgZ3hoZIywxdmZgZ+YOCpA13xvbOT4RmQ"\
"ZmBlZfgH9QJAADGBkgEonr9sWcUg+vwCAxcPA8PrdwwMn+LTGZSBUfctI4Ph+ZcvDHzA9KD08CHDi927"\
"GX5BNYNcABBALMBEBg5V3vgchlfvHjD8ObyD4WNyAYNySS0DDxc7A09VFcNjISGG6ytWMHwwM2OQ8PNj"\
"YAGmAVA6AAGAAAKHwT9glLBLSjH8L53C8CnwJoOcvj4D299fDF9ffmBgATpXJj6e4YWREYOwhASDgIgI"\
"w58fP2AJiQEggFiYmZkZQYo4gFHDKS3OIKggy/D32zeGv79+MrBwc4NDmw2YgVSsrBj+AtX8/v6dgZOL"\
"i4GTkxOU0ZgAAojl3Llz3y0sLDh+A10BcxYsimBxjcwH4V9AtZcvX2b4/PnzL4AAYuTm5k6UkpJKA8qz"\
"/odmLOSsDDMEWQyIWV6/fv31/fv3kwACDABG7KuTJezUdwAAAABJRU5ErkJggg=="


class cArgs(object):
    def __init__(self, stylesheet=''):
        self.stylesheet = stylesheet
        self.outputFileName = None
        self.plainFormat = False
        self.databaseName = None


class cCommandLineProcessor(object):
    def __init__(self, stylesheet=''):
        self.args = cArgs(stylesheet)

    def version(self):
        print("Version " + __revision__)

    def usage(self):
        print("Usage:\n%s [-h|--help] [-V|--version] [-s <xslfile>|--stylesheet=<xslfile>] [-o <ofile>|--output=<ofile>] <ifile>\n"
        "  -h, --help                             show help and exit\n"
        "  -V, --version                          show version and exit\n"
        "  -s <xslfile>, --stylesheet=<xslfile>   include xsl stylesheet\n"
        "  -o <ofile>, --output=<ofile>           output to file <ofile>\n"
        "  -p, --plain                            plain output format\n"
        "  <ifile>                                database file"
        % os.path.basename(sys.argv[0]))

    def parseOpts(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:s:Vp", ["help", "output=", "stylesheet=", "version", "plain"])
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
            elif o in ("-s", "--stylesheet"):
                self.args.stylesheet = a
            elif o in ("-p", "--plain"):
                self.args.plainFormat = True
            else:
                assert False, "unhandled option"
        if len(args) != 1:
            self.usage()
            sys.exit(1)
        if self.args.outputFileName is None:
            self.args.outputFileName =  os.path.splitext(args[0])[0] + ".xml"
        self.args.databaseName = args[0]


class cExportBaseXml(object):
    def __init__(self, args):
        self.encoding = 'UTF-8'
        self.args = args
        self.getItemForId = nafdb.getRawItemForId

    def setupXmlDoc(self):
        self.impl = getDOMImplementation()
        self.xmldoc = self.impl.createDocument(None, "artefacts", None)
        self.root = self.xmldoc.documentElement
        self.root.setAttribute('source', self.args.databaseName)
        self.root.setAttribute('creationdate', datetime.datetime.now().isoformat())
        if len(self.args.stylesheet) > 0:
            stylesheet = self.xmldoc.createProcessingInstruction('xml-stylesheet', 'type="text/xsl" href="%s"' % self.args.stylesheet)
            self.xmldoc.insertBefore(stylesheet, self.root)

    def writeXmlDoc(self, pretty=True):
        f = codecs.open(self.args.outputFileName, encoding='UTF-8', mode="w", errors='strict')
        if pretty:
            self.xmldoc.writexml(f, indent='', addindent=' '*2, newl='\n', encoding=self.encoding)
        else:
            self.xmldoc.writexml(f, encoding=self.encoding)
        f.close()

    def _createElement(self, elementname, attribute={}):
        node = self.xmldoc.createElement(elementname)
        for name, value in attribute.iteritems():
            node.setAttribute(name, value)
        return node

    def _createTextElement(self, tagName, text, attribute={}):
        node = self.xmldoc.createElement(tagName)
        for name, value in attribute.iteritems():
            node.setAttribute(name, value)
        node.appendChild(self.xmldoc.createTextNode(text))
        return node

    def writeDatabaseVersion(self):
        cursor = nafdb.connection.cursor()
        cursor.execute("select version from __info__")
        self.root.setAttribute("dbversion", str(cursor.fetchone()[0]))


class cExportPlainXml(cExportBaseXml):
    "Plain XML export, all tables as they are"

    htmlBodyRegexp = re.compile(r'.*<body[^>]*>(.*)</body>',  re.DOTALL)
    imgIdRegexp = re.compile(r'#(\d+)')

    def run(self):
        self.setupXmlDoc()
        nafdb.openDatabase(self.args.databaseName)
        self.writeDatabaseVersion()
        for table in nafdb.tables:
            self.exportTable(table)
        for name, _ in nafdb.lookupTables.iteritems():
            self.exportSimpleTable(name, ['key', 'value'])
        self.exportSimpleTable('relations', ['id', 'relatedid'])
        self.writeXmlDoc(pretty=False)

    def exportSimpleTable(self, tableName, columnNames):
        cursor = nafdb.connection.cursor()
        cursor.execute("select * from %s" % tableName)
        tableNode = self._createElement(tableName)
        while True:
            itemNode = self._createElement('item')
            data = cursor.fetchone()
            if data is None:
                break
            for i in range(len(columnNames)):
                itemNode.appendChild(self._createTextElement(columnNames[i], unicode(data[i])))
            tableNode.appendChild(itemNode)
        self.root.appendChild(tableNode)

    def renderItem(self, table, itemid, nodeName='item'):
        itemNode = self._createElement(nodeName)
        for column in table.columns:
            data = self.getItemForId(table.name, itemid, column.name)
            if column._type == 'blob':
                data = base64.b64encode(data)
            else:
                data = unicode(data)
            node = self._createTextElement(column.name, data)
            itemNode.appendChild(node)
        return itemNode

    def exportTable(self, table):
        tableNode = self._createElement(table.name)
        cursor = nafdb.connection.cursor()
        cursor.execute("select id from %s" % table.name)
        idList = cursor.fetchall()
        for id in idList:
            tableNode.appendChild(self.renderItem(table, id[0]))
        self.root.appendChild(tableNode)


class cExportPrettyXml(cExportPlainXml):
    "Pretty XML export, basis for Html reports"
    def __init__(self, args):
        super(cExportPrettyXml, self).__init__(args)
        self.getItemForId = nafdb.getItemForId

    def run(self):
        self.setupXmlDoc()
        nafdb.openDatabase(self.args.databaseName)
        self.writeDatabaseVersion()
        self.cursor = nafdb.connection.cursor()
        command = []
        for tableName in nafdb.getTableNames():
            command.append('select id, typeid, title, viewpos from %s ' % (tableName, ))
        command = ' union '.join(command)
        command = 'create temporary view allitems as ' + command + ';'
        self.cursor.execute(command)
        self.cursor.execute('create temporary view id_and_pid as select relatedid as "id", id as "parentid" from relations where id in (select id from folders)')
        self.cursor.execute('create temporary view ordereditems as select id, parentid, typeid, title from id_and_pid inner join (select id as childid, typeid, title from allitems order by viewpos) on id==childid')
        tocnode = self._createElement("tableofcontents")
        self.root.appendChild(tocnode)
        node = self._createElement("contents")
        self.root.appendChild(node)
        self.traverseChilds(0, node, tocnode)
        self.cursor.execute('drop view allitems;');
        self.cursor.execute('drop view id_and_pid;');
        self.cursor.execute('drop view ordereditems;');
        self.writeXmlDoc()

    def traverseChilds(self, parentid, parentnode, parenttocnode, indent=0):
        cursor = nafdb.connection.cursor()
        cursor.execute("select * from ordereditems where id==?", (parentid,))
        row = cursor.fetchone()
        if row is not None:
            (itemid, pid, typeid, title) = row
            table = nafdb.getTableForTypeId(typeid)
            node = self.renderItem(table, itemid, table.name[:-1])
            tocnode = self.renderTocItem(table, itemid, 'toc'+table.name[:-1], indent)
        else:
            node = parentnode
            tocnode = parenttocnode
        cursor.execute("select * from ordereditems where parentid==?", (parentid,))
        while True:
            row = cursor.fetchone()
            if row is None: break
            (itemid, pid, typeid, title) = row
            if typeid == nafdb.TYPE_FOLDER:
                subnode, subtocnode = self.traverseChilds(itemid, node, tocnode, indent+1)
            else:
                table = nafdb.getTableForTypeId(typeid)
                subnode = self.renderItem(table, itemid, table.name[:-1])
                subtocnode = self.renderTocItem(table, itemid, 'toc'+table.name[:-1], indent)
                relatedNode = self._createElement("relations")
                relatedCnt = 0
                for relatedId in nafdb.connection.execute("select relatedid from relations where id==?",  (itemid, )):
                    (relatedTypeId,  relatedTitle) = nafdb.connection.execute("select typeid, title from ordereditems where id==?",  relatedId).fetchone()
                    relatedTableName = nafdb.getTableForTypeId(relatedTypeId).name
                    tmpNode = self._createElement(relatedTableName[:-1])
                    tmpNode.appendChild(self._createTextElement('id',  str(relatedId[0])))
                    tmpNode.appendChild(self._createTextElement('title',  relatedTitle))
                    relatedNode.appendChild(tmpNode)
                    relatedCnt += 1
                relatedNode.setAttribute('cnt', str(relatedCnt))
                subnode.appendChild(relatedNode)
            node.appendChild(subnode)
            tocnode.appendChild(subtocnode)
        return node, tocnode

    def renderItem(self, table, itemid, nodeName='item'):
        itemNode = self._createElement(nodeName)
        for column in table.columns:
            node = None
            data = self.getItemForId(table.name, itemid, column.name)
            if column._type == 'blob':
                data = '<img src="data:image/png;base64,' + base64.b64encode(data) + '"/>'
                dom = parseString(data)
                node = self._createElement(column.name)
                node.appendChild(dom.documentElement)
            else:
                data = unicode(data)
                if column._type == 'text' and  data.startswith("<!DOCTYPE HTML"):
                    mo = self.htmlBodyRegexp.search(data)
                    if mo is not None:
                        data = mo.group(1)
                        data = '<div class="__from_qt__">'+data+"</div>"
                        try:
                            dom = parseString(data.encode('UTF-8'))
                        except ExpatError:
                            print "Trouble with %s, ID %s, field %s" %  (table.name, itemid, column.name)
                            raise 
                        for imgElement in dom.documentElement.getElementsByTagName('img'):
                            imgId = imgElement.getAttribute('src')
                            mo = self.imgIdRegexp.search(imgId)
                            if mo is not None:
                                imgId = int(mo.group(1))
                                try:
                                    imgData = nafdb.getItemForId('images', imgId, 'image')
                                    if imgData is None:
                                        logging.error("broken image, id=%d", imgId)
                                        imgData = 'data:image/png;base64,' + BROKEN_IMAGE_DATA
                                        imgTitle = "broken image"
                                    else:
                                        imgData = 'data:image/png;base64,' + base64.b64encode(imgData)
                                        imgTitle = nafdb.getItemForId('images', imgId, 'title')
                                    imgElement.removeAttribute('src')
                                    imgElement.setAttribute('src', imgData)
                                    imgElement.setAttribute('alt', imgTitle)
                                    imgElement.setAttribute('title', imgTitle)
                                except:
                                    logging.error(traceback.format_exc())
                        node = self._createElement(column.name)
                        node.appendChild(dom.documentElement)
            if node is None:
                node = self._createTextElement(column.name, data)
            itemNode.appendChild(node)
        return itemNode
        
    def renderTocItem(self, table, itemid, nodeName='item', indent=0):
        itemNode = self._createElement(nodeName, {'indent':str(indent)})
        for name in ['id', 'title']:
            data = unicode(self.getItemForId(table.name, itemid, name))
            itemNode.appendChild(self._createTextElement(name, data))
        return itemNode
        



def run(args):
    if args.plainFormat:
        exporter = cExportPlainXml(args)
    else:
        exporter = cExportPrettyXml(args)
    exporter.run()


if __name__ == '__main__':

    logFormat = '%(module)s:%(lineno)s (%(funcName)s): %(message)s'
    level=logging.NOTSET
    ##level=logging.DEBUG
    ##level=logging.INFO,
    ##level=logging.ERROR,
    logging.basicConfig(format=logFormat, level=level,
                        ##, filemode='w', filename='myapp.log'
                        )

    clp = cCommandLineProcessor(DEFAULT_XSL_FILE)
    clp.parseOpts()
    run(clp.args)

