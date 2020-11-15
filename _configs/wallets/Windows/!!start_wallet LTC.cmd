

rem timeout /t 5


rem ================== Bitcoin start
tasklist | find /I "litecoin-qt.exe"
if %errorlevel%==1 start "litecoin-qt.exe" /MIN "C:\Program Files\Litecoin\litecoin-qt.exe" -conf=daemon.conf -txindex=1 -datadir=d:\blockchains\Litecoin


timeout /t 122

tasklist | find /I "litecoin-qt.exe"
if %errorlevel%==1 start "litecoin-qt.exe" /MIN "C:\Program Files\Litecoin\litecoin-qt.exe" -conf=daemon.conf -reindex -txindex=1 -datadir=d:\blockchains\Litecoin

pause