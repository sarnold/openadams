# -*- coding: utf-8  -*-
# $Id: _naf_testcase.py 50 2012-02-16 18:15:16Z achimk $

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
        