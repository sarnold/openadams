set BACKUPDIR=c:/work/backup
robocopy "c:\work\projects\nafms" %BACKUPDIR%  /V /NP /R:10 /W:30 /E /XD .svn /XF *.pyc
set TARFILE=%BACKUPDIR%/nafms.tar
rem tar -c -v -f %TARFILE% --exclude=*.svn/* *.*
rem tar -c -v -f %TARFILE%  -X exclude.txt *.*
tar -c -v -f %TARFILE% %BACKUPDIR%/*
gzip %TARFILE%
ls -l %TARFILE%.gz
