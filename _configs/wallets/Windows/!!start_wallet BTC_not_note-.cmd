

rem timeout /t 5


rem ================== Bitcoin start
tasklist | find /I "bitcoin-qt.exe"

REM rescan
REM if %errorlevel%==1 start "bitcoin-qt.exe" /MIN "C:\Program Files\Bitcoin\bitcoin-qt.exe" -conf=daemon_not_note.conf -txindex=1 -rescan=1

if %errorlevel%==1 start "bitcoin-qt.exe" /MIN "C:\Program Files\Bitcoin\bitcoin-qt.exe" -conf=daemon_not_note.conf -txindex=1

pause


timeout /t 122

tasklist | find /I "bitcoin-qt.exe"
if %errorlevel%==1 start "bitcoin-qt.exe" /MIN "C:\Program Files\Bitcoin\bitcoin-qt.exe" -conf=daemon_not_note.conf -reindex -txindex=1

pause