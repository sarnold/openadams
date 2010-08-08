# naf_model.py
# $Id$


import os, sys, sqlite3, random
sys.path.append('..')

from _naf_database import TYPE_ROOT, TYPE_FOLDER, TYPE_REQUIREMENT, TYPE_USECASE, TYPE_IMAGE, DEFAULT_VIEW_POS
from _naf_database import tables, lookupTables, createEmptyDatabase


def createSampleDatabase(filename):
    createEmptyDatabase(filename)
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    title = "id%4d The quick brown fox jumps over the lazy dog "
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_ROOT, "ROOT"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "Project"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "100 System Requirements"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "200 System Architecture"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "300 Software Requirements"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "400 Software Architecture"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "310 Functional"))
    cursor.execute("insert into folders (id, typeid, title) values((select cnt from counter), ?, ?)", (TYPE_FOLDER, "320 Non Functional"))

    nPriority = len(lookupTables['priorityLUT'])
    nStatus = len(lookupTables['statusLUT'])
    nUseFrequency = len(lookupTables['usefrequencyLUT'])
    for i in range(5):
        priority = i % nPriority
        status = (4-i) % nStatus
        cursor.execute("insert into requirements values((select cnt from counter), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (TYPE_REQUIREMENT, "Requirement %d" % i, priority, status, 1, 'somebody', i%4, 1, 'Comes from', 'Some rationale', 'Some description', 'Any keywords', DEFAULT_VIEW_POS))
    for i in range(15):
        priority = (i+1)%nPriority
        cursor.execute("insert into requirements values((select cnt from counter), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (TYPE_REQUIREMENT, "Requirement %d" % (10*(i+1)), priority, 0, 1, 'anybody', (i+1)%4, 1, 'Comes from', 'Some rationale', 'Some description<br/><img src="#%d">' % [61,62,63][i%3], 'Any keywords', DEFAULT_VIEW_POS))

    for i in range(4):
        priority = i%nPriority
        usefreq = random.randint(0, nUseFrequency-1)
        cursor.execute("insert into usecases values((select cnt from counter), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (TYPE_USECASE, "Usecase %d" % i, priority, usefreq, 'Some actor', 'Some stakeholder', 'The prerequisites', 'Main scenario', 'Alt scenario', 'Some notes', 'Any keywords', 10-i))
    for i in range(29):
        priority = random.randint(0, nPriority-1)
        usefreq = random.randint(0, nUseFrequency-1)
        cursor.execute("insert into usecases values((select cnt from counter), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (TYPE_USECASE, "Usecase %d" % ((i+1)*100), priority, usefreq, 'Some actor', 'Some stakeholder', 'The prerequisites', 'Main scenario', 'Alt scenario', 'Some notes', 'Any keywords', DEFAULT_VIEW_POS))

    f = open('hello_world.png', 'rb')
    imagedata = buffer(f.read())
    f.close()
    cursor.execute("insert into images values((select cnt from counter), ?, ?, ?, ?, ?, ?, ?, ?)",
            (TYPE_IMAGE, "Title of image 1", '<b>Description</b> of image 1', imagedata, 'mspaint', 'Any keywords', 'PNG', DEFAULT_VIEW_POS))
    f = open('timing.png', 'rb')
    imagedata = buffer(f.read())
    f.close()
    cursor.execute("insert into images values((select cnt from counter), ?, ?, ?, ?, ?, ?, ?, ?)",
            (TYPE_IMAGE, "Title of image 2", '<b>Description</b> of image 2', imagedata, 'mspaint', 'Any keywords', 'PNG', DEFAULT_VIEW_POS))



    cursor.execute('insert into relations values (?, ?);', (8, 32))
    cursor.execute('insert into relations values (?, ?);', (8, 34))
    cursor.execute('insert into relations values (?, ?);', (8, 37))

    cursor.execute('insert into relations values (?, ?);', (18, 28))
    cursor.execute('insert into relations values (?, ?);', (18, 29))
    cursor.execute('insert into relations values (?, ?);', (18, 31))

    cursor.execute('insert into relations values (?, ?);', (18, 10))

    folderrelations = [
    (0, 1), (1, 2), (1,3), (1,4), (1,5), (4,6), (4,7), # folder relations
    (2, 28), (2,29), (2,30), (2,31),
    (3, 32), (3, 33), (3, 34), (3, 35), (3, 36), (3, 37), (3, 38), (3, 39),
    (3, 40), (3, 41), (3, 42), (3, 45), (3, 46), (3, 47), (3, 48), (3, 49),
    (3, 50), (3, 51), (3, 52), (3, 55), (3, 56), (3, 57), (3, 58), (3, 59),
    (3, 60),
    (6, 8), (6,9), (6,10), (6,11), (6,12),
    (7,13), (7,14), (7,15), (7,16), (7,17), (7,18), (7,19),
    (7,20), (7,21), (7,22), (7,23), (7,24), (7,25), (7,26), (7,27),
    (4,61), (5,62),
    ]
    for fr in folderrelations:
        cursor.execute('insert into relations values (?, ?);', fr)

    conn.commit()
    conn.close()


"""
1: Project
    2: 100 System Requirements
        28: Usecase0
        :
        31: Usecase3
    3: 200 System Architecture
        32: Usecase0
        :
        60: Usecase2800
    4: 300 Software Requirements
        6: 310 Functional
            8: Requirement0
            9: Requirement2
            :
            12: Requirement4
        7: 320 Non Functional
            13: Requirement10
            :
            27: Requirementxxx
    5: 400 Software Architecture
"""

if __name__ == '__main__':
    createSampleDatabase("sample.db")
    sys.exit(0)

