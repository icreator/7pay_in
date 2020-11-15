rem 
rem if NOT "%3"=="test" @echo off
if "%1"=="reload" goto reload1

@echo ... >>!Started_log.txt
@time /T >>!Started_log.txt
@date /T >>!Started_log.txt

:start /? >!start.txt
rem clear block_proc .locks!
@del /Q .lock_* >nul


cd DAT
for /D %%i in (*) do ( 
echo %%i
rem dir %AppData%\%%i\wallet.dat
copy %AppData%\%%i\wallet.dat %%i\
copy D:\blockchains\%%i\wallet.dat %%i\
del %AppData%\%%i\debug.*
del D:\blockchains\%%i\debug.*
)
cd ..


timeout /t 5
:reload1

rem ================== Bitcoin start
set p=C:\Program Files\Bitcoin\daemon\
set name=bitcoin

tasklist | findstr /b /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%name%d" -conf=daemon.conf -txindex=1


rem =========================
set p=C:\Program Files\Litecoin\daemon
set exe=litecoind
set name=litecoin
set ddir=-datadir=d:\blockchains\Litecoin
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon.conf -txindex=1



rem =========================
set n=dogecoin
tasklist | findstr /b /I "%n%"
if %errorlevel%==1 start "%n%" /MIN "C:\Program Files\%n%\daemon\%n%d.exe" -datadir=d:\blockchains\%n% -conf=daemon.conf -txindex=1


set p=C:\Program Files\Dash
set exe=dash-qt
set name=dash
set ddir=-datadir=d:\blockchains\Dash
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon.conf -txindex=1


goto cont1



rem if "%1"=="reload" pause
if "%1"=="reload" exit


:cont1

rem если реиндекс нужен и кошель свалился то запустим с ним
timeout /t 122

rem ================== Bitcoin start
set p=C:\Program Files\Bitcoin\daemon\
set name=bitcoin

tasklist | findstr /b /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%%name%d" -conf=daemon.conf -txindex=1 -reindex

rem =========================
set p=C:\Program Files\Litecoin\daemon
set exe=litecoind
set name=litecoin
set ddir=-datadir=d:\blockchains\Litecoin
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon.conf -txindex=1 -reindex


rem =========================
set n=dogecoin
tasklist | findstr /b /I "%n%"
if %errorlevel%==1 start "%n%" /MIN "C:\Program Files\%n%\daemon\%n%d.exe" -datadir=d:\blockchains\%n% -conf=daemon.conf -txindex -reindex -rescan


set p=C:\Program Files\Dash
set exe=dash-qt
set name=dash
set ddir=-datadir=d:\blockchains\Dash
tasklist | find /I "%name%"
if %errorlevel%==1 start "%name%" /MIN "%p%\%exe%.exe" %ddir% -conf=daemon.conf -txindex=1 -reindex

:end1
goto end




:pause

:end