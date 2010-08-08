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

"""
Update a nafms database version 1 to version 2
"""

import sys, os, sqlite3

OLD_DATABASE_VERSION = (1,)
NEW_DATABASE_VERSION = (2,)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: %s <database file>" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    filename = sys.argv[1]    
    if not os.path.exists(filename):
        print("File %s does not exist" % filename)
        sys.exit(1)
    filename = os.path.realpath(filename.encode('utf-8'))
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    version = cursor.execute("SELECT version FROM __info__;").fetchone()
    if version != OLD_DATABASE_VERSION:
        print("Database version %s not matching" % version)
        sys.exit(1)
    cursor.execute("UPDATE __info__ SET version=?", NEW_DATABASE_VERSION)
    
    print("INFO: adding priority to testcases")
    cursor.execute("ALTER TABLE testcases ADD COLUMN priority integer")
    cursor.execute("UPDATE testcases SET priority=0")
    
    print("INFO: adding testability, baseline and risk to requirements")
    cursor.execute("ALTER TABLE requirements ADD COLUMN testability text")
    cursor.execute("UPDATE requirements SET testability=''")
    cursor.execute("ALTER TABLE requirements ADD COLUMN baseline text")
    cursor.execute("UPDATE requirements SET baseline=''")
    cursor.execute("ALTER TABLE requirements ADD COLUMN risk integer")
    cursor.execute("UPDATE requirements SET risk=0")
    
    cursor.execute("INSERT INTO statusLUT VALUES (3, 'In discussion')")
    cursor.execute("INSERT INTO statusLUT VALUES (4, 'Rejected')")
    
    cursor.execute("SELECT id, risk FROM features WHERE risk<=1")
    for item in cursor.fetchall():
        print("WARNING: altering risk of feature %d"  % item[0])
    cursor.execute("UPDATE features SET risk=0 WHERE risk<=1")
    
    # no warning, just remapping
    cursor.execute("UPDATE features SET risk=1 WHERE risk==2")

    cursor.execute("SELECT id, risk FROM features WHERE risk>=3")
    for item in cursor.fetchall():
        print("WARNING: altering risk of feature %d"  % item[0])
    cursor.execute("UPDATE features SET risk=2 WHERE risk>=3")

    cursor.execute("DELETE FROM riskLUT")
    cursor.execute("INSERT INTO riskLUT values (0, 'Dangerous')")
    cursor.execute("INSERT INTO riskLUT values (1, 'Medium')")
    cursor.execute("INSERT INTO riskLUT values (2, 'Safe')")
    
    cursor.execute("CREATE VIEW testability_view AS SELECT DISTINCT testability AS value FROM requirements")
    cursor.execute("CREATE VIEW baseline_view AS SELECT DISTINCT baseline AS value FROM requirements")

    
    connection.commit()
    
