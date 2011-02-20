import re,  os.path
import _naf_database as nafdb

    
class cHierarchicExporter(object):
    def __init__(self,  databaseName,  args):
        self.databaseName = databaseName
        self.getItemForId = nafdb.getRawItemForId
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


class cQtHelpExporterArgs(object):
    def __init__(self,  projectname=None,  projectfolder=None,  title=None,  language=None,  cssfile=None):
        self.language = language or '0x809 Englisch'
        self.cssfile = cssfile or 'oareport.css'
        self.projectname = projectname or 'oareport'
        self.projectfolder = projectfolder or '.'
        self.title = title or 'openADAMS Report'
        
    def __getitem__(self, key):
       return getattr(self,  key) 
 
    
class cQtHelpExporter(cHierarchicExporter):
    
    def setUp(self):
        self.indent = -1
        self.renderers = {
            nafdb.TYPE_FOLDER : self.renderFolder, 
            nafdb.TYPE_REQUIREMENT : self.renderRequirement,
            nafdb.TYPE_USECASE : self.renderUsecase,
            nafdb.TYPE_IMAGE : self.renderImage,
            nafdb.TYPE_FEATURE : self.renderFeature,
            nafdb.TYPE_TESTCASE : self.renderTestcase,
            nafdb.TYPE_TESTSUITE : self.renderTestsuite,
            nafdb.TYPE_SIMPLESECTION : self.renderSimplesection,
            nafdb.TYPE_COMPONENT : self.renderComponent,
            nafdb.TYPE_CHANGE : self.renderChange,
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
        fname = os.path.join("%(projectfolder)s" % args,  "%(projectname)s.hhp" % args)
        self.fpHhp = open(fname,  "w")
        self.fpHhp.write(self.trimString(t))
        
        t = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
                    "http://www.w3.org/TR/html4/strict.dtd">
                <html>
                <head>
                <meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
                <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                <!-- Sitemap 1.0 -->
                </head><body>'''
        fname = os.path.join("%(projectfolder)s" % args,  "%(projectname)s.hhc" % args)
        self.fpToc = open(fname,  "w")
        self.fpToc.write(self.trimString(t))

    def tearDown(self):
        #self.fp.write('\n'.join(self._fileList(self.tocnode.nodes[0])))
        self.fpHhp.write('\n[INFOTYPES]\n\n')
        self.fpHhp.close()
        self.fpToc.write('\ul></ul></body></html>\n')
        self.fpToc.close()
        
    def renderItem(self, table, itemid, nodeName='item',  relatedItems=[]):
        prefix = PREFIX[table.typeid]
        label = '%s_%05d' % (prefix ,  itemid)
        fname = os.path.join("%(projectfolder)s" % args,  "%s.html" % label)
        fp = open(fname,  'w')
        t = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
                    "http://www.w3.org/TR/html4/strict.dtd">
                    <html>
                    <head>
                    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
                    <title>%s</title>
                    <link rel="stylesheet" type="text/css" media="screen" href="oareport.css">
                    </head>
                    <body>""" % label
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
            self.fpToc.write('<ul>')
        elif indent < self.indent:
            self.fpToc.write('</ul>\n')
        else:
            pass
        self.indent = indent
        id = unicode(self.getItemForId(table.name, itemid, 'id'))
        title = unicode(self.getItemForId(table.name, itemid, 'title'))
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
        return
    
    def getHeadline(self, table, itemid, tag='h1', withanchor=False):
        id = unicode(self.getItemForId(table.name, itemid, 'id'))
        title = unicode(self.getItemForId(table.name, itemid, 'title'))
        prefix = PREFIX[table.typeid]
        dict = {'tag':tag, 'prefix':prefix, 'id': int(id), 'title':title}
        format = ((
                   "<%(tag)s class='%(prefix)s'>%(prefix)s-%(id)s: %(title)s</%(tag)s>",   # withanchor=False, isFolder = False
                   "<%(tag)s class='%(prefix)s'>%(title)s</%(tag)s>"),                                # withanchor=False, isFolder = True
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
    
    def renderRequirement(self, table, itemid, relatedItems): 
        s = self.getHeadline(table, itemid)
        return s
        
    def renderUsecase(self, table, itemid, relatedItems): return ''
    
    def renderImage(self, table, itemid, relatedItems): 
        format = self.getItemForId(table.name, itemid, 'format')
        prefix = PREFIX[nafdb.TYPE_IMAGE]
        fname = '%s_%d.%s' % (prefix,  itemid,  format)
        s = [self.getHeadline(table, itemid)]
        data = self.getItemForId(table.name, itemid, 'image')
        s.append(self.extractHtmlBody(unicode(self.getItemForId(table.name, itemid, 'description'))))
        s.append('<p><img src="%s"/></p>' % fname)
        source = self.getItemForId(table.name, itemid, 'source')
        keywords = self.getItemForId(table.name, itemid, 'keywords')
        fname = os.path.join("%(projectfolder)s" % args,  fname)
        fp = open(fname,  'wb')
        fp.write(data)
        fp.close()
        return '\n'.join(s)
    
    def renderFeature(self, table, itemid, relatedItems): return ''
    def renderTestcase(self, table, itemid, relatedItems): return ''
    def renderTestsuite(self, table, itemid, relatedItems): return ''
    
    def renderSimplesection(self, table, itemid, relatedItems): 
        s = [self.getHeadline(table, itemid)]
        s.append(self.extractHtmlBody(unicode(self.getItemForId(table.name, itemid, 'content'))))
        return '\n'.join(s)
    
    def renderComponent(self, table, itemid, relatedItems): return ''
    def renderChange(self, table, itemid, relatedItems): return ''
    
args = cQtHelpExporterArgs(projectname='sample',  projectfolder='htmlhelp')
databaseName = "test.db"
exporter = cQtHelpExporter(databaseName,  args)
exporter.run()
