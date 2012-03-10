# -*- coding: utf-8  -*-
import subprocess, os, os.path, shutil
import _nafhelp_createtranslationsstrings


PYTHON_SITE_PCKG = r"C:\Python27\Lib\site-packages"
PYQTPATH = r"C:\Python27\Lib\site-packages\PyQt4"

UIC = PYQTPATH + r"\pyuic4.bat"
PYLUPDATE = PYQTPATH + r"\pylupdate4.exe"
LRELEASE = PYQTPATH + r"\lrelease.exe"
PYRCC4  = PYQTPATH + r"\pyrcc4.exe"
SUBWCREF = r"C:\Programme\tools\SubWCRev\subwcrev.exe"

SCRIPTS = "oaeditor.py oaeditor.pyw oalogview.py oalogview.pyw oatestrunner.py oatestrunner.pyw"
SOURCES = "_naf_usecase.py _naf_tree.py _naf_tableview.py _naf_requirement.py "\
    "_naf_itemmodel.py _naf_filter.py _naf_commons.py _naf_component.py _naf_database.py _naf_feature.py "\
    "_naf_folder.py _naf_image.py _naf_imageviewer.py _naf_simplesection.py "\
    "_naf_testcase.py _naf_testsuite.py _naf_textviewer.py naf_exportxml.py naf_editor.py " \
    "naf_updatedb_v1_to_v2.py _naf_about.py _oatr_database.py _oatr_tableview.py filepicker.py"\
    "oaxml2db.py _oatr_importwizard.py _oatr_testrun.py _oatr_commons.py _oatr_testsuite.py"
DATAFILES = 'nafms_de.qm oareport.css oareport.xsl oareportlang.xsl README.txt CHANGELOG.txt COPYING.txt'

TRANSLATIONSOURCES = SCRIPTS + SOURCES + '_nafhelp_translationsstrings.py'

def add(f, names):
    for name in names:
        f.write('include %s\n' % name)
    
def subwcref():
    subprocess.call(SUBWCREF + " . _naf_version.tmpl _naf_version.py")
    
def build():
    subwcref()
    _nafhelp_createtranslationsstrings.run()
    subprocess.call(PYLUPDATE + ' -verbose ' + TRANSLATIONSOURCES + ' -ts nafms_de.ts')
    subprocess.call(LRELEASE + ' nafms_de.ts')
    subprocess.call(PYRCC4 + " -py2 -o _naf_resources.py nafms.qrc")
    subprocess.call('python setup.py sdist')

def make_win32_zip():
    basename = 'openadams-win32-%s' % VERSION
    rootdir = os.getcwd() + r"\dist"
    zipfile = rootdir + "\\%s" % basename
    shutil.make_archive(zipfile, "zip", rootdir, basename) 
    
def buildbin():
    subwcref()
    if 0:
        subprocess.call('python %s\pyinstaller-1.5.1\Makespec.py --icon=icons/appicon.ico -w oaeditor.py' % PYTHON_SITE_PCKG)
        subprocess.call('python %s\pyinstaller-1.5.1\Makespec.py --icon=icons/appicon.ico -w oatestrunner.py' % PYTHON_SITE_PCKG)
        subprocess.call('python %s\pyinstaller-1.5.1\Makespec.py --icon=icons/appicon.ico -w oalogview.py' % PYTHON_SITE_PCKG)
    subprocess.call('python %s\pyinstaller-1.5.1\Build.py oaeditor.spec' % PYTHON_SITE_PCKG)
    subprocess.call('python %s\pyinstaller-1.5.1\Build.py oatestrunner.spec' % PYTHON_SITE_PCKG)
    subprocess.call('python %s\pyinstaller-1.5.1\Build.py oalogview.spec' % PYTHON_SITE_PCKG)
    make_win32_zip()

def manifest():
    modules = SOURCES.split() + ['_naf_resources.py', '_naf_version.py']
    modules += SCRIPTS.split()
    data_files = DATAFILES.split()

    f = open('MANIFEST.in', 'w')
    add(f, modules)
    add(f, data_files)
    f.close()

def copy_files():
    basename = 'openadams-win32-%s' % VERSION
    shutil.copyfile(r'dist\oatestrunner\oatestrunner.exe', r'dist\%s\oatestrunner.exe' % basename)
    shutil.copyfile(r'dist\oatestrunner\oatestrunner.exe.manifest', r'dist\%s\oatestrunner.exe.manifest' % basename)
    shutil.copyfile(r'dist\oalogview\oalogview.exe', r'dist\%s\oalogview.exe' % basename)
    shutil.copyfile(r'dist\oalogview\oalogview.exe.manifest', r'dist\%s\oalogview.exe.manifest' % basename)
    shutil.copyfile(r'dist\oatestrunner\PyQt4.QtSql.pyd', r'dist\%s\PyQt4.QtSql.pyd' % basename)
    shutil.copyfile(r'dist\oatestrunner\QtSql4.dll', r'dist\%s\QtSql4.dll' % basename)
    shutil.copytree(r'dist\oatestrunner\qt4_plugins\sqldrivers', r'dist\%s\qt4_plugins\sqldrivers' % basename)


subwcref()
from _naf_version import VERSION
manifest()
build()
buildbin()
copy_files()
make_win32_zip()
    
    



