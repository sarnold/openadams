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
