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

from PyQt4 import QtGui,  QtCore, QtSql
from PyQt4.QtCore import Qt

import _oatr_database as oadb
import _oatr_commons
import _naf_database as nafdb

class cTestsuiteView(QtGui.QWidget):
                    
    def __init__(self, parent, model):
        super(cTestsuiteView, self).__init__(parent)
        self.mapper = QtGui.QDataWidgetMapper()
        self.mapper.setModel(model)
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QtGui.QLabel(nafdb.getColumnDisplayName("testsuites", "title")), 0, 0)
        layout.addWidget(QtGui.QLabel(nafdb.getColumnDisplayName("testsuites", "id")), 1, 0)
        layout.addWidget(QtGui.QLabel(nafdb.getColumnDisplayName("testsuites", "keywords")), 2, 0)
        layout.addWidget(QtGui.QLabel(nafdb.getColumnDisplayName("testsuites", "description"), alignment=Qt.AlignTop), 3, 0)
        layout.addWidget(QtGui.QLabel(nafdb.getColumnDisplayName("testsuites", "execorder")), 4, 0)
                
        ledId = QtGui.QSpinBox(self)
        ledId.setReadOnly(True) # id is always read only
        ledTitle = QtGui.QLineEdit(self, readOnly=True)
        ledKeywords = QtGui.QLineEdit(self, readOnly=True)
        tedDescription = _oatr_commons.getTextViewer(self)
        ledExecorder = QtGui.QLineEdit(self, readOnly=True)
        

        # addWidget(widget, fromRow, fromColumn, rowSpan, columnSpan, alignment)
        layout.addWidget(ledTitle,        0, 1, 1, 1)
        layout.addWidget(ledId,           1, 1, 1, 1)
        layout.addWidget(ledKeywords,     2, 1, 1, 1)
        layout.addWidget(tedDescription,  3, 1, 1, 1)
        layout.addWidget(ledExecorder,    4, 1, 1, 1)
                                 
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(3, 2)
    
        self.mapper.addMapping(ledId, model.fieldIndex('id'))
        self.mapper.addMapping(ledTitle, model.fieldIndex('title'))
        self.mapper.addMapping(ledKeywords, model.fieldIndex('keywords'))
        self.mapper.addMapping(tedDescription, model.fieldIndex('description'))
        self.mapper.addMapping(ledExecorder, model.fieldIndex('execorder'))
        
        
