
set p=C:\Program Files (x86)\Emercoin\
set exe=emercoin-qt
set name=emercoin

rem timeout /t 5


rem ================== Bitcoin start
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%exe%.exe" -conf=daemon.conf -txindex=1



timeout /t 122

tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%exe%.exe" -conf=daemon.conf -reindex -txindex=1

pause
