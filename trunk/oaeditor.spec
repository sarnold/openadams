# -*- mode: python -*-

from _naf_version import VERSION

NAME = 'openadams-win32-%s' % VERSION

a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'oaeditor.py'],
             pathex=[r'C:\home\projects\openadams'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\oaeditor', 'oaeditor.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='icons\\appicon.ico')
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               [('nafms_de.qm', 'nafms_de.qm', 'DATA'), 
                ('README.txt', 'README.txt', 'DATA'),
                ('CHANGELOG.txt', 'CHANGELOG.txt', 'DATA'),
                ('COPYING.txt', 'COPYING.txt', 'DATA'),
                ('oareport.css', 'oareport.css', 'DATA'), 
                ('oareport.xsl', 'oareport.xsl', 'DATA'),
                ('oareportlang.xsl', 'oareportlang.xsl', 'DATA'),
                ],
               strip=False,
               upx=True,
               name=os.path.join('dist', NAME))
