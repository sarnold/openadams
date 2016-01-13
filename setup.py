# -*- coding: utf-8  -*-
from setuptools import setup
from _naf_version import VERSION
import subprocess

SCRIPTS = ["oaeditor.py", "oalogview.py", "oatestrunner.py", 
           "naf_exportchm.py", "filepicker.py", "oaxml2db.py",
           "naf_exportxml.py", "naf_editor.py", "naf_updatedb_v1_to_v2.py",
           "_naf_usecase.py", "_naf_tree.py", "_naf_tableview.py", 
           "_naf_requirement.py", "_naf_itemmodel.py", "_naf_filter.py", 
           "_naf_commons.py", "_naf_component.py", "_naf_database.py", 
           "_naf_feature.py", "_naf_folder.py", "_naf_image.py", 
           "_naf_imageviewer.py", "_naf_simplesection.py", 
           "_naf_testcase.py", "_naf_testsuite.py", "_naf_textviewer.py", 
           "_naf_about.py", "_oatr_database.py", "_oatr_tableview.py", 
           "_oatr_importwizard.py", "_oatr_testrun.py", "_oatr_commons.py", 
           "_oatr_testsuite.py"]
           
DATAFILES = ["nafms_de.qm", "oareport.css", "oareport.xsl", "oareportlang.xsl",
             "README.txt", "CHANGELOG.txt", "COPYING.txt" ]

# build binary version of Qt translation ile
subprocess.call(["lrelease", "nafms_de.ts"])

# update version file
subprocess.call(["./update_version.sh"])

setup(name='openadams',
      description = 'Artifact Documentation And Management System',
      version=VERSION,
      url = "https://sourceforge.net/projects/openadams/",
      author = "Achim Köhler",
      author_email = "achimk@users.sourceforge.net",
      scripts = SCRIPTS,
      data_files = DATAFILES
      )
