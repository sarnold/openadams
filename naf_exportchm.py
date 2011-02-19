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
        t = '\n'.join([s.strip() for s in """[OPTIONS]
                Compatibility=1.1 or later
                Compiled file=oa.chm
                Contents file=oa.hhc
                Default topic=FO_00001.html
                Display compile progress=No
                Language=0x407 Deutsch (Deutschland)
                Title=openADAMS Report

                [FILES]
                """.split('\n')])
        self.fpHhp = open('htmlhelp/sample.hhp',  "w")
        self.fpHhp.write(t)
        
        t = '\n'.join([s.strip() for s in '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
                <HTML>
                <HEAD>
                <meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
                <!-- Sitemap 1.0 -->
                </HEAD><BODY>
                '''.split('\n')])
        self.fpToc = open('htmlhelp/oa.hhc',  "w")
        self.fpToc.write(t)

    def tearDown(self):
        #self.fp.write('\n'.join(self._fileList(self.tocnode.nodes[0])))
        self.fpHhp.write('\n[INFOTYPES]\n\n')
        self.fpHhp.close()
        self.fpToc.write('\n</UL></UL></BODY></HTML>\n')
        self.fpToc.close()
        
    def renderItem(self, table, itemid, nodeName='item',  relatedItems=[]):
        prefix = PREFIX[table.typeid]
        label = '%s_%05d' % (prefix ,  itemid)
        fp = open('htmlhelp/%s.html' % label,  'w')
        fp.write('<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">\n<HTML>\n<HEAD>\n<title>%s</title>\n' % label)
        fp.write('<link rel="stylesheet" type="text/css" media="screen" href="oareport.css"/>\n</HEAD>\n<BODY>\n')
        fp.write(self.renderers[table.typeid](table, itemid, relatedItems))
        fp.write('</BODY>\n</HTML>')
        fp.close()
        
    def renderTocItem(self, table, itemid, nodeName='item', indent=0):
        prefix = PREFIX[table.typeid]
        label = '%s_%05d' % (prefix ,  itemid)
        # append file name to list of files in hhp file
        self.fpHhp.write('%s.html\n' % label)
        if indent > self.indent:
            self.fpToc.write('<UL>')
        elif indent < self.indent:
            self.fpToc.write('</UL>\n')
        else:
            pass
        self.indent = indent
        id = unicode(self.getItemForId(table.name, itemid, 'id'))
        title = unicode(self.getItemForId(table.name, itemid, 'title'))
        if table.typeid == nafdb.TYPE_FOLDER:
            imageId = 5
        else:
            imageId = 11
        self.fpToc.write("""
        <LI> <OBJECT type="text/sitemap">
            <param name="Name" value="%s">
            <param name="Local" value="%s.html">
            <param name="ImageNumber" value="%d">
            </OBJECT>
        """ % (title, label,  imageId))            
        return
    
    def getHeadline(self, table, itemid, tag='h1', withanchor=False):
        id = unicode(self.getItemForId(table.name, itemid, 'id'))
        title = unicode(self.getItemForId(table.name, itemid, 'title'))
        prefix = PREFIX[table.typeid]
        if withanchor:
            return "<%s><a href='%s_%05d.html'>%s-%s: %s</a></%s>" % (tag, prefix, int(id), prefix, id, title, tag)
        else:
            return "<%s>%s-%s: %s</%s>" % (tag, prefix, id, title, tag)
        
    def renderFolder(self, table, itemid, relatedItems): 
        s = [self.getHeadline(table, itemid)]
        if len(relatedItems) > 0:
            s.append('<ul>')
            for relatedItem in relatedItems:
                s.append(self.getHeadline(relatedItem['table'], relatedItem['id'], 'li', withanchor=True))
            s.append('</ul>')
        return '\n'.join(s)
    
    def renderRequirement(self, table, itemid, relatedItems): 
        s = self.getHeadline(table, itemid)
        return s
        
    def renderUsecase(self, table, itemid, relatedItems): return ''
    def renderImage(self, table, itemid, relatedItems): return ''
    def renderFeature(self, table, itemid, relatedItems): return ''
    def renderTestcase(self, table, itemid, relatedItems): return ''
    def renderTestsuite(self, table, itemid, relatedItems): return ''
    
    def renderSimplesection(self, table, itemid, relatedItems): 
        s = [self.getHeadline(table, itemid)]
        s.append(unicode(self.getItemForId(table.name, itemid, 'content')))
        return '\n'.join(s)
    
    def renderComponent(self, table, itemid, relatedItems): return ''
    def renderChange(self, table, itemid, relatedItems): return ''
    
databaseName = "test.db"
exporter = cQtHelpExporter(databaseName,  None)
exporter.run()
