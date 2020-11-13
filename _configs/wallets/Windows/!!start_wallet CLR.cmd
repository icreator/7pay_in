

rem timeout /t 5
rem https://sourceforge.net/projects/novacoin/files/

rem =========================
tasklist | find /I "CopperLark.exe"
if %errorlevel%==1 start "CopperLark.exe" /MIN "C:\Program Files (x86)\CopperLark\CopperLark.exe" -conf=daemon.conf -txindex=1

pause


timeout /t 122

rem =========================
tasklist | find /I "CopperLark.exe"
if %errorlevel%==1 start "CopperLark.exe" /MIN "C:\Program Files (x86)\CopperLark\CopperLark.exe" -conf=daemon.conf -reindex -txindex=1

pause
