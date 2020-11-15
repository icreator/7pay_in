

rem timeout /t 5
rem https://sourceforge.net/projects/novacoin/files/

rem ================== Bitcoin start
tasklist | find /I "novacoin-qt.exe"
if %errorlevel%==1 start "novacoin-qt.exe" /MIN "C:\Program Files (x86)\NovaCoin\novacoin-qt.exe" -conf=daemon_not_note.conf -txindex=1



timeout /t 122

tasklist | find /I "novacoin-qt.exe"
if %errorlevel%==1 start "novacoin-qt.exe" /MIN "C:\Program Files (x86)\NovaCoin\novacoin-qt.exe" -conf=daemon_not_note.conf -reindex -txindex=1

pause
