

rem timeout /t 5

set p=C:\Program Files\Bitcoin\
set exe=bitcoin-qt
set name=bitcoin


rem -rescan
rem ================== Bitcoin start
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%exe%.exe" -conf=daemon.conf -txindex=1


timeout /t 122

tasklist | find /I "bitcoin-qt.exe"
if %errorlevel%==1 start "%name%" /MIN "%p%%exe%.exe" -conf=daemon.conf -txindex=1 -reindex -rescan

pause