import re,  os.path, subprocess, codecs
import xml.sax.saxutils as saxutils
import base64,  sys,  shutil
import argparse

import _naf_database as nafdb
from naf_exportxml import BROKEN_IMAGE_DATA

BROKEN_IMAGE_FILENAME = "missing.png"
DEFAULT_OUTPUT_FOLDER = 'htmlhelp'
DEFAULT_HHC_LOCATION = 'hhc.exe'

class cHierarchicExporter(object):
    def __init__(self,  databaseName,  args):
        self.databaseName = databaseName
        self.getItemForId = nafdb.getItemForId
        self.args = args
        
    def _setUp(self):
        nafdb.openDatabase(self.databaseName)
        self.cursor = nafdb.connection.cursor()
        self.cursor.execute("select version from __info__")
        self.dbVersion = str(self.cursor.fetchone()[0])
        command = []
        for tableName in nafdb.getTableNames():
            command.append('select id, typeid, title, viewpos from %s ' % (tableName, ))
        command = ' union '.join(command)
        command = 'create temporary view allitems as ' + command + ';'
        self.cursor.execute(command)
        self.cursor.execute('create temporary view id_and_pid as select relatedid as "id", id as "parentid" from relations where id in (select id from folders)')
        self.cursor.execute('create temporary view ordereditems as select id, parentid, typeid, title from id_and_pid inner join (select id as childid, typeid, title from allitems order by viewpos) on id==childid')

    def _tearDown(self):
        self.cursor.execute('drop view allitems;');
        self.cursor.execute('drop view id_and_pid;');
        self.cursor.execute('drop view ordereditems;');

    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def renderItem(self, table, itemid, nodeName='item',  relatedItems=[]):
         pass
        
    def renderTocItem(self, table, itemid, nodeName='item', indent=0):
        pass
        
    def traverseChilds(self, parentid, indent=0):
        cursor = nafdb.connection.cursor()
        cursor.execute("select * from ordereditems where id==?", (parentid,))
        row = cursor.fetchone()
        if row is not None:
            (itemid, pid, typeid, title) = row
            table = nafdb.getTableForTypeId(typeid)
            self.renderItem(table, itemid, table.name[:-1], self.getRelatedItems(itemid))
            self.renderTocItem(table, itemid, table.name[:-1], indent)
        else:
            pass
        cursor.execute("select * from ordereditems where parentid==?", (parentid,))
        while True:
            row = cursor.fetchone()
            if row is None: break
            (itemid, pid, typeid, title) = row
            if typeid == nafdb.TYPE_FOLDER:
                self.traverseChilds(itemid, indent+1)
            else:
                table = nafdb.getTableForTypeId(typeid)
                self.renderItem(table, itemid, table.name[:-1], self.getRelatedItems(itemid))
                self.renderTocItem(table, itemid, table.name[:-1], indent+1)
        return 
        
    def getRelatedItems(self, itemid):
        relatedItems = []
        for relatedId in nafdb.connection.execute("select relatedid from relations where id==?",  (itemid, )):
            (relatedTypeId,  relatedTitle) = nafdb.connection.execute("select typeid, title from ordereditems where id==?",  relatedId).fetchone()
            relatedTableName = nafdb.getTableForTypeId(relatedTypeId)
            relatedItems.append({'table':  relatedTableName,  'id': relatedId[0],  'title':relatedTitle})
        return relatedItems
    
    def trimString(self,  s):
        return '\n'.join([st.strip() for st in s.split('\n')])
       
    htmlBodyPattern = re.compile(r'.*<body[^>]*>(.*)</body>',  re.DOTALL)
    imgTagPattern = re.compile(r'img\s* src="#(\d+)"')
    
    def extractHtmlBody(self,  s):
        def fixImageTag(mo):
            imgId = int(mo.group(1))
            imgType = self.getItemForId('images', imgId, 'format')
            if imgType is None:
                # hmmm..., let's check if an image with given id is actually in the database
                if self.getItemForId('images', imgId, 'id') is None:
                    # no image with given id is in the database
                    return 'img src="%s" alt="Missing image" title="Missing image"' % BROKEN_IMAGE_FILENAME
            prefix = PREFIX[nafdb.TYPE_IMAGE]
            return 'img src="%s_%d.%s"' % (prefix,  imgId,  imgType)
        mo = self.htmlBodyPattern.search(s)
        if not mo:
            return s
        body = mo.group(1)
        body = re.sub(self.imgTagPattern,  fixImageTag,  body)
        return body
        
    def run(self):
        self._setUp()
        self.setUp()
        self.traverseChilds(0)
        self.tearDown()
        self._tearDown()    
    
