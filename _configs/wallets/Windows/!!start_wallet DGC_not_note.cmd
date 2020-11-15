set name=dogecoin
set p=C:\Program Files\%name%
set exe=%name%-qt
set ddir=-datadir=d:\blockchains\%name%


rem timeout /t 5

rem ================== %name% start
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon_not_note.conf -txindex=1

timeout /t 122

tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon_not_note.conf -reindex -txindex=1 -rescan


pause