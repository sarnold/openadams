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

from PyQt4 import QtGui,  QtCore
from PyQt4.QtCore import Qt


class cArtifactDetailsView(QtGui.QWidget):
    "Base class for artifact details view"
    editSignal = QtCore.pyqtSignal(QtCore.QString, QtCore.QString, 'int')

    def __init__(self, *args, **kwargs):
        super(cArtifactDetailsView, self).__init__(*args, **kwargs)

    def makeEditLinkLabel(self, fieldName, clickable=True):
        #text = '<span>%s</span><br/><a href="%s">%s</a>' % (obj.mapper.model().getLabel(fieldName), fieldName, str(obj.tr('Edit')))
        if clickable:
            text = '<a href="%s">%s</a>' % (fieldName, self.mapper.model().getLabel(fieldName))
        else:
            text = self.mapper.model().getLabel(fieldName)
        label = QtGui.QLabel(text  , alignment=Qt.AlignTop)
        label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.LinksAccessibleByKeyboard)
        label.setToolTip(self.tr("Open in Text Editor"))
        return label

    def sendEditSignal(self, url):
        tableName = self.mapper.model().tableName
        self.editSignal.emit(tableName, url, self.mapper.currentIndex())