PREFIX = {
    nafdb.TYPE_ROOT : 'RT', 
    nafdb.TYPE_FOLDER : 'FO', 
    nafdb.TYPE_REQUIREMENT : 'RQ',
    nafdb.TYPE_USECASE : 'UC',
    nafdb.TYPE_IMAGE : 'IM',
    nafdb.TYPE_FEATURE : 'FT',
    nafdb.TYPE_TESTCASE : 'TC',
    nafdb.TYPE_TESTSUITE : 'TS',
    nafdb.TYPE_SIMPLESECTION : 'SS',
    nafdb.TYPE_COMPONENT : 'CM',
    nafdb.TYPE_CHANGE : 'CH',
    }


class cChmExporterArgs(object):
    def __init__(self,  projectname=None,  projectfolder=None,  title=None,  language=None,  cssfile=None, hhcpath=None):
        self.language = language or '0x809 Englisch'
        self.cssfile = cssfile 
        self.projectname = projectname 
        self.projectfolder = projectfolder
        self.title = title or 'openADAMS Report'
        self.hhcpath = hhcpath or "hhc.exe"
        self.outputfile = None
        
    def __getitem__(self, key):
       return getattr(self,  key) 
 
    
class cChmExporter(cHierarchicExporter):
    
    def setUp(self):
        self.args.outputfile = None
        self.indent = -1
        self.renderers = {
            nafdb.TYPE_FOLDER : self.renderFolder, 
            nafdb.TYPE_REQUIREMENT : self.renderArtifact,
            nafdb.TYPE_USECASE : self.renderArtifact,
            nafdb.TYPE_IMAGE : self.renderImage,
            nafdb.TYPE_FEATURE : self.renderArtifact,
            nafdb.TYPE_TESTCASE : self.renderArtifact,
            nafdb.TYPE_TESTSUITE : self.renderArtifact,
            nafdb.TYPE_SIMPLESECTION : self.renderArtifact,
            nafdb.TYPE_COMPONENT : self.renderArtifact,
            nafdb.TYPE_CHANGE : self.renderArtifact,
        }
        t = """[OPTIONS]
                Compatibility=1.1 or later
                Compiled file=%(projectname)s.chm
                Contents file=%(projectname)s.hhc
                Default topic=FO_00001.html
                Display compile progress=No
                Language=%(language)s
                Title=%(title)s

                [FILES]
                """ % self.args
        # create projectfolder if it not exists
        if not os.path.exists(self.args.projectfolder):
            os.mkdir(self.args.projectfolder)
        
        # create help project file 
        fname = os.path.join("%(projectfolder)s" % self.args,  "%(projectname)s.hhp" % self.args)
        self.fpHhp = codecs.open(fname, "w", 'ascii')
        self.fpHhp.write(self.trimString(t))
        
        # create table of contents file
        t = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
                    "http://www.w3.org/TR/html4/strict.dtd">
                <html>
                <head>
                <meta name="GENERATOR" content="naf_exportchm">
                <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                <!-- Sitemap 1.0 -->
                </head><body>'''
        fname = os.path.join("%(projectfolder)s" % self.args,  "%(projectname)s.hhc" % self.args)
        self.fpToc = codecs.open(fname,  "w", 'latin-1')
        self.fpToc.write(self.trimString(t))
        
        # create file with missing image icon
        fname = os.path.join("%(projectfolder)s" % self.args, BROKEN_IMAGE_FILENAME)
        fp = open(fname, "wb")
        fp.write(base64.b64decode(BROKEN_IMAGE_DATA))
        fp.close()
        
        # copy cascading style sheet file
        if self.args.cssfile is not None:
            css_path,  css_basename = os.path.split(self.args.cssfile)
            dest = os.path.join(self.args.projectfolder,  css_basename)
            if not os.path.exists(dest):
                shutil.copy(self.args.cssfile,  self.args.projectfolder)
            self.args.cssfile = css_basename

    def tearDown(self):
        self.fpHhp.write('\n[INFOTYPES]\n\n')
        self.fpHhp.close()
        self.fpToc.write('</ul></body></html>\n')
        self.fpToc.close()
        cmdline = '%s %s' % (os.path.normpath(self.args.hhcpath), os.path.normpath(self.fpHhp.name))
        fname = os.path.join("%(projectfolder)s" % self.args,  "build.bat")
        fp = open(fname, "w")
        fp.write(cmdline)
        fp.close()
        try:
            retcode = subprocess.call(cmdline, stdout=subprocess.PIPE)            
            self.args.outputfile = os.path.normpath(os.path.join("%(projectfolder)s" % self.args,  "%(projectname)s.chm" % self.args))           
            if retcode != 1:
                raise OSError("%s returns %d" % (cmdline,  retcode))
        except WindowsError,  e:
            raise WindowsError(cmdline)
        
    def renderItem(self, table, itemid, nodeName='item',  relatedItems=[]):
        if self.args.cssfile is not None:
            linkstr = '<link rel="stylesheet" type="text/css" media="screen" href="%s">' %  self.args.cssfile
        else:
            linkstr = ''
        prefix = PREFIX[table.typeid]
        label = '%s_%05d' % (prefix ,  itemid)
        fname = os.path.join("%(projectfolder)s" % self.args,  "%s.html" % label)
        fp = codecs.open(fname,  'w', 'utf-8')
        t = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
                    "http://www.w3.org/TR/html4/strict.dtd">
                    <html>
                    <head>
                    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                    <title>%s</title>
                    %s
                    </head>
                    <body>""" % (label, linkstr)
        fp.write(self.trimString(t))
        fp.write(self.renderers[table.typeid](table, itemid, relatedItems))
        fp.write('</body>\n</html>')
        fp.close()
        
    def renderTocItem(self, table, itemid, nodeName='item', indent=0):
        prefix = PREFIX[table.typeid]
        label = '%s_%05d' % (prefix ,  itemid)
        # append file name to list of files in hhp file
        self.fpHhp.write('%s.html\n' % label)
        if indent > self.indent:
            # increase of indent could only be done in steps of 1
            self.fpToc.write('<ul>')
        elif indent < self.indent:
            # decrease of indent could  be done in steps of 1, 2, ...
            self.fpToc.write('</ul>\n' * (self.indent-indent))
        else:
            pass
        self.indent = indent
        id = unicode(self.getItemForId(table.name, itemid, 'id'))
        title = saxutils.escape(unicode(self.getItemForId(table.name, itemid, 'title')))
        if table.typeid == nafdb.TYPE_FOLDER:
            imageId = 5
        else:
            imageId = 11
            title = "%s-%d: %s" %  (prefix,  int(id),  title)
        self.fpToc.write("""
        <li> <object type="text/sitemap">
            <param name="Name" value="%s">
            <param name="Local" value="%s.html">
            <param name="ImageNumber" value="%d">
            </object>
        """ % (title, label,  imageId))            
    
    def renderKeyValuePairs(self, keys, values):
        s = ['<table class="keyvalue">']
        for key, value in zip(keys, values):
            value = saxutils.escape(value) or '&mdash;'
            key = saxutils.escape(key)
            s.append('<tr>\n<td>\n%s\n</td>\n<td>%s</td>\n</tr>' % (key, value))
        return '\n'.join(s)
    
    def getHeadline(self, table, itemid, tag='h1', withanchor=False):
        id = unicode(self.getItemForId(table.name, itemid, 'id'))
        title = saxutils.escape(unicode(self.getItemForId(table.name, itemid, 'title')))
        prefix = PREFIX[table.typeid]
        dict = {'tag':tag, 'prefix':prefix, 'id': int(id), 'title':title}
        format = ((
                   "<%(tag)s class='%(prefix)s'>%(prefix)s-%(id)s: %(title)s</%(tag)s>",   # withanchor=False, isFolder = False
                   "<%(tag)s class='%(prefix)s'>%(title)s</%(tag)s>"),                     # withanchor=False, isFolder = True
                   (
                   "<%(tag)s class='%(prefix)s'><a href='%(prefix)s_%(id)05d.html'>%(prefix)s-%(id)s: %(title)s</a></%(tag)s>",     # withanchor=True, isFolder = False
                   "<%(tag)s class='%(prefix)s'><a href='%(prefix)s_%(id)05d.html'>%(title)s</a></%(tag)s>",                                   # withanchor=True, isFolder = True
                   ))
        return format[withanchor][table.typeid==nafdb.TYPE_FOLDER] % dict
        
    def renderFolder(self, table, itemid, relatedItems): 
        s = [self.getHeadline(table, itemid)]
        if len(relatedItems) > 0:
            s.append('<ul>')
            for relatedItem in relatedItems:
                id = unicode(self.getItemForId(relatedItem['table'].name, relatedItem['id'], 'id'))
                title = unicode(self.getItemForId(relatedItem['table'].name, relatedItem['id'], 'title'))
                prefix = PREFIX[relatedItem['table'].typeid]
                s.append(self.getHeadline(relatedItem['table'], relatedItem['id'], 'li',  withanchor=True))
            s.append('</ul>')
        return '\n'.join(s)
        
    def renderArtifact(self, table, itemid, relatedItems):
        s = [self.getHeadline(table, itemid)]
        multilineFields = []
        multilineHeadings = []
        singlelineFields = []
        singlelineHeadings = []
        for column in table.columns:
            if column.view == nafdb.VIEW_SINGLE_LINE:
                singlelineFields.append(column.name)
                singlelineHeadings.append(column.displayname)
            elif column.view == nafdb.VIEW_MULTI_LINE:
                multilineFields.append(column.name)
                multilineHeadings.append(column.displayname)
            else:
                pass
        for heading, field  in zip(multilineHeadings, multilineFields):
            s.append('<h2>%s</h2>' % heading)
            s.append('<div class="user">')
            s.append(self.extractHtmlBody(unicode(self.getItemForId(table.name, itemid, field))))
            s.append('</div>')
        values = [self.getItemForId(table.name, itemid, field) for field in singlelineFields]
        s.append(self.renderKeyValuePairs(singlelineHeadings, values))
        return '\n'.join(s)
            
    def renderImage(self, table, itemid, relatedItems): 
        format = self.getItemForId(table.name, itemid, 'format')
        source = self.getItemForId(table.name, itemid, 'source')
        keywords = self.getItemForId(table.name, itemid, 'keywords')
        data = self.getItemForId(table.name, itemid, 'image')        
        prefix = PREFIX[nafdb.TYPE_IMAGE]
        fname = '%s_%d.%s' % (prefix,  itemid,  format)
        s = [self.getHeadline(table, itemid)]
        s.append('<div class="user">')
        s.append(self.extractHtmlBody(unicode(self.getItemForId(table.name, itemid, 'description'))))
        s.append('</div>')
        s.append('<p><img src="%s"/></p>' % fname)
        s.append(self.renderKeyValuePairs(['Source', 'Keywords'], [source, keywords]))
        fname = os.path.join("%(projectfolder)s" % self.args,  fname)
        fp = open(fname,  'wb')
        fp.write(data)
        fp.close()
        return '\n'.join(s)


def run(databaseName,  args):
    database_path,  database_basename = os.path.split(databaseName)
    args.projectname= args.projectname or os.path.splitext(database_basename)[0]
    exporter = cChmExporter(databaseName,  args)
    exporter.run()
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export database to compressed help file.')
    parser.add_argument('-o',  '--out',  metavar='file', required=False,  type=str, help='output file base name')
    parser.add_argument('-d',  '--dir',  metavar='folder', required=False,  type=str, help='output folder name (default %s)' % DEFAULT_OUTPUT_FOLDER,  default=DEFAULT_OUTPUT_FOLDER)
    parser.add_argument('-c',  '--css',  metavar='cssfile', required=False,  type=str, help='Cascading Style Sheet file')
    parser.add_argument('--hhc',  metavar='hhc', required=False,  type=str, help='Path to HTML Help Compiler (default %s)' % DEFAULT_HHC_LOCATION, default=DEFAULT_HHC_LOCATION)
    parser.add_argument('--title',  '-t',  metavar='title', required=False,  type=str, help='Report title')
    parser.add_argument('database',  metavar='database',  type=str, help='Database file')
    args = parser.parse_args()
    
    exporterArgs= cChmExporterArgs(projectname = args.out, 
        projectfolder=args.dir, 
        cssfile=args.css, 
        hhcpath=args.hhc, 
        title=args.title)
    run(args.database,  exporterArgs)
    

