from PyQt4 import QtSql, QtCore
import _naf_textviewer

TR_FILE_SUFFIX = "dbt"

def getTextViewer(parent):
    tvObj = _naf_textviewer.cTextEditor(parent, readOnly=True)
    tvObj.setImageProvider(__imageProvider)
    return tvObj

def __imageProvider(imgId):
    retval = QtCore.QVariant().toByteArray()
    query = QtSql.QSqlQuery('SELECT image FROM images WHERE id==%d' % imgId)
    if query.isActive():
        query.next()
        if query.isValid():
            retval = query.value(0).toByteArray()
    return retval