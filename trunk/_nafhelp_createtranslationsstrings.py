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

import _naf_database as nafdb

def run():
    filename = '_nafhelp_translationsstrings.py'
    f = open(filename, "w")
    f.write("from PyQt4 import QtCore\n")

    for table in nafdb.tables:
        f.write("QtCore.QCoreApplication.translate('cTable', '%s')\n" % table.displayname)
        for column in table.columns:
            f.write("QtCore.QCoreApplication.translate('cColumn', '%s')\n" % column.displayname)
    
    for table, items in nafdb.lookupTables.iteritems():
        for item in items:
            f.write("QtCore.QCoreApplication.translate('lookupTable', '%s')\n" % item)
            
    f.close()


if __name__ == '__main__':
    run()
