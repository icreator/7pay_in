set name=dogecoin
set p=C:\Program Files\%name%
set exe=%name%-qt
set ddir=-datadir=d:\blockchains\%name%


rem timeout /t 5

rem ================== %name% start
rem tasklist | find /I "%name%"
rem if %errorlevel%==1 start "%name%.exe" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon.conf -txindex=1


rem =========================
set n=dogecoin
tasklist | findstr /b /I "%n%"
rem if %errorlevel%==1 start "%n%" /MIN "C:\Program Files\%n%\daemon\%n%d.exe" -datadir=d:\blockchains\%n% -conf=daemon.conf -txindex=1
if %errorlevel%==1 start "%n%" /MIN "C:\Program Files\%n%\%n%-qt.exe" -datadir=d:\blockchains\%n% -conf=daemon.conf -txindex=1

timeout /t 122

rem tasklist | find /I "%name%"
rem if %errorlevel%==1 start "%name%.exe" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon.conf -reindex -txindex=1 -rescan

rem =========================
set n=dogecoin
tasklist | findstr /b /I "%n%"
rem if %errorlevel%==1 start "%n%" /MIN "C:\Program Files\%n%\daemon\%n%d.exe" -datadir=d:\blockchains\%n% -conf=daemon.conf -txindex -reindex -rescan
if %errorlevel%==1 start "%n%" /MIN "C:\Program Files\%n%\%n%-qt.exe" -datadir=d:\blockchains\%n% -conf=daemon.conf -txindex -reindex -rescan



pause