
set p=C:\Program Files (x86)\Sibcoin\
set exe=sibcoin-qt
set name=sibcoin

rem timeout /t 5


rem ================== Bitcoin start
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%exe%.exe" -conf=daemon.conf -txindex=1 -datadir=d:\blockchains\Sibcoin



timeout /t 122

tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%exe%.exe" -conf=daemon.conf -reindex -txindex=1 -datadir=d:\blockchains\Sibcoin

pause
